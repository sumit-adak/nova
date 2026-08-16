"""Pydantic Settings configuration for NOVA."""
from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for NOVA application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="NOVA_",
        extra="ignore"
    )

    # General
    app_name: str = "NOVA"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".nova")
    db_filename: str = "nova.db"

    # Security & Path Allow-listing
    allowed_roots: list[str] = Field(
        default_factory=lambda: [
            str(Path.home()),
            str(Path.home() / "Desktop"),
            str(Path.home() / "Documents"),
            str(Path.home() / "Downloads"),
            str(Path.home() / "Projects"),
        ]
    )
    blocked_paths: list[str] = Field(
        default_factory=lambda: [
            "C:\\Windows",
            "C:\\Program Files",
            "C:\\Program Files (x86)",
            "C:\\System Volume Information",
        ]
    )

    # AI Configuration
    ai_provider: Literal["offline", "openai", "gemini", "anthropic", "local"] = "offline"
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    local_model_endpoint: str = "http://localhost:11434/v1"
    openai_model: str = "gpt-4o"
    gemini_model: str = "gemini-2.0-flash"
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    # Voice / Audio Configuration
    voice_enabled: bool = True
    tts_enabled: bool = True
    stt_provider: Literal["whisper_local", "cloud", "speech_recognition"] = "speech_recognition"
    tts_provider: Literal["edge_tts", "piper", "pyttsx3"] = "pyttsx3"
    voice_rate: int = 175
    voice_volume: float = 1.0

    # System & Monitoring
    monitor_interval_sec: float = 2.0
    cpu_high_threshold: float = 90.0
    ram_high_threshold: float = 90.0
    battery_low_threshold: float = 20.0

    # Browser & Dev Tools
    default_browser: Literal["chrome", "edge", "firefox", "default"] = "chrome"
    vscode_path: str | None = None

    @property
    def db_path(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir / self.db_filename

    @property
    def db_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.db_path.as_posix()}"

    @property
    def logs_dir(self) -> Path:
        path = self.data_dir / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path


_settings_instance: Settings | None = None


def get_settings() -> Settings:
    """Get or create singleton Settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
