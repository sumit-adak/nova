"""Global Emergency Stop kill-switch."""
from dataclasses import dataclass
from nova_app.core.events import Event, get_event_bus


@dataclass
class EmergencyStopStateChangedEvent(Event):
    is_active: bool = False
    reason: str = ""


class EmergencyStop:
    """Global kill-switch that blocks execution of all mutating and high-risk tools immediately."""

    def __init__(self):
        self._is_active: bool = False
        self._reason: str = ""

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def reason(self) -> str:
        return self._reason

    def trigger(self, reason: str = "Emergency stop requested by user") -> None:
        """Activate the emergency kill-switch."""
        self._is_active = True
        self._reason = reason
        get_event_bus().publish_sync(EmergencyStopStateChangedEvent(is_active=True, reason=reason))

    def reset(self) -> None:
        """Reset the emergency kill-switch."""
        self._is_active = False
        self._reason = ""
        get_event_bus().publish_sync(EmergencyStopStateChangedEvent(is_active=False, reason=""))


_emergency_stop_instance = EmergencyStop()


def get_emergency_stop() -> EmergencyStop:
    """Get singleton EmergencyStop instance."""
    return _emergency_stop_instance
