"""Monitoring events and data models."""
from dataclasses import dataclass
from nova_app.core.events import Event


@dataclass
class HighCpuAlertEvent(Event):
    cpu_percent: float = 0.0
    threshold: float = 90.0


@dataclass
class HighRamAlertEvent(Event):
    ram_percent: float = 0.0
    threshold: float = 90.0


@dataclass
class LowBatteryAlertEvent(Event):
    battery_percent: float = 0.0
    threshold: float = 20.0


@dataclass
class MetricsSnapshotEvent(Event):
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    disk_percent: float = 0.0
    battery_percent: float | None = None
