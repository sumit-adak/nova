"""Visual Studio Code integration."""
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any
import structlog
from nova_app.config.settings import Settings, get_settings
from nova_app.core.exceptions import SecurityError
from nova_app.tools.validators.path_validator import get_path_validator

logger = structlog.get_logger(__name__)


class VSCodeClient:
    """Manages launching VS Code with project directories and files."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def find_vscode_executable(self) -> str | None:
        """Find VS Code binary path in PATH or standard installation directories."""
        if self.settings.vscode_path and Path(self.settings.vscode_path).is_file():
            return self.settings.vscode_path

        candidates = [
            shutil.which("code.cmd"),
            shutil.which("code.exe"),
            shutil.which("code"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd"),
            r"C:\Program Files\Microsoft VS Code\Code.exe",
            r"C:\Program Files\Microsoft VS Code\bin\code.cmd",
        ]

        for cand in candidates:
            if cand and Path(cand).exists():
                return str(cand)

        return "code"  # fallback to standard PATH call

    # Alias
    get_executable = find_vscode_executable

    def open_workspace(self, path: str | Path, file_to_open: str | None = None) -> dict[str, Any]:
        """Open a directory or file in VS Code."""
        validator = get_path_validator()
        valid_path = validator.validate_path(str(path))

        exec_bin = self.find_vscode_executable()

        cmd = [exec_bin, str(valid_path)]
        if file_to_open:
            file_path = validator.validate_path(str(file_to_open))
            cmd.append(str(file_path))

        subprocess.Popen(cmd, shell=False)
        logger.info("Launched VS Code", path=str(valid_path))

        return {
            "status": "opened_in_vscode",
            "path": str(valid_path),
            "binary": exec_bin,
        }


_vscode_client_instance: VSCodeClient | None = None


def get_vscode_client() -> VSCodeClient:
    """Get singleton VSCodeClient instance."""
    global _vscode_client_instance
    if _vscode_client_instance is None:
        _vscode_client_instance = VSCodeClient()
    return _vscode_client_instance
