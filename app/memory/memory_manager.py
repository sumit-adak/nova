"""User preference memory management."""

from __future__ import annotations

from app.memory.database import Database


class MemoryManager:
    """High-level memory operations for user preferences."""

    FORBIDDEN_KEYS = {"api_key", "password", "secret", "token", "credential"}

    def __init__(self, db: Database | None = None) -> None:
        self.db = db or Database()

    def _is_safe_key(self, key: str) -> bool:
        key_lower = key.lower()
        return not any(forbidden in key_lower for forbidden in self.FORBIDDEN_KEYS)

    def remember(self, key: str, value: str, category: str = "preference") -> bool:
        if not self._is_safe_key(key):
            return False
        self.db.set_memory(key, value, category)
        return True

    def recall(self, key: str) -> str | None:
        return self.db.get_memory(key)

    def forget(self, key: str) -> bool:
        return self.db.delete_memory(key)

    def get_all(self) -> list[dict]:
        return self.db.get_all_memory()

    def clear_all(self) -> int:
        return self.db.clear_memory()

    def get_context(self) -> dict[str, str]:
        """Return memory items useful for AI context."""
        items = self.db.get_all_memory()
        return {item["key"]: item["value"] for item in items[:20]}
