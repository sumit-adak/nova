"""Custom UI widgets for NOVA."""

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import QWidget, QProgressBar, QLabel, QVBoxLayout

from app.ui.theme import ACCENT_PURPLE, ACCENT_ORANGE, BG_CARD, TEXT_SECONDARY


class GlowProgressBar(QProgressBar):
    """Styled progress bar with gradient fill."""

    def __init__(self, label: str = "", parent=None):
        super().__init__(parent)
        self.setRange(0, 100)
        self.setTextVisible(False)
        self.setFixedHeight(8)
        self._label = label

    def set_label(self, label: str) -> None:
        self._label = label


class MetricRow(QWidget):
    """A labeled metric row with progress bar."""

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(4)

        header = QWidget()
        from PySide6.QtWidgets import QHBoxLayout
        h = QHBoxLayout(header)
        h.setContentsMargins(0, 0, 0, 0)

        self.name_label = QLabel(name)
        self.name_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        self.value_label = QLabel("0%")
        self.value_label.setStyleSheet("font-size: 12px; font-weight: 600;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        h.addWidget(self.name_label)
        h.addWidget(self.value_label)

        self.bar = GlowProgressBar()
        layout.addWidget(header)
        layout.addWidget(self.bar)

    def update_value(self, percent: float, extra: str = "") -> None:
        self.bar.setValue(int(percent))
        text = f"{percent:.0f}%"
        if extra:
            text = f"{text}  {extra}"
        self.value_label.setText(text)


class PulsingMicButton(QWidget):
    """Animated microphone button with pulse effect."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80)
        self._pulse = 0
        self._listening = False
        self._animation = QPropertyAnimation(self, b"pulse")
        self._animation.setDuration(1000)
        self._animation.setStartValue(0)
        self._animation.setEndValue(100)
        self._animation.setLoopCount(-1)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutSine)

    def get_pulse(self) -> int:
        return self._pulse

    def set_pulse(self, value: int) -> None:
        self._pulse = value
        self.update()

    pulse = Property(int, get_pulse, set_pulse)

    def set_listening(self, listening: bool) -> None:
        self._listening = listening
        if listening:
            self._animation.start()
        else:
            self._animation.stop()
            self._pulse = 0
            self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = self.width() // 2, self.height() // 2
        base_r = 28

        if self._listening:
            glow_r = base_r + (self._pulse / 100) * 12
            glow = QColor(ACCENT_ORANGE)
            glow.setAlpha(60)
            painter.setBrush(glow)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(cx - glow_r), int(cy - glow_r), int(glow_r * 2), int(glow_r * 2))

        color = QColor(ACCENT_ORANGE if self._listening else ACCENT_PURPLE)
        painter.setBrush(color)
        painter.setPen(QPen(QColor(ACCENT_PURPLE), 2))
        painter.drawEllipse(cx - base_r, cy - base_r, base_r * 2, base_r * 2)

        painter.setPen(QColor("white"))
        font = QFont("Segoe UI", 20)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "\U0001F3A4")


class StateIndicator(QLabel):
    """Visual indicator for assistant state."""

    STATE_TEXT = {
        "idle": ("\u25CF ONLINE", "#2ECC71"),
        "listening": ("\u25CF LISTENING", ACCENT_ORANGE),
        "thinking": ("\u25CF THINKING", ACCENT_PURPLE),
        "executing": ("\u25CF EXECUTING", ACCENT_PURPLE),
        "success": ("\u25CF DONE", "#2ECC71"),
        "error": ("\u25CF ERROR", "#E74C3C"),
        "confirmation_required": ("\u25CF CONFIRM?", "#F1C40F"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_state("idle")

    def set_state(self, state: str) -> None:
        text, color = self.STATE_TEXT.get(state, self.STATE_TEXT["idle"])
        self.setText(f"Status: {text}")
        self.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600;")
