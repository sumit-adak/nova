"""Multi-platform messaging integrations (WhatsApp, Discord, Slack, Telegram)."""
import json
import urllib.parse
import urllib.request
import webbrowser
from typing import Any
import structlog

logger = structlog.get_logger(__name__)


class WhatsAppClient:
    """WhatsApp Web client opening pre-filled chat URLs."""

    def send_or_open_chat(self, phone_number: str | None, message: str) -> dict[str, Any]:
        """Open WhatsApp Web with prefilled message."""
        encoded_msg = urllib.parse.quote(message)
        if phone_number:
            clean_phone = "".join(filter(str.isdigit, phone_number))
            url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"
        else:
            url = f"https://web.whatsapp.com/send?text={encoded_msg}"

        webbrowser.open(url)
        logger.info("Opened WhatsApp Web", phone=phone_number)
        return {
            "platform": "whatsapp",
            "status": "opened_web",
            "phone": phone_number,
            "url": url,
        }


class DiscordWebhookClient:
    """Sends messages to Discord channel via webhook."""

    def send_message(self, webhook_url: str, content: str, username: str = "NOVA") -> dict[str, Any]:
        """Dispatch payload to Discord webhook."""
        payload = json.dumps({"content": content, "username": username}).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "NOVA-Assistant/0.1.0"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            return {
                "platform": "discord",
                "status": "delivered",
                "code": resp.status,
            }


class SlackWebhookClient:
    """Sends messages to Slack channel via incoming webhook."""

    def send_message(self, webhook_url: str, text: str) -> dict[str, Any]:
        """Dispatch payload to Slack webhook."""
        payload = json.dumps({"text": text}).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            return {
                "platform": "slack",
                "status": "delivered",
                "code": resp.status,
            }


class TelegramClient:
    """Sends messages via Telegram Bot API."""

    def send_message(self, bot_token: str, chat_id: str, text: str) -> dict[str, Any]:
        """Dispatch message to Telegram chat."""
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            return {
                "platform": "telegram",
                "status": "delivered",
                "code": resp.status,
            }
