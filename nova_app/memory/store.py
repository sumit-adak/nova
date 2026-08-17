"""SQLite Memory Store for Preferences, Projects, Shortcuts, and Task History."""
from datetime import datetime, timezone
import json
from typing import Any
import structlog
from sqlalchemy import delete, desc, select
from nova_app.db.models.memory import (
    MemoryPreference,
    MemoryProject,
    MemoryShortcut,
    MemoryTaskHistory,
)
from nova_app.db.session import get_session_factory
from nova_app.memory.models import MemoryContext, PreferenceItem, ProjectMemoryItem, ShortcutItem, TaskHistoryItem
from nova_app.memory.secret_guard import get_secret_guard

logger = structlog.get_logger(__name__)


class MemoryStore:
    """Manages memory persistence and contextual retrieval."""

    def __init__(self):
        self.guard = get_secret_guard()

    # Preferences
    async def set_preference(self, key: str, value: str) -> None:
        """Store or update a preference after SecretGuard validation."""
        self.guard.validate_content(key, value)

        session_factory = get_session_factory()
        async with session_factory() as session:
            stmt = select(MemoryPreference).where(MemoryPreference.key == key)
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()

            if existing:
                existing.value = value
                existing.updated_at = datetime.now(timezone.utc)
            else:
                session.add(
                    MemoryPreference(
                        key=key,
                        value=value,
                        updated_at=datetime.now(timezone.utc),
                    )
                )
            await session.commit()
            logger.info("Saved preference", key=key)

    async def get_preference(self, key: str, default: str | None = None) -> str | None:
        """Retrieve preference value by key."""
        session_factory = get_session_factory()
        async with session_factory() as session:
            stmt = select(MemoryPreference).where(MemoryPreference.key == key)
            res = await session.execute(stmt)
            pref = res.scalar_one_or_none()
            return pref.value if pref else default

    async def list_preferences(self) -> dict[str, str]:
        """List all stored preferences."""
        session_factory = get_session_factory()
        async with session_factory() as session:
            stmt = select(MemoryPreference)
            res = await session.execute(stmt)
            prefs = res.scalars().all()
            return {p.key: p.value for p in prefs}

    async def delete_preference(self, key: str) -> bool:
        """Delete a preference."""
        session_factory = get_session_factory()
        async with session_factory() as session:
            stmt = delete(MemoryPreference).where(MemoryPreference.key == key)
            res = await session.execute(stmt)
            await session.commit()
            return res.rowcount > 0

    # Shortcuts
    async def set_shortcut(self, phrase: str, tool_name: str, default_args: dict[str, Any] | None = None) -> None:
        """Save a voice or text shortcut."""
        clean_phrase = phrase.strip().lower()
        args_json = json.dumps(default_args or {})
        self.guard.validate_content(clean_phrase, args_json)

        session_factory = get_session_factory()
        async with session_factory() as session:
            stmt = select(MemoryShortcut).where(MemoryShortcut.phrase == clean_phrase)
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()

            if existing:
                existing.tool_name = tool_name
                existing.default_args_json = args_json
            else:
                session.add(
                    MemoryShortcut(
                        phrase=clean_phrase,
                        tool_name=tool_name,
                        default_args_json=args_json,
                    )
                )
            await session.commit()

    async def get_shortcut(self, phrase: str) -> ShortcutItem | None:
        """Get matching shortcut for a phrase."""
        clean_phrase = phrase.strip().lower()
        session_factory = get_session_factory()
        async with session_factory() as session:
            stmt = select(MemoryShortcut).where(MemoryShortcut.phrase == clean_phrase)
            res = await session.execute(stmt)
            sc = res.scalar_one_or_none()
            if sc:
                return ShortcutItem(
                    phrase=sc.phrase,
                    tool_name=sc.tool_name,
                    default_args=json.loads(sc.default_args_json),
                )
        return None

    # Context Retrieval Ranking
    async def retrieve_context(self, query: str | None = None, limit: int = 5) -> MemoryContext:
        """
        Rank and retrieve relevant memory context (preferences, recent projects, recent tasks)
        for injection into the AI Intent Engine.
        """
        prefs = await self.list_preferences()

        session_factory = get_session_factory()
        recent_projs = []
        recent_tasks = []

        async with session_factory() as session:
            # Recent projects
            p_stmt = (
                select(MemoryProject)
                .order_by(desc(MemoryProject.last_opened_at))
                .limit(limit)
            )
            p_res = await session.execute(p_stmt)
            recent_projs = [f"{p.name} ({p.root_path})" for p in p_res.scalars().all()]

            # Recent tasks
            t_stmt = (
                select(MemoryTaskHistory)
                .order_by(desc(MemoryTaskHistory.created_at))
                .limit(limit)
            )
            t_res = await session.execute(t_stmt)
            recent_tasks = [t.description for t in t_res.scalars().all()]

        return MemoryContext(
            preferences=prefs,
            recent_projects=recent_projs,
            recent_tasks=recent_tasks,
        )


_memory_store_instance: MemoryStore | None = None


def get_memory_store() -> MemoryStore:
    """Get singleton MemoryStore instance."""
    global _memory_store_instance
    if _memory_store_instance is None:
        _memory_store_instance = MemoryStore()
    return _memory_store_instance
