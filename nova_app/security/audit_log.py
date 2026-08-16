"""Append-only audit logger writing to SQLite audit_log table."""
import json
import time
from datetime import datetime, timezone
from typing import Any
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from nova_app.db.models.permissions import AuditLogEntry
from nova_app.db.session import get_session_factory

logger = structlog.get_logger(__name__)


class AuditLogger:
    """Records all tool call attempts, confirmations, and results to an append-only audit table."""

    async def log_action(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        risk_tier: str,
        actor: str = "ai",
        confirmation_required: bool = False,
        confirmed_by_user: bool | None = None,
        result_data: Any = None,
        error_message: str | None = None,
        duration_ms: float = 0.0,
    ) -> AuditLogEntry:
        """Append an entry to the audit log."""
        session_factory = get_session_factory()
        async with session_factory() as session:
            entry = AuditLogEntry(
                timestamp=datetime.now(timezone.utc),
                actor=actor,
                tool_name=tool_name,
                arguments_json=json.dumps(arguments, default=str),
                risk_tier=risk_tier,
                confirmation_required=confirmation_required,
                confirmed_by_user=confirmed_by_user,
                result_json=json.dumps(result_data, default=str) if result_data is not None else None,
                error_message=error_message,
                duration_ms=duration_ms,
            )
            session.add(entry)
            await session.commit()
            await session.refresh(entry)

            logger.info(
                "Audit log recorded",
                tool=tool_name,
                risk=risk_tier,
                duration_ms=duration_ms,
                success=error_message is None,
            )
            return entry


_audit_logger_instance: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get singleton AuditLogger instance."""
    global _audit_logger_instance
    if _audit_logger_instance is None:
        _audit_logger_instance = AuditLogger()
    return _audit_logger_instance
