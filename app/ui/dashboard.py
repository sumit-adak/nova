"""Dashboard page."""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QFrame,
)

from app.ui.theme import TEXT_SECONDARY, BG_CARD, ACCENT_PURPLE
from app.ui.widgets.common import PulsingMicButton, MetricRow, StateIndicator
from app.system_monitor.monitor import SystemMonitor


class DashboardPage(QWidget):
    """Main dashboard with mic, metrics, and recent activity."""

    command_submitted = Signal(str)
    mic_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitor = SystemMonitor()
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_metrics)
        self._timer.start(1500)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        title = QLabel("NOVA")
        title.setObjectName("titleLabel")
        subtitle = QLabel("How can I help you?")
        subtitle.setObjectName("subtitleLabel")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        mic_container = QWidget()
        mic_layout = QHBoxLayout(mic_container)
        mic_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mic_btn = PulsingMicButton()
        self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mic_btn.mousePressEvent = lambda e: self.mic_clicked.emit()
        mic_layout.addWidget(self.mic_btn)
        layout.addWidget(mic_container)

        input_row = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a command or question...")
        self.input_field.returnPressed.connect(self._submit)
        send_btn = QPushButton("Send")
        send_btn.setObjectName("primaryBtn")
        send_btn.clicked.connect(self._submit)
        input_row.addWidget(self.input_field)
        input_row.addWidget(send_btn)
        layout.addLayout(input_row)

        self.state_indicator = StateIndicator()
        layout.addWidget(self.state_indicator)

        metrics_frame = QFrame()
        metrics_frame.setStyleSheet(
            f"background: {BG_CARD}; border-radius: 12px; padding: 16px;"
        )
        metrics_layout = QVBoxLayout(metrics_frame)
        metrics_title = QLabel("System")
        metrics_title.setStyleSheet("font-weight: 600; font-size: 14px;")
        metrics_layout.addWidget(metrics_title)

        self.cpu_row = MetricRow("CPU")
        self.ram_row = MetricRow("RAM")
        self.gpu_row = MetricRow("GPU")
        self.storage_row = MetricRow("Storage")
        for row in (self.cpu_row, self.ram_row, self.gpu_row, self.storage_row):
            metrics_layout.addWidget(row)
        layout.addWidget(metrics_frame)

        activity_label = QLabel("Recent Activity")
        activity_label.setStyleSheet("font-weight: 600; font-size: 14px; margin-top: 8px;")
        layout.addWidget(activity_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(160)
        scroll.setStyleSheet("border: none; background: transparent;")
        self.activity_container = QWidget()
        self.activity_layout = QVBoxLayout(self.activity_container)
        self.activity_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.activity_container)
        layout.addWidget(scroll)

        layout.addStretch()

    def _submit(self) -> None:
        text = self.input_field.text().strip()
        if text:
            self.command_submitted.emit(text)
            self.input_field.clear()

    def _update_metrics(self) -> None:
        snap = self.monitor.get_snapshot()
        self.cpu_row.update_value(snap["cpu_percent"])
        self.ram_row.update_value(
            snap["memory_percent"],
            f"{snap['memory_used_gb']}/{snap['memory_total_gb']} GB",
        )
        gpu = snap["gpu"]
        if gpu["available"]:
            self.gpu_row.update_value(gpu["load"])
        else:
            self.gpu_row.update_value(0, "N/A")
        self.storage_row.update_value(
            snap["disk_percent"],
            f"{snap['disk_used_gb']}/{snap['disk_total_gb']} GB",
        )

    def set_state(self, state: str) -> None:
        self.state_indicator.set_state(state)
        self.mic_btn.set_listening(state == "listening")

    def add_activity(self, text: str) -> None:
        label = QLabel(f"> {text}")
        label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; padding: 2px 0;")
        self.activity_layout.insertWidget(0, label)
        while self.activity_layout.count() > 10:
            item = self.activity_layout.takeAt(self.activity_layout.count() - 1)
            if item.widget():
                item.widget().deleteLater()

    def refresh_activity(self, items: list[dict]) -> None:
        while self.activity_layout.count():
            item = self.activity_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for item in items[:8]:
            cmd = item.get("user_command", "")
            status = item.get("status", "")
            text = f"{cmd} ({status})"
            self.add_activity(text)
