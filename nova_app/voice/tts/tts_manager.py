"""TTS Manager coordinating speech synthesis queues and interruption."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import structlog
from nova_app.config.settings import Settings, get_settings
from nova_app.core.events import get_event_bus
from nova_app.voice.models import VoiceSpeakingEvent, VoiceStoppedEvent
from nova_app.voice.tts.base import TTSEngine
from nova_app.voice.tts.pyttsx3_engine import Pyttsx3Engine

logger = structlog.get_logger(__name__)


class TTSManager:
    """Manages asynchronous speech playback and interruption."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._engine: TTSEngine = Pyttsx3Engine()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="nova_tts")
        self._is_speaking = False

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

    def stop(self) -> None:
        """Interrupt and stop current speech immediately."""
        self._engine.stop()
        self._is_speaking = False
        get_event_bus().publish_sync(VoiceStoppedEvent())
        logger.info("TTS playback stopped")

    async def speak_async(self, text: str) -> None:
        """Speak text asynchronously in background thread."""
        if not self.settings.tts_enabled or not text or not text.strip():
            return

        self._is_speaking = True
        get_event_bus().publish_sync(VoiceSpeakingEvent(text=text, is_speaking=True))

        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(
                self._executor,
                self._engine.speak,
                text,
                self.settings.voice_rate,
                self.settings.voice_volume,
            )
        finally:
            self._is_speaking = False
            get_event_bus().publish_sync(VoiceSpeakingEvent(text=text, is_speaking=False))


_tts_manager_instance: TTSManager | None = None


def get_tts_manager() -> TTSManager:
    """Get singleton TTSManager instance."""
    global _tts_manager_instance
    if _tts_manager_instance is None:
        _tts_manager_instance = TTSManager()
    return _tts_manager_instance
