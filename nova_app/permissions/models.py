"""Pydantic models for permissions and confirmation requests."""
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
from nova_app.permissions.policy import PolicyDecision, RiskTier


class PermissionEvaluation(BaseModel):
    """Result of evaluating a tool call against permission policy."""
    tool_name: str
    risk_tier: RiskTier
    decision: PolicyDecision
    reason: str
    requires_confirmation: bool = False


class ConfirmationRequest(BaseModel):
    """Pending confirmation item for user approval."""
    id: str
    tool_name: str
    arguments: dict[str, Any]
    risk_tier: RiskTier
    reasoning: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    timeout_sec: float = 60.0
