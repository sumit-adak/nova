"""Unit tests for Phase 0: Scaffolding, DI Container, Event Bus, Config, and DB."""
import pytest
from dataclasses import dataclass
from sqlalchemy import select
from nova_app.config.settings import Settings
from nova_app.core.di import Container
from nova_app.core.events import Event, EventBus
from nova_app.core.exceptions import (
    NovaError,
    SecurityError,
    PermissionDeniedError,
    ToolExecutionError,
    EmergencyStopActiveError
)
from nova_app.db.base import Base
from nova_app.db.models import (
    Conversation,
    Message,
    MemoryPreference,
    MemoryProject,
    IndexedFile,
    InstalledApp,
    PermissionPolicy,
    AuditLogEntry,
    SystemMetricsSnapshot,
)
from nova_app.db.session import create_async_engine, async_sessionmaker, AsyncSession


def test_di_container_singleton_and_factory():
    container = Container()

    class ServiceA:
        def __init__(self, val: int):
            self.val = val

    class ServiceB:
        def __init__(self, service_a: ServiceA):
            self.service_a = service_a

    # Register singleton
    a = ServiceA(42)
    container.register_singleton(ServiceA, a)
    assert container.has(ServiceA)
    assert container.resolve(ServiceA).val == 42

    # Register factory
    container.register_factory(ServiceB, lambda c: ServiceB(c.resolve(ServiceA)))
    assert container.has(ServiceB)
    resolved_b = container.resolve(ServiceB)
    assert resolved_b.service_a.val == 42

    # Unregistered service raises KeyError
    class UnregisteredService:
        pass

    with pytest.raises(KeyError):
        container.resolve(UnregisteredService)


@pytest.mark.asyncio
async def test_event_bus_pub_sub():
    event_bus = EventBus()

    @dataclass
    class CustomAlertEvent(Event):
        alert_text: str = ""

    received_events = []

    async def async_handler(evt: CustomAlertEvent):
        received_events.append(evt.alert_text)

    event_bus.subscribe(CustomAlertEvent, async_handler)

    test_event = CustomAlertEvent(alert_text="High CPU Warning")
    await event_bus.publish(test_event)

    assert len(received_events) == 1
    assert received_events[0] == "High CPU Warning"

    # Unsubscribe
    event_bus.unsubscribe(CustomAlertEvent, async_handler)
    await event_bus.publish(CustomAlertEvent(alert_text="Ignored"))
    assert len(received_events) == 1


def test_settings_defaults():
    settings = Settings()
    assert settings.app_name == "NOVA"
    assert "C:\\Windows" in settings.blocked_paths
    assert len(settings.allowed_roots) > 0
    assert settings.db_filename == "nova.db"


def test_exceptions_hierarchy():
    err = EmergencyStopActiveError("Emergency stop triggered", {"source": "ui"})
    assert isinstance(err, SecurityError)
    assert isinstance(err, NovaError)
    assert err.details["source"] == "ui"


@pytest.mark.asyncio
async def test_db_schema_and_models(tmp_path):
    test_db_path = tmp_path / "test_nova.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{test_db_path.as_posix()}", future=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Create conversation & message
        conv = Conversation(title="Test Session")
        session.add(conv)
        await session.flush()

        msg = Message(conversation_id=conv.id, role="user", content="Hello NOVA")
        session.add(msg)

        # Create Preference
        pref = MemoryPreference(key="theme", value="dark")
        session.add(pref)

        # Create Audit Log Entry
        audit = AuditLogEntry(
            actor="user",
            tool_name="test_tool",
            arguments_json="{}",
            risk_tier="LOW",
            confirmation_required=False,
            result_json='{"status": "ok"}'
        )
        session.add(audit)

        await session.commit()

    # Query back
    async with session_factory() as session:
        result = await session.execute(select(Conversation))
        conversations = result.scalars().all()
        assert len(conversations) == 1
        assert conversations[0].title == "Test Session"

        pref_result = await session.execute(select(MemoryPreference).where(MemoryPreference.key == "theme"))
        saved_pref = pref_result.scalar_one()
        assert saved_pref.value == "dark"

    await engine.dispose()
