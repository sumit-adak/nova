"""System monitor page."""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QFrame

from app.ui.theme import BG_CARD, TEXT_SECONDARY
from app.ui.widgets.common import MetricRow
from app.system_monitor.monitor import SystemMonitor


class MonitorPage(QWidget):
    """Detailed real-time system monitoring."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitor = SystemMonitor()
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(1500)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        title = QLabel("System Monitor")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(12)

        self.cpu_row = MetricRow("CPU Usage")
        self.ram_row = MetricRow("Memory (RAM)")
        self.gpu_row = MetricRow("GPU")
        self.disk_row = MetricRow("Storage (C:)")
        self.net_label = QLabel("Network: --")
        self.net_label.setStyleSheet(f"color: {TEXT_SECONDARY}; padding: 8px;")
        self.battery_label = QLabel("Battery: --")
        self.battery_label.setStyleSheet(f"color: {TEXT_SECONDARY}; padding: 8px;")
        self.temp_label = QLabel("Temperature: --")
        self.temp_label.setStyleSheet(f"color: {TEXT_SECONDARY}; padding: 8px;")

        for i, widget in enumerate([
            self.cpu_row, self.ram_row, self.gpu_row, self.disk_row,
        ]):
            frame = QFrame()
            frame.setStyleSheet(f"background: {BG_CARD}; border-radius: 12px; padding: 12px;")
            fl = QVBoxLayout(frame)
            fl.addWidget(widget)
            grid.addWidget(frame, i // 2, i % 2)

        layout.addLayout(grid)

        info_frame = QFrame()
        info_frame.setStyleSheet(f"background: {BG_CARD}; border-radius: 12px; padding: 16px;")
        info_layout = QVBoxLayout(info_frame)
        info_layout.addWidget(self.net_label)
        info_layout.addWidget(self.battery_label)
        info_layout.addWidget(self.temp_label)
        layout.addWidget(info_frame)
        layout.addStretch()

    def _refresh(self) -> None:
        snap = self.monitor.get_snapshot()
        self.cpu_row.update_value(snap["cpu_percent"], f"{snap['cpu_count']} cores")
        self.ram_row.update_value(
            snap["memory_percent"],
            f"{snap['memory_used_gb']}/{snap['memory_total_gb']} GB",
        )
        gpu = snap["gpu"]
        if gpu["available"]:
            extra = f"{gpu['name']}"
            if gpu.get("temperature"):
                extra += f" | {gpu['temperature']}°C"
            self.gpu_row.update_value(gpu["load"], extra)
        else:
            self.gpu_row.update_value(0, "Not available")
        self.disk_row.update_value(
            snap["disk_percent"],
            f"{snap['disk_used_gb']}/{snap['disk_total_gb']} GB",
        )
        self.net_label.setText(
            f"Network: \u2191 {snap['network_sent_mbps']} MB/s  "
            f"\u2193 {snap['network_recv_mbps']} MB/s"
        )
        if snap["battery_percent"] is not None:
            plugged = "plugged in" if snap["battery_plugged"] else "on battery"
            self.battery_label.setText(
                f"Battery: {snap['battery_percent']:.0f}% ({plugged})"
            )
        else:
            self.battery_label.setText("Battery: Desktop system (no battery)")

        temps = snap.get("temperatures", {})
        if temps:
            temp_str = ", ".join(f"{k}: {v:.0f}°C" for k, v in temps.items())
            self.temp_label.setText(f"Temperature: {temp_str}")
        else:
            self.temp_label.setText("Temperature: Not available")
