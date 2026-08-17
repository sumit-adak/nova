"""Email drafting and content synthesis assistant."""
from typing import Any
from pydantic import BaseModel, Field


class EmailDraft(BaseModel):
    subject: str
    recipient: str
    body: str


def draft_email_content(
    recipient: str,
    purpose: str,
    context: str = "",
    sender_name: str = "User",
    tone: str = "professional",
) -> EmailDraft:
    """Draft a structured email based on purpose and context."""
    p_lower = purpose.lower()

    if "absent" in p_lower or "leave" in p_lower or "sick" in p_lower:
        subject = f"Absence Notification - {sender_name}"
        body = (
            f"Dear {recipient},\n\n"
            f"I am writing to inform you that I will be unable to attend today due to {context if context else 'unforeseen circumstances'}.\n\n"
            "I will ensure that any pending items or coursework are caught up promptly upon my return.\n\n"
            f"Best regards,\n{sender_name}"
        )
    elif "follow up" in p_lower or "follow-up" in p_lower:
        subject = f"Follow-up: {context if context else 'Our Discussion'}"
        body = (
            f"Hi {recipient},\n\n"
            f"I wanted to follow up on {context if context else 'our previous conversation'}.\n\n"
            "Please let me know if you need any further information or updates from my end.\n\n"
            f"Best regards,\n{sender_name}"
        )
    else:
        subject = f"Inquiry regarding {purpose}"
        body = (
            f"Dear {recipient},\n\n"
            f"I am reaching out regarding {purpose}.\n\n"
            f"{context}\n\n"
            f"Thank you for your time and assistance.\n\n"
            f"Sincerely,\n{sender_name}"
        )

    return EmailDraft(
        subject=subject,
        recipient=recipient,
        body=body,
    )
