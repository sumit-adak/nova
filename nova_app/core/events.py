"""In-process asynchronous Event Bus for NOVA."""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Type, TypeVar
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Event:
    """Base class for all system events."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


TEvent = TypeVar("TEvent", bound=Event)
EventHandler = Callable[[TEvent], Coroutine[Any, Any, None] | None]


class EventBus:
    """Async-enabled in-process Event Bus with sync and async subscriber support."""

    def __init__(self):
        self._subscribers: dict[Type[Event], list[EventHandler]] = {}

    def subscribe(self, event_type: Type[TEvent], handler: EventHandler) -> None:
        """Subscribe a handler to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: Type[TEvent], handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type."""
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribed handlers asynchronously."""
        event_type = type(event)
        handlers = self._subscribers.get(event_type, []).copy()

        # Also dispatch to handlers subscribed to base Event
        if event_type is not Event and Event in self._subscribers:
            handlers.extend(self._subscribers[Event])

        for handler in handlers:
            try:
                res = handler(event)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                logger.error("Error in event handler", handler=handler.__name__, event=event_type.__name__, error=str(e))

    def publish_sync(self, event: Event) -> None:
        """Publish an event synchronously (runs async handlers in active loop if available)."""
        event_type = type(event)
        handlers = self._subscribers.get(event_type, []).copy()

        if event_type is not Event and Event in self._subscribers:
            handlers.extend(self._subscribers[Event])

        for handler in handlers:
            try:
                res = handler(event)
                if asyncio.iscoroutine(res):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(res)
                    except RuntimeError:
                        asyncio.run(res)
            except Exception as e:
                logger.error("Error in sync event handler", handler=handler.__name__, event=event_type.__name__, error=str(e))

    def clear(self) -> None:
        """Remove all subscriptions."""
        self._subscribers.clear()


# Global default EventBus instance
_global_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Return the global EventBus instance."""
    return _global_event_bus
