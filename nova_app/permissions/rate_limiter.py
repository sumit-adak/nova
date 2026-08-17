"""Sliding-window rate limiter for tool executions."""
import time
from collections import defaultdict, deque
from nova_app.core.exceptions import SecurityError
from nova_app.permissions.policy import RiskTier


class RateLimiter:
    """Tracks and limits tool invocation frequency per risk tier and per tool."""

    def __init__(self):
        # Default max calls per minute per risk tier
        self.tier_limits = {
            RiskTier.READ: 120,      # 120 / min
            RiskTier.LOW: 60,        # 60 / min
            RiskTier.MEDIUM: 20,     # 20 / min
            RiskTier.HIGH: 5,        # 5 / min
            RiskTier.CRITICAL: 2,    # 2 / min
        }
        self._history: dict[str, deque[float]] = defaultdict(deque)

    def check_and_record(self, tool_name: str, risk_tier: RiskTier, window_seconds: float = 60.0) -> None:
        """
        Record an invocation and raise SecurityError if rate limit is exceeded.
        """
        now = time.monotonic()
        history = self._history[tool_name]

        # Purge entries outside window
        while history and now - history[0] > window_seconds:
            history.popleft()

        max_allowed = self.tier_limits.get(risk_tier, 10)
        if len(history) >= max_allowed:
            raise SecurityError(
                f"Rate limit exceeded for tool '{tool_name}' ({risk_tier.value} tier). "
                f"Limit is {max_allowed} calls per {int(window_seconds)}s."
            )

        history.append(now)

    def reset(self) -> None:
        """Clear all rate limit history."""
        self._history.clear()


_rate_limiter_instance: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Get singleton RateLimiter instance."""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RateLimiter()
    return _rate_limiter_instance
