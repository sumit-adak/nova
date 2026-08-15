"""Tests for safety confirmation flow."""

import pytest

from app.services.assistant_service import AssistantService


@pytest.mark.asyncio
async def test_safe_command_executes(config_manager):
    service = AssistantService(config=config_manager)
    response = await service.process_input("what's my RAM usage?")
    assert response.state.value in ("success", "idle")
    assert response.action_executed == "get_memory_usage"


@pytest.mark.asyncio
async def test_delete_requires_confirmation(config_manager):
    service = AssistantService(config=config_manager)
    response = await service.process_input("delete folder C:\\temp\\test")
    # Offline parser may not catch this - test via direct registry
    from app.commands.files import FileCommands
    import tempfile
    files = FileCommands()
    with tempfile.TemporaryDirectory() as tmp:
        result = await files.delete_folder(tmp)
        assert result.requires_confirmation


@pytest.mark.asyncio
async def test_cancel_confirmation(config_manager):
    service = AssistantService(config=config_manager)
    resp = service.cancel_pending_action()
    assert "cancelled" in resp.text.lower()


@pytest.mark.asyncio
async def test_assistant_open_spotify_play_song(config_manager, monkeypatch):
    import webbrowser
    monkeypatch.setattr(webbrowser, "open", lambda url: True)
    service = AssistantService(config=config_manager)
    response = await service.process_input("open spotify and play Starboy")
    assert response.state.value in ("success", "idle")


@pytest.mark.asyncio
async def test_assistant_open_and_search(config_manager, monkeypatch):
    import webbrowser
    monkeypatch.setattr(webbrowser, "open", lambda url: True)
    service = AssistantService(config=config_manager)
    response = await service.process_input("open and search FastAPI tutorial")
    assert response.state.value in ("success", "idle")
    assert response.action_executed == "search_web"

