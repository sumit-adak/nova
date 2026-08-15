"""Assistant state management."""

from enum import Enum


class AssistantState(str, Enum):
    """Visual and operational states for the NOVA assistant."""

    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    EXECUTING = "executing"
    SUCCESS = "success"
    ERROR = "error"
    CONFIRMATION_REQUIRED = "confirmation_required"


class PermissionLevel(str, Enum):
    """Safety permission levels for registered actions."""

    SAFE = "safe"
    CONFIRMATION_REQUIRED = "confirmation_required"
    NEVER = "never"
