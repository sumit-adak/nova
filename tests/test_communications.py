"""Tests for communication commands: WhatsApp, Email, and File sharing."""

import pytest
from app.commands.communications import CommunicationCommands


@pytest.fixture
def comms(config_manager):
    return CommunicationCommands(config_manager)


@pytest.mark.asyncio
async def test_send_whatsapp_message(comms, monkeypatch):
    import webbrowser
    opened_urls = []
    monkeypatch.setattr(webbrowser, "open", lambda url: opened_urls.append(url))

    result = await comms.send_whatsapp_message(
        phone="+1234567890",
        message="Hello from NOVA",
        auto_send=False,
    )
    assert result.success
    assert "WhatsApp" in result.message
    assert result.data["phone"] == "1234567890"
    assert result.data["message"] == "Hello from NOVA"


@pytest.mark.asyncio
async def test_send_whatsapp_empty_phone(comms):
    result = await comms.send_whatsapp_message(phone="", message="Hello")
    assert not result.success
    assert "phone number" in result.message.lower()


@pytest.mark.asyncio
async def test_open_whatsapp(comms, monkeypatch):
    import webbrowser
    monkeypatch.setattr(webbrowser, "open", lambda url: True)

    result = await comms.open_whatsapp()
    assert result.success
    assert "WhatsApp" in result.message


@pytest.mark.asyncio
async def test_send_email(comms, monkeypatch):
    import webbrowser
    opened_urls = []
    monkeypatch.setattr(webbrowser, "open", lambda url: opened_urls.append(url))

    result = await comms.send_email(
        to="test@example.com",
        subject="Project Update",
        body="All systems nominal.",
    )
    assert result.success
    assert "test@example.com" in result.message
    assert result.data["to"] == "test@example.com"
    assert result.data["subject"] == "Project Update"


@pytest.mark.asyncio
async def test_send_file_nonexistent(comms):
    result = await comms.send_file(
        path="nonexistent_file_xyz123.pdf",
        recipient="user@example.com",
        channel="email",
    )
    assert not result.success
    assert "not found" in result.message.lower()


@pytest.mark.asyncio
async def test_send_file_existing(comms, tmp_path, monkeypatch):
    import webbrowser
    monkeypatch.setattr(webbrowser, "open", lambda url: True)

    test_file = tmp_path / "report.pdf"
    test_file.write_text("dummy content")

    result = await comms.send_file(
        path=str(test_file),
        recipient="manager@example.com",
        channel="email",
    )
    assert result.success
    assert "manager@example.com" in result.message
