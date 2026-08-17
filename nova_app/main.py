"""NOVA application entry point and service bootstrap."""
import argparse
import asyncio
import sys
import structlog
from PySide6.QtWidgets import QApplication

from nova_app.config.settings import Settings, get_settings
from nova_app.config.logging_config import setup_logging
from nova_app.core.async_bridge import get_async_bridge
from nova_app.core.di import Container, get_container
from nova_app.core.events import EventBus, get_event_bus
from nova_app.db.session import init_db, close_db
from nova_app.monitoring.event_handlers import register_system_event_handlers
from nova_app.monitoring.event_watchers import get_event_watcher_coordinator
from nova_app.monitoring.system_monitor import get_system_monitor
from nova_app.ui.main_window import NovaMainWindow
from nova_app.ui.theme import apply_theme

logger = structlog.get_logger(__name__)


async def bootstrap_services(settings: Settings, container: Container, event_bus: EventBus) -> None:
    """Initialize and wire all core services into the DI container."""
    logger.info("Bootstrapping NOVA services", version=settings.app_version)

    # Register core singletons
    container.register_singleton(Settings, settings)
    container.register_singleton(EventBus, event_bus)

    # Initialize Database
    await init_db(settings)
    logger.info("Database initialized successfully", db_url=settings.db_url)

    # Register system event handlers
    register_system_event_handlers()

    # Start system monitor & hardware event watchers
    get_system_monitor().start()
    await get_event_watcher_coordinator().start()


def main() -> int:
    """Main CLI / GUI entry point."""
    parser = argparse.ArgumentParser(description="NOVA — Personal AI Operating Layer")
    parser.add_argument("--dry-run", action="store_true", help="Bootstrap services and exit without GUI")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    settings = get_settings()
    if args.debug:
        settings.debug = True
        settings.log_level = "DEBUG"

    # Setup Logging
    setup_logging(settings)
    logger.info("Starting NOVA", app_name=settings.app_name)

    container = get_container()
    event_bus = get_event_bus()

    # Initialize async bridge loop
    bridge = get_async_bridge()

    # Bootstrap services on the persistent async bridge loop
    bridge.run_coroutine(bootstrap_services(settings, container, event_bus)).result()

    if args.dry_run:
        logger.info("Dry-run bootstrap completed successfully")
        bridge.run_coroutine(close_db()).result()
        bridge.stop()
        return 0

    # Launch PySide6 GUI
    app = QApplication(sys.argv)
    apply_theme(app)
    window = NovaMainWindow(settings=settings)
    window.show()

    exit_code = app.exec()
    bridge.run_coroutine(close_db()).result()
    bridge.stop()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
