"""Main Window implementation for NOVA in PySide6 with full Polish & System Tray."""
import asyncio
from PySide6.QtCore import QKeyCombination, Qt, QTimer
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from nova_app.config.settings import Settings, get_settings
from nova_app.conversation.manager import get_conversation_manager
from nova_app.conversation.models import ConversationTurn
from nova_app.core.async_bridge import get_async_bridge
from nova_app.core.events import get_event_bus
from nova_app.permissions.confirmation_queue import ConfirmationRequestedEvent, get_confirmation_queue
from nova_app.security.emergency_stop import get_emergency_stop
from nova_app.ui.settings_dialog import SettingsDialog
from nova_app.ui.system_tray import NovaSystemTray, create_nova_icon
from nova_app.ui.theme import apply_theme
from nova_app.ui.widgets.chat_view import ChatViewWidget
from nova_app.ui.widgets.confirmation_dialog import ToolConfirmationDialog
from nova_app.ui.widgets.hardware_status import HardwareStatusWidget
from nova_app.ui.widgets.voice_waveform import VoiceWaveformWidget
from nova_app.voice.orchestrator import get_voice_orchestrator


class MainWindow(QMainWindow):
    """NOVA Desktop Assistant Main Window."""

    def __init__(self, settings: Settings | None = None):
        super().__init__()
        self.settings = settings or get_settings()
        self.conv_manager = get_conversation_manager()
        self.voice_orchestrator = get_voice_orchestrator()
        self.bridge = get_async_bridge()

        self.setWindowTitle("NOVA — Personal AI Operating Layer")
        self.setWindowIcon(create_nova_icon())
        self.resize(800, 680)
        self.setMinimumSize(600, 480)

        self._init_ui()
        self._init_tray()
        self._init_shortcuts()
        self._subscribe_events()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top Header Bar
        top_bar = QFrame(self)
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 8, 16, 8)

        app_title = QLabel("NOVA", self)
        app_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #58a6ff; letter-spacing: 1px;")
        top_layout.addWidget(app_title)

        # Real-time hardware status metrics
        self.hw_status = HardwareStatusWidget(self)
        top_layout.addWidget(self.hw_status)
        top_layout.addStretch()

        # Voice Waveform
        self.voice_wave = VoiceWaveformWidget(self)
        self.voice_wave.setFixedWidth(160)
        top_layout.addWidget(self.voice_wave)

        # Emergency Stop Button
        self.btn_estop = QPushButton("🛑 HALT", self)
        self.btn_estop.setProperty("class", "dangerButton")
        self.btn_estop.setToolTip("Emergency Stop: Immediately halt all tool execution")
        self.btn_estop.clicked.connect(self._on_emergency_stop_clicked)
        top_layout.addWidget(self.btn_estop)

        main_layout.addWidget(top_bar)

        # 2. Middle Scrollable Chat View
        self.chat_view = ChatViewWidget(self)
        main_layout.addWidget(self.chat_view, 1)

        # 3. Bottom Command Bar
        bottom_bar = QFrame(self)
        bottom_bar.setObjectName("topBar")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(16, 12, 16, 12)
        bottom_layout.setSpacing(10)

        # Push to talk button
        self.btn_mic = QPushButton("🎙️ Talk", self)
        self.btn_mic.setToolTip("Push-to-Talk (Ctrl+Space)")
        self.btn_mic.clicked.connect(self._on_mic_clicked)
        bottom_layout.addWidget(self.btn_mic)

        # Text input box
        self.txt_input = QLineEdit(self)
        self.txt_input.setPlaceholderText("Ask NOVA anything or type a command... (e.g. 'git status', 'how much ram')")
        self.txt_input.returnPressed.connect(self._on_send_clicked)
        bottom_layout.addWidget(self.txt_input, 1)

        # Send button
        self.btn_send = QPushButton("Send", self)
        self.btn_send.setProperty("class", "primaryButton")
        self.btn_send.clicked.connect(self._on_send_clicked)
        bottom_layout.addWidget(self.btn_send)

        # Settings button
        self.btn_settings = QPushButton("⚙️", self)
        self.btn_settings.setFixedWidth(36)
        self.btn_settings.setToolTip("Settings")
        self.btn_settings.clicked.connect(self.open_settings)
        bottom_layout.addWidget(self.btn_settings)

        main_layout.addWidget(bottom_bar)

    def _init_tray(self) -> None:
        self.tray = NovaSystemTray(main_window=self, parent=self)
        self.tray.show()

    def _init_shortcuts(self) -> None:
        # Push-to-talk hotkey (Ctrl+Space)
        self.shortcut_talk = QShortcut(QKeySequence("Ctrl+Space"), self)
        self.shortcut_talk.activated.connect(self._on_mic_clicked)

    def _subscribe_events(self) -> None:
        # Subscribe to confirmation requests
        get_event_bus().subscribe(ConfirmationRequestedEvent, self._on_confirmation_requested)

    def _on_confirmation_requested(self, event: ConfirmationRequestedEvent) -> None:
        """Present confirmation dialog on the main UI thread."""
        dialog = ToolConfirmationDialog(
            request_id=event.request_id,
            tool_name=event.tool_name,
            arguments=event.arguments,
            risk_tier=event.risk_tier,
            reasoning=event.reasoning,
            parent=self,
        )
        dialog.show()

    def _on_send_clicked(self) -> None:
        text = self.txt_input.text().strip()
        if not text:
            return

        self.txt_input.clear()
        self.chat_view.add_user_message(text)

        # Process safely across thread boundary
        self.bridge.run_coroutine(
            self._process_input_task(text),
            on_success=self._on_turn_completed,
            on_error=self._on_turn_error,
        )

    async def _process_input_task(self, text: str) -> ConversationTurn:
        return await self.conv_manager.process_user_input(
            user_text=text,
            auto_prompt_confirmation=True,
        )

    def _on_turn_completed(self, turn: ConversationTurn) -> None:
        """Called on Qt main thread when turn completes."""
        self.chat_view.add_turn(turn)

    def _on_turn_error(self, exc: Exception) -> None:
        """Called on Qt main thread on error."""
        self.chat_view.add_user_message(f"[Error: {str(exc)}]")

    def _on_mic_clicked(self) -> None:
        """Trigger voice push-to-talk cycle."""
        self.bridge.run_coroutine(
            self._voice_turn_task(),
            on_success=self._on_voice_turn_completed,
            on_error=self._on_turn_error,
        )

    async def _voice_turn_task(self) -> ConversationTurn | None:
        return await self.voice_orchestrator.handle_push_to_talk_turn(timeout_sec=5.0)

    def _on_voice_turn_completed(self, turn: ConversationTurn | None) -> None:
        if turn:
            self.chat_view.add_user_message(turn.user_input)
            self.chat_view.add_turn(turn)

    def _on_emergency_stop_clicked(self) -> None:
        get_emergency_stop().trigger(reason="HALT button clicked in header")
        self.chat_view.add_user_message("[🛑 EMERGENCY STOP TRIGGERED BY USER]")

    def open_settings(self) -> None:
        dialog = SettingsDialog(parent=self, settings=self.settings)
        dialog.exec()

    def close_app(self) -> None:
        """Fully exit application."""
        self.tray.hide()
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Minimize to system tray on window close."""
        if self.tray.isVisible():
            self.hide()
            self.tray.showMessage(
                "NOVA Minimized",
                "NOVA is still running in the background.",
                NovaSystemTray.MessageIcon.Information,
                2000
            )
            event.ignore()
        else:
            event.accept()


# Alias for backward compatibility
NovaMainWindow = MainWindow
