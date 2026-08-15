"""Application configuration management."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.logger import get_logger

logger = get_logger("config")

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"


class Settings(BaseSettings):
    """Environment-based settings loaded from .env."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    nova_ai_provider: str = Field(default="offline", alias="NOVA_AI_PROVIDER")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.7-flash", alias="GEMINI_MODEL")
    nova_log_level: str = Field(default="INFO", alias="NOVA_LOG_LEVEL")
    nova_default_browser: str = Field(default="chrome", alias="NOVA_DEFAULT_BROWSER")
    nova_voice_enabled: bool = Field(default=True, alias="NOVA_VOICE_ENABLED")
    nova_tts_enabled: bool = Field(default=True, alias="NOVA_TTS_ENABLED")


class ConfigManager:
    """Manages persistent JSON configuration files."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.settings_path = self.data_dir / "settings.json"
        self.projects_path = self.data_dir / "projects.json"
        self.apps_path = self.data_dir / "applications.json"
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        """Create default config files if missing."""
        if not self.settings_path.exists():
            self.save_settings(self.default_settings())
        if not self.projects_path.exists():
            self.save_projects(self.default_projects())
        if not self.apps_path.exists():
            self.save_applications(self.default_applications())

    @staticmethod
    def default_settings() -> dict[str, Any]:
        username = os.environ.get("USERNAME", "User")
        return {
            "preferred_name": username,
            "voice_enabled": True,
            "tts_enabled": True,
            "wake_word_enabled": False,
            "wake_word": "hey nova",
            "theme": "dark",
            "accent_color": "#9B59B6",
            "secondary_color": "#E67E22",
            "startup_page": "dashboard",
            "default_browser": "chrome",
            "default_editor": "vscode",
            "default_terminal": "terminal",
            "confirm_destructive": True,
            "offline_mode": False,
        }

    @staticmethod
    def default_projects() -> dict[str, str]:
        home = Path.home()
        desktop = home / "Desktop"
        return {
            "PlantGuard": str(desktop / "PlantGuard-AI"),
            "Portfolio": str(desktop / "Portfolio"),
            "Railway": str(desktop / "Railway"),
        }

    @staticmethod
    def default_applications() -> dict[str, dict[str, str]]:
        """Default application launcher configuration."""
        local = os.environ.get("LOCALAPPDATA", "")
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")

        return {
            "chrome": {
                "name": "Google Chrome",
                "paths": [
                    f"{program_files}\\Google\\Chrome\\Application\\chrome.exe",
                    f"{program_files_x86}\\Google\\Chrome\\Application\\chrome.exe",
                ],
            },
            "edge": {
                "name": "Microsoft Edge",
                "paths": [
                    f"{program_files}\\Microsoft\\Edge\\Application\\msedge.exe",
                ],
            },
            "firefox": {
                "name": "Mozilla Firefox",
                "paths": [
                    f"{program_files}\\Mozilla Firefox\\firefox.exe",
                    f"{program_files_x86}\\Mozilla Firefox\\firefox.exe",
                ],
            },
            "vscode": {
                "name": "Visual Studio Code",
                "paths": [
                    f"{local}\\Programs\\Microsoft VS Code\\Code.exe",
                    f"{program_files}\\Microsoft VS Code\\Code.exe",
                ],
            },
            "terminal": {
                "name": "Windows Terminal",
                "paths": [
                    f"{local}\\Microsoft\\WindowsApps\\wt.exe",
                    f"{local}\\Microsoft\\WindowsApps\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\wt.exe",
                ],
            },
            "powershell": {
                "name": "PowerShell",
                "paths": [
                    f"{program_files}\\PowerShell\\7\\pwsh.exe",
                    "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                ],
            },
            "notepad": {
                "name": "Notepad",
                "paths": ["C:\\Windows\\System32\\notepad.exe"],
            },
            "calculator": {
                "name": "Calculator",
                "paths": ["C:\\Windows\\System32\\calc.exe"],
            },
            "explorer": {
                "name": "File Explorer",
                "paths": ["C:\\Windows\\explorer.exe"],
            },
            "taskmanager": {
                "name": "Task Manager",
                "paths": ["C:\\Windows\\System32\\Taskmgr.exe"],
            },
            "discord": {
                "name": "Discord",
                "paths": [
                    f"{local}\\Discord\\Update.exe",
                    f"{local}\\Discord\\app-1.0.9003\\Discord.exe",
                ],
                "args": "--processStart Discord.exe",
            },
            "spotify": {
                "name": "Spotify",
                "paths": [
                    f"{local}\\Microsoft\\WindowsApps\\Spotify.exe",
                    f"{local}\\Spotify\\Spotify.exe",
                ],
            },
            "jupyter": {
                "name": "Jupyter Notebook",
                "paths": [],
                "command": "jupyter notebook",
            },
        }

    def load_json(self, path: Path) -> dict[str, Any]:
        """Load JSON file safely."""
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load %s: %s", path, exc)
            return {}

    def save_json(self, path: Path, data: dict[str, Any]) -> None:
        """Save JSON file atomically."""
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp")
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        temp.replace(path)

    def load_settings(self) -> dict[str, Any]:
        return self.load_json(self.settings_path)

    def save_settings(self, settings: dict[str, Any]) -> None:
        self.save_json(self.settings_path, settings)

    def load_projects(self) -> dict[str, str]:
        return self.load_json(self.projects_path)

    def save_projects(self, projects: dict[str, str]) -> None:
        self.save_json(self.projects_path, projects)

    def load_applications(self) -> dict[str, dict[str, str]]:
        return self.load_json(self.apps_path)

    def save_applications(self, apps: dict[str, dict[str, str]]) -> None:
        self.save_json(self.apps_path, apps)


def get_settings() -> Settings:
    """Return environment settings singleton."""
    return Settings()

def get_config_manager() -> ConfigManager:
    """Return config manager singleton."""
    return ConfigManager()
