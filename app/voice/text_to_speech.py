"""Text-to-speech using pyttsx3."""

from __future__ import annotations

import threading

from app.core.logger import get_logger

logger = get_logger("tts")


class TextToSpeech:
    """Offline text-to-speech engine."""

    def __init__(self, rate: int = 175, volume: float = 1.0) -> None:
        self._engine = None
        self._available = False
        self._rate = rate
        self._volume = volume
        self._lock = threading.Lock()
        self._init_engine()

    def _init_engine(self) -> None:
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self._rate)
            self._engine.setProperty("volume", self._volume)
            self._available = True
            logger.info("Text-to-speech initialized")
        except Exception as exc:
            logger.warning("TTS init failed: %s", exc)

    @property
    def is_available(self) -> bool:
        return self._available

    def speak(self, text: str) -> None:
        """Speak text synchronously."""
        if not self._available or not text:
            return
        with self._lock:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as exc:
                logger.error("TTS speak error: %s", exc)

    def speak_async(self, text: str) -> threading.Thread:
        """Speak text in a background thread."""
        thread = threading.Thread(target=self.speak, args=(text,), daemon=True)
        thread.start()
        return thread

    def set_rate(self, rate: int) -> None:
        self._rate = rate
        if self._engine:
            self._engine.setProperty("rate", rate)

    def set_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(1.0, volume))
        if self._engine:
            self._engine.setProperty("volume", self._volume)
