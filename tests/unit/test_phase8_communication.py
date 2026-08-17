"""Unit tests for Phase 8: Communication Automation (Email & Messaging)."""
import pytest
from unittest.mock import MagicMock, patch
from nova_app.integrations.content_generation.commit_message_writer import format_commit_message
from nova_app.integrations.content_generation.email_writer import draft_email_content
from nova_app.integrations.email.email_client import EmailClient, is_valid_email
from nova_app.integrations.messaging.clients import WhatsAppClient
from nova_app.tools.registry import ToolRegistry
from nova_app.tools.schema import ToolCall


def test_email_writer_drafting():
    # Absence email
    draft1 = draft_email_content(
        recipient="Prof. Davis",
        purpose="absent from lecture",
        context="mild fever",
        sender_name="Alex",
    )
    assert "Absence Notification" in draft1.subject
    assert "Prof. Davis" in draft1.body
    assert "mild fever" in draft1.body
    assert "Alex" in draft1.body

    # Follow-up email
    draft2 = draft_email_content(
        recipient="Sarah",
        purpose="follow-up",
        context="project roadmap",
        sender_name="Alex",
    )
    assert "Follow-up" in draft2.subject
    assert "project roadmap" in draft2.body


def test_commit_message_writer():
    msg1 = format_commit_message(change_type="feat", scope="auth", summary="add OAuth login")
    assert msg1 == "feat(auth): add OAuth login"

    msg2 = format_commit_message(
        change_type="fix",
        scope=None,
        summary="resolve memory leak",
        details=["cleanup DB connection pool", "close dangling file descriptors"]
    )
    assert "fix: resolve memory leak" in msg2
    assert "- cleanup DB connection pool" in msg2


def test_email_validation():
    assert is_valid_email("user@example.com") is True
    assert is_valid_email("alex.smith+tag@work.co.uk") is True
    assert is_valid_email("invalid-email") is False
    assert is_valid_email("@no-user.com") is False


def test_whatsapp_client_url_generation():
    client = WhatsAppClient()
    with patch("webbrowser.open") as mock_open:
        res = client.send_or_open_chat(phone_number="+1 (555) 123-4567", message="Hello from NOVA")
        assert res["status"] == "opened_web"
        assert "15551234567" in res["url"]
        assert "Hello%20from%20NOVA" in res["url"]
        mock_open.assert_called_once()


@pytest.mark.asyncio
async def test_communication_tools_confirmation_gating():
    registry = ToolRegistry()

    # draft_email is READ risk -> auto-allowed
    draft_call = ToolCall(
        tool_name="draft_email",
        arguments={
            "recipient": "Professor",
            "purpose": "sick leave",
            "context": "cold",
            "sender_name": "Student",
        }
    )
    res = await registry.execute_tool_call(draft_call, actor="test")
    assert res.success is True
    assert res.data["status"] == "drafted"

    # send_email is HIGH risk -> blocked without confirmation
    send_call = ToolCall(
        tool_name="send_email",
        arguments={"recipient": "boss@company.com", "subject": "Update", "body": "All done"}
    )
    send_res = await registry.execute_tool_call(send_call, confirmed_by_user=None, auto_prompt_confirmation=False)
    assert send_res.success is False
    assert "requires explicit user confirmation" in send_res.error

    # send_message is HIGH risk -> blocked without confirmation
    msg_call = ToolCall(
        tool_name="send_message",
        arguments={"platform": "whatsapp", "message": "Hi", "recipient": "+15551234567"}
    )
    msg_res = await registry.execute_tool_call(msg_call, confirmed_by_user=None, auto_prompt_confirmation=False)
    assert msg_res.success is False
    assert "requires explicit user confirmation" in msg_res.error
