"""SpeechRecognition STT implementation for Windows."""
import structlog
import speech_recognition as sr
from nova_app.voice.stt.base import STTEngine

logger = structlog.get_logger(__name__)


class SpeechRecognitionEngine(STTEngine):
    """STT Engine using SpeechRecognition library with noise adjustment."""

    def __init__(self):
        self._recognizer = sr.Recognizer()
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.pause_threshold = 0.8

    def is_available(self) -> bool:
        try:
            return len(sr.Microphone.list_microphone_names()) > 0
        except Exception:
            return False

    def listen_and_transcribe(self, timeout_sec: float = 5.0) -> str:
        """Capture audio from default microphone and transcribe."""
        try:
            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                logger.info("Microphone listening...")
                audio = self._recognizer.listen(source, timeout=timeout_sec, phrase_time_limit=10.0)

            transcript = self._recognizer.recognize_google(audio)
            logger.info("Transcribed audio successfully", transcript=transcript)
            return transcript.strip()
        except sr.WaitTimeoutError:
            logger.info("Listening timed out with no speech detected")
            return ""
        except sr.UnknownValueError:
            logger.info("Speech was unintelligible")
            return ""
        except sr.RequestError as e:
            logger.error("STT network error", error=str(e))
            raise RuntimeError(f"Speech recognition service request error: {str(e)}")
        except Exception as e:
            logger.error("Audio capture failed", error=str(e))
            raise
