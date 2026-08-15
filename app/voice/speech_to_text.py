"""Speech-to-text using SpeechRecognition."""

from __future__ import annotations

import threading
from typing import Callable

from app.core.logger import get_logger

logger = get_logger("stt")


class SpeechToText:
    """Microphone speech recognition with push-to-talk support."""

    def __init__(self) -> None:
        self._recognizer = None
        self._microphone = None
        self._available = False
        self._calibrated = False
        self._init_engine()

    def _init_engine(self) -> None:
        try:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
            self._recognizer.dynamic_energy_threshold = True
            self._recognizer.energy_threshold = 300
            self._recognizer.pause_threshold = 0.8
            self._recognizer.phrase_threshold = 0.3
            self._recognizer.non_speaking_duration = 0.5
            self._microphone = sr.Microphone()
            self._available = True
            logger.info("Speech recognition initialized")
            # Calibrate ambient noise in background thread on startup
            threading.Thread(target=self._calibrate_ambient, daemon=True).start()
        except ImportError:
            logger.warning("SpeechRecognition not available")
        except Exception as exc:
            logger.warning("Microphone init failed: %s", exc)

    def _calibrate_ambient(self) -> None:
        """One-time calibration for ambient noise."""
        if not self._available or self._calibrated or not self._microphone:
            return
        try:
            with self._microphone as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
                self._calibrated = True
                logger.info("Microphone ambient noise calibrated (energy_threshold=%.1f)", self._recognizer.energy_threshold)
        except Exception as exc:
            logger.debug("Ambient calibration skipped: %s", exc)

    @property
    def is_available(self) -> bool:
        return self._available

    def listen(self, timeout: int = 7, phrase_limit: int = 15) -> str | None:
        """Listen for speech and return transcribed text."""
        if not self._available or not self._microphone:
            return None

        import speech_recognition as sr

        try:
            with self._microphone as source:
                logger.info("Listening for speech (timeout=%ds, limit=%ds)...", timeout, phrase_limit)
                audio = self._recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_limit
                )

            try:
                text = self._recognizer.recognize_google(audio)
                logger.info("Recognized: %s", text)
                return text
            except sr.UnknownValueError:
                logger.info("Could not understand audio")
                return None
            except sr.RequestError as exc:
                logger.error("Speech recognition service error: %s", exc)
                return None
        except sr.WaitTimeoutError:
            logger.info("Listening timed out (no speech detected)")
            return None
        except Exception as exc:
            logger.error("Listen error: %s", exc)
            return None

    def listen_async(
        self,
        callback: Callable[[str | None], None],
        timeout: int = 7,
    ) -> threading.Thread:
        """Listen in a background thread."""
        def _worker():
            result = self.listen(timeout=timeout)
            callback(result)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread
