"""Retention policies and periodic pruning for memory and history records."""
from datetime import datetime, timedelta, timezone
import structlog
from sqlalchemy import delete, select
from nova_app.db.models.conversation import Message
from nova_app.db.models.memory import MemoryTaskHistory
from nova_app.db.session import get_session_factory

logger = structlog.get_logger(__name__)


class RetentionManager:
    """Manages TTL-based pruning and historical record limits."""

    async def prune_task_history(self, max_records: int = 500) -> int:
        """Keep only the latest max_records in task history."""
        session_factory = get_session_factory()
        async with session_factory() as session:
            # Find ID cutoff
            stmt = (
                select(MemoryTaskHistory.id)
                .order_by(MemoryTaskHistory.created_at.desc())
                .offset(max_records)
                .limit(1)
            )
            res = await session.execute(stmt)
            cutoff_id = res.scalar_one_or_none()

            if cutoff_id is not None:
                del_stmt = delete(MemoryTaskHistory).where(MemoryTaskHistory.id <= cutoff_id)
                del_res = await session.execute(del_stmt)
                await session.commit()
                logger.info("Pruned task history", deleted_count=del_res.rowcount)
                return del_res.rowcount

        return 0

    async def prune_old_messages(self, days: int = 90) -> int:
        """Delete messages older than specified days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        session_factory = get_session_factory()
        async with session_factory() as session:
            del_stmt = delete(Message).where(Message.created_at < cutoff_date)
            del_res = await session.execute(del_stmt)
            await session.commit()
            logger.info("Pruned old messages", deleted_count=del_res.rowcount, cutoff=cutoff_date)
            return del_res.rowcount


_retention_manager_instance: RetentionManager | None = None


def get_retention_manager() -> RetentionManager:
    """Get singleton RetentionManager instance."""
    global _retention_manager_instance
    if _retention_manager_instance is None:
        _retention_manager_instance = RetentionManager()
    return _retention_manager_instance
