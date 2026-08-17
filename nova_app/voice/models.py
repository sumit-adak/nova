"""Voice event models and data structures."""
from dataclasses import dataclass
from nova_app.core.events import Event


@dataclass
class VoiceListeningEvent(Event):
    """Fired when microphone starts recording."""
    is_listening: bool = True


@dataclass
class VoiceTranscribedEvent(Event):
    """Fired when speech has been transcribed to text."""
    transcript: str = ""
    confidence: float = 1.0


@dataclass
class VoiceSpeakingEvent(Event):
    """Fired when TTS starts speaking a response."""
    text: str = ""
    is_speaking: bool = True


@dataclass
class VoiceStoppedEvent(Event):
    """Fired when TTS or audio capture stops."""
    pass
