"""Computer Index subsystem."""
from nova_app.computer_index.app_registry import WindowsAppRegistry
from nova_app.computer_index.indexer import FileIndexer
from nova_app.computer_index.models import DiscoveredApp, IndexedFileDTO
from nova_app.computer_index.watcher import (
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileWatcher,
)

__all__ = [
    "WindowsAppRegistry",
    "FileIndexer",
    "FileWatcher",
    "DiscoveredApp",
    "IndexedFileDTO",
    "FileCreatedEvent",
    "FileModifiedEvent",
    "FileDeletedEvent",
]
