"""Unit tests for Phase 7: Web Intelligence & Browser Automation."""
import pytest
from unittest.mock import MagicMock, patch
from nova_app.ai_engine.offline_router import OfflineIntentRouter
from nova_app.integrations.browser.browser_driver import BrowserDriver
from nova_app.integrations.browser.web_search import WebSearchClient, sanitize_search_query
from nova_app.tools.executors.web import FetchWebpageTextArgs, fetch_webpage_text_executor
from nova_app.tools.registry import ToolRegistry
from nova_app.tools.schema import ToolCall


def test_sanitize_search_query_removes_local_paths_and_secrets():
    query = "Search how to fix bug in C:\\Users\\Administrator\\Documents\\nova\\main.py with key sk-1234567890abcdef1234567890"
    sanitized = sanitize_search_query(query)

    assert "C:\\Users\\Administrator" not in sanitized
    assert "sk-1234567890abcdef" not in sanitized
    assert "[local_path]" in sanitized or "[REDACTED_" in sanitized


def test_web_search_client():
    client = WebSearchClient()
    res = client.search("python asyncio tutorial", open_in_browser=False)

    assert res["query"] == "python asyncio tutorial"
    assert "duckduckgo.com" in res["search_url"]
    assert res["opened_in_browser"] is False


def test_browser_driver_open_url():
    driver = BrowserDriver()
    with patch("webbrowser.open") as mock_open:
        res = driver.open_url("github.com", browser_name="default")
        assert res["status"] == "opened"
        assert res["url"] == "https://github.com"
        mock_open.assert_called_once_with("https://github.com")


def test_fetch_webpage_text():
    # Mock urllib response with HTML
    mock_html = b"<html><head><style>.ad{color:red;}</style></head><body><h1>NOVA Docs</h1><script>alert(1);</script><p>Hello World</p></body></html>"

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_html
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = fetch_webpage_text_executor(FetchWebpageTextArgs(url="https://example.com"))
        assert res["status"] == "success"
        assert "NOVA Docs" in res["text"]
        assert "Hello World" in res["text"]
        assert "<script>" not in res["text"]
        assert "alert(1)" not in res["text"]


@pytest.mark.asyncio
async def test_web_tools_in_registry_and_router():
    registry = ToolRegistry()
    assert registry.get("search_web") is not None
    assert registry.get("open_website") is not None
    assert registry.get("fetch_webpage_text") is not None

    router = OfflineIntentRouter()
    call = router.parse("search web for fastapi docs")
    assert call is not None
    assert call.tool_name == "search_web"
    assert call.arguments["query"] == "fastapi docs"

    site_call = router.parse("open website github.com")
    assert site_call is not None
    assert site_call.tool_name == "open_website"
    assert site_call.arguments["url"] == "github.com"
