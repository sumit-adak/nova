"""Pydantic data schemas for Memory subsystem."""
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field


class PreferenceItem(BaseModel):
    key: str
    value: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectMemoryItem(BaseModel):
    name: str
    root_path: str
    project_type: str = "unknown"
    git_remote: str | None = None
    last_opened_at: datetime | None = None


class ShortcutItem(BaseModel):
    phrase: str
    tool_name: str
    default_args: dict[str, Any] = Field(default_factory=dict)


class TaskHistoryItem(BaseModel):
    id: int | None = None
    description: str
    status: str = "completed"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class MemoryContext(BaseModel):
    """Aggregated memory context injected into AI prompts."""
    preferences: dict[str, str] = Field(default_factory=dict)
    recent_projects: list[str] = Field(default_factory=list)
    recent_tasks: list[str] = Field(default_factory=list)
