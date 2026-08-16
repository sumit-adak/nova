"""Initial database schema for NOVA.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-16 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Conversations
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )

    # Messages
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_calls_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # Memory Preferences
    op.create_table(
        "memory_preferences",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_memory_preferences_key"), "memory_preferences", ["key"], unique=True)

    # Memory Projects
    op.create_table(
        "memory_projects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("root_path", sa.String(length=512), nullable=False),
        sa.Column("project_type", sa.String(length=64), nullable=False),
        sa.Column("git_remote", sa.String(length=512), nullable=True),
        sa.Column("last_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("root_path")
    )
    op.create_index(op.f("ix_memory_projects_name"), "memory_projects", ["name"], unique=False)

    # Memory Shortcuts
    op.create_table(
        "memory_shortcuts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("phrase", sa.String(length=256), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("default_args_json", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_memory_shortcuts_phrase"), "memory_shortcuts", ["phrase"], unique=True)

    # Memory Task History
    op.create_table(
        "memory_task_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )

    # Indexed Files
    op.create_table(
        "indexed_files",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("extension", sa.String(length=32), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("modified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_indexed_files_path"), "indexed_files", ["path"], unique=True)
    op.create_index(op.f("ix_indexed_files_name"), "indexed_files", ["name"], unique=False)
    op.create_index(op.f("ix_indexed_files_extension"), "indexed_files", ["extension"], unique=False)

    # Installed Apps
    op.create_table(
        "installed_apps",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("exec_path", sa.String(length=1024), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=True),
        sa.Column("publisher", sa.String(length=256), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_installed_apps_name"), "installed_apps", ["name"], unique=True)

    # Detected Projects
    op.create_table(
        "detected_projects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("root_path", sa.String(length=1024), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("project_type", sa.String(length=64), nullable=False),
        sa.Column("vcs", sa.String(length=32), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_detected_projects_root_path"), "detected_projects", ["root_path"], unique=True)
    op.create_index(op.f("ix_detected_projects_name"), "detected_projects", ["name"], unique=False)

    # Permission Policies
    op.create_table(
        "permission_policies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("risk_tier", sa.String(length=32), nullable=False),
        sa.Column("default_mode", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_permission_policies_tool_name"), "permission_policies", ["tool_name"], unique=True)

    # Permission Grants
    op.create_table(
        "permission_grants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("scope_json", sa.Text(), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_permission_grants_tool_name"), "permission_grants", ["tool_name"], unique=False)

    # Append-only Audit Log
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor", sa.String(length=64), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("arguments_json", sa.Text(), nullable=False),
        sa.Column("risk_tier", sa.String(length=32), nullable=False),
        sa.Column("confirmation_required", sa.Boolean(), nullable=False),
        sa.Column("confirmed_by_user", sa.Boolean(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_audit_log_timestamp"), "audit_log", ["timestamp"], unique=False)
    op.create_index(op.f("ix_audit_log_tool_name"), "audit_log", ["tool_name"], unique=False)

    # System Metrics Snapshots
    op.create_table(
        "system_metrics_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cpu_pct", sa.Float(), nullable=False),
        sa.Column("ram_pct", sa.Float(), nullable=False),
        sa.Column("gpu_pct", sa.Float(), nullable=True),
        sa.Column("disk_pct", sa.Float(), nullable=False),
        sa.Column("net_sent_kb", sa.Float(), nullable=False),
        sa.Column("net_recv_kb", sa.Float(), nullable=False),
        sa.Column("battery_pct", sa.Float(), nullable=True),
        sa.Column("temperature_c", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_system_metrics_snapshots_timestamp"), "system_metrics_snapshots", ["timestamp"], unique=False)

    # System Alerts
    op.create_table(
        "system_alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column("message", sa.String(length=512), nullable=False),
        sa.Column("acknowledged", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade() -> None:
    op.drop_table("system_alerts")
    op.drop_table("system_metrics_snapshots")
    op.drop_table("audit_log")
    op.drop_table("permission_grants")
    op.drop_table("permission_policies")
    op.drop_table("detected_projects")
    op.drop_table("installed_apps")
    op.drop_table("indexed_files")
    op.drop_table("memory_task_history")
    op.drop_table("memory_shortcuts")
    op.drop_table("memory_projects")
    op.drop_table("memory_preferences")
    op.drop_table("messages")
    op.drop_table("conversations")
