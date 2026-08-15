"""Tests for configuration."""

from app.core.config import ConfigManager, Settings


def test_default_projects(config_manager):
    projects = config_manager.load_projects()
    assert "PlantGuard" in projects


def test_save_and_load_settings(config_manager):
    settings = config_manager.load_settings()
    settings["preferred_name"] = "TestUser"
    config_manager.save_settings(settings)
    loaded = config_manager.load_settings()
    assert loaded["preferred_name"] == "TestUser"


def test_settings_env_defaults():
    settings = Settings()
    assert settings.nova_ai_provider in ("offline", "openai", "gemini")
