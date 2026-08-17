"""Web search, browser navigation, and webpage reading executors."""
import html
import re
import urllib.request
from typing import Any
from pydantic import BaseModel, Field
from nova_app.integrations.browser.browser_driver import get_browser_driver
from nova_app.integrations.browser.web_search import get_web_search_client


class SearchWebArgs(BaseModel):
    query: str = Field(description="Search query string")
    open_in_browser: bool = Field(default=True, description="Whether to open the search page in the user's browser")


class OpenWebsiteArgs(BaseModel):
    url: str = Field(description="Web URL to open")
    browser: str | None = Field(default=None, description="Optional browser to use (chrome, edge, firefox)")


class FetchWebpageTextArgs(BaseModel):
    url: str = Field(description="URL of public webpage to fetch text from")
    max_length: int = Field(default=4000, description="Max character length to return")


def search_web_executor(args: SearchWebArgs) -> dict[str, Any]:
    """Execute web search with privacy scrubbing."""
    search_client = get_web_search_client()
    return search_client.search(args.query, open_in_browser=args.open_in_browser)


def open_website_executor(args: OpenWebsiteArgs) -> dict[str, Any]:
    """Open website in browser."""
    driver = get_browser_driver()
    return driver.open_url(args.url, browser_name=args.browser)


def fetch_webpage_text_executor(args: FetchWebpageTextArgs) -> dict[str, Any]:
    """Fetch public webpage and extract readable plain text."""
    clean_url = args.url.strip()
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    req = urllib.request.Request(
        clean_url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NOVA/0.1.0"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            raw_html = resp.read().decode("utf-8", errors="replace")

        # Strip scripts, styles, and html tags
        no_scripts = re.sub(r"<(script|style).*?>.*?</\1>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
        plain_text = re.sub(r"<.*?>", " ", no_scripts)
        unescaped = html.unescape(plain_text)
        cleaned_text = re.sub(r"\s+", " ", unescaped).strip()

        truncated = cleaned_text[:args.max_length]
        return {
            "status": "success",
            "url": clean_url,
            "text": truncated,
            "length": len(truncated),
            "truncated": len(cleaned_text) > args.max_length,
        }
    except Exception as e:
        return {
            "status": "error",
            "url": clean_url,
            "error": str(e),
        }
