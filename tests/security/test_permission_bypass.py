"""Security and permission bypass prevention tests."""
import asyncio
import pytest
from pydantic import BaseModel
from nova_app.core.exceptions import EmergencyStopActiveError, SecurityError
from nova_app.permissions.confirmation_queue import ConfirmationQueue
from nova_app.permissions.engine import PermissionEngine
from nova_app.permissions.grants_manager import GrantsManager
from nova_app.permissions.policy import PolicyDecision, RiskTier
from nova_app.security.emergency_stop import EmergencyStop
from nova_app.tools.registry import ToolRegistry
from nova_app.tools.schema import ToolCall, ToolDefinition
from nova_app.tools.validators.rate_limiter import RateLimiter


class DummyHighRiskArgs(BaseModel):
    target: str


def dummy_high_risk_executor(args: DummyHighRiskArgs):
    return {"executed": True, "target": args.target}


@pytest.mark.asyncio
async def test_high_risk_tool_blocked_without_confirmation():
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="dangerous_destructive_action",
            description="Dangerous test tool",
            risk_tier=RiskTier.HIGH,
            arg_schema=DummyHighRiskArgs,
            executor=dummy_high_risk_executor,
        )
    )

    call = ToolCall(tool_name="dangerous_destructive_action", arguments={"target": "system_db"})

    # Attempt execution without confirmation
    result = await registry.execute_tool_call(call, confirmed_by_user=None, auto_prompt_confirmation=False)
    assert result.success is False
    assert "requires explicit user confirmation" in result.error


@pytest.mark.asyncio
async def test_confirmation_queue_approval_and_denial():
    queue = ConfirmationQueue()

    # 1. Approval flow
    async def _approve_task():
        await asyncio.sleep(0.05)
        pending = queue.list_pending()
        assert len(pending) == 1
        queue.resolve_confirmation(pending[0].id, approved=True, remember_choice=True)

    task = asyncio.create_task(_approve_task())
    approved, remember = await queue.request_confirmation(
        tool_name="dangerous_destructive_action",
        arguments={"target": "val"},
        risk_tier=RiskTier.HIGH,
    )
    await task
    assert approved is True
    assert remember is True

    # 2. Denial flow
    async def _deny_task():
        await asyncio.sleep(0.05)
        pending = queue.list_pending()
        assert len(pending) == 1
        queue.resolve_confirmation(pending[0].id, approved=False)

    deny_task = asyncio.create_task(_deny_task())
    approved, remember = await queue.request_confirmation(
        tool_name="dangerous_destructive_action",
        arguments={"target": "val"},
        risk_tier=RiskTier.HIGH,
    )
    await deny_task
    assert approved is False


@pytest.mark.asyncio
async def test_confirmation_queue_timeout_auto_denies():
    queue = ConfirmationQueue()
    # Request with 0.1s timeout
    approved, _ = await queue.request_confirmation(
        tool_name="critical_tool",
        arguments={},
        risk_tier=RiskTier.CRITICAL,
        timeout_sec=0.1,
    )
    assert approved is False


@pytest.mark.asyncio
async def test_standing_session_grant():
    grants_mgr = GrantsManager()
    tool_name = "format_workspace"

    assert not grants_mgr.has_session_grant(tool_name)
    assert not await grants_mgr.has_active_grant(tool_name)

    grants_mgr.grant_for_session(tool_name)
    assert grants_mgr.has_session_grant(tool_name)
    assert await grants_mgr.has_active_grant(tool_name)

    grants_mgr.revoke_session_grant(tool_name)
    assert not grants_mgr.has_session_grant(tool_name)


def test_rate_limiter_exceeded():
    limiter = RateLimiter()
    limiter.tier_limits[RiskTier.HIGH] = 3

    # 3 calls should succeed
    limiter.check_and_record("delete_item", RiskTier.HIGH)
    limiter.check_and_record("delete_item", RiskTier.HIGH)
    limiter.check_and_record("delete_item", RiskTier.HIGH)

    # 4th call should raise SecurityError
    with pytest.raises(SecurityError, match="Rate limit exceeded"):
        limiter.check_and_record("delete_item", RiskTier.HIGH)


@pytest.mark.asyncio
async def test_emergency_stop_overrides_confirmed_actions():
    from nova_app.security.emergency_stop import get_emergency_stop
    stop = get_emergency_stop()
    stop.trigger("Test emergency lock")

    engine = PermissionEngine()
    with pytest.raises(EmergencyStopActiveError, match="Emergency Stop is active"):
        await engine.evaluate("delete_file", RiskTier.HIGH)

    stop.reset()
    # After reset, evaluation proceeds normally
    res = await engine.evaluate("delete_file", RiskTier.HIGH)
    assert res.requires_confirmation is True
