"""Hardware status pill widget displaying real-time metrics in NOVA header."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget
from nova_app.core.events import get_event_bus
from nova_app.monitoring.models import MetricsSnapshotEvent


class HardwareStatusWidget(QWidget):
    """Compact status pill showing CPU, RAM, Battery, and Disk state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._subscribe_events()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.lbl_cpu = QLabel("CPU: --%", self)
        self.lbl_cpu.setObjectName("statusPill")

        self.lbl_ram = QLabel("RAM: --%", self)
        self.lbl_ram.setObjectName("statusPill")

        self.lbl_battery = QLabel("BAT: --%", self)
        self.lbl_battery.setObjectName("statusPill")

        layout.addWidget(self.lbl_cpu)
        layout.addWidget(self.lbl_ram)
        layout.addWidget(self.lbl_battery)

    def _subscribe_events(self) -> None:
        get_event_bus().subscribe(MetricsSnapshotEvent, self._on_metrics_snapshot)

    def _on_metrics_snapshot(self, event: MetricsSnapshotEvent) -> None:
        if not event.metrics:
            return
        m = event.metrics
        self.lbl_cpu.setText(f"CPU: {m.cpu_percent:.0f}%")
        self.lbl_ram.setText(f"RAM: {m.ram_used_gb:.1f}/{m.ram_total_gb:.0f} GB ({m.ram_percent:.0f}%)")

        if m.battery_percent is not None:
            plug_icon = " ⚡" if m.power_plugged else ""
            self.lbl_battery.setText(f"BAT: {m.battery_percent:.0f}%{plug_icon}")
            self.lbl_battery.show()
        else:
            self.lbl_battery.hide()
