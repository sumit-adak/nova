"""SQLite database for NOVA memory and activity."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from app.core.config import DATA_DIR
from app.core.logger import get_logger

logger = get_logger("database")


class Database:
    """SQLite database manager."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DATA_DIR / "nova.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'preference',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_command TEXT NOT NULL,
                    intent_action TEXT,
                    intent_params TEXT,
                    result_message TEXT,
                    status TEXT NOT NULL
                );
            """)

    def set_memory(self, key: str, value: str, category: str = "preference") -> None:
        now = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO memory (key, value, category, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET
                   value=excluded.value, category=excluded.category, updated_at=excluded.updated_at""",
                (key, value, category, now, now),
            )

    def get_memory(self, key: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM memory WHERE key=?", (key,)).fetchone()
            return row["value"] if row else None

    def get_all_memory(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT key, value, category, updated_at FROM memory ORDER BY updated_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def delete_memory(self, key: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM memory WHERE key=?", (key,))
            return cursor.rowcount > 0

    def clear_memory(self) -> int:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM memory")
            return cursor.rowcount

    def log_activity(
        self,
        user_command: str,
        intent_action: str | None,
        intent_params: str,
        result_message: str,
        status: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO activity
                   (timestamp, user_command, intent_action, intent_params, result_message, status)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    datetime.now().isoformat(),
                    user_command,
                    intent_action,
                    intent_params,
                    result_message,
                    status,
                ),
            )

    def get_activity(self, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM activity ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def clear_activity(self) -> int:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM activity")
            return cursor.rowcount
