"""System monitoring data structures and event definitions."""
from dataclasses import dataclass
from typing import Any
from pydantic import BaseModel, Field
from nova_app.core.events import Event


class SystemMetrics(BaseModel):
    cpu_percent: float = Field(description="Total CPU usage percent")
    ram_percent: float = Field(description="Total RAM usage percent")
    ram_used_gb: float = Field(description="RAM used in Gigabytes")
    ram_total_gb: float = Field(description="Total RAM in Gigabytes")
    disk_percent: float = Field(default=0.0, description="Primary disk usage percent")
    disk_free_gb: float = Field(default=0.0, description="Primary disk free in Gigabytes")
    battery_percent: float | None = Field(default=None, description="Battery level percent")
    power_plugged: bool | None = Field(default=None, description="Whether AC power is plugged in")

    @property
    def cpu_pct(self) -> float:
        return self.cpu_percent

    @property
    def ram_pct(self) -> float:
        return self.ram_percent

    @property
    def disk_pct(self) -> float:
        return self.disk_percent

    @property
    def battery_pct(self) -> float | None:
        return self.battery_percent


@dataclass
class MetricsSnapshotEvent(Event):
    """Event emitted whenever a new periodic metric snapshot is recorded."""
    metrics: SystemMetrics | None = None


@dataclass
class HighCpuAlertEvent(Event):
    """Event emitted when CPU usage exceeds threshold."""
    cpu_percent: float = 0.0
    threshold: float = 85.0


@dataclass
class HighRamAlertEvent(Event):
    """Event emitted when RAM usage exceeds threshold."""
    ram_percent: float = 0.0
    threshold: float = 90.0


@dataclass
class LowBatteryAlertEvent(Event):
    """Event emitted when battery falls below critical threshold."""
    battery_percent: float = 0.0
    threshold: float = 20.0


@dataclass
class SystemAlertEvent(Event):
    """Generic event emitted when a resource exceeds high threshold."""
    metric_name: str = ""
    current_value: float = 0.0
    threshold_value: float = 0.0
    severity: str = "warning"  # info, warning, critical


@dataclass
class USBConnectedEvent(Event):
    """Event emitted when a USB drive/storage is plugged in."""
    device: str = ""
    mountpoint: str = ""
    fstype: str = ""


@dataclass
class USBDisconnectedEvent(Event):
    """Event emitted when a USB drive/storage is unplugged."""
    mountpoint: str = ""


@dataclass
class PowerStateChangedEvent(Event):
    """Event emitted when AC power or battery status changes."""
    is_plugged: bool = False
    battery_percent: float | None = None


@dataclass
class AppInstalledEvent(Event):
    """Event emitted when a new software application is detected."""
    app_name: str = ""
    install_location: str | None = None
