"""Tests for application launcher."""

import pytest

from app.commands.applications import ApplicationLauncher


def test_resolve_alias(config_manager):
    launcher = ApplicationLauncher(config_manager)
    assert launcher.resolve_alias("VS Code") == "vscode"
    assert launcher.resolve_alias("windows terminal") == "terminal"


def test_notepad_available(config_manager):
    launcher = ApplicationLauncher(config_manager)
    assert launcher.is_available("notepad")


def test_unknown_app(config_manager):
    launcher = ApplicationLauncher(config_manager)
    assert not launcher.is_available("nonexistent_app_xyz")
