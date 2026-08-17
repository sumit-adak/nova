"""Offline intent parser using pattern matching and compound phrase handling."""

from __future__ import annotations

import re
from typing import Any

from app.core.logger import get_logger

logger = get_logger("intent_parser")


class OfflineIntentParser:
    """Rule-based intent parser for offline mode and local fallback."""

    PATTERNS: list[tuple[re.Pattern, str, dict[str, Any] | None]] = [
        # WhatsApp Messaging & Open
        (re.compile(r"^(?:open whatsapp and )?(?:send (?:a )?(?:whatsapp(?: message)?|message on whatsapp) to|whatsapp) (\+?[\d\-]+|\w+)(?: (?:saying|with message|message) (?:that )?)?[:\s]+['\"]?(.+?)['\"]?$", re.I),
         "send_whatsapp_message", None),
        (re.compile(r"^open whatsapp and (?:search|find) (?:for )?(\+?[\d\-]+|\w+)(?: (?:and )?(?:send|write|type) (?:message )?['\"]?(.+?)['\"]?)?$", re.I),
         "send_whatsapp_message", None),
        (re.compile(r"^send whatsapp to (\+?[\d\-]+|\w+)[:\s]+(.+)", re.I),
         "send_whatsapp_message", None),
        (re.compile(r"^whatsapp (\+?[\d\-]+|\w+)[:\s]+(.+)", re.I),
         "send_whatsapp_message", None),
        (re.compile(r"^open whatsapp\b", re.I),
         "open_whatsapp", {}),

        # Email Writing & Sending
        (re.compile(r"^(?:send|write|compose) (?:an? )?email to (\S+@\S+|\S+)(?: (?:with )?subject ['\"]?(.+?)['\"]?)?(?: (?:and )?(?:with )?body ['\"]?(.+?)['\"]?)?$", re.I),
         "send_email", None),
        (re.compile(r"^(?:send|write|compose) (?:an? )?email to (\S+@\S+|\S+) (?:saying|with message) (?:that )?['\"]?(.+?)['\"]?$", re.I),
         "send_email", None),
        (re.compile(r"^email (\S+@\S+|\S+)[:\s]+['\"]?(.+?)['\"]?$", re.I),
         "send_email", None),

        # File Sending / Sharing
        (re.compile(r"^send (?:the )?file (.+?) (?:to|via) (email|whatsapp)(?: to (\S+))?$", re.I),
         "send_file", None),
        (re.compile(r"^send (?:the )?file (.+?) to (\S+)$", re.I),
         "send_file", None),

        # Music & Media Playback (Spotify & YouTube)
        (re.compile(r"^(?:open spotify and )?play (?:any |some |a )?(?:music|songs?)$", re.I),
         "play_music", {"query": "Today's Top Hits", "platform": "spotify"}),
        (re.compile(r"^(?:open spotify and )?play (?:the song |the track |song |track )?(.+?)(?: on (spotify|youtube))$", re.I),
         "play_music", None),
        (re.compile(r"^open spotify and play (?:the song |the track |song |track )?(.+)", re.I),
         "play_music", {"platform": "spotify"}),
        (re.compile(r"^play (?:the song |the track |the video |song |track |video )?(.+?) on (spotify|youtube)$", re.I),
         "play_music", None),
        (re.compile(r"^play (?:the song |the track |song |track )?(.+)", re.I),
         "play_music", {"platform": "spotify"}),

        # Open & Search / Web Search
        (re.compile(r"^(?:open (?:the )?(?:browser|chrome|google|edge) and )?open and search (?:for |about )?(.+)", re.I),
         "search_web", {"engine": "google"}),
        (re.compile(r"^open (youtube|spotify|google|bing|github|stackoverflow|duckduckgo|reddit|wikipedia) and search (?:for |about )?(.+)", re.I),
         "search_web", None),
        (re.compile(r"^search (?:for |about )?(.+?) on (youtube|spotify|google|bing|github|stackoverflow|duckduckgo|reddit|wikipedia)$", re.I),
         "search_web", None),
        (re.compile(r"^search (?:on )?(youtube|spotify|google|bing|github|stackoverflow|duckduckgo|reddit|wikipedia) (?:for |about )?(.+)", re.I),
         "search_web", None),
        (re.compile(r"^search (?:this )?error (.+)", re.I),
         "search_error", None),
        (re.compile(r"^search (?:for |about )?(.+)", re.I),
         "search_web", None),

        # Specific applications
        (re.compile(r"open (?:vs ?code|visual studio code|code)\b", re.I),
         "open_application", {"app": "vscode"}),
        (re.compile(r"open (?:terminal|windows terminal|wt)\b", re.I),
         "open_application", {"app": "terminal"}),
        (re.compile(r"open (?:powershell|pwsh)\b", re.I),
         "open_application", {"app": "powershell"}),
        (re.compile(r"open (?:chrome|google chrome)\b", re.I),
         "open_application", {"app": "chrome"}),
        (re.compile(r"open (?:edge|microsoft edge)\b", re.I),
         "open_application", {"app": "edge"}),
        (re.compile(r"open (?:firefox)\b", re.I),
         "open_application", {"app": "firefox"}),
        (re.compile(r"open (?:notepad|calculator|calc|discord|spotify|explorer|jupyter)\b", re.I),
         "open_application", None),
        (re.compile(r"start jupyter\b", re.I),
         "open_application", {"app": "jupyter"}),
        (re.compile(r"close (\w+(?:\s+\w+)*)", re.I),
         "close_application", None),

        # Git operations & Developer sync
        (re.compile(r"(?:commit and push|commit & push|sync and push|push and commit|git sync|sync)(?: (?:it )?to (?:the )?(?:branch )?(\w+))?", re.I),
         "git_sync", None),
        (re.compile(r"(?:git )?push(?: (?:it )?to (?:the )?(?:branch )?(\w+))?", re.I),
         "git_push", None),
        (re.compile(r"(?:git )?commit(?: (?:all )?(?:with message|message)?:?\s*['\"]?([^'\"]+)['\"]?)?", re.I),
         "git_commit", None),
        (re.compile(r"(?:git )?status\b", re.I),
         "git_status", {}),
        (re.compile(r"(?:git )?diff\b", re.I),
         "git_diff", {}),

        # File modifications & Readme
        (re.compile(r"(?:do (?:some )?changes? (?:in|to)|edit|update|modify) (?:the )?(?:current )?(readme(?:\.md)?|file\s+\S+)", re.I),
         "edit_file", None),
        (re.compile(r"(?:read|view|show|display) (?:the )?(readme(?:\.md)?|file\s+\S+)", re.I),
         "read_file", None),

        # Web & Dev URLs
        (re.compile(r"open github\b", re.I),
         "open_github", {}),
        (re.compile(r"open localhost\b", re.I),
         "open_localhost", {}),
        (re.compile(r"open (?:youtube|yt)\b", re.I),
         "open_url", {"url": "https://www.youtube.com"}),
        (re.compile(r"open (https?://\S+)", re.I),
         "open_url", None),

        # Known project aliases
        (re.compile(r"open (?:my )?(?:the )?plant\s*guard(?:-ai)?(?:\s+project)?", re.I),
         "launch_project", {"project_name": "PlantGuard"}),
        (re.compile(r"start (?:my )?(?:the )?plant\s*guard(?:-ai)?(?:\s+project)?", re.I),
         "launch_project", {"project_name": "PlantGuard"}),
        (re.compile(r"open (?:my )?portfolio(?:\s+project)?", re.I),
         "launch_project", {"project_name": "Portfolio"}),
        (re.compile(r"open (?:my )?railway(?:\s+project)?", re.I),
         "launch_project", {"project_name": "Railway"}),
        (re.compile(r"open project (\w+)", re.I),
         "launch_project", None),
        (re.compile(r"(?:launch|start) project (\w+)", re.I),
         "launch_project", None),

        # System Metrics & Info
        (re.compile(r"(?:what(?:'s| is) my )?ram usage", re.I),
         "get_memory_usage", {}),
        (re.compile(r"(?:what(?:'s| is) my )?(?:memory|ram)", re.I),
         "get_memory_usage", {}),
        (re.compile(r"(?:what(?:'s| is) my )?cpu usage", re.I),
         "get_cpu_usage", {}),
        (re.compile(r"(?:what(?:'s| is) my )?cpu", re.I),
         "get_cpu_usage", {}),
        (re.compile(r"(?:what(?:'s| is) my )?gpu", re.I),
         "get_gpu_usage", {}),
        (re.compile(r"(?:what(?:'s| is) my )?(?:disk|storage)", re.I),
         "get_disk_usage", {}),
        (re.compile(r"(?:show|get) (?:my )?system stats?", re.I),
         "get_system_info", {}),
        (re.compile(r"system info(?:rmation)?", re.I),
         "get_system_info", {}),
        (re.compile(r"take (?:a )?screenshot", re.I),
         "take_screenshot", {}),

        # Files & Folders
        (re.compile(r"delete folder (.+)", re.I),
         "delete_folder", None),
        (re.compile(r"delete file (.+)", re.I),
         "delete_file", None),
        (re.compile(r"open folder (.+)", re.I),
         "open_folder", None),
        (re.compile(r"open file (.+)", re.I),
         "open_file", None),

        # Utilities
        (re.compile(r"(?:set )?volume (?:to )?(\d+)", re.I),
         "set_volume", None),
        (re.compile(r"(?:set )?(?:a )?timer (?:for )?(\d+)(?: seconds?)?", re.I),
         "start_timer", None),
        (re.compile(r"list projects?", re.I),
         "list_projects", {}),

        # Confirmation / Power operations
        (re.compile(r"shut\s*down", re.I),
         "shutdown", {}),
        (re.compile(r"restart(?: system| computer)?", re.I),
         "restart", {}),
        (re.compile(r"kill (?:process )?(\S+)", re.I),
         "kill_process", None),
    ]

    APP_NAMES = {
        "notepad": "notepad", "calculator": "calculator", "calc": "calculator",
        "discord": "discord", "spotify": "spotify", "explorer": "explorer",
        "jupyter": "jupyter", "jupyter notebook": "jupyter",
    }

    GENERIC_SONG_NAMES = {
        "any song", "some song", "a song", "music", "song", "any",
        "something", "random song", "random", "any music", "songs",
    }

    KNOWN_ENGINES = {
        "youtube", "spotify", "google", "bing", "github",
        "stackoverflow", "duckduckgo", "reddit", "wikipedia",
    }

    def parse(self, user_input: str) -> dict[str, Any]:
        """Parse user input into structured single or multi-action intents."""
        text = user_input.strip()
        if not text:
            return {"type": "conversation", "action": None, "parameters": {}, "response": "How can I help?"}

        # Check for compound conjunctions (e.g. " and then ", " then ", " and ")
        segments = self._split_compound_input(text)
        if len(segments) > 1:
            actions_list = []
            responses = []
            for seg in segments:
                res = self._parse_single(seg)
                if res.get("type") == "action" and res.get("action"):
                    actions_list.append({
                        "action": res["action"],
                        "parameters": res.get("parameters", {}),
                    })
                    responses.append(res.get("response", "Executing step."))

            if len(actions_list) > 1:
                return {
                    "type": "actions",
                    "actions": actions_list,
                    "response": "Executing multi-step workflow: " + ", ".join(responses),
                }
            elif len(actions_list) == 1:
                return {
                    "type": "action",
                    "action": actions_list[0]["action"],
                    "parameters": actions_list[0]["parameters"],
                    "response": responses[0],
                }

        # Otherwise parse as single intent
        return self._parse_single(text)

    def _split_compound_input(self, text: str) -> list[str]:
        """Split compound request on 'and then', 'then', or 'and'."""
        # Don't split unified commands like "open and search ...", "open <engine> and search ...", "open spotify and play ...", or "open whatsapp and ..."
        if re.match(r"^open (?:and search|\w+ and (?:search|play)|whatsapp and (?:search|find|send|write))\b", text, re.I):
            return [text]
        parts = re.split(r"\s+(?:and\s+then|then|and)\s+", text, flags=re.I)
        cleaned = [p.strip() for p in parts if p.strip()]
        return cleaned if len(cleaned) > 1 else [text]

    def _parse_single(self, text: str) -> dict[str, Any]:
        """Parse a single command segment into an intent."""
        for pattern, action, fixed_params in self.PATTERNS:
            match = pattern.search(text)
            if not match:
                continue

            params = dict(fixed_params) if fixed_params is not None else {}

            if action == "send_whatsapp_message":
                groups = [g for g in match.groups() if g is not None]
                if len(groups) >= 2:
                    params["phone"] = groups[0].strip()
                    params["recipient"] = groups[0].strip()
                    params["message"] = groups[1].strip()
                elif len(groups) == 1:
                    params["phone"] = groups[0].strip()
                    params["recipient"] = groups[0].strip()
                    params["message"] = ""

            if action == "open_whatsapp":
                if match.groups() and match.group(1):
                    params["search"] = match.group(1).strip()
                else:
                    params["search"] = ""

            if action == "send_email":
                groups = [g for g in match.groups() if g is not None]
                if len(groups) >= 3:
                    params["to"] = groups[0].strip()
                    params["subject"] = groups[1].strip()
                    params["body"] = groups[2].strip()
                elif len(groups) == 2:
                    params["to"] = groups[0].strip()
                    params["subject"] = "Message from NOVA"
                    params["body"] = groups[1].strip()
                elif len(groups) == 1:
                    params["to"] = groups[0].strip()
                    params["subject"] = "Message from NOVA"
                    params["body"] = ""

            if action == "send_file":
                groups = [g for g in match.groups() if g is not None]
                if len(groups) >= 3:
                    params["path"] = groups[0].strip()
                    params["channel"] = groups[1].strip().lower()
                    params["recipient"] = groups[2].strip()
                elif len(groups) == 2:
                    params["path"] = groups[0].strip()
                    target = groups[1].strip()
                    if "@" in target:
                        params["recipient"] = target
                        params["channel"] = "email"
                    elif re.match(r"^\+?\d+$", target):
                        params["recipient"] = target
                        params["channel"] = "whatsapp"
                    else:
                        params["recipient"] = target
                        params["channel"] = "email"
                elif len(groups) == 1:
                    params["path"] = groups[0].strip()

            if action == "play_music":
                if "query" not in params:
                    if match.groups() and match.group(1):
                        q = match.group(1).strip()
                        if q.lower() in self.GENERIC_SONG_NAMES:
                            q = "Today's Top Hits"
                        params["query"] = q
                    else:
                        params["query"] = "Today's Top Hits"

                if "platform" not in params:
                    if len(match.groups()) > 1 and match.group(2):
                        params["platform"] = match.group(2).lower()
                    else:
                        params["platform"] = "spotify"

            if action == "search_web":
                groups = [g for g in match.groups() if g is not None]
                if "query" not in params:
                    if len(groups) >= 2:
                        g0, g1 = groups[0].strip(), groups[1].strip()
                        if g0.lower() in self.KNOWN_ENGINES:
                            params["engine"] = g0.lower()
                            params["query"] = g1
                        elif g1.lower() in self.KNOWN_ENGINES:
                            params["query"] = g0
                            params["engine"] = g1.lower()
                        else:
                            params["query"] = g0
                    elif len(groups) == 1:
                        params["query"] = groups[0].strip()
                if "engine" not in params:
                    params["engine"] = "google"

            if action == "launch_project" and "project_name" not in params and match.groups():
                params["project_name"] = match.group(1)

            if action == "open_application" and "app" not in params:
                if match.groups() and match.group(1):
                    app_raw = match.group(1).lower()
                    params["app"] = self.APP_NAMES.get(app_raw, app_raw)
                else:
                    for name, key in self.APP_NAMES.items():
                        if name in text.lower():
                            params["app"] = key
                            break

            if action == "close_application" and match.groups():
                params["app"] = match.group(1)

            if action == "git_sync":
                branch = match.group(1) if match.groups() and match.group(1) else "main"
                params["branch"] = branch
                params["message"] = "Update files"

            if action == "git_push":
                branch = match.group(1) if match.groups() and match.group(1) else "main"
                params["branch"] = branch

            if action == "git_commit":
                msg = match.group(1) if match.groups() and match.group(1) else "Update files"
                params["message"] = msg or "Update files"

            if action in ("edit_file", "read_file"):
                target = match.group(1) if match.groups() and match.group(1) else "README.md"
                target = target.replace("file", "").strip()
                if "readme" in target.lower():
                    target = "README.md"
                params["path"] = target
                if action == "edit_file":
                    params["mode"] = "append"
                    params["content"] = "\n<!-- Updated by NOVA assistant -->"

            if action == "search_error" and match.groups():
                params["error"] = match.group(1)

            if action == "open_url" and match.groups():
                params["url"] = match.group(1)

            if action == "set_volume" and match.groups():
                params["level"] = int(match.group(1))

            if action == "start_timer" and match.groups():
                params["seconds"] = int(match.group(1))

            if action in ("open_folder", "delete_folder", "open_file", "delete_file") and match.groups():
                params["path"] = match.group(1).strip()

            if action == "kill_process" and match.groups():
                params["process_name"] = match.group(1).strip()

            response = self._generate_response(action, params)
            return {
                "type": "action",
                "action": action,
                "parameters": params,
                "response": response,
            }

        return {
            "type": "conversation",
            "action": None,
            "parameters": {},
            "response": "",
        }

    @staticmethod
    def _generate_response(action: str, params: dict[str, Any]) -> str:
        """Generate a friendly response for an action."""
        engine = params.get("engine", "google")
        engine_str = f" on {engine.title()}" if engine and engine != "google" else ""
        query_val = params.get("query", "")
        platform_str = params.get("platform", "Spotify").title()
        recipient_val = params.get("recipient", params.get("phone", params.get("to", "")))

        responses = {
            "send_whatsapp_message": f"Opening WhatsApp chat for '{recipient_val}' with your message.",
            "open_whatsapp": f"Opening WhatsApp{' with search ' + params.get('search', '') if params.get('search') else ''}.",
            "send_email": f"Composing email to '{params.get('to', '')}' with subject '{params.get('subject', 'Message from NOVA')}'.",
            "send_file": f"Sending file '{params.get('path', '')}' to '{recipient_val}' via {params.get('channel', 'email').title()}.",
            "play_music": f"Playing {query_val} on {platform_str}." if query_val else f"Playing music on {platform_str}.",
            "search_web": f"Searching for: {query_val}{engine_str}.",
            "search_error": f"Searching error: {params.get('error', '')}.",
            "launch_project": f"Opening {params.get('project_name', 'project')}.",
            "open_application": f"Opening {params.get('app', 'application')}.",
            "close_application": f"Closing {params.get('app', 'application')}.",
            "git_sync": f"Syncing and pushing changes to {params.get('branch', 'main')}.",
            "git_push": f"Pushing changes to {params.get('branch', 'main')}.",
            "git_commit": f"Committing changes with message '{params.get('message', 'Update files')}'.",
            "git_status": "Checking Git status.",
            "git_diff": "Checking Git diff.",
            "edit_file": f"Updating file {params.get('path', 'file')}.",
            "read_file": f"Reading file {params.get('path', 'file')}.",
            "get_memory_usage": "Checking your RAM usage.",
            "get_cpu_usage": "Checking CPU usage.",
            "get_gpu_usage": "Checking GPU usage.",
            "get_disk_usage": "Checking storage usage.",
            "get_system_info": "Gathering system information.",
            "take_screenshot": "Taking a screenshot.",
            "open_github": "Opening GitHub.",
            "open_localhost": "Opening localhost.",
            "open_url": f"Opening {params.get('url', 'web page')}.",
            "open_folder": f"Opening folder {params.get('path', '')}.",
            "open_file": f"Opening file {params.get('path', '')}.",
            "set_volume": f"Setting volume to {params.get('level', 50)}%.",
            "start_timer": f"Starting timer for {params.get('seconds', 60)} seconds.",
            "list_projects": "Listing your projects.",
        }
        return responses.get(action, "On it.")

