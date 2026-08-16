"""Media control and timer executors."""
import asyncio
import webbrowser
from typing import Any
import pyautogui
from pydantic import BaseModel, Field
from nova_app.core.events import Event, get_event_bus
from dataclasses import dataclass


class PlayMusicArgs(BaseModel):
    query: str | None = Field(default=None, description="Song title, artist, or query")


class PauseMusicArgs(BaseModel):
    pass


class StartTimerArgs(BaseModel):
    seconds: int = Field(ge=1, description="Timer duration in seconds")
    label: str = Field(default="Timer", description="Label for the timer")


@dataclass
class TimerExpiredEvent(Event):
    label: str = "Timer"
    seconds: int = 0


def play_music_executor(args: PlayMusicArgs) -> dict[str, Any]:
    """Play music via Windows media key or open Spotify / YouTube Music web."""
    if args.query:
        # Search on YouTube / Spotify
        search_url = f"https://www.youtube.com/results?search_query={args.query.replace(' ', '+')}"
        webbrowser.open(search_url)
        return {
            "status": "opened_web_music",
            "query": args.query,
            "url": search_url,
        }
    else:
        # Toggle Windows Play/Pause media key
        pyautogui.press("playpause")
        return {
            "status": "media_key_toggled",
            "action": "playpause",
        }


def pause_music_executor(args: PauseMusicArgs) -> dict[str, Any]:
    """Send Windows play/pause media key."""
    pyautogui.press("playpause")
    return {
        "status": "media_key_toggled",
        "action": "playpause",
    }


def start_timer_executor(args: StartTimerArgs) -> dict[str, Any]:
    """Start an asynchronous background timer that fires a TimerExpiredEvent."""
    async def _timer_worker():
        await asyncio.sleep(args.seconds)
        get_event_bus().publish_sync(TimerExpiredEvent(label=args.label, seconds=args.seconds))

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_timer_worker())
    except RuntimeError:
        asyncio.create_task(_timer_worker())

    return {
        "status": "timer_started",
        "label": args.label,
        "seconds": args.seconds,
    }
