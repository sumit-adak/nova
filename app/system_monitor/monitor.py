"""Real-time system monitoring."""

from __future__ import annotations

import psutil

from app.system_monitor.gpu import GPUMonitor


class SystemMonitor:
    """Collects real-time system metrics."""

    def __init__(self) -> None:
        self.gpu_monitor = GPUMonitor()
        import time
        self._last_net = psutil.net_io_counters()
        self._last_net_time = time.time()

    def get_snapshot(self) -> dict:
        """Return a complete system metrics snapshot."""
        import time

        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\")
        gpu = self.gpu_monitor.get_usage()
        net = psutil.net_io_counters()
        battery = psutil.sensors_battery()

        now = time.time()
        elapsed = max(now - self._last_net_time, 0.001) if self._last_net_time else 1
        net_sent_rate = (net.bytes_sent - self._last_net.bytes_sent) / elapsed if self._last_net else 0
        net_recv_rate = (net.bytes_recv - self._last_net.bytes_recv) / elapsed if self._last_net else 0
        self._last_net = net
        self._last_net_time = now

        temps = {}
        try:
            if hasattr(psutil, "sensors_temperatures"):
                for name, entries in psutil.sensors_temperatures().items():
                    if entries:
                        temps[name] = entries[0].current
        except (AttributeError, OSError):
            pass

        return {
            "cpu_percent": psutil.cpu_percent(interval=0),
            "cpu_count": psutil.cpu_count(),
            "memory_percent": mem.percent,
            "memory_used_gb": round(mem.used / (1024**3), 2),
            "memory_total_gb": round(mem.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "gpu": gpu,
            "network_sent_mbps": round(net_sent_rate / (1024**2), 2),
            "network_recv_mbps": round(net_recv_rate / (1024**2), 2),
            "battery_percent": battery.percent if battery else None,
            "battery_plugged": battery.power_plugged if battery else None,
            "temperatures": temps,
        }
