"""Utility commands: screenshots, volume, timers, etc."""

from __future__ import annotations

import asyncio
import datetime
from pathlib import Path

from app.commands.registry import ActionResult
from app.core.config import BASE_DIR
from app.core.logger import get_logger

logger = get_logger("utilities")

# Active timers storage
_active_timers: dict[str, asyncio.Task] = {}


class UtilityCommands:
    """Miscellaneous utility operations."""

    def __init__(self) -> None:
        self.screenshot_dir = BASE_DIR / "data" / "screenshots"
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    async def take_screenshot(self, filename: str = "") -> ActionResult:
        """Capture a screenshot of the primary display."""
        try:
            import pyautogui

            if not filename:
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{ts}.png"
            path = self.screenshot_dir / filename
            screenshot = pyautogui.screenshot()
            screenshot.save(str(path))
            logger.info("Screenshot saved: %s", path)
            return ActionResult(
                success=True,
                message=f"Screenshot saved to {path.name}",
                data={"path": str(path)},
            )
        except ImportError:
            return ActionResult(
                success=False,
                message="Screenshot feature requires pyautogui.",
            )
        except Exception as exc:
            return ActionResult(success=False, message=f"Screenshot failed: {exc}")

    async def set_volume(self, level: int) -> ActionResult:
        """Set system volume level (0-100)."""
        level = max(0, min(100, int(level)))
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            return ActionResult(success=True, message=f"Volume set to {level}%.")
        except ImportError:
            return ActionResult(
                success=False,
                message="Volume control requires pycaw. Install with: pip install pycaw",
            )
        except Exception as exc:
            return ActionResult(success=False, message=f"Volume control failed: {exc}")

    async def start_timer(self, seconds: int, label: str = "Timer") -> ActionResult:
        """Start a countdown timer."""
        seconds = max(1, int(seconds))
        timer_id = f"{label}_{seconds}"

        async def _timer_callback() -> None:
            await asyncio.sleep(seconds)
            logger.info("Timer '%s' completed after %d seconds", label, seconds)
            _active_timers.pop(timer_id, None)

        if timer_id in _active_timers:
            _active_timers[timer_id].cancel()

        task = asyncio.create_task(_timer_callback())
        _active_timers[timer_id] = task

        mins, secs = divmod(seconds, 60)
        time_str = f"{mins}m {secs}s" if mins else f"{secs}s"
        return ActionResult(
            success=True,
            message=f"Timer '{label}' set for {time_str}.",
            data={"seconds": seconds, "label": label},
        )

    async def run_dev_command(self, command: str) -> ActionResult:
        """Run an approved developer command (requires confirmation)."""
        allowed_prefixes = (
            "git status", "git log", "git diff", "git branch",
            "npm run", "npm test", "npm start",
            "python -m pytest", "python -m pip list",
            "pip list", "node -v", "python --version",
        )
        cmd_lower = command.lower().strip()
        if not any(cmd_lower.startswith(p) for p in allowed_prefixes):
            return ActionResult(
                success=False,
                requires_confirmation=True,
                confirmation_message=(
                    f"Run developer command?\n\n{command}\n\nThis command was not "
                    "in the pre-approved list. Continue?"
                ),
                data={"command": command, "action": "run_dev_command_confirmed"},
            )
        return ActionResult(
            success=False,
            requires_confirmation=True,
            confirmation_message=f"Run command: {command}?",
            data={"command": command, "action": "run_dev_command_confirmed"},
        )

    async def run_dev_command_confirmed(self, command: str) -> ActionResult:
        """Execute developer command after confirmation."""
        import subprocess

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(Path.home()),
            )
            output = result.stdout or result.stderr or "(no output)"
            if len(output) > 500:
                output = output[:500] + "..."
            status = "completed" if result.returncode == 0 else f"failed (code {result.returncode})"
            return ActionResult(
                success=result.returncode == 0,
                message=f"Command {status}.\n{output}",
                data={"output": output, "returncode": result.returncode},
            )
        except subprocess.TimeoutExpired:
            return ActionResult(success=False, message="Command timed out after 60 seconds.")
        except OSError as exc:
            return ActionResult(success=False, message=f"Command failed: {exc}")
