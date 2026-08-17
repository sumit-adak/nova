"""Browser driver managing browser selection and web navigation."""
import os
import shutil
import subprocess
import webbrowser
from typing import Any, Literal
import structlog
from nova_app.config.settings import Settings, get_settings

logger = structlog.get_logger(__name__)

BROWSER_PATHS: dict[str, list[str]] = {
    "chrome": [
        "chrome.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ],
    "edge": [
        "msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "firefox": [
        "firefox.exe",
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    ],
}


class BrowserDriver:
    """Controls opening web pages in preferred browsers."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def open_url(self, url: str, browser_name: str | None = None) -> dict[str, Any]:
        """Open a URL in the configured or requested browser."""
        target_browser = (browser_name or self.settings.default_browser).lower()

        # Sanitize url
        clean_url = url.strip()
        if not clean_url.startswith(("http://", "https://")):
            clean_url = "https://" + clean_url

        if target_browser in BROWSER_PATHS:
            for candidate in BROWSER_PATHS[target_browser]:
                bin_path = shutil.which(candidate) or (candidate if os.path.isfile(candidate) else None)
                if bin_path:
                    subprocess.Popen([bin_path, clean_url], shell=False)
                    logger.info("Opened URL in browser", browser=target_browser, url=clean_url)
                    return {
                        "status": "opened",
                        "url": clean_url,
                        "browser": target_browser,
                        "binary": bin_path,
                    }

        # Fallback to system default browser via webbrowser standard library
        webbrowser.open(clean_url)
        logger.info("Opened URL via default system handler", url=clean_url)
        return {
            "status": "opened",
            "url": clean_url,
            "browser": "default",
        }


_browser_driver_instance: BrowserDriver | None = None


def get_browser_driver() -> BrowserDriver:
    """Get singleton BrowserDriver instance."""
    global _browser_driver_instance
    if _browser_driver_instance is None:
        _browser_driver_instance = BrowserDriver()
    return _browser_driver_instance
