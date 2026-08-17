"""System monitoring package."""
from nova_app.monitoring.event_handlers import register_system_event_handlers
from nova_app.monitoring.event_watchers import (
    BatteryWatcher,
    EventWatcherCoordinator,
    USBWatcher,
    get_event_watcher_coordinator,
)
from nova_app.monitoring.models import (
    AppInstalledEvent,
    PowerStateChangedEvent,
    SystemAlertEvent,
    SystemMetrics,
    USBConnectedEvent,
    USBDisconnectedEvent,
)
from nova_app.monitoring.system_monitor import (
    SystemMonitorService,
    get_system_monitor,
)

__all__ = [
    "SystemMetrics",
    "SystemAlertEvent",
    "USBConnectedEvent",
    "USBDisconnectedEvent",
    "PowerStateChangedEvent",
    "AppInstalledEvent",
    "SystemMonitorService",
    "get_system_monitor",
    "USBWatcher",
    "BatteryWatcher",
    "EventWatcherCoordinator",
    "get_event_watcher_coordinator",
    "register_system_event_handlers",
]
