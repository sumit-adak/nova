"""Event subscription handlers reacting to system and hardware events."""
from datetime import datetime, timezone
import structlog
from nova_app.computer_index.indexer import get_computer_indexer
from nova_app.core.events import get_event_bus
from nova_app.db.models.monitoring import SystemAlert
from nova_app.db.session import get_session_factory
from nova_app.monitoring.models import (
    PowerStateChangedEvent,
    SystemAlertEvent,
    USBConnectedEvent,
    USBDisconnectedEvent,
)

logger = structlog.get_logger(__name__)


async def handle_usb_connected(event: USBConnectedEvent) -> None:
    """Record USB alert and index new mountpoint."""
    logger.info("Handling USB Connected Event", mountpoint=event.mountpoint)
    session_factory = get_session_factory()
    async with session_factory() as session:
        alert = SystemAlert(
            alert_type="usb_connected",
            message=f"USB drive connected at {event.mountpoint} ({event.device})",
            timestamp=datetime.now(timezone.utc),
        )
        session.add(alert)
        await session.commit()


async def handle_usb_disconnected(event: USBDisconnectedEvent) -> None:
    """Record USB disconnect alert."""
    logger.info("Handling USB Disconnected Event", mountpoint=event.mountpoint)
    session_factory = get_session_factory()
    async with session_factory() as session:
        alert = SystemAlert(
            alert_type="usb_disconnected",
            message=f"USB drive disconnected from {event.mountpoint}",
            timestamp=datetime.now(timezone.utc),
        )
        session.add(alert)
        await session.commit()


async def handle_power_state_changed(event: PowerStateChangedEvent) -> None:
    """Record power transition alert."""
    state_str = "AC Power Connected" if event.is_plugged else "Running on Battery"
    logger.info("Handling Power State Changed", state=state_str, battery=event.battery_percent)
    session_factory = get_session_factory()
    async with session_factory() as session:
        alert = SystemAlert(
            alert_type="power_changed",
            message=f"{state_str} (Battery: {event.battery_percent}%)",
            timestamp=datetime.now(timezone.utc),
        )
        session.add(alert)
        await session.commit()


def register_system_event_handlers() -> None:
    """Wire event handlers into global EventBus."""
    bus = get_event_bus()
    bus.subscribe(USBConnectedEvent, handle_usb_connected)
    bus.subscribe(USBDisconnectedEvent, handle_usb_disconnected)
    bus.subscribe(PowerStateChangedEvent, handle_power_state_changed)
    logger.info("System event handlers registered with EventBus")
