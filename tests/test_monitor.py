"""Tests for system monitoring."""

from app.system_monitor.monitor import SystemMonitor
from app.system_monitor.gpu import GPUMonitor


def test_monitor_snapshot():
    monitor = SystemMonitor()
    snap = monitor.get_snapshot()
    assert "cpu_percent" in snap
    assert "memory_percent" in snap
    assert "disk_percent" in snap
    assert "gpu" in snap


def test_gpu_fallback():
    gpu = GPUMonitor()
    usage = gpu.get_usage()
    assert "available" in usage
    assert "load" in usage
