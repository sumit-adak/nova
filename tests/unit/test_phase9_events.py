"""Unit tests for Phase 9: Event-Driven Awareness (USB, Power, and Event Subscriptions)."""
from collections import namedtuple
from unittest.mock import MagicMock, patch
import pytest
from nova_app.core.events import EventBus
from nova_app.monitoring.event_handlers import (
    handle_power_state_changed,
    handle_usb_connected,
    handle_usb_disconnected,
    register_system_event_handlers,
)
from nova_app.monitoring.event_watchers import BatteryWatcher, USBWatcher
from nova_app.monitoring.models import (
    PowerStateChangedEvent,
    USBConnectedEvent,
    USBDisconnectedEvent,
)

Partition = namedtuple("Partition", ["device", "mountpoint", "fstype", "opts"])
Battery = namedtuple("Battery", ["percent", "power_plugged"])


def test_usb_watcher_differentials():
    watcher = USBWatcher()

    # Initial state
    p1 = Partition(device="C:", mountpoint="C:\\", fstype="NTFS", opts="rw,fixed")
    with patch("psutil.disk_partitions", return_value=[p1]):
        conn, disconn = watcher.check_diffs()
        assert len(conn) == 0
        assert len(disconn) == 0

    # Plug in USB drive E:\
    p2 = Partition(device="E:", mountpoint="E:\\", fstype="FAT32", opts="rw,removable")
    with patch("psutil.disk_partitions", return_value=[p1, p2]):
        conn, disconn = watcher.check_diffs()
        assert len(conn) == 1
        assert conn[0].mountpoint == "E:\\"
        assert conn[0].device == "E:"
        assert len(disconn) == 0

    # Unplug USB drive E:\
    with patch("psutil.disk_partitions", return_value=[p1]):
        conn, disconn = watcher.check_diffs()
        assert len(conn) == 0
        assert len(disconn) == 1
        assert disconn[0].mountpoint == "E:\\"


def test_battery_watcher_state_transition():
    watcher = BatteryWatcher()

    # Initial AC plugged
    b1 = Battery(percent=95.0, power_plugged=True)
    with patch("psutil.sensors_battery", return_value=b1):
        events = watcher.check_diffs()
        assert len(events) == 0  # First reading initializes baseline

    # Unplug AC power
    b2 = Battery(percent=94.0, power_plugged=False)
    with patch("psutil.sensors_battery", return_value=b2):
        events = watcher.check_diffs()
        assert len(events) == 1
        assert events[0].is_plugged is False
        assert events[0].battery_percent == 94.0


@pytest.mark.asyncio
async def test_event_handlers_record_alerts():
    # USB Connected
    await handle_usb_connected(
        USBConnectedEvent(device="E:", mountpoint="E:\\", fstype="FAT32")
    )
    # USB Disconnected
    await handle_usb_disconnected(
        USBDisconnectedEvent(mountpoint="E:\\")
    )
    # Power Changed
    await handle_power_state_changed(
        PowerStateChangedEvent(is_plugged=False, battery_percent=45.0)
    )

    # Register handlers
    register_system_event_handlers()
