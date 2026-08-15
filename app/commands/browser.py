"""Browser and web search commands."""

from __future__ import annotations

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
        "github": "https://github.com/search?q={query}",
        "stackoverflow": "https://stackoverflow.com/search?q={query}",
    }

    QUICK_URLS = {
        "github": "https://github.com",
        "stackoverflow": "https://stackoverflow.com",
        "localhost": "http://localhost:3000",
        "google": "https://www.google.com",
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
        """Search the web using the specified engine."""
        if not query or not query.strip():
            return ActionResult(success=False, message="Search query cannot be empty")

        engine = engine.lower()
        template = self.SEARCH_URLS.get(engine, self.SEARCH_URLS["google"])
        encoded = urllib.parse.quote_plus(query.strip())
        url = template.format(query=encoded)

        try:
            webbrowser.open(url)
            return ActionResult(success=True, message=f"Searching for: {query}")
        except Exception as exc:
            return ActionResult(success=False, message=f"Search failed: {exc}")

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
