"""PySide6 Confirmation Dialog Widget for high-risk tool actions."""
import json
from typing import Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class ToolConfirmationDialog(QDialog):
    """Modal dialog prompting user approval for MEDIUM/HIGH/CRITICAL risk tool executions."""

    def __init__(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        risk_tier: str = "MEDIUM",
        reasoning: str | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.tool_name = tool_name
        self.arguments = arguments
        self.risk_tier = risk_tier
        self.reasoning = reasoning

        self.approved = False
        self.remember_choice = False

        self.setWindowTitle("⚠️ NOVA — Permission Confirmation Required")
        self.setFixedSize(540, 420)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._init_ui()

    def _init_ui(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background-color: #161b22;
                color: #e6edf3;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QLabel#HeaderTitle {
                font-size: 16px;
                font-weight: 700;
                color: #f0883e;
            }
            QLabel#RiskBadge {
                background-color: #bd561d;
                color: #ffffff;
                font-size: 11px;
                font-weight: 700;
                padding: 3px 8px;
                border-radius: 4px;
            }
            QTextEdit#ArgsViewer {
                background-color: #0d1117;
                color: #58a6ff;
                border: 1px solid #30363d;
                border-radius: 6px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
            QPushButton#ApproveBtn {
                background-color: #238636;
                color: white;
                font-weight: 600;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton#ApproveBtn:hover {
                background-color: #2ea043;
            }
            QPushButton#DenyBtn {
                background-color: #da3633;
                color: white;
                font-weight: 600;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton#DenyBtn:hover {
                background-color: #f85149;
            }
            QCheckBox {
                color: #8b949e;
                font-size: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header Row
        header_row = QHBoxLayout()
        header_label = QLabel(f"Action Confirmation: {self.tool_name}", self)
        header_label.setObjectName("HeaderTitle")
        header_row.addWidget(header_label)

        badge = QLabel(self.risk_tier.upper(), self)
        badge.setObjectName("RiskBadge")
        header_row.addWidget(badge, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(header_row)

        if self.reasoning:
            reason_label = QLabel(f"Reason: {self.reasoning}", self)
            reason_label.setStyleSheet("color: #8b949e; font-style: italic;")
            layout.addWidget(reason_label)

        args_title = QLabel("Proposed Arguments:", self)
        args_title.setStyleSheet("font-weight: 600; color: #c9d1d9;")
        layout.addWidget(args_title)

        # Arguments Viewer
        args_viewer = QTextEdit(self)
        args_viewer.setObjectName("ArgsViewer")
        args_viewer.setReadOnly(True)
        args_viewer.setText(json.dumps(self.arguments, indent=2))
        layout.addWidget(args_viewer)

        # Remember choice checkbox
        self.remember_cb = QCheckBox("Remember this choice for the current session", self)
        layout.addWidget(self.remember_cb)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        deny_btn = QPushButton("Deny", self)
        deny_btn.setObjectName("DenyBtn")
        deny_btn.clicked.connect(self._on_deny)
        btn_row.addWidget(deny_btn)

        approve_btn = QPushButton("Approve", self)
        approve_btn.setObjectName("ApproveBtn")
        approve_btn.clicked.connect(self._on_approve)
        btn_row.addWidget(approve_btn)

        layout.addLayout(btn_row)

    def _on_approve(self) -> None:
        self.approved = True
        self.remember_choice = self.remember_cb.isChecked()
        self.accept()

    def _on_deny(self) -> None:
        self.approved = False
        self.remember_choice = False
        self.reject()
