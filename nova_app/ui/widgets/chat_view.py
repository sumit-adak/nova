"""Rich Chat & Activity Stream widget for NOVA."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from nova_app.conversation.models import ConversationTurn
from nova_app.tools.schema import ToolCall, ToolResult


class ChatMessageCard(QFrame):
    """Card displaying a single message turn (User or Assistant)."""

    def __init__(self, role: str, text: str, parent=None):
        super().__init__(parent)
        self.setProperty("class", "glassCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Header tag
        is_user = role.lower() == "user"
        header_layout = QHBoxLayout()
        role_label = QLabel("You" if is_user else "NOVA Assistant", self)
        role_label.setStyleSheet("font-weight: bold; color: #58a6ff;" if not is_user else "font-weight: bold; color: #7ee787;")
        header_layout.addWidget(role_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Body
        body_label = QLabel(text, self)
        body_label.setWordWrap(True)
        body_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(body_label)


class ToolExecutionBadge(QFrame):
    """Card displaying an executed tool call and its result."""

    def __init__(self, tool_call: ToolCall, result: ToolResult | None = None, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #1c2128;
                border-left: 3px solid #1f6feb;
                border-radius: 4px;
                padding: 6px 10px;
                margin-top: 4px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        status_text = "✓ Success" if (result and result.success) else ("✗ Failed" if result else "Executing...")
        status_color = "#3fb950" if (result and result.success) else ("#f85149" if result else "#db61a2")

        header = QLabel(f"🔧 Tool: <b>{tool_call.tool_name}</b> &nbsp;&nbsp;<span style='color:{status_color};'>{status_text}</span>")
        header.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(header)

        if tool_call.reasoning:
            reason_lbl = QLabel(f"<i>Reason: {tool_call.reasoning}</i>")
            reason_lbl.setStyleSheet("color: #8b949e; font-size: 11px;")
            layout.addWidget(reason_lbl)


class ChatViewWidget(QWidget):
    """Scrollable chat history and activity stream."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(16, 16, 16, 16)
        self.container_layout.setSpacing(12)
        self.container_layout.addStretch()

        self.scroll_area.setWidget(self.container)
        main_layout.addWidget(self.scroll_area)

    def add_user_message(self, text: str) -> None:
        """Add user message card."""
        card = ChatMessageCard(role="user", text=text, parent=self.container)
        self.container_layout.insertWidget(self.container_layout.count() - 1, card)
        self._scroll_to_bottom()

    def add_turn(self, turn: ConversationTurn) -> None:
        """Add full conversation turn with thought, tools, and assistant response."""
        # Tool badges
        for i, call in enumerate(turn.tool_calls):
            res = turn.tool_results[i] if i < len(turn.tool_results) else None
            badge = ToolExecutionBadge(tool_call=call, result=res, parent=self.container)
            self.container_layout.insertWidget(self.container_layout.count() - 1, badge)

        # Assistant response
        if turn.assistant_response:
            card = ChatMessageCard(role="assistant", text=turn.assistant_response, parent=self.container)
            self.container_layout.insertWidget(self.container_layout.count() - 1, card)

        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        QTimer_single_shot = getattr(self, "_schedule_scroll", None)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
