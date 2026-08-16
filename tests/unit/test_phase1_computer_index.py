"""Unit tests for Computer Index and Monitoring subsystems."""
import pytest
from pathlib import Path
from nova_app.computer_index.indexer import FileIndexer
from nova_app.computer_index.app_registry import WindowsAppRegistry
from nova_app.monitoring.system_monitor import SystemMonitorService


@pytest.mark.asyncio
async def test_file_indexer(tmp_path):
    # Setup files in tmp_path
    (tmp_path / "file1.txt").write_text("content1")
    (tmp_path / "file2.py").write_text("content2")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "file3.json").write_text("{}")

    indexer = FileIndexer()
    indexed_count = await indexer.index_directory(tmp_path)
    assert indexed_count == 3


def test_app_registry_scanning():
    registry = WindowsAppRegistry()
    apps = registry.scan_windows_registry()
    # On Windows, registry should discover installed applications or return list
    assert isinstance(apps, list)


@pytest.mark.asyncio
async def test_system_monitor_snapshot():
    monitor = SystemMonitorService()
    snapshot = await monitor.collect_snapshot()

    assert snapshot.cpu_pct >= 0.0
    assert snapshot.ram_pct > 0.0
    assert snapshot.disk_pct >= 0.0
