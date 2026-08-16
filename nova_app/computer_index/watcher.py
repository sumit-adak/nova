"""Real-time filesystem watcher using Watchdog."""
from dataclasses import dataclass
from pathlib import Path
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer
import structlog
from nova_app.config.settings import Settings, get_settings
from nova_app.core.events import Event, get_event_bus

logger = structlog.get_logger(__name__)


@dataclass
class FileCreatedEvent(Event):
    src_path: str = ""
    is_directory: bool = False


@dataclass
class FileModifiedEvent(Event):
    src_path: str = ""
    is_directory: bool = False


@dataclass
class FileDeletedEvent(Event):
    src_path: str = ""
    is_directory: bool = False


class _NovaWatchdogHandler(FileSystemEventHandler):
    """Dispatches watchdog events into the typed Event Bus."""

    def on_created(self, event: FileSystemEvent) -> None:
        get_event_bus().publish_sync(
            FileCreatedEvent(src_path=str(event.src_path), is_directory=event.is_directory)
        )

    def on_modified(self, event: FileSystemEvent) -> None:
        get_event_bus().publish_sync(
            FileModifiedEvent(src_path=str(event.src_path), is_directory=event.is_directory)
        )

    def on_deleted(self, event: FileSystemEvent) -> None:
        get_event_bus().publish_sync(
            FileDeletedEvent(src_path=str(event.src_path), is_directory=event.is_directory)
        )


class FileWatcher:
    """Manages real-time filesystem observers on allowed directories."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._observer = Observer()
        self._handler = _NovaWatchdogHandler()
        self._is_running = False

    def start(self, directories: list[str | Path] | None = None) -> None:
        """Start watching directories."""
        if self._is_running:
            return

        targets = directories or [self.settings.data_dir]
        for dir_target in targets:
            path = Path(dir_target).resolve()
            if path.exists() and path.is_dir():
                self._observer.schedule(self._handler, str(path), recursive=True)
                logger.info("Watching directory", path=str(path))

        self._observer.start()
        self._is_running = True

    def stop(self) -> None:
        """Stop watching directories."""
        if self._is_running:
            self._observer.stop()
            self._observer.join()
            self._is_running = False
            logger.info("File watcher stopped")
