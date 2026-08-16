"""Memory subsystem ORM models (preferences, projects, shortcuts, task history)."""
from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from nova_app.db.base import Base


class MemoryPreference(Base):
    """User preferences stored locally."""
    __tablename__ = "memory_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class MemoryProject(Base):
    """Remembered developer project directories and contexts."""
    __tablename__ = "memory_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    root_path: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    project_type: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)  # python, node, rust, etc.
    git_remote: Mapped[str | None] = mapped_column(String(512), nullable=True)
    last_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MemoryShortcut(Base):
    """Custom voice or text shortcuts mapped to actions."""
    __tablename__ = "memory_shortcuts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phrase: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    default_args_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)


class MemoryTaskHistory(Base):
    """History of high-level tasks performed."""
    __tablename__ = "memory_task_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)  # pending, completed, failed
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
