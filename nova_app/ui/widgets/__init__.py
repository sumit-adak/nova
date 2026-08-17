"""UI Widgets package for NOVA."""
from nova_app.ui.widgets.chat_view import ChatViewWidget
from nova_app.ui.widgets.confirmation_dialog import ToolConfirmationDialog
from nova_app.ui.widgets.hardware_status import HardwareStatusWidget
from nova_app.ui.widgets.voice_waveform import VoiceWaveformWidget

__all__ = [
    "ToolConfirmationDialog",
    "VoiceWaveformWidget",
    "HardwareStatusWidget",
    "ChatViewWidget",
]
