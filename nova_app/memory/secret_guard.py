"""Secret Guard preventing sensitive credentials from entering SQLite memory tables."""
import structlog
from nova_app.ai_engine.redaction import get_redaction_engine
from nova_app.core.exceptions import SecurityError

logger = structlog.get_logger(__name__)


class SecretGuard:
    """Scans and blocks storing passwords, API keys, private keys, or tokens in memory."""

    def __init__(self):
        self.redactor = get_redaction_engine()

    def validate_content(self, key: str, value: str) -> None:
        """
        Validate memory key and value.
        Raises SecurityError if a secret pattern or credential is detected.
        """
        # Check key
        key_lower = key.lower()
        if any(term in key_lower for term in ["password", "secret", "api_key", "token", "private_key", "credential"]):
            raise SecurityError(
                f"Memory key '{key}' appears to refer to a secret or credential and cannot be stored."
            )

        # Check value using RedactionEngine
        if self.redactor.contains_secrets(value):
            raise SecurityError(
                f"Memory value for key '{key}' contains sensitive credentials (API key/token/private key) and cannot be stored."
            )


_secret_guard_instance: SecretGuard | None = None


def get_secret_guard() -> SecretGuard:
    """Get singleton SecretGuard instance."""
    global _secret_guard_instance
    if _secret_guard_instance is None:
        _secret_guard_instance = SecretGuard()
    return _secret_guard_instance
