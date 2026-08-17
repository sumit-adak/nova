"""TTS subsystem package."""
from nova_app.voice.tts.base import TTSEngine
from nova_app.voice.tts.pyttsx3_engine import Pyttsx3Engine
from nova_app.voice.tts.tts_manager import TTSManager, get_tts_manager

__all__ = [
    "TTSEngine",
    "Pyttsx3Engine",
    "TTSManager",
    "get_tts_manager",
]
