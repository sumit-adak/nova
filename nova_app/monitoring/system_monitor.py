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
)

logger = structlog.get_logger(__name__)


class SystemMonitorService:
    """Monitors system hardware performance metrics and raises threshold alerts."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._is_running = False
        self._task: asyncio.Task | None = None

    async def collect_snapshot(self) -> SystemMetricsSnapshot:
        """Collect current metrics snapshot and persist to DB."""
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\" if psutil.WINDOWS else "/")
        battery = psutil.sensors_battery()
        net = psutil.net_io_counters()

        snapshot = SystemMetricsSnapshot(
            timestamp=datetime.now(timezone.utc),
            cpu_pct=cpu,
            ram_pct=ram.percent,
            disk_pct=disk.percent,
            net_sent_kb=round(net.bytes_sent / 1024, 2),
            net_recv_kb=round(net.bytes_recv / 1024, 2),
            battery_pct=battery.percent if battery else None,
        )

        # Persist snapshot
        session_factory = get_session_factory()
        async with session_factory() as session:
            session.add(snapshot)
            await session.commit()

        # Emit metrics event
        get_event_bus().publish_sync(
            MetricsSnapshotEvent(
                cpu_percent=cpu,
                ram_percent=ram.percent,
                disk_percent=disk.percent,
                battery_percent=battery.percent if battery else None,
            )
        )

        # Threshold checks
        await self._check_thresholds(snapshot)
        return snapshot

    async def _check_thresholds(self, snapshot: SystemMetricsSnapshot) -> None:
        """Evaluate thresholds and trigger alerts."""
        event_bus = get_event_bus()

        if snapshot.cpu_pct >= self.settings.cpu_high_threshold:
            event_bus.publish_sync(
                HighCpuAlertEvent(cpu_percent=snapshot.cpu_pct, threshold=self.settings.cpu_high_threshold)
            )
            await self._record_alert("high_cpu", f"CPU usage reached {snapshot.cpu_pct}%")

        if snapshot.ram_pct >= self.settings.ram_high_threshold:
            event_bus.publish_sync(
                HighRamAlertEvent(ram_percent=snapshot.ram_pct, threshold=self.settings.ram_high_threshold)
            )
            await self._record_alert("high_ram", f"RAM usage reached {snapshot.ram_pct}%")

        if snapshot.battery_pct is not None and snapshot.battery_pct <= self.settings.battery_low_threshold:
            battery = psutil.sensors_battery()
            if battery and not battery.power_plugged:
                event_bus.publish_sync(
                    LowBatteryAlertEvent(
                        battery_percent=snapshot.battery_pct,
                        threshold=self.settings.battery_low_threshold
                    )
                )
                await self._record_alert("low_battery", f"Battery low: {snapshot.battery_pct}% remaining")

    async def _record_alert(self, alert_type: str, message: str) -> None:
        """Save alert to database."""
        session_factory = get_session_factory()
        async with session_factory() as session:
            alert = SystemAlert(
                timestamp=datetime.now(timezone.utc),
                alert_type=alert_type,
                message=message,
                acknowledged=False,
            )
            session.add(alert)
            await session.commit()

    async def _polling_loop(self) -> None:
        """Background monitoring polling loop."""
        logger.info("System Monitor service loop started")
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
