"""Continuous system hardware monitor polling and alert engine."""
import asyncio
from datetime import datetime, timezone
import psutil
import structlog
from nova_app.config.settings import Settings, get_settings
from nova_app.core.events import get_event_bus
from nova_app.db.models.monitoring import SystemAlert, SystemMetricsSnapshot
from nova_app.db.session import get_session_factory
from nova_app.monitoring.models import (
    HighCpuAlertEvent,
    HighRamAlertEvent,
    LowBatteryAlertEvent,
    MetricsSnapshotEvent,
    SystemMetrics,
)

logger = structlog.get_logger(__name__)


class SystemMonitorService:
    """Monitors system hardware performance metrics and raises threshold alerts."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._is_running = False
        self._task: asyncio.Task | None = None

    async def get_current_metrics(self) -> SystemMetrics:
        """Fetch real-time snapshot of system hardware resources."""
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\" if psutil.WINDOWS else "/")

        battery_pct = None
        power_plugged = None
        try:
            battery = psutil.sensors_battery()
            if battery:
                battery_pct = battery.percent
                power_plugged = battery.power_plugged
        except Exception:
            pass

        return SystemMetrics(
            cpu_percent=cpu,
            ram_percent=ram.percent,
            ram_used_gb=round(ram.used / (1024**3), 2),
            ram_total_gb=round(ram.total / (1024**3), 2),
            disk_percent=disk.percent,
            disk_free_gb=round(disk.free / (1024**3), 2),
            battery_percent=battery_pct,
            power_plugged=power_plugged,
        )

    async def collect_snapshot(self) -> SystemMetrics:
        """Collect metrics, persist snapshot to SQLite DB, and check thresholds."""
        metrics = await self.get_current_metrics()
        now = datetime.now(timezone.utc)

        # 1. Persist to DB
        session_factory = get_session_factory()
        async with session_factory() as session:
            snapshot = SystemMetricsSnapshot(
                cpu_pct=metrics.cpu_percent,
                ram_pct=metrics.ram_percent,
                disk_pct=metrics.disk_percent,
                battery_pct=metrics.battery_percent,
                timestamp=now,
            )
            session.add(snapshot)

            # 2. Threshold Alerts
            event_bus = get_event_bus()

            if metrics.cpu_percent >= self.settings.cpu_high_threshold:
                alert = SystemAlert(
                    alert_type="cpu_high",
                    message=f"CPU usage at {metrics.cpu_percent}% (threshold: {self.settings.cpu_high_threshold}%)",
                    timestamp=now,
                )
                session.add(alert)
                await event_bus.publish(
                    HighCpuAlertEvent(
                        cpu_percent=metrics.cpu_percent,
                        threshold=self.settings.cpu_high_threshold,
                    )
                )

            if metrics.ram_percent >= self.settings.ram_high_threshold:
                alert = SystemAlert(
                    alert_type="ram_high",
                    message=f"RAM usage at {metrics.ram_percent}% (threshold: {self.settings.ram_high_threshold}%)",
                    timestamp=now,
                )
                session.add(alert)
                await event_bus.publish(
                    HighRamAlertEvent(
                        ram_percent=metrics.ram_percent,
                        threshold=self.settings.ram_high_threshold,
                    )
                )

            if (
                metrics.battery_percent is not None
                and metrics.battery_percent <= self.settings.battery_low_threshold
                and not metrics.power_plugged
            ):
                alert = SystemAlert(
                    alert_type="battery_low",
                    message=f"Low battery warning: {metrics.battery_percent}% remaining",
                    timestamp=now,
                )
                session.add(alert)
                await event_bus.publish(
                    LowBatteryAlertEvent(
                        battery_percent=metrics.battery_percent,
                        threshold=self.settings.battery_low_threshold,
                    )
                )

            await session.commit()

        # Publish snapshot event
        await get_event_bus().publish(MetricsSnapshotEvent(metrics=metrics))
        return metrics

    async def _polling_loop(self) -> None:
        logger.info("System Monitor service loop started", interval=self.settings.monitor_interval_sec)
        while self._is_running:
            try:
                await self.collect_snapshot()
            except Exception as e:
                logger.error("Error in system monitoring collection", error=str(e))
            await asyncio.sleep(self.settings.monitor_interval_sec)

    def start(self) -> None:
        """Start the background monitoring loop."""
        if self._is_running:
            return
        self._is_running = True
        self._task = asyncio.create_task(self._polling_loop())

    def stop(self) -> None:
        """Stop the monitoring loop."""
        self._is_running = False
        if self._task:
            self._task.cancel()
            self._task = None
            logger.info("System Monitor service stopped")


_system_monitor_instance: SystemMonitorService | None = None


def get_system_monitor() -> SystemMonitorService:
    """Get singleton SystemMonitorService instance."""
    global _system_monitor_instance
    if _system_monitor_instance is None:
        _system_monitor_instance = SystemMonitorService()
    return _system_monitor_instance
