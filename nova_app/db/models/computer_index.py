"""Computer Index models (IndexedFiles, InstalledApps, Projects)."""
from datetime import datetime, timezone
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from nova_app.db.base import Base


class IndexedFile(Base):
    """File index entries for fast local search without scanning."""
    __tablename__ = "indexed_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path: Mapped[str] = mapped_column(String(1024), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    extension: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    modified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class InstalledApp(Base):
    """Discovered installed Windows applications."""
    __tablename__ = "installed_apps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)
    exec_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(256), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class DetectedProject(Base):
    """Detected software repositories on the host machine."""
    __tablename__ = "detected_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    root_path: Mapped[str] = mapped_column(String(1024), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    project_type: Mapped[str] = mapped_column(String(64), default="generic", nullable=False)
    vcs: Mapped[str] = mapped_column(String(32), default="git", nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
