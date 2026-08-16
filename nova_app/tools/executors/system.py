"""System introspection, volume control, and screenshot executors."""
from datetime import datetime
from pathlib import Path
from typing import Any
import psutil
from pydantic import BaseModel, Field
from nova_app.config.settings import get_settings


class GetSystemStatsArgs(BaseModel):
    include_disks: bool = Field(default=True, description="Whether to include disk usage details")


class SetVolumeArgs(BaseModel):
    level: int = Field(ge=0, le=100, description="Target volume level percentage between 0 and 100")


class TakeScreenshotArgs(BaseModel):
    save_path: str | None = Field(default=None, description="Optional custom destination path")


def get_system_stats_executor(args: GetSystemStatsArgs) -> dict[str, Any]:
    """Inspect real-time CPU, RAM, Disk, and Battery metrics."""
    cpu_percent = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory()

    # Disk usage
    disk_info = []
    if args.include_disks:
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disk_info.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "total_gb": round(usage.total / (1024 ** 3), 2),
                    "used_gb": round(usage.used / (1024 ** 3), 2),
                    "free_gb": round(usage.free / (1024 ** 3), 2),
                    "percent": usage.percent,
                })
            except (PermissionError, OSError):
                continue

    # Battery
    battery = psutil.sensors_battery()
    battery_info = None
    if battery:
        battery_info = {
            "percent": battery.percent,
            "power_plugged": battery.power_plugged,
            "seconds_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None,
        }

    return {
        "cpu": {
            "percent": cpu_percent,
            "cores_logical": psutil.cpu_count(logical=True),
            "cores_physical": psutil.cpu_count(logical=False),
        },
        "ram": {
            "total_gb": round(ram.total / (1024 ** 3), 2),
            "used_gb": round(ram.used / (1024 ** 3), 2),
            "free_gb": round(ram.available / (1024 ** 3), 2),
            "percent": ram.percent,
        },
        "disks": disk_info,
        "battery": battery_info,
    }


def set_volume_executor(args: SetVolumeArgs) -> dict[str, Any]:
    """Set Windows master volume level using pycaw or comtypes."""
    target_scalar = args.level / 100.0

    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        from ctypes import cast, POINTER

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(target_scalar, None)
        return {
            "status": "success",
            "volume_percent": args.level,
        }
    except Exception as e:
        # Fallback or error report
        return {
            "status": "warning",
            "message": f"Volume controller fallback: {str(e)}",
            "requested_level": args.level,
        }


def take_screenshot_executor(args: TakeScreenshotArgs) -> dict[str, Any]:
    """Capture full desktop screenshot and save to screenshots directory."""
    import pyautogui

    settings = get_settings()
    screenshots_dir = settings.data_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    if args.save_path:
        dest = Path(args.save_path)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = screenshots_dir / f"screenshot_{timestamp}.png"

    screenshot = pyautogui.screenshot()
    screenshot.save(dest)

    return {
        "status": "saved",
        "path": str(dest),
        "filename": dest.name,
        "size_bytes": dest.stat().st_size if dest.exists() else 0,
    }
