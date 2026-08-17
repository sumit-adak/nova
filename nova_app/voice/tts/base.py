"""Abstract base class for Text-to-Speech engines."""
from abc import ABC, abstractmethod


class TTSEngine(ABC):
    """Abstract interface for speech synthesis engines."""

    @abstractmethod
    def speak(self, text: str, rate: int = 175, volume: float = 1.0) -> None:
        """Synthesize and play speech synchronously."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop playback immediately."""
        pass
