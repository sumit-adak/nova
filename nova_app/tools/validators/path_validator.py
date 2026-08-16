"""Path validation and security boundary checks for NOVA."""
from pathlib import Path
from nova_app.config.settings import Settings, get_settings
from nova_app.core.exceptions import SecurityError


class PathValidator:
    """Validates filesystem paths against allow-listed roots and blocks traversal / system paths."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def validate_path(self, path_str: str, allow_create: bool = False) -> Path:
        """
        Validate and resolve a path.
        - Canonicalizes path using Path.resolve()
        - Checks for directory traversal attempts
        - Checks against blocked paths (e.g. C:\\Windows, C:\\Program Files)
        - Verifies the path falls within at least one allow-listed root
        """
        if not path_str or not path_str.strip():
            raise SecurityError("Path argument cannot be empty.")

        # Check for obvious traversal tokens before resolve
        raw_path = Path(path_str.strip())
        resolved = raw_path.resolve()

        resolved_str = str(resolved).lower()

        # 1. Check against blocked system paths
        for blocked in self.settings.blocked_paths:
            blocked_clean = str(Path(blocked).resolve()).lower()
            if resolved_str == blocked_clean or resolved_str.startswith(blocked_clean + "\\"):
                raise SecurityError(f"Access to protected system path '{resolved}' is blocked.")

        # 2. Check if path exists or parent exists if creating
        if not allow_create and not resolved.exists():
            raise FileNotFoundError(f"Path does not exist: '{resolved}'")

        # 3. Check against allowed roots
        is_allowed = False
        for allowed in self.settings.allowed_roots:
            allowed_clean = str(Path(allowed).resolve()).lower()
            if resolved_str == allowed_clean or resolved_str.startswith(allowed_clean + "\\"):
                is_allowed = True
                break

        if not is_allowed:
            raise SecurityError(
                f"Path '{resolved}' is outside allowed user roots. Allowed roots: {self.settings.allowed_roots}"
            )

        return resolved


_path_validator_instance: PathValidator | None = None


def get_path_validator() -> PathValidator:
    """Get singleton PathValidator instance."""
    global _path_validator_instance
    if _path_validator_instance is None:
        _path_validator_instance = PathValidator()
    return _path_validator_instance
