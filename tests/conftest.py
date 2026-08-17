"""Test configuration."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@pytest.fixture(autouse=True)
async def init_test_db(tmp_path, monkeypatch):
    """Ensure database tables are initialized and isolated for every test."""
    import nova_app.config.settings as settings_mod
    import nova_app.db.session as session_mod
    from nova_app.config.settings import Settings

    # Reset any cached engine/session_factory
    await session_mod.close_db()

    # Isolate test DB to tmp_path/.nova_test_data
    test_settings = Settings(data_dir=tmp_path / ".nova_test_data")
    monkeypatch.setattr(settings_mod, "_settings_instance", test_settings)

    # Initialize tables
    await session_mod.init_db(test_settings)
    yield
    await session_mod.close_db()


@pytest.fixture
def config_manager(tmp_path):
    from app.core.config import ConfigManager
    return ConfigManager(data_dir=tmp_path)

@pytest.fixture
def registry(config_manager):
    from app.commands import build_registry
    return build_registry(config_manager)

@pytest.fixture
def memory_manager(tmp_path):
    from app.memory.database import Database
    from app.memory.memory_manager import MemoryManager
    db = Database(db_path=tmp_path / "test.db")
    return MemoryManager(db)

