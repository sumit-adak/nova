"""Email client with recipient validation and mailto/SMTP dispatch."""
import re
import urllib.parse
import webbrowser
from typing import Any
import structlog

logger = structlog.get_logger(__name__)

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def is_valid_email(email_str: str) -> bool:
    """Validate email address format."""
    return bool(EMAIL_REGEX.match(email_str.strip()))


class EmailClient:
    """Handles email composition and system mail client / SMTP delivery."""

    def compose_mailto(self, recipient: str, subject: str, body: str) -> dict[str, Any]:
        """Open default mail client with prefilled email fields."""
        if not is_valid_email(recipient):
            raise ValueError(f"Invalid email address: '{recipient}'")

        params = urllib.parse.urlencode({
            "subject": subject,
            "body": body,
        })
        mailto_url = f"mailto:{recipient}?{params}"
        webbrowser.open(mailto_url)

        logger.info("Opened mail client", recipient=recipient, subject=subject)
        return {
            "status": "opened_mail_client",
            "recipient": recipient,
            "subject": subject,
        }


_email_client_instance: EmailClient | None = None


def get_email_client() -> EmailClient:
    """Get singleton EmailClient instance."""
    global _email_client_instance
    if _email_client_instance is None:
        _email_client_instance = EmailClient()
    return _email_client_instance
