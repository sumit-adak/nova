"""Voice Orchestrator managing Push-to-Talk, STT, AI processing, and TTS speech synthesis."""
import asyncio
import structlog
from nova_app.config.settings import Settings, get_settings
from nova_app.conversation.manager import get_conversation_manager
from nova_app.conversation.models import ConversationTurn
from nova_app.voice.stt.stt_manager import get_stt_manager
from nova_app.voice.tts.tts_manager import get_tts_manager

logger = structlog.get_logger(__name__)


class VoiceOrchestrator:
    """Coordinates Push-to-Talk audio capture, AI execution, and spoken response."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.stt = get_stt_manager()
        self.tts = get_tts_manager()
        self.conv_manager = get_conversation_manager()
        self._is_active = False

    def interrupt(self) -> None:
        """Interrupt active TTS speech synthesis."""
        self.tts.stop()

    async def handle_push_to_talk_turn(self, timeout_sec: float = 5.0) -> ConversationTurn | None:
        """
        Execute one full push-to-talk cycle:
        1. Capture speech from microphone and transcribe
        2. Process transcribed text via ConversationManager (same safety/tools pipeline as text)
        3. Speak the assistant's final response via TTS
        """
        self.interrupt()

        logger.info("Voice turn initiated")
        # 1. Listen & Transcribe
        transcript = await self.stt.listen_and_transcribe_async(timeout_sec=timeout_sec)
        if not transcript or not transcript.strip():
            logger.info("No speech detected or empty transcript")
            return None

        # 2. Process through unified ConversationManager pipeline
        turn = await self.conv_manager.process_user_input(
            user_text=transcript,
            auto_prompt_confirmation=True,
        )

        # 3. Speak assistant response if TTS is enabled
        if turn.assistant_response and self.settings.tts_enabled:
            asyncio.create_task(self.tts.speak_async(turn.assistant_response))

        return turn


_voice_orchestrator_instance: VoiceOrchestrator | None = None


def get_voice_orchestrator() -> VoiceOrchestrator:
    """Get singleton VoiceOrchestrator instance."""
    global _voice_orchestrator_instance
    if _voice_orchestrator_instance is None:
        _voice_orchestrator_instance = VoiceOrchestrator()
    return _voice_orchestrator_instance
