"""Content Generation package."""
from nova_app.integrations.content_generation.commit_message_writer import format_commit_message
from nova_app.integrations.content_generation.email_writer import EmailDraft, draft_email_content

__all__ = [
    "EmailDraft",
    "draft_email_content",
    "format_commit_message",
]
