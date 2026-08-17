"""Hardware and system differential event watchers (USB, Battery, Power)."""
import asyncio
from typing import Any
import psutil
import structlog
from nova_app.core.events import get_event_bus
from nova_app.monitoring.models import (
    PowerStateChangedEvent,
    USBConnectedEvent,
    USBDisconnectedEvent,
)

logger = structlog.get_logger(__name__)


class USBWatcher:
    """Detects USB and external drive connection/disconnection differentials."""

    def __init__(self):
        self._known_mounts: dict[str, dict[str, Any]] = {}
        self._initialized = False

    def check_diffs(self) -> tuple[list[USBConnectedEvent], list[USBDisconnectedEvent]]:
        """Check for drive insertion/removal without continuous high-CPU loops."""
        connected: list[USBConnectedEvent] = []
        disconnected: list[USBDisconnectedEvent] = []

        try:
            current_partitions = {p.mountpoint: p for p in psutil.disk_partitions(all=True)}
        except Exception as e:
            logger.warning("Failed to query disk partitions", error=str(e))
            return [], []

        if not self._initialized:
            for mount, p in current_partitions.items():
                self._known_mounts[mount] = {"device": p.device, "fstype": p.fstype}
            self._initialized = True
            return [], []

        # Check for newly connected drives
        for mount, p in current_partitions.items():
            if mount not in self._known_mounts:
                self._known_mounts[mount] = {"device": p.device, "fstype": p.fstype}
                # If removable or new volume
                if "cdrom" not in p.opts:
                    connected.append(
                        USBConnectedEvent(
                            device=p.device,
                            mountpoint=p.mountpoint,
                            fstype=p.fstype,
                        )
                    )

        # Check for disconnected drives
        removed_mounts = [m for m in self._known_mounts if m not in current_partitions]
        for mount in removed_mounts:
            del self._known_mounts[mount]
            disconnected.append(USBDisconnectedEvent(mountpoint=mount))

        return connected, disconnected


class BatteryWatcher:
    """Detects AC adapter plugged/unplugged state transitions and low battery."""

    def __init__(self):
        self._last_plugged: bool | None = None
        self._last_percent: float | None = None

    def check_diffs(self) -> list[PowerStateChangedEvent]:
        """Check for power state transitions."""
        events: list[PowerStateChangedEvent] = []
        try:
            battery = psutil.sensors_battery()
        except Exception:
            battery = None

        if battery is None:
            return events

        plugged = bool(battery.power_plugged)
        percent = float(battery.percent)

        if self._last_plugged is None:
            self._last_plugged = plugged
            self._last_percent = percent
            return events

        if plugged != self._last_plugged:
            events.append(
                PowerStateChangedEvent(
                    is_plugged=plugged,
                    battery_percent=percent,
                )
            )
            self._last_plugged = plugged

        self._last_percent = percent
        return events


class EventWatcherCoordinator:
    """Coordinates periodic non-blocking hardware event checks."""

    def __init__(self):
        self.usb_watcher = USBWatcher()
        self.battery_watcher = BatteryWatcher()
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self, interval_sec: float = 3.0) -> None:
        """Start background differential watcher loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop(interval_sec))
        logger.info("EventWatcherCoordinator started", interval=interval_sec)

    async def stop(self) -> None:
        """Stop background watcher loop."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("EventWatcherCoordinator stopped")

    async def _poll_loop(self, interval_sec: float) -> None:
        event_bus = get_event_bus()
        while self._running:
            try:
                # 1. USB Checks
                conn, disconn = self.usb_watcher.check_diffs()
                for c_ev in conn:
                    logger.info("USB device connected", mount=c_ev.mountpoint)
                    await event_bus.publish(c_ev)
                for d_ev in disconn:
                    logger.info("USB device disconnected", mount=d_ev.mountpoint)
                    await event_bus.publish(d_ev)

                # 2. Battery Checks
                p_events = self.battery_watcher.check_diffs()
                for p_ev in p_events:
                    logger.info("Power state changed", plugged=p_ev.is_plugged, pct=p_ev.battery_percent)
                    await event_bus.publish(p_ev)

            except Exception as e:
                logger.error("Error in event watcher loop", error=str(e))

            await asyncio.sleep(interval_sec)


_coordinator_instance: EventWatcherCoordinator | None = None


def get_event_watcher_coordinator() -> EventWatcherCoordinator:
    """Get singleton EventWatcherCoordinator instance."""
    global _coordinator_instance
    if _coordinator_instance is None:
        _coordinator_instance = EventWatcherCoordinator()
    return _coordinator_instance
