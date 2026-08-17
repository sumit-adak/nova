"""Web Search integration with privacy scrubbing."""
import re
import urllib.parse
from typing import Any
import structlog
from nova_app.ai_engine.redaction import get_redaction_engine
from nova_app.integrations.browser.browser_driver import get_browser_driver

logger = structlog.get_logger(__name__)

# Regex to detect and strip local file paths like C:\Users\... or /home/...
LOCAL_PATH_REGEX = re.compile(r"(?:[a-zA-Z]:[\\/][^ \n\r\t]+)|(?:\/[a-zA-Z0-9_\-\.\/]+)", re.IGNORECASE)


def sanitize_search_query(query: str) -> str:
    """Strip local filesystem paths and secrets from query."""
    # 1. Redact API keys and passwords
    clean = get_redaction_engine().redact(query)
    # 2. Strip local path references
    clean = LOCAL_PATH_REGEX.sub("[local_path]", clean)
    return clean.strip()


class WebSearchClient:
    """Manages web searching with privacy redaction."""

    def search(self, query: str, open_in_browser: bool = True) -> dict[str, Any]:
        """Perform search query via DuckDuckGo / Google."""
        sanitized = sanitize_search_query(query)
        encoded_query = urllib.parse.quote_plus(sanitized)
        search_url = f"https://duckduckgo.com/?q={encoded_query}"

        if open_in_browser:
            get_browser_driver().open_url(search_url)

        return {
            "query": query,
            "sanitized_query": sanitized,
            "search_url": search_url,
            "opened_in_browser": open_in_browser,
        }


_web_search_instance: WebSearchClient | None = None


def get_web_search_client() -> WebSearchClient:
    """Get singleton WebSearchClient instance."""
    global _web_search_instance
    if _web_search_instance is None:
        _web_search_instance = WebSearchClient()
    return _web_search_instance
