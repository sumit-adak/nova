"""Permission and safety evaluation engine."""
from nova_app.core.exceptions import EmergencyStopActiveError, PermissionDeniedError
from nova_app.permissions.grants_manager import get_grants_manager
from nova_app.permissions.models import PermissionEvaluation
from nova_app.permissions.policy import DEFAULT_TIER_POLICIES, PolicyDecision, RiskTier
from nova_app.permissions.rate_limiter import get_rate_limiter
from nova_app.security.emergency_stop import get_emergency_stop


class PermissionEngine:
    """Evaluates whether a proposed tool call can execute automatically, needs confirmation, or is denied."""

    def __init__(self):
        self._custom_policies: dict[str, PolicyDecision] = {}

    def set_tool_policy(self, tool_name: str, decision: PolicyDecision) -> None:
        """Override policy for a specific tool."""
        self._custom_policies[tool_name] = decision

    async def evaluate(self, tool_name: str, risk_tier: RiskTier) -> PermissionEvaluation:
        """
        Evaluate tool execution:
        1. Emergency Stop check (blocks all mutating/non-READ actions)
        2. Rate limiter check (raises SecurityError if flooded)
        3. Standing permission grants check (allows execution if granted for session/unexpired)
        4. Custom policy overrides check
        5. Default risk tier policy check
        """
        emergency_stop = get_emergency_stop()

        # 1. Emergency Stop check: blocks all non-READ operations immediately
        if emergency_stop.is_active and risk_tier != RiskTier.READ:
            raise EmergencyStopActiveError(
                f"Action '{tool_name}' blocked because Emergency Stop is active: {emergency_stop.reason}"
            )

        # 2. Rate limiter check
        get_rate_limiter().check_and_record(tool_name, risk_tier)

        # 3. Check standing grants (session or DB)
        grants_mgr = get_grants_manager()
        if await grants_mgr.has_active_grant(tool_name):
            return PermissionEvaluation(
                tool_name=tool_name,
                risk_tier=risk_tier,
                decision=PolicyDecision.ALLOW,
                reason="Active standing permission grant found",
                requires_confirmation=False,
            )

        # 4. Check custom tool override
        if tool_name in self._custom_policies:
            decision = self._custom_policies[tool_name]
            return PermissionEvaluation(
                tool_name=tool_name,
                risk_tier=risk_tier,
                decision=decision,
                reason=f"Custom policy rule applied: {decision.value}",
                requires_confirmation=(decision == PolicyDecision.CONFIRM),
            )

        # 5. Default tier policy
        decision = DEFAULT_TIER_POLICIES.get(risk_tier, PolicyDecision.CONFIRM)
        return PermissionEvaluation(
            tool_name=tool_name,
            risk_tier=risk_tier,
            decision=decision,
            reason=f"Default {risk_tier.value} tier policy applied",
            requires_confirmation=(decision == PolicyDecision.CONFIRM),
        )


_permission_engine_instance: PermissionEngine | None = None


def get_permission_engine() -> PermissionEngine:
    """Get singleton PermissionEngine instance."""
    global _permission_engine_instance
    if _permission_engine_instance is None:
        _permission_engine_instance = PermissionEngine()
    return _permission_engine_instance
