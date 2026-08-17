"""Communication executors for email drafting, sending, and messaging platforms."""
from typing import Any, Literal
from pydantic import BaseModel, Field
from nova_app.integrations.content_generation.email_writer import draft_email_content
from nova_app.integrations.email.email_client import get_email_client
from nova_app.integrations.messaging.clients import (
    DiscordWebhookClient,
    SlackWebhookClient,
    TelegramClient,
    WhatsAppClient,
)


class DraftEmailArgs(BaseModel):
    recipient: str = Field(description="Recipient name or email address")
    purpose: str = Field(description="Purpose of the email (e.g. sick leave, absent, inquiry, project update)")
    context: str = Field(default="", description="Additional details or context for the email body")
    sender_name: str = Field(default="User", description="Name of the sender to sign off with")


class SendEmailArgs(BaseModel):
    recipient: str = Field(description="Target recipient email address (e.g. name@domain.com)")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Full email body content")


class SendMessageArgs(BaseModel):
    platform: Literal["whatsapp", "discord", "slack", "telegram"] = Field(description="Target messaging platform")
    message: str = Field(description="Message text to send")
    recipient: str | None = Field(default=None, description="Phone number or user/channel identifier")
    webhook_or_token: str | None = Field(default=None, description="Webhook URL or Bot token if using Discord/Slack/Telegram")


def draft_email_executor(args: DraftEmailArgs) -> dict[str, Any]:
    """Draft an email according to purpose and context."""
    draft = draft_email_content(
        recipient=args.recipient,
        purpose=args.purpose,
        context=args.context,
        sender_name=args.sender_name,
    )
    return {
        "status": "drafted",
        "subject": draft.subject,
        "recipient": draft.recipient,
        "body": draft.body,
    }


def send_email_executor(args: SendEmailArgs) -> dict[str, Any]:
    """Send or compose email (HIGH risk)."""
    client = get_email_client()
    return client.compose_mailto(
        recipient=args.recipient,
        subject=args.subject,
        body=args.body,
    )


def send_message_executor(args: SendMessageArgs) -> dict[str, Any]:
    """Send message to WhatsApp, Discord, Slack, or Telegram (HIGH risk)."""
    if args.platform == "whatsapp":
        client = WhatsAppClient()
        return client.send_or_open_chat(phone_number=args.recipient, message=args.message)

    elif args.platform == "discord":
        if not args.webhook_or_token:
            raise ValueError("Discord webhook URL is required.")
        d_client = DiscordWebhookClient()
        return d_client.send_message(webhook_url=args.webhook_or_token, content=args.message)

    elif args.platform == "slack":
        if not args.webhook_or_token:
            raise ValueError("Slack webhook URL is required.")
        s_client = SlackWebhookClient()
        return s_client.send_message(webhook_url=args.webhook_or_token, text=args.message)

    elif args.platform == "telegram":
        if not args.webhook_or_token or not args.recipient:
            raise ValueError("Telegram Bot Token and Chat ID (recipient) are required.")
        t_client = TelegramClient()
        return t_client.send_message(bot_token=args.webhook_or_token, chat_id=args.recipient, text=args.message)

    raise ValueError(f"Unsupported messaging platform: '{args.platform}'")
