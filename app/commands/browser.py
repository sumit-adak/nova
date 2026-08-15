"""Browser and web search commands."""

from __future__ import annotations

import os
import urllib.parse
import webbrowser

from app.commands.registry import ActionResult
from app.core.config import ConfigManager
from app.core.security import SecurityError, validate_url


class BrowserCommands:
    """Web browser and search operations."""

    SEARCH_URLS = {
        "google": "https://www.google.com/search?q={query}",
        "bing": "https://www.bing.com/search?q={query}",
        "youtube": "https://www.youtube.com/results?search_query={query}",
        "spotify": "https://open.spotify.com/search/{query}",
        "github": "https://github.com/search?q={query}",
        "stackoverflow": "https://stackoverflow.com/search?q={query}",
        "duckduckgo": "https://duckduckgo.com/?q={query}",
        "reddit": "https://www.reddit.com/search/?q={query}",
        "wikipedia": "https://en.wikipedia.org/wiki/Special:Search?search={query}",
        "amazon": "https://www.amazon.com/s?k={query}",
        "twitter": "https://x.com/search?q={query}",
    }

    QUICK_URLS = {
        "github": "https://github.com",
        "stackoverflow": "https://stackoverflow.com",
        "localhost": "http://localhost:3000",
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "spotify": "https://open.spotify.com",
    }

    def __init__(self, config: ConfigManager) -> None:
        self.config = config

    def _get_browser(self) -> str | None:
        settings = self.config.load_settings()
        return settings.get("default_browser")

    async def open_url(self, url: str) -> ActionResult:
        """Open a URL in the default or configured browser."""
        try:
            safe_url = validate_url(url)
            browser_name = self._get_browser()
            if browser_name:
                try:
                    browser = webbrowser.get(browser_name)
                    browser.open(safe_url)
                except webbrowser.Error:
                    webbrowser.open(safe_url)
            else:
                webbrowser.open(safe_url)
            return ActionResult(success=True, message=f"Opening {safe_url}")
        except SecurityError as exc:
            return ActionResult(success=False, message=str(exc))

    async def search_web(self, query: str, engine: str = "google") -> ActionResult:
        """Search the web or specific platform using the specified engine."""
        if not query or not query.strip():
            return ActionResult(success=False, message="Search query cannot be empty")

        clean_query = query.strip()
        engine_key = (engine or "google").lower().strip()

        aliases = {
            "yt": "youtube",
            "sp": "spotify",
            "ddg": "duckduckgo",
            "gh": "github",
            "so": "stackoverflow",
            "wiki": "wikipedia",
            "chrome": "google",
            "edge": "bing",
            "browser": "google",
        }
        engine_key = aliases.get(engine_key, engine_key)
        template = self.SEARCH_URLS.get(engine_key, self.SEARCH_URLS["google"])
        encoded = urllib.parse.quote_plus(clean_query)
        url = template.format(query=encoded)

        try:
            webbrowser.open(url)
            engine_name = engine_key.title() if engine_key in self.SEARCH_URLS else "Google"
            return ActionResult(
                success=True,
                message=f"Searching for: {clean_query} on {engine_name}",
                data={"query": clean_query, "engine": engine_key, "url": url},
            )
        except Exception as exc:
            return ActionResult(success=False, message=f"Search failed: {exc}")

    async def play_music(self, query: str = "", platform: str = "spotify", auto_play: bool = True) -> ActionResult:
        """Play music or search a track/artist on Spotify or YouTube and automatically trigger playback."""
        import asyncio

        clean_query = query.strip() if query else ""
        generic_queries = {
            "any song", "some song", "a song", "music", "song", "any",
            "something", "random song", "random", "any music", "songs",
        }
        if not clean_query or clean_query.lower() in generic_queries:
            target_query = "Today's Top Hits"
            display_title = "popular tracks"
        else:
            target_query = clean_query
            display_title = f"'{clean_query}'"

        platform_norm = platform.lower().strip() if platform else "spotify"

        if "youtube" in platform_norm:
            encoded = urllib.parse.quote_plus(target_query)
            # Link directly to search/watch results
            url = f"https://www.youtube.com/results?search_query={encoded}"
            try:
                webbrowser.open(url)
                if auto_play:
                    async def _auto_play_youtube() -> None:
                        try:
                            await asyncio.sleep(2.5)
                            import pyautogui
                            pyautogui.press("enter")
                        except Exception:
                            pass
                    asyncio.create_task(_auto_play_youtube())

                return ActionResult(
                    success=True,
                    message=f"Playing {display_title} on YouTube.",
                    data={"query": target_query, "platform": "youtube", "url": url},
                )
            except Exception as exc:
                return ActionResult(success=False, message=f"Failed to play on YouTube: {exc}")
        else:
            # Spotify
            encoded_uri = urllib.parse.quote(target_query)
            encoded_web = urllib.parse.quote_plus(target_query)
            spotify_uri = f"spotify:search:{encoded_uri}"
            spotify_web = f"https://open.spotify.com/search/{encoded_web}"

            opened = False
            if hasattr(os, "startfile"):
                try:
                    os.startfile(spotify_uri)
                    opened = True
                except (OSError, AttributeError):
                    opened = False

            if not opened:
                try:
                    webbrowser.open(spotify_web)
                    opened = True
                except Exception as exc:
                    return ActionResult(success=False, message=f"Failed to open Spotify: {exc}")

            if auto_play:
                async def _auto_play_spotify() -> None:
                    try:
                        # Wait for Spotify desktop or web player to focus, then press Enter or Play
                        await asyncio.sleep(2.0)
                        import pyautogui
                        pyautogui.press("enter")
                    except Exception:
                        pass
                asyncio.create_task(_auto_play_spotify())

            return ActionResult(
                success=True,
                message=f"Playing {display_title} on Spotify.",
                data={
                    "query": target_query,
                    "platform": "spotify",
                    "uri": spotify_uri,
                    "web_url": spotify_web,
                },
            )

    async def search_error(self, error: str) -> ActionResult:
        """Search for a programming error online."""
        query = f"{error} stackoverflow"
        return await self.search_web(query, engine="google")

    async def open_quick_url(self, name: str) -> ActionResult:
        """Open a predefined quick URL."""
        url = self.QUICK_URLS.get(name.lower())
        if not url:
            return ActionResult(success=False, message=f"Unknown quick URL: {name}")
        return await self.open_url(url)
