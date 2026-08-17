"""Unit tests for Phase 2: AI Brain, Redaction, Providers, Tool Planner, and Conversation Manager."""
import pytest
from unittest.mock import AsyncMock, patch
from nova_app.ai_engine.intent_engine import IntentEngine
from nova_app.ai_engine.provider_base import AIIntentResponse, LLMProvider
from nova_app.ai_engine.redaction import RedactionEngine
from nova_app.conversation.manager import ConversationManager
from nova_app.conversation.session import ConversationSession
from nova_app.tools.planner import ToolPlanner
from nova_app.tools.schema import ToolCall


def test_redaction_engine_strips_secrets():
    redactor = RedactionEngine()

    sample_prompt = "My OpenAI key is sk-1234567890abcdef1234567890 and my github token is ghp_1234567890abcdef1234567890abcdef1234"
    assert redactor.contains_secrets(sample_prompt) is True

    redacted = redactor.redact(sample_prompt)
    assert "sk-1234567890abcdef" not in redacted
    assert "ghp_1234567890" not in redacted
    assert "[REDACTED_" in redacted


def test_redaction_engine_benign_text():
    redactor = RedactionEngine()
    benign = "Hello NOVA, please open notepad and show me my CPU usage."
    assert redactor.contains_secrets(benign) is False
    assert redactor.redact(benign) == benign


@pytest.mark.asyncio
async def test_intent_engine_offline_routing():
    engine = IntentEngine()
    resp = await engine.analyze_intent([{"role": "user", "content": "how much ram is free"}])

    assert isinstance(resp, AIIntentResponse)
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].tool_name == "get_system_stats"


@pytest.mark.asyncio
async def test_tool_planner_fuzzy_resolution():
    planner = ToolPlanner()
    calls = [
        ToolCall(tool_name="open_file", arguments={"path": "nonexistent_resume.pdf"}),
        ToolCall(tool_name="open_application", arguments={"app_name": "notepad"}),
    ]

    refined = await planner.plan_and_refine(calls)
    assert len(refined) == 2
    assert refined[1].arguments["app_name"] == "notepad"


@pytest.mark.asyncio
async def test_conversation_manager_end_to_end_turn():
    manager = ConversationManager()
    turn = await manager.process_user_input("how much ram is free")

    assert turn.id is not None
    assert turn.user_input == "how much ram is free"
    assert len(turn.tool_calls) == 1
    assert turn.tool_calls[0].tool_name == "get_system_stats"
    assert len(turn.tool_results) == 1
    assert turn.tool_results[0].success is True
    assert "ram" in turn.tool_results[0].data


@pytest.mark.asyncio
async def test_multi_turn_session_context():
    session = ConversationSession(session_id=1, title="Test")
    session.add_turn(
        turn=pytest.importorskip("nova_app.conversation.models").ConversationTurn(
            id="1",
            user_input="Hello",
            assistant_response="Hi! How can I help?"
        )
    )
    messages = session.to_message_list()
    assert len(messages) == 2
    assert messages[0]["content"] == "Hello"
    assert messages[1]["content"] == "Hi! How can I help?"
