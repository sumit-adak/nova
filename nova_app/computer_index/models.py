"""Data transfer models for computer index."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DiscoveredApp:
    name: str
    exec_path: str
    version: str | None = None
    publisher: str | None = None


@dataclass
class IndexedFileDTO:
    path: str
    name: str
    extension: str
    size_bytes: int
    modified_at: datetime
