"""Conversation models and turn execution data classes."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from nova_app.tools.schema import ToolCall, ToolResult


@dataclass
class ConversationTurn:
    """Represents a single user message and resulting assistant response/actions."""
    id: str
    user_input: str
    assistant_thought: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    assistant_response: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
