"""Email integration package."""
from nova_app.integrations.email.email_client import (
    EmailClient,
    get_email_client,
    is_valid_email,
)

__all__ = [
    "EmailClient",
    "get_email_client",
    "is_valid_email",
]
