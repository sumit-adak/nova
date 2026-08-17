"""Abstract base class for Speech-to-Text engines."""
from abc import ABC, abstractmethod


class STTEngine(ABC):
    """Abstract interface for speech transcription engines."""

    @abstractmethod
    def listen_and_transcribe(self, timeout_sec: float = 5.0) -> str:
        """Listen to microphone and return transcribed text."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if microphone and dependencies are available."""
        pass
