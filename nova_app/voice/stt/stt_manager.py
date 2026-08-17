"""Speech-to-Text Manager coordinating microphone inputs and async transcription."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import structlog
from nova_app.config.settings import Settings, get_settings
from nova_app.core.events import get_event_bus
from nova_app.voice.models import VoiceListeningEvent, VoiceTranscribedEvent
from nova_app.voice.stt.base import STTEngine
from nova_app.voice.stt.speech_recognition_engine import SpeechRecognitionEngine

logger = structlog.get_logger(__name__)


class STTManager:
    """Manages audio listening and async transcription."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._engine: STTEngine = SpeechRecognitionEngine()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="nova_stt")

    def is_available(self) -> bool:
        return self._engine.is_available()

    async def listen_and_transcribe_async(self, timeout_sec: float = 5.0) -> str:
        """Listen asynchronously without blocking the event loop."""
        get_event_bus().publish_sync(VoiceListeningEvent(is_listening=True))

        loop = asyncio.get_running_loop()
        try:
            transcript = await loop.run_in_executor(
                self._executor,
                self._engine.listen_and_transcribe,
                timeout_sec
            )
            if transcript:
                get_event_bus().publish_sync(
                    VoiceTranscribedEvent(transcript=transcript)
                )
            return transcript
        finally:
            get_event_bus().publish_sync(VoiceListeningEvent(is_listening=False))


_stt_manager_instance: STTManager | None = None


def get_stt_manager() -> STTManager:
    """Get singleton STTManager instance."""
    global _stt_manager_instance
    if _stt_manager_instance is None:
        _stt_manager_instance = STTManager()
    return _stt_manager_instance
