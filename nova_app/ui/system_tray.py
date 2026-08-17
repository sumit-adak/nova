"""Windows System Tray Icon and Context Menu for NOVA."""
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon
from nova_app.security.emergency_stop import get_emergency_stop


def create_nova_icon() -> QIcon:
    """Generate a clean dark-mode NOVA application icon programmatically."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#1f6feb"))
    painter.setPen(QColor("#58a6ff"))
    painter.drawEllipse(2, 2, 28, 28)

    painter.setPen(QColor("#ffffff"))
    font = painter.font()
    font.setBold(True)
    font.setPointSize(10)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), 0x0084, "N")  # Qt.AlignCenter
    painter.end()

    return QIcon(pixmap)


class NovaSystemTray(QSystemTrayIcon):
    """System Tray controller with quick actions and notifications."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent or main_window)
        self.main_window = main_window
        self.setIcon(create_nova_icon())
        self.setToolTip("NOVA — Personal AI Operating Layer")

        self._init_menu()
        self.activated.connect(self._on_tray_activated)

    def _init_menu(self) -> None:
        menu = QMenu()

        # Show / Hide
        self.action_toggle = QAction("Show / Hide NOVA", self)
        self.action_toggle.triggered.connect(self._toggle_window)
        menu.addAction(self.action_toggle)

        menu.addSeparator()

        # Settings
        self.action_settings = QAction("⚙️ Settings...", self)
        self.action_settings.triggered.connect(self.main_window.open_settings)
        menu.addAction(self.action_settings)

        # Emergency Stop
        self.action_emergency_stop = QAction("🛑 Emergency Stop", self)
        self.action_emergency_stop.triggered.connect(self._trigger_emergency_stop)
        menu.addAction(self.action_emergency_stop)

        menu.addSeparator()

        # Quit
        self.action_quit = QAction("Quit NOVA", self)
        self.action_quit.triggered.connect(self.main_window.close_app)
        menu.addAction(self.action_quit)

        self.setContextMenu(menu)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_window()

    def _toggle_window(self) -> None:
        if self.main_window.isVisible():
            self.main_window.hide()
        else:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def _trigger_emergency_stop(self) -> None:
        get_emergency_stop().trigger(reason="Triggered via System Tray menu")
        self.showMessage(
            "NOVA Emergency Stop",
            "Emergency Stop is ACTIVE. All background executions and tools are halted.",
            QSystemTrayIcon.MessageIcon.Critical,
            4000
        )
