"""Local filesystem indexer for fast search."""
import os
from datetime import datetime, timezone
from pathlib import Path
import structlog
from sqlalchemy import select
from nova_app.config.settings import Settings, get_settings
from nova_app.db.models.computer_index import IndexedFile
from nova_app.db.session import get_session_factory

logger = structlog.get_logger(__name__)


class FileIndexer:
    """Indexes files in allowed directories into the SQLite indexed_files table."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    async def index_directory(self, target_dir: Path | str, max_files: int = 5000) -> int:
        """Index files from a target directory."""
        dir_path = Path(target_dir).resolve()
        if not dir_path.is_dir():
            return 0

        session_factory = get_session_factory()
        indexed_count = 0

        async with session_factory() as session:
            for root, dirs, files in os.walk(dir_path):
                # Ignore hidden and noisy dependency folders
                dirs[:] = [
                    d for d in dirs
                    if not d.startswith(".")
                    and d not in ["node_modules", ".venv", "venv", "__pycache__", "dist", "build"]
                ]

                for f in files:
                    if f.startswith("."):
                        continue

                    full_path = Path(root) / f
                    try:
                        stat = full_path.stat()
                        mod_time = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                        path_str = str(full_path)

                        # Upsert check
                        stmt = select(IndexedFile).where(IndexedFile.path == path_str)
                        result = await session.execute(stmt)
                        existing = result.scalar_one_or_none()

                        if existing:
                            existing.name = f
                            existing.extension = full_path.suffix.lower()
                            existing.size_bytes = stat.st_size
                            existing.modified_at = mod_time
                            existing.indexed_at = datetime.now(timezone.utc)
                        else:
                            item = IndexedFile(
                                path=path_str,
                                name=f,
                                extension=full_path.suffix.lower(),
                                size_bytes=stat.st_size,
                                modified_at=mod_time,
                                indexed_at=datetime.now(timezone.utc),
                            )
                            session.add(item)

                        indexed_count += 1
                        if indexed_count >= max_files:
                            break
                    except (OSError, PermissionError):
                        continue

                if indexed_count >= max_files:
                    break

            await session.commit()

        logger.info("File indexing finished", directory=str(dir_path), indexed_count=indexed_count)
        return indexed_count
