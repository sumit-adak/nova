"""Activity log page."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QFrame,
)

from app.ui.theme import BG_CARD, TEXT_SECONDARY, TEXT_PRIMARY


class ActivityPage(QWidget):
    """Activity history viewer."""

    clear_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)

        header = QWidget()
        from PySide6.QtWidgets import QHBoxLayout
        h = QHBoxLayout(header)
        h.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Activity")
        title.setObjectName("titleLabel")
        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self.clear_requested.emit)
        h.addWidget(title)
        h.addStretch()
        h.addWidget(clear_btn)
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        self.list_widget = QWidget()
        from PySide6.QtCore import Qt
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.list_widget)
        layout.addWidget(scroll)

    def load_activity(self, items: list[dict]) -> None:
        from PySide6.QtCore import Qt
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not items:
            empty = QLabel("No activity yet.")
            empty.setStyleSheet(f"color: {TEXT_SECONDARY};")
            self.list_layout.addWidget(empty)
            return

        for entry in items:
            frame = QFrame()
            frame.setStyleSheet(
                f"background: {BG_CARD}; border-radius: 8px; padding: 12px; margin: 4px 0;"
            )
            fl = QVBoxLayout(frame)
            ts = entry.get("timestamp", "")[:19].replace("T", " ")
            ts_label = QLabel(ts)
            ts_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
            cmd_label = QLabel(f"User: {entry.get('user_command', '')}")
            cmd_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 500;")
            action = entry.get("intent_action") or "conversation"
            result = entry.get("result_message", "")[:100]
            status = entry.get("status", "")
            detail = QLabel(f"Action: {action} | {status}\n{result}")
            detail.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
            detail.setWordWrap(True)
            fl.addWidget(ts_label)
            fl.addWidget(cmd_label)
            fl.addWidget(detail)
            self.list_layout.addWidget(frame)
