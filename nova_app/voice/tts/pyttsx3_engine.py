"""Offline Text-to-Speech Engine using pyttsx3 (Windows SAPI5)."""
import structlog
import pyttsx3
from nova_app.voice.tts.base import TTSEngine

logger = structlog.get_logger(__name__)


class Pyttsx3Engine(TTSEngine):
    """Offline TTS engine using Windows SAPI5 voice."""

    def __init__(self):
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            self._engine = pyttsx3.init()
        return self._engine

    def speak(self, text: str, rate: int = 175, volume: float = 1.0) -> None:
        """Synthesize speech."""
        if not text or not text.strip():
            return

        try:
            engine = self._get_engine()
            engine.setProperty("rate", rate)
            engine.setProperty("volume", volume)
            logger.info("Speaking text via pyttsx3", text=text[:50])
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            logger.error("TTS playback error", error=str(e))

    def stop(self) -> None:
        """Stop current speech synthesis."""
        if self._engine is not None:
            try:
                self._engine.stop()
            except Exception as e:
                logger.warning("Error stopping TTS engine", error=str(e))
