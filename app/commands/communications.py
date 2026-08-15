"""Communications commands: WhatsApp, Email, and File sharing."""

from __future__ import annotations

import asyncio
import os
import re
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Any

from app.commands.registry import ActionResult
from app.core.config import ConfigManager
from app.core.logger import get_logger

logger = get_logger("communications")


class CommunicationCommands:
    """Handle WhatsApp messaging, email composition, and file sharing."""

    def __init__(self, config: ConfigManager | None = None) -> None:
        self.config = config or ConfigManager()

    def _normalize_phone(self, phone: str) -> str:
        """Strip non-digits except leading plus from phone number."""
        clean = re.sub(r"[^\d+]", "", phone.strip())
        if clean.startswith("+"):
            return clean[1:]
        return clean

    async def open_whatsapp(self, search: str = "") -> ActionResult:
        """Open WhatsApp desktop app or WhatsApp Web."""
        try:
            if search:
                clean_search = urllib.parse.quote(search.strip())
                url = f"https://web.whatsapp.com/send?phone={clean_search}"
            else:
                url = "https://web.whatsapp.com"

            # Try protocol first on Windows, then fallback to Web
            opened = False
            if hasattr(os, "startfile"):
                try:
                    os.startfile("whatsapp://")
                    opened = True
                except (OSError, AttributeError):
                    opened = False

            if not opened or search:
                webbrowser.open(url)

            target_info = f" with contact '{search}'" if search else ""
            return ActionResult(
                success=True,
                message=f"Opened WhatsApp{target_info}.",
                data={"search": search, "url": url},
            )
        except Exception as exc:
            logger.error("Failed to open WhatsApp: %s", exc)
            return ActionResult(success=False, message=f"Failed to open WhatsApp: {exc}")

    async def send_whatsapp_message(
        self,
        phone: str = "",
        message: str = "",
        recipient: str = "",
        auto_send: bool = True,
    ) -> ActionResult:
        """Compose and send a WhatsApp message to a specific phone number or contact."""
        target_num = phone or recipient
        if not target_num:
            return ActionResult(
                success=False,
                message="Please provide a phone number or recipient for WhatsApp.",
            )

        clean_number = self._normalize_phone(target_num)
        msg_text = message.strip() if message else ""
        encoded_msg = urllib.parse.quote(msg_text)

        web_url = f"https://web.whatsapp.com/send?phone={clean_number}&text={encoded_msg}"
        protocol_url = f"whatsapp://send?phone={clean_number}&text={encoded_msg}"

        try:
            opened = False
            if hasattr(os, "startfile"):
                try:
                    os.startfile(protocol_url)
                    opened = True
                except (OSError, AttributeError):
                    opened = False

            if not opened:
                webbrowser.open(web_url)

            # If auto_send is True, trigger Enter key via PyAutoGUI after a brief delay in background
            if auto_send and msg_text:
                async def _auto_press_enter() -> None:
                    try:
                        await asyncio.sleep(5)
                        import pyautogui
                        pyautogui.press("enter")
                    except Exception:
                        pass

                asyncio.create_task(_auto_press_enter())

            recipient_display = f"'{target_num}'" if target_num else "recipient"
            msg_display = f" with message: '{msg_text}'" if msg_text else ""
            return ActionResult(
                success=True,
                message=f"Opening WhatsApp chat for {recipient_display}{msg_display}.",
                data={
                    "phone": clean_number,
                    "message": msg_text,
                    "web_url": web_url,
                },
            )
        except Exception as exc:
            logger.error("Failed to send WhatsApp message: %s", exc)
            return ActionResult(
                success=False,
                message=f"Failed to send WhatsApp message: {exc}",
            )

    async def send_email(
        self,
        to: str = "",
        subject: str = "",
        body: str = "",
        attachment_path: str = "",
    ) -> ActionResult:
        """Compose an email with subject, body, and optional attachment."""
        recipient = to.strip() if to else ""
        sub = subject.strip() if subject else "Message from NOVA"
        body_text = body.strip() if body else ""

        if attachment_path:
            att_path = Path(attachment_path)
            if att_path.exists():
                body_text = f"{body_text}\n\n[Attachment: {att_path.name} located at {att_path.resolve()}]".strip()
            else:
                logger.warning("Attachment file does not exist: %s", attachment_path)

        encoded_to = urllib.parse.quote(recipient)
        encoded_sub = urllib.parse.quote(sub)
        encoded_body = urllib.parse.quote(body_text)

        # Build standard mailto URL
        mailto_url = f"mailto:{encoded_to}?subject={encoded_sub}&body={encoded_body}"

        # Web Gmail compose URL fallback
        gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={encoded_to}&su={encoded_sub}&body={encoded_body}"

        try:
            opened = False
            if hasattr(os, "startfile") and recipient:
                try:
                    os.startfile(mailto_url)
                    opened = True
                except (OSError, AttributeError):
                    opened = False

            if not opened:
                webbrowser.open(gmail_url)

            recip_info = f" to '{recipient}'" if recipient else ""
            return ActionResult(
                success=True,
                message=f"Composing email{recip_info} with subject '{sub}'.",
                data={
                    "to": recipient,
                    "subject": sub,
                    "body": body_text,
                    "attachment": attachment_path,
                    "url": mailto_url if opened else gmail_url,
                },
            )
        except Exception as exc:
            logger.error("Failed to compose email: %s", exc)
            return ActionResult(success=False, message=f"Failed to compose email: {exc}")

    async def send_file(
        self,
        path: str = "",
        recipient: str = "",
        channel: str = "email",
    ) -> ActionResult:
        """Send or share a file via Email or WhatsApp."""
        if not path:
            return ActionResult(success=False, message="Please specify a file path to send.")

        file_path = Path(path).expanduser().resolve()
        if not file_path.exists():
            # Check relative to desktop or current directory
            desktop_path = Path.home() / "Desktop" / path
            if desktop_path.exists():
                file_path = desktop_path
            else:
                return ActionResult(
                    success=False,
                    message=f"File not found: {path}. Please check the path and try again.",
                )

        channel_norm = channel.lower().strip() if channel else "email"

        if "whatsapp" in channel_norm:
            # WhatsApp file sharing
            msg = f"Sending file: {file_path.name}"
            return await self.send_whatsapp_message(
                recipient=recipient,
                message=msg,
            )
        else:
            # Email file sharing
            sub = f"Sending file: {file_path.name}"
            body = f"Please find attached {file_path.name}."
            return await self.send_email(
                to=recipient,
                subject=sub,
                body=body,
                attachment_path=str(file_path),
            )
