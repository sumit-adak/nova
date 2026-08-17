"""Animated Voice Waveform Widget for PySide6."""
import math
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter
from PySide6.QtWidgets import QWidget
from nova_app.core.events import Event, get_event_bus
from nova_app.voice.models import (
    VoiceListeningEvent,
    VoiceSpeakingEvent,
    VoiceStoppedEvent,
)


class VoiceWaveformWidget(QWidget):
    """Futuristic glowing animated waveform visualizer reacting to listening/speaking states."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(240, 60)
        self.setFixedHeight(80)

        self._num_bars = 16
        self._phase = 0.0
        self._state = "idle"  # idle, listening, speaking

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_step)
        self._timer.start(40)  # 25 FPS

        # Subscribe to voice events on EventBus
        event_bus = get_event_bus()
        event_bus.subscribe(VoiceListeningEvent, self._on_listening_event)
        event_bus.subscribe(VoiceSpeakingEvent, self._on_speaking_event)
        event_bus.subscribe(VoiceStoppedEvent, self._on_stopped_event)

    def _on_listening_event(self, event: VoiceListeningEvent) -> None:
        self._state = "listening" if event.is_listening else "idle"

    def _on_speaking_event(self, event: VoiceSpeakingEvent) -> None:
        self._state = "speaking" if event.is_speaking else "idle"

    def _on_stopped_event(self, event: VoiceStoppedEvent) -> None:
        self._state = "idle"

    def _animate_step(self) -> None:
        self._phase += 0.15
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        mid_y = h / 2.0

        bar_width = max(4.0, (w - (self._num_bars * 6)) / self._num_bars)
        spacing = 6.0
        total_width = self._num_bars * (bar_width + spacing)
        start_x = (w - total_width) / 2.0

        for i in range(self._num_bars):
            # Calculate dynamic bar height
            if self._state == "listening":
                # Pulsing wave
                intensity = math.sin(self._phase + i * 0.4) * 0.5 + 0.5
                bar_h = 10.0 + intensity * (h * 0.6)
                color_top = QColor("#58a6ff")
                color_bot = QColor("#1f6feb")
            elif self._state == "speaking":
                # Active energetic wave
                intensity = (math.sin(self._phase * 1.5 + i * 0.6) + math.cos(self._phase * 0.8 + i * 0.3)) * 0.4 + 0.5
                bar_h = 12.0 + intensity * (h * 0.7)
                color_top = QColor("#3fb950")
                color_bot = QColor("#238636")
            else:
                # Idle subtle breathing
                intensity = math.sin(self._phase * 0.5 + i * 0.2) * 0.2 + 0.3
                bar_h = 6.0 + intensity * 8.0
                color_top = QColor("#484f58")
                color_bot = QColor("#30363d")

            x = start_x + i * (bar_width + spacing)
            y = mid_y - (bar_h / 2.0)

            gradient = QLinearGradient(x, y, x, y + bar_h)
            gradient.setColorAt(0.0, color_top)
            gradient.setColorAt(1.0, color_bot)

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, y, bar_width, bar_h, bar_width / 2.0, bar_width / 2.0)
