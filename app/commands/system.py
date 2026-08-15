"""System information and control commands."""

from __future__ import annotations

import platform
import socket
import subprocess
from datetime import datetime

import psutil

from app.commands.registry import ActionResult
from app.system_monitor.gpu import GPUMonitor


class SystemCommands:
    """System stats and control operations."""

    def __init__(self) -> None:
        self.gpu_monitor = GPUMonitor()

    async def get_system_info(self) -> ActionResult:
        """Return general system information."""
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": socket.gethostname(),
            "python_version": platform.python_version(),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        }
        message = (
            f"System: {info['os']} | Host: {info['hostname']} | "
            f"CPU: {info['processor'][:50]}"
        )
        return ActionResult(success=True, message=message, data=info)

    async def get_cpu_usage(self) -> ActionResult:
        """Return current CPU usage percentage."""
        usage = psutil.cpu_percent(interval=0.5)
        count = psutil.cpu_count()
        message = f"CPU usage is {usage:.1f}% across {count} cores."
        return ActionResult(
            success=True,
            message=message,
            data={"cpu_percent": usage, "cores": count},
        )

    async def get_memory_usage(self) -> ActionResult:
        """Return current memory usage."""
        mem = psutil.virtual_memory()
        used_gb = mem.used / (1024**3)
        total_gb = mem.total / (1024**3)
        message = f"You're using {used_gb:.1f} GB of {total_gb:.1f} GB RAM ({mem.percent:.0f}%)."
        return ActionResult(
            success=True,
            message=message,
            data={
                "percent": mem.percent,
                "used_gb": round(used_gb, 2),
                "total_gb": round(total_gb, 2),
            },
        )

    async def get_gpu_usage(self) -> ActionResult:
        """Return GPU usage if available."""
        gpu = self.gpu_monitor.get_usage()
        if gpu.get("available"):
            message = f"GPU usage is {gpu['load']:.0f}%."
            if gpu.get("memory_used"):
                message += f" VRAM: {gpu['memory_used']}/{gpu['memory_total']} MB."
        else:
            message = "GPU metrics are not available on this system."
        return ActionResult(success=True, message=message, data=gpu)

    async def get_disk_usage(self, path: str = "C:\\") -> ActionResult:
        """Return disk usage for a drive."""
        try:
            usage = psutil.disk_usage(path)
            used_gb = usage.used / (1024**3)
            total_gb = usage.total / (1024**3)
            message = (
                f"Storage on {path}: {used_gb:.1f} GB used of {total_gb:.1f} GB "
                f"({usage.percent:.0f}%)."
            )
            return ActionResult(
                success=True,
                message=message,
                data={
                    "path": path,
                    "percent": usage.percent,
                    "used_gb": round(used_gb, 2),
                    "total_gb": round(total_gb, 2),
                },
            )
        except OSError as exc:
            return ActionResult(success=False, message=f"Disk info unavailable: {exc}")

    async def get_network_stats(self) -> ActionResult:
        """Return network I/O statistics."""
        net = psutil.net_io_counters()
        sent_mb = net.bytes_sent / (1024**2)
        recv_mb = net.bytes_recv / (1024**2)
        message = f"Network: {sent_mb:.1f} MB sent, {recv_mb:.1f} MB received."
        return ActionResult(
            success=True,
            message=message,
            data={"bytes_sent": net.bytes_sent, "bytes_recv": net.bytes_recv},
        )

    async def get_battery_status(self) -> ActionResult:
        """Return battery status if available."""
        battery = psutil.sensors_battery()
        if battery is None:
            return ActionResult(
                success=True,
                message="No battery detected (desktop system).",
                data={"available": False},
            )
        plugged = "plugged in" if battery.power_plugged else "on battery"
        message = f"Battery at {battery.percent:.0f}%, {plugged}."
        return ActionResult(
            success=True,
            message=message,
            data={
                "percent": battery.percent,
                "plugged": battery.power_plugged,
                "secsleft": battery.secsleft,
            },
        )

    async def kill_process(self, process_name: str) -> ActionResult:
        """Kill a process (requires confirmation)."""
        return ActionResult(
            success=False,
            requires_confirmation=True,
            confirmation_message=(
                f"This will forcefully terminate all '{process_name}' processes. Continue?"
            ),
            data={"process_name": process_name, "action": "kill_process_confirmed"},
        )

    async def kill_process_confirmed(self, process_name: str) -> ActionResult:
        """Execute process kill after confirmation."""
        try:
            result = subprocess.run(
                ["taskkill", "/IM", process_name, "/F"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return ActionResult(success=True, message=f"Terminated {process_name}.")
            return ActionResult(success=False, message=f"Could not terminate {process_name}.")
        except subprocess.TimeoutExpired:
            return ActionResult(success=False, message="Process termination timed out.")

    async def shutdown(self) -> ActionResult:
        """Shutdown system (requires confirmation)."""
        return ActionResult(
            success=False,
            requires_confirmation=True,
            confirmation_message="This will shut down your computer. Continue?",
            data={"action": "shutdown_confirmed"},
        )

    async def shutdown_confirmed(self) -> ActionResult:
        """Execute shutdown after confirmation."""
        subprocess.Popen(["shutdown", "/s", "/t", "30"])
        return ActionResult(
            success=True,
            message="System will shut down in 30 seconds. Run 'shutdown /a' to cancel.",
        )

    async def restart(self) -> ActionResult:
        """Restart system (requires confirmation)."""
        return ActionResult(
            success=False,
            requires_confirmation=True,
            confirmation_message="This will restart your computer. Continue?",
            data={"action": "restart_confirmed"},
        )

    async def restart_confirmed(self) -> ActionResult:
        """Execute restart after confirmation."""
        subprocess.Popen(["shutdown", "/r", "/t", "30"])
        return ActionResult(
            success=True,
            message="System will restart in 30 seconds. Run 'shutdown /a' to cancel.",
        )
