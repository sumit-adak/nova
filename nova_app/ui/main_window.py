"""Main Application Window for NOVA using PySide6."""
import sys
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont, QIcon, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from nova_app.config.settings import Settings, get_settings
from nova_app.core.di import get_container
from nova_app.core.events import get_event_bus


DARK_GLASS_STYLE = """
QMainWindow {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}

QWidget#CentralWidget {
    background-color: #0d1117;
}

QFrame#Sidebar {
    background-color: #161b22;
    border-right: 1px solid #30363d;
    min-width: 220px;
    max-width: 220px;
}

QLabel#AppTitle {
    color: #58a6ff;
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 2px;
    padding: 16px;
}

QPushButton.NavButton {
    background-color: transparent;
    color: #8b949e;
    border: none;
    border-radius: 6px;
    text-align: left;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: 500;
    margin: 2px 8px;
}

QPushButton.NavButton:hover {
    background-color: #21262d;
    color: #f0f6fc;
}

QPushButton.NavButton:checked {
    background-color: #1f6feb;
    color: #ffffff;
    font-weight: 600;
}

QFrame#ContentPane {
    background-color: #0d1117;
}

QLabel#PageHeader {
    color: #f0f6fc;
    font-size: 22px;
    font-weight: 600;
    padding: 24px 24px 8px 24px;
}

QLabel#StatusBadge {
    background-color: rgba(35, 134, 54, 0.2);
    color: #3fb950;
    border: 1px solid rgba(63, 185, 80, 0.4);
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
}
"""


class NovaMainWindow(QMainWindow):
    """Main window shell for NOVA desktop assistant."""

    def __init__(self, settings: Settings | None = None):
        super().__init__()
        self.settings = settings or get_settings()
        self.container = get_container()
        self.event_bus = get_event_bus()

        self.setWindowTitle(f"{self.settings.app_name} — Personal AI Operating Layer")
        self.resize(1200, 800)
        self.setMinimumSize(960, 600)
        self.setStyleSheet(DARK_GLASS_STYLE)

        self._init_ui()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame(self)
        sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 16, 8, 16)
        sidebar_layout.setSpacing(6)

        title_label = QLabel("⚡ NOVA", self)
        title_label.setObjectName("AppTitle")
        sidebar_layout.addWidget(title_label)

        # Navigation buttons
        self.nav_buttons: list[QPushButton] = []
        nav_items = [
            ("Dashboard", 0),
            ("Chat & AI", 1),
            ("Computer Index", 2),
            ("System Monitor", 3),
            ("Permissions", 4),
            ("Settings", 5),
        ]

        for text, index in nav_items:
            btn = QPushButton(text, sidebar)
            btn.setProperty("class", "NavButton")
            btn.setCheckable(True)
            if index == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, idx=index: self._switch_page(idx))
            self.nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # Status badge at bottom of sidebar
        status_label = QLabel("● CORE ONLINE", sidebar)
        status_label.setObjectName("StatusBadge")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(status_label)

        root_layout.addWidget(sidebar)

        # Main content area
        content_frame = QFrame(self)
        content_frame.setObjectName("ContentPane")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(24, 24, 24, 24)

        self.stack = QStackedWidget(content_frame)
        for text, _ in nav_items:
            page = QWidget()
            page_layout = QVBoxLayout(page)
            header = QLabel(f"{text}", page)
            header.setObjectName("PageHeader")
            page_layout.addWidget(header)
            
            desc = QLabel(f"NOVA {text} workspace initialized.", page)
            desc.setStyleSheet("color: #8b949e; font-size: 14px; padding-left: 24px;")
            page_layout.addWidget(desc)
            page_layout.addStretch()
            self.stack.addWidget(page)

        content_layout.addWidget(self.stack)
        root_layout.addWidget(content_frame, 1)

    def _switch_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
