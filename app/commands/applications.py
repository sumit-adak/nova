"""Application launcher commands."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from app.commands.registry import ActionResult
from app.core.config import ConfigManager
from app.core.logger import get_logger

logger = get_logger("applications")


class ApplicationLauncher:
    """Launch configured Windows applications safely."""

    ALIASES: dict[str, str] = {
        "chrome": "chrome",
        "google chrome": "chrome",
        "edge": "edge",
        "microsoft edge": "edge",
        "firefox": "firefox",
        "vscode": "vscode",
        "vs code": "vscode",
        "visual studio code": "vscode",
        "code": "vscode",
        "terminal": "terminal",
        "windows terminal": "terminal",
        "wt": "terminal",
        "powershell": "powershell",
        "pwsh": "powershell",
        "notepad": "notepad",
        "calculator": "calculator",
        "calc": "calculator",
        "explorer": "explorer",
        "file explorer": "explorer",
        "task manager": "taskmanager",
        "taskmanager": "taskmanager",
        "discord": "discord",
        "spotify": "spotify",
        "jupyter": "jupyter",
        "jupyter notebook": "jupyter",
    }

    def __init__(self, config: ConfigManager) -> None:
        self.config = config

    def resolve_alias(self, app_name: str) -> str:
        """Resolve application alias to canonical key."""
        key = app_name.lower().strip()
        return self.ALIASES.get(key, key)

    def find_executable(self, app_key: str) -> tuple[str | None, dict[str, Any]]:
        """Find executable path for an application."""
        apps = self.config.load_applications()
        app_config = apps.get(app_key)
        if not app_config:
            return None, {}

        for path_str in app_config.get("paths", []):
            path = Path(path_str)
            if path.exists():
                return str(path), app_config

        command = app_config.get("command")
        if command:
            return command, app_config

        return None, app_config

    def is_available(self, app_key: str) -> bool:
        """Check if application is installed."""
        exe, _ = self.find_executable(app_key)
        return exe is not None

    async def open_application(self, app: str, args: str = "") -> ActionResult:
        """Launch an application by name."""
        app_key = self.resolve_alias(app)
        exe, config = self.find_executable(app_key)

        if not exe:
            name = config.get("name", app)
            return ActionResult(
                success=False,
                message=(
                    f"{name} wasn't found. Please configure its installation path in Settings."
                ),
            )

        try:
            launch_args = config.get("args", "")
            if "command" in config and not Path(exe).exists():
                cmd = f'{exe} {args} {launch_args}'.strip()
                subprocess.Popen(cmd, shell=True)
            else:
                cmd_args = [exe]
                if launch_args:
                    cmd_args.extend(launch_args.split())
                if args:
                    cmd_args.extend(args.split())
                subprocess.Popen(cmd_args)

            display_name = config.get("name", app_key)
            logger.info("Launched application: %s", display_name)
            return ActionResult(
                success=True,
                message=f"Opened {display_name}.",
                data={"app": app_key},
            )
        except OSError as exc:
            logger.error("Failed to launch %s: %s", app_key, exc)
            return ActionResult(success=False, message=f"Failed to open {app}: {exc}")

    async def close_application(self, app: str) -> ActionResult:
        """Close an application by process name."""
        app_key = self.resolve_alias(app)
        process_names = {
            "chrome": "chrome.exe",
            "edge": "msedge.exe",
            "firefox": "firefox.exe",
            "vscode": "Code.exe",
            "terminal": "WindowsTerminal.exe",
            "notepad": "notepad.exe",
            "discord": "Discord.exe",
            "spotify": "Spotify.exe",
        }
        proc_name = process_names.get(app_key, f"{app_key}.exe")

        try:
            result = subprocess.run(
                ["taskkill", "/IM", proc_name, "/F"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return ActionResult(success=True, message=f"Closed {app}.")
            return ActionResult(
                success=False,
                message=f"Could not close {app}. It may not be running.",
            )
        except subprocess.TimeoutExpired:
            return ActionResult(success=False, message=f"Timeout closing {app}.")
