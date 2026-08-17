"""Unit tests for Phase 10: UI Polish & System Tray Integration."""
from unittest.mock import MagicMock
import pytest
from PySide6.QtWidgets import QApplication
from nova_app.conversation.models import ConversationTurn
from nova_app.monitoring.models import MetricsSnapshotEvent, SystemMetrics
from nova_app.tools.schema import ToolCall, ToolResult
from nova_app.ui.main_window import MainWindow
from nova_app.ui.settings_dialog import SettingsDialog
from nova_app.ui.system_tray import NovaSystemTray, create_nova_icon
from nova_app.ui.widgets.chat_view import ChatViewWidget
from nova_app.ui.widgets.hardware_status import HardwareStatusWidget


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_nova_icon_generation(qapp):
    icon = create_nova_icon()
    assert not icon.isNull()


def test_hardware_status_widget(qapp):
    widget = HardwareStatusWidget()
    assert "CPU:" in widget.lbl_cpu.text()

    # Simulate metrics event
    metrics = SystemMetrics(
        cpu_percent=25.0,
        ram_percent=50.0,
        ram_used_gb=8.0,
        ram_total_gb=16.0,
        disk_percent=40.0,
        disk_free_gb=120.0,
        battery_percent=85.0,
        power_plugged=True,
    )
    widget._on_metrics_snapshot(MetricsSnapshotEvent(metrics=metrics))
    assert "25%" in widget.lbl_cpu.text()
    assert "8.0/16 GB" in widget.lbl_ram.text()
    assert "85%" in widget.lbl_battery.text()


def test_chat_view_widget(qapp):
    view = ChatViewWidget()
    view.add_user_message("What is my CPU usage?")

    turn = ConversationTurn(
        id="turn-1",
        user_input="What is my CPU usage?",
        assistant_thought="Look up system stats",
        tool_calls=[ToolCall(tool_name="get_system_stats", arguments={})],
        tool_results=[ToolResult(tool_name="get_system_stats", success=True, data={"cpu": 12.0})],
        assistant_response="Your CPU usage is 12%.",
    )
    view.add_turn(turn)
    # Check that widgets were added to container
    assert view.container_layout.count() >= 3


def test_main_window_initialization(qapp):
    window = MainWindow()
    assert window.windowTitle() == "NOVA — Personal AI Operating Layer"
    assert window.hw_status is not None
    assert window.chat_view is not None
    assert window.tray is not None
    window.tray.hide()
    window.close()


def test_settings_dialog_saves(qapp):
    dialog = SettingsDialog()
    dialog.combo_ai_provider.setCurrentText("openai")
    dialog.txt_openai_key.setText("sk-mock-key")
    dialog.combo_browser.setCurrentText("firefox")
    dialog._save_and_accept()

    assert dialog.settings.ai_provider == "openai"
    assert dialog.settings.openai_api_key == "sk-mock-key"
    assert dialog.settings.default_browser == "firefox"
