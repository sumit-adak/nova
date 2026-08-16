"""Offline deterministic intent router for zero-AI local operations."""
import re
from typing import Any
from nova_app.tools.schema import ToolCall


class OfflineIntentRouter:
    """Parses natural language commands deterministically into safe ToolCalls without LLM."""

    def parse(self, text: str) -> ToolCall | None:
        """Attempt to map text input to a known registered tool call."""
        cleaned = text.strip().lower()

        # 1. System stats & hardware
        if any(w in cleaned for w in ["system stats", "hardware", "cpu usage", "ram usage", "how much ram", "how is my laptop", "laptop status"]):
            return ToolCall(
                tool_name="get_system_stats",
                arguments={"include_disks": True},
                reasoning="Matched offline pattern for system stats request",
            )

        # 2. Screenshot
        if "screenshot" in cleaned or "capture screen" in cleaned or "snip screen" in cleaned:
            return ToolCall(
                tool_name="take_screenshot",
                arguments={},
                reasoning="Matched offline pattern for desktop screenshot",
            )

        # 3. Volume control
        vol_match = re.search(r"(?:set\s+)?volume(?:\s+to)?\s+(\d+)", cleaned)
        if vol_match:
            level = int(vol_match.group(1))
            return ToolCall(
                tool_name="set_volume",
                arguments={"level": max(0, min(100, level))},
                reasoning=f"Matched offline volume pattern for {level}%",
            )

        # 4. Timer
        timer_min_match = re.search(r"(?:set\s+)?timer\s+(?:for\s+)?(\d+)\s*(?:min|minute|minutes)", cleaned)
        if timer_min_match:
            mins = int(timer_min_match.group(1))
            return ToolCall(
                tool_name="start_timer",
                arguments={"seconds": mins * 60, "label": f"{mins} minute timer"},
                reasoning="Matched timer minutes pattern",
            )

        timer_sec_match = re.search(r"(?:set\s+)?timer\s+(?:for\s+)?(\d+)\s*(?:sec|second|seconds)", cleaned)
        if timer_sec_match:
            secs = int(timer_sec_match.group(1))
            return ToolCall(
                tool_name="start_timer",
                arguments={"seconds": secs, "label": f"{secs} second timer"},
                reasoning="Matched timer seconds pattern",
            )

        # 5. Media control
        if cleaned in ["pause", "pause music", "stop music", "pause playback"]:
            return ToolCall(
                tool_name="pause_music",
                arguments={},
                reasoning="Matched pause music pattern",
            )

        play_match = re.search(r"play\s+(?:song\s+|music\s+)?(.+)", cleaned)
        if play_match:
            query = play_match.group(1).strip()
            return ToolCall(
                tool_name="play_music",
                arguments={"query": query},
                reasoning="Matched play music pattern",
            )

        if cleaned in ["play music", "play", "resume music"]:
            return ToolCall(
                tool_name="play_music",
                arguments={},
                reasoning="Matched play music toggle pattern",
            )

        # 6. File & Folder opening / search
        search_match = re.search(r"(?:search\s+for|find)\s+files?\s+(?:named\s+)?(.+)", cleaned)
        if search_match:
            q = search_match.group(1).strip()
            return ToolCall(
                tool_name="search_files",
                arguments={"query": q},
                reasoning="Matched file search pattern",
            )

        folder_match = re.search(r"open\s+(?:folder|directory)\s+(.+)", cleaned)
        if folder_match:
            target = folder_match.group(1).strip()
            return ToolCall(
                tool_name="open_folder",
                arguments={"path": target},
                reasoning="Matched open folder pattern",
            )

        file_match = re.search(r"open\s+file\s+(.+)", cleaned)
        if file_match:
            target = file_match.group(1).strip()
            return ToolCall(
                tool_name="open_file",
                arguments={"path": target},
                reasoning="Matched open file pattern",
            )

        # 7. Application launching
        app_match = re.search(r"(?:open|launch|start)\s+([a-zA-Z0-9_\-\s]+)", cleaned)
        if app_match:
            app_target = app_match.group(1).strip()
            # Avoid matching verbs like "settings", "music", etc if ambiguous
            if app_target not in ["music", "a screenshot", "screenshot"]:
                return ToolCall(
                    tool_name="open_application",
                    arguments={"app_name": app_target},
                    reasoning=f"Matched open application pattern for '{app_target}'",
                )

        return None


_offline_router_instance: OfflineIntentRouter | None = None


def get_offline_router() -> OfflineIntentRouter:
    """Get singleton OfflineIntentRouter instance."""
    global _offline_router_instance
    if _offline_router_instance is None:
        _offline_router_instance = OfflineIntentRouter()
    return _offline_router_instance
