"""Security utilities for path validation and input sanitization."""

import os
import re
from pathlib import Path


class SecurityError(Exception):
    """Raised when a security validation fails."""


def normalize_path(path: str | Path) -> Path:
    """Resolve and normalize a filesystem path."""
    return Path(path).expanduser().resolve()


def validate_path(path: str | Path, must_exist: bool = False) -> Path:
    """
    Validate a filesystem path for safe use.

    Raises SecurityError on path traversal or invalid paths.
    """
    if not path or not str(path).strip():
        raise SecurityError("Path cannot be empty")

    raw = str(path).strip()
    if ".." in raw.split(os.sep):
        raise SecurityError(f"Path traversal detected: {path}")

    try:
        resolved = normalize_path(raw)
    except (OSError, ValueError) as exc:
        raise SecurityError(f"Invalid path: {path}") from exc

    if must_exist and not resolved.exists():
        raise SecurityError(f"Path does not exist: {resolved}")

    return resolved


def validate_url(url: str) -> str:
    """Validate a URL for safe browser opening."""
    if not url or not url.strip():
        raise SecurityError("URL cannot be empty")

    cleaned = url.strip()
    if cleaned.startswith(("http://", "https://")):
        return cleaned
    if cleaned.startswith("localhost") or cleaned.startswith("127.0.0.1"):
        return f"http://{cleaned}"
    if re.match(r"^[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}", cleaned):
        return f"https://{cleaned}"
    raise SecurityError(f"Invalid URL: {url}")


def sanitize_filename(name: str) -> str:
    """Remove dangerous characters from filenames."""
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name.strip())
    if not sanitized:
        raise SecurityError("Invalid filename")
    return sanitized


def is_destructive_action(action: str) -> bool:
    """Check if an action requires user confirmation."""
    destructive = {
        "delete_file",
        "delete_folder",
        "move_files",
        "shutdown",
        "restart",
        "kill_process",
        "run_script",
        "install_software",
        "modify_system_settings",
    }
    return action in destructive
