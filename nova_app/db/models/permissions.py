"""Permissions, Policy Overrides, Grants, and Append-only Audit Log models."""
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from nova_app.db.base import Base


class PermissionPolicy(Base):
    """Configured policy for individual tools."""
    __tablename__ = "permission_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tool_name: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(32), nullable=False)  # READ, LOW, MEDIUM, HIGH, CRITICAL
    default_mode: Mapped[str] = mapped_column(String(32), default="confirm", nullable=False)  # auto, confirm, deny
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class PermissionGrant(Base):
    """Standing permission grant with optional scope and expiration."""
    __tablename__ = "permission_grants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tool_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    scope_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLogEntry(Base):
    """Append-only audit log table recording every tool call attempt and outcome."""
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False
    )
    actor: Mapped[str] = mapped_column(String(64), default="ai", nullable=False)  # ai, user, scheduled
    tool_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    arguments_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(32), nullable=False)
    confirmation_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confirmed_by_user: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
