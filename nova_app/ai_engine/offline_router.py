"""Offline deterministic intent router for zero-AI local operations."""
import re
from typing import Any
from nova_app.tools.schema import ToolCall


class OfflineIntentRouter:
    """Parses natural language commands deterministically into safe ToolCalls without LLM."""

    def parse(self, text: str) -> ToolCall | None:
        """Attempt to map text input to a known registered tool call."""
        cleaned = text.strip().lower()

        # 1. Web Search & Website Navigation
        search_web_match = re.search(r"(?:search\s+(?:the\s+)?web\s+for|search\s+google\s+for|google|search\s+for)\s+(.+)", cleaned)
        if search_web_match:
            q = search_web_match.group(1).strip()
            if not q.startswith("file") and not q.startswith("folder"):
                return ToolCall(
                    tool_name="search_web",
                    arguments={"query": q, "open_in_browser": True},
                    reasoning=f"Matched offline web search pattern for '{q}'",
                )

        site_match = re.search(r"(?:open\s+website|open\s+site|open\s+url|go\s+to)\s+(.+)", cleaned)
        if site_match:
            url_target = site_match.group(1).strip()
            return ToolCall(
                tool_name="open_website",
                arguments={"url": url_target},
                reasoning=f"Matched open website pattern for '{url_target}'",
            )

        # 2. Developer Commands
        if cleaned in ["git status", "repo status", "git branch", "show git status"]:
            return ToolCall(
                tool_name="git_status",
                arguments={},
                reasoning="Matched offline pattern for git status",
            )

        proj_match = re.search(r"open\s+(?:project|workspace|repo)\s+(.+)", cleaned)
        if proj_match:
            target = proj_match.group(1).strip()
            return ToolCall(
                tool_name="open_project",
                arguments={"project_path": target},
                reasoning=f"Matched open project pattern for '{target}'",
            )

        terminal_match = re.search(r"open\s+terminal(?:\s+in|\s+at)?\s*(.*)", cleaned)
        if terminal_match:
            path_arg = terminal_match.group(1).strip()
            return ToolCall(
                tool_name="open_terminal",
                arguments={"path": path_arg if path_arg else None},
                reasoning="Matched open terminal pattern",
            )

        # 3. System stats & hardware
        if any(w in cleaned for w in ["system stats", "hardware", "cpu usage", "ram usage", "how much ram", "how is my laptop", "laptop status"]):
            return ToolCall(
                tool_name="get_system_stats",
                arguments={"include_disks": True},
                reasoning="Matched offline pattern for system stats request",
            )

        # 4. Screenshot
        if "screenshot" in cleaned or "capture screen" in cleaned or "snip screen" in cleaned:
            return ToolCall(
                tool_name="take_screenshot",
                arguments={},
                reasoning="Matched offline pattern for desktop screenshot",
            )

        # 5. Volume control
        vol_match = re.search(r"(?:set\s+)?volume(?:\s+to)?\s+(\d+)", cleaned)
        if vol_match:
            level = int(vol_match.group(1))
            return ToolCall(
                tool_name="set_volume",
                arguments={"level": max(0, min(100, level))},
                reasoning=f"Matched offline volume pattern for {level}%",
            )

        # 6. Timer
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

        # 7. Media control
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

        # 8. File & Folder opening / search
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

        # 9. Application launching
        app_match = re.search(r"(?:open|launch|start)\s+([a-zA-Z0-9_\-\s]+)", cleaned)
        if app_match:
            app_target = app_match.group(1).strip()
            if app_target not in ["music", "a screenshot", "screenshot", "terminal", "website", "site"]:
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
