"""Chat page."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame,
)

from app.ui.theme import BG_CARD, ACCENT_PURPLE, TEXT_SECONDARY, TEXT_PRIMARY


class ChatBubble(QFrame):
    """A single chat message bubble."""

    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        color = ACCENT_PURPLE if is_user else BG_CARD
        align = "right" if is_user else "left"
        role = "You" if is_user else "NOVA"
        self.setStyleSheet(
            f"background: {color}; border-radius: 12px; padding: 12px; margin: 4px;"
        )
        layout = QVBoxLayout(self)
        role_label = QLabel(role)
        role_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 11px; font-weight: 600;"
        )
        msg_label = QLabel(text)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px;")
        msg_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(role_label)
        layout.addWidget(msg_label)


class ChatPage(QWidget):
    """ChatGPT-like conversation interface."""

    message_sent = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)

        title = QLabel("Chat")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.addStretch()
        scroll.setWidget(self.messages_widget)
        layout.addWidget(scroll, stretch=1)

        input_row = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask NOVA anything...")
        self.input_field.returnPressed.connect(self._send)
        send_btn = QPushButton("Send")
        send_btn.setObjectName("primaryBtn")
        send_btn.clicked.connect(self._send)
        input_row.addWidget(self.input_field)
        input_row.addWidget(send_btn)
        layout.addLayout(input_row)

    def _send(self) -> None:
        text = self.input_field.text().strip()
        if text:
            self.message_sent.emit(text)
            self.input_field.clear()

    def add_message(self, text: str, is_user: bool) -> None:
        bubble = ChatBubble(text, is_user)
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        if is_user:
            row.addStretch()
            row.addWidget(bubble, stretch=0)
        else:
            row.addWidget(bubble, stretch=0)
            row.addStretch()
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, container)

    def clear_messages(self) -> None:
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
