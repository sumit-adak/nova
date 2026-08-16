"""NOVA core exceptions hierarchy."""

class NovaError(Exception):
    """Base exception for all NOVA errors."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SecurityError(NovaError):
    """Raised when a security boundary is violated (e.g. path traversal, secret leakage)."""
    pass


class PermissionDeniedError(NovaError):
    """Raised when an action is rejected by the permission engine or user confirmation."""
    pass


class ToolExecutionError(NovaError):
    """Raised when an approved tool executor fails during execution."""
    pass


class ValidationError(NovaError):
    """Raised when tool arguments or schemas fail validation."""
    pass


class EmergencyStopActiveError(SecurityError):
    """Raised when an action is blocked because Emergency Stop kill-switch is engaged."""
    pass
