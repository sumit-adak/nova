"""Unit tests for Phase 6: Voice Interface (STT, TTS, Interruption, Orchestrator)."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from nova_app.voice.models import (
    VoiceListeningEvent,
    VoiceSpeakingEvent,
    VoiceStoppedEvent,
    VoiceTranscribedEvent,
)
from nova_app.voice.orchestrator import VoiceOrchestrator
from nova_app.voice.stt.stt_manager import STTManager
from nova_app.voice.tts.tts_manager import TTSManager


@pytest.mark.asyncio
async def test_stt_manager_listen_and_transcribe():
    stt = STTManager()

    # Mock underlying engine
    mock_engine = MagicMock()
    mock_engine.is_available.return_value = True
    mock_engine.listen_and_transcribe.return_value = "how much ram is free"
    stt._engine = mock_engine

    transcript = await stt.listen_and_transcribe_async(timeout_sec=1.0)
    assert transcript == "how much ram is free"
    mock_engine.listen_and_transcribe.assert_called_once_with(1.0)


@pytest.mark.asyncio
async def test_tts_manager_speak_and_interruption():
    tts = TTSManager()

    mock_engine = MagicMock()
    tts._engine = mock_engine

    # Speak
    await tts.speak_async("Hello! I am NOVA.")
    mock_engine.speak.assert_called_once()

    # Interrupt / Stop
    tts.stop()
    mock_engine.stop.assert_called_once()
    assert tts.is_speaking is False


@pytest.mark.asyncio
async def test_voice_orchestrator_push_to_talk_cycle():
    orchestrator = VoiceOrchestrator()

    # Mock STT to return a valid command
    orchestrator.stt.listen_and_transcribe_async = AsyncMock(return_value="how much ram is free")
    orchestrator.tts.speak_async = AsyncMock()

    turn = await orchestrator.handle_push_to_talk_turn(timeout_sec=1.0)

    assert turn is not None
    assert turn.user_input == "how much ram is free"
    assert len(turn.tool_calls) == 1
    assert turn.tool_calls[0].tool_name == "get_system_stats"
    assert turn.tool_results[0].success is True

    # Check TTS was called with response
    orchestrator.tts.speak_async.assert_called_once()
