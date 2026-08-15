"""Test configuration."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
