"""Main application window."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer, Signal, QThread, QObject
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QStackedWidget, QPushButton, QFrame, QMessageBox,
)

from app.core.config import ConfigManager
from app.core.logger import get_logger
from app.core.state import AssistantState
from app.services.assistant_service import AssistantService, AssistantResponse
from app.ui.theme import STYLESHEET, BG_SECONDARY, ACCENT_PURPLE, TEXT_SECONDARY
from app.ui.dashboard import DashboardPage
from app.ui.chat import ChatPage
from app.ui.monitor import MonitorPage
from app.ui.activity import ActivityPage
from app.ui.settings import SettingsPage
from app.voice.speech_to_text import SpeechToText
from app.voice.text_to_speech import TextToSpeech

logger = get_logger("main_window")

if TYPE_CHECKING:
    pass


class AsyncWorker(QObject):
    """Run async coroutines from Qt threads."""

    finished = Signal(object)

    def __init__(self, coro):
        super().__init__()
        self._coro = coro

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self._coro)
            self.finished.emit(result)
        except Exception as exc:
            logger.error("Async worker error: %s", exc)
            self.finished.emit(AssistantResponse(text=str(exc), state=AssistantState.ERROR))
        finally:
            loop.close()


class VoiceWorker(QObject):
    """Run speech recognition on a background thread and emit Qt signals."""

    recognized = Signal(str)
    finished = Signal()
    failed = Signal(str)

    def __init__(self, stt: SpeechToText, timeout: int = 7):
        super().__init__()
        self._stt = stt
        self._timeout = timeout

    def run(self) -> None:
        try:
            text = self._stt.listen(timeout=self._timeout)
            if text:
                self.recognized.emit(text)
            else:
                self.finished.emit()
        except Exception as exc:
            logger.error("Voice worker error: %s", exc)
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    """NOVA main application window."""

    NAV_ITEMS = [
        ("dashboard", "Dashboard"),
        ("chat", "Chat"),
        ("monitor", "System Monitor"),
        ("activity", "Activity"),
        ("settings", "Settings"),
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NOVA - AI Desktop Assistant")
        self.setMinimumSize(960, 640)
        self.resize(1100, 720)

        self.config = ConfigManager()
        self.assistant = AssistantService(config=self.config)
        self.assistant.on_state_change(self._on_state_change)
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self._nav_labels: dict[str, QLabel] = {}
        self._confirmation_bar: QFrame | None = None

        self._build_ui()
        self.setStyleSheet(STYLESHEET)
        self._refresh_activity()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet(f"background: {BG_SECONDARY}; border-right: 1px solid #2A2A3A;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 24, 12, 24)
        sidebar_layout.setSpacing(4)

        logo = QLabel("NOVA")
        logo.setStyleSheet(
            f"font-size: 22px; font-weight: 800; color: {ACCENT_PURPLE}; padding: 8px;"
        )
        sidebar_layout.addWidget(logo)

        for key, label in self.NAV_ITEMS:
            nav = QLabel(f"  {label}")
            nav.setCursor(Qt.CursorShape.PointingHandCursor)
            nav.setObjectName("navLabel")
            nav.mousePressEvent = lambda e, k=key: self._navigate(k)
            self._nav_labels[key] = nav
            sidebar_layout.addWidget(nav)

        sidebar_layout.addStretch()
        version = QLabel("v1.0.0")
        version.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; padding: 8px;")
        sidebar_layout.addWidget(version)
        root.addWidget(sidebar)

        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        self.dashboard = DashboardPage()
        self.chat = ChatPage()
        self.monitor = MonitorPage()
        self.activity = ActivityPage()
        self.settings = SettingsPage(self.config)

        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.chat)
        self.stack.addWidget(self.monitor)
        self.stack.addWidget(self.activity)
        self.stack.addWidget(self.settings)

        self.dashboard.command_submitted.connect(self._handle_command)
        self.dashboard.mic_clicked.connect(self._start_listening)
        self.chat.message_sent.connect(self._handle_command)
        self.activity.clear_requested.connect(self._clear_activity)
        self.settings.settings_saved.connect(self._on_settings_saved)
        self.settings.memory_cleared.connect(self._clear_memory)

        content.addWidget(self.stack)

        self._confirmation_bar = self._build_confirmation_bar()
        content.addWidget(self._confirmation_bar)
        self._confirmation_bar.hide()

        content_widget = QWidget()
        content_widget.setLayout(content)
        root.addWidget(content_widget, stretch=1)

        self._navigate("dashboard")

    def _build_confirmation_bar(self) -> QFrame:
        bar = QFrame()
        bar.setStyleSheet("background: #2A2010; border-top: 2px solid #F1C40F; padding: 8px;")
        layout = QHBoxLayout(bar)
        self.confirm_label = QLabel("Confirmation required")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self._cancel_confirmation)
        confirm_btn = QPushButton("Confirm")
        confirm_btn.setObjectName("primaryBtn")
        confirm_btn.clicked.connect(self._confirm_action)
        layout.addWidget(self.confirm_label, stretch=1)
        layout.addWidget(cancel_btn)
        layout.addWidget(confirm_btn)
        return bar

    def _navigate(self, page: str) -> None:
        pages = {"dashboard": 0, "chat": 1, "monitor": 2, "activity": 3, "settings": 4}
        idx = pages.get(page, 0)
        self.stack.setCurrentIndex(idx)
        for key, label in self._nav_labels.items():
            label.setObjectName("navLabelActive" if key == page else "navLabel")
            label.style().unpolish(label)
            label.style().polish(label)
        if page == "activity":
            self._refresh_activity()
        if page == "settings":
            self.settings.refresh_memory(self.assistant.memory.get_all())

    def _handle_command(self, text: str) -> None:
        self.chat.add_message(text, is_user=True)
        self._run_async(self.assistant.process_input(text))

    def _run_async(self, coro) -> None:
        self.thread = QThread()
        self.worker = AsyncWorker(coro)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_response)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _on_response(self, response: AssistantResponse) -> None:
        if not isinstance(response, AssistantResponse):
            return

        self.chat.add_message(response.text, is_user=False)
        self.dashboard.add_activity(response.text[:60])

        settings = self.config.load_settings()
        if settings.get("tts_enabled", True) and self.tts.is_available:
            self.tts.speak_async(response.text)

        if response.requires_confirmation:
            self.confirm_label.setText(response.text)
            self._confirmation_bar.show()
        else:
            self._confirmation_bar.hide()

        QTimer.singleShot(2000, lambda: self._reset_state_if_done(response.state))

    def _reset_state_if_done(self, state: AssistantState) -> None:
        if state in (AssistantState.SUCCESS, AssistantState.ERROR):
            self._on_state_change(AssistantState.IDLE)

    def _on_state_change(self, state: AssistantState) -> None:
        self.dashboard.set_state(state.value)

    def _start_listening(self) -> None:
        if not self.stt.is_available:
            self.chat.add_message("Voice input is not available. Check microphone setup.", is_user=False)
            return

        if self.assistant.state == AssistantState.LISTENING:
            return

        self._on_state_change(AssistantState.LISTENING)

        self.voice_thread = QThread()
        self.voice_worker = VoiceWorker(self.stt)
        self.voice_worker.moveToThread(self.voice_thread)
        self.voice_thread.started.connect(self.voice_worker.run)

        self.voice_worker.recognized.connect(self._on_voice_recognized)
        self.voice_worker.finished.connect(self._on_voice_finished)
        self.voice_worker.failed.connect(self._on_voice_failed)

        self.voice_worker.recognized.connect(self.voice_thread.quit)
        self.voice_worker.finished.connect(self.voice_thread.quit)
        self.voice_worker.failed.connect(self.voice_thread.quit)
        self.voice_worker.finished.connect(self.voice_worker.deleteLater)
        self.voice_thread.finished.connect(self.voice_thread.deleteLater)

        self.voice_thread.start()

    def _on_voice_recognized(self, text: str) -> None:
        self._on_state_change(AssistantState.IDLE)
        if text:
            self._handle_command(text)

    def _on_voice_finished(self) -> None:
        self._on_state_change(AssistantState.IDLE)

    def _on_voice_failed(self, error: str) -> None:
        self._on_state_change(AssistantState.IDLE)
        logger.warning("Voice listening failed: %s", error)

    def _confirm_action(self) -> None:
        self._confirmation_bar.hide()
        self._run_async(self.assistant.confirm_pending_action())

    def _cancel_confirmation(self) -> None:
        self._confirmation_bar.hide()
        resp = self.assistant.cancel_pending_action()
        self.chat.add_message(resp.text, is_user=False)

    def _refresh_activity(self) -> None:
        items = self.assistant.get_recent_activity()
        self.activity.load_activity(items)
        self.dashboard.refresh_activity(items)

    def _clear_activity(self) -> None:
        self.assistant.clear_activity()
        self._refresh_activity()

    def _clear_memory(self) -> None:
        count = self.assistant.memory.clear_all()
        self.settings.refresh_memory([])
        QMessageBox.information(self, "Memory Cleared", f"Removed {count} memory entries.")

    def _on_settings_saved(self) -> None:
        QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
