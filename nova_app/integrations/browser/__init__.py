"""Browser and Web Search integration package."""
from nova_app.integrations.browser.browser_driver import BrowserDriver, get_browser_driver
from nova_app.integrations.browser.web_search import (
    WebSearchClient,
    get_web_search_client,
    sanitize_search_query,
)

__all__ = [
    "BrowserDriver",
    "get_browser_driver",
    "WebSearchClient",
    "get_web_search_client",
    "sanitize_search_query",
]
