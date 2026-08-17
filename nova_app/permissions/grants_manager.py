"""Standing permission grants manager with session memory and SQLite persistence."""
from datetime import datetime, timezone
import json
import structlog
from sqlalchemy import select
from nova_app.db.models.permissions import PermissionGrant
from nova_app.db.session import get_session_factory

logger = structlog.get_logger(__name__)


class GrantsManager:
    """Manages active, session-based, and persistent permission grants."""

    def __init__(self):
        # In-memory session grants: tool_name -> set of scopes / flags
        self._session_grants: dict[str, dict] = {}

    def grant_for_session(self, tool_name: str, scope: dict | None = None) -> None:
        """Grant permission for a tool for the duration of the current session."""
        self._session_grants[tool_name] = scope or {}
        logger.info("Granted session permission", tool=tool_name)

    def revoke_session_grant(self, tool_name: str) -> None:
        """Revoke a session grant."""
        if tool_name in self._session_grants:
            del self._session_grants[tool_name]

    def has_session_grant(self, tool_name: str) -> bool:
        """Check if active session grant exists."""
        return tool_name in self._session_grants

    async def add_persistent_grant(
        self,
        tool_name: str,
        scope: dict | None = None,
        expires_at: datetime | None = None,
    ) -> PermissionGrant:
        """Persist a standing permission grant to SQLite DB."""
        session_factory = get_session_factory()
        async with session_factory() as session:
            grant = PermissionGrant(
                tool_name=tool_name,
                scope_json=json.dumps(scope or {}),
                granted_at=datetime.now(timezone.utc),
                expires_at=expires_at,
            )
            session.add(grant)
            await session.commit()
            await session.refresh(grant)
            logger.info("Added persistent permission grant", tool=tool_name, expires_at=expires_at)
            return grant

    async def has_active_grant(self, tool_name: str) -> bool:
        """Check if either a session grant or an unexpired DB grant exists."""
        # 1. Session grant check
        if self.has_session_grant(tool_name):
            return True

        # 2. Database persistent grant check
        session_factory = get_session_factory()
        now = datetime.now(timezone.utc)
        async with session_factory() as session:
            try:
                stmt = select(PermissionGrant).where(PermissionGrant.tool_name == tool_name)
                res = await session.execute(stmt)
                grants = res.scalars().all()

                for g in grants:
                    if g.expires_at is None or g.expires_at > now:
                        return True
            except Exception as e:
                logger.warning("Failed to check active grant from DB", error=str(e))
                return False

        return False

    def clear_session_grants(self) -> None:
        """Clear all session-scoped grants."""
        self._session_grants.clear()


_grants_manager_instance: GrantsManager | None = None


def get_grants_manager() -> GrantsManager:
    """Get singleton GrantsManager instance."""
    global _grants_manager_instance
    if _grants_manager_instance is None:
        _grants_manager_instance = GrantsManager()
    return _grants_manager_instance
