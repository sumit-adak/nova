"""Pydantic schemas for Tool calls, Tool results, and tool definitions."""
from datetime import datetime, timezone
from typing import Any, Callable, Type
from pydantic import BaseModel, Field
from nova_app.permissions.policy import RiskTier


class ToolCall(BaseModel):
    """Structured tool invocation request."""
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    reasoning: str | None = None
    requires_confirmation: bool = False


class ToolResult(BaseModel):
    """Structured result returned by tool execution."""
    tool_name: str
    success: bool
    data: Any = None
    error: str | None = None
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolDefinition(BaseModel):
    """Definition of a registered tool."""
    name: str
    description: str
    risk_tier: RiskTier
    arg_schema: Type[BaseModel]
    executor: Callable[..., Any]
    allow_offline: bool = True

    model_config = {
        "arbitrary_types_allowed": True
    }
