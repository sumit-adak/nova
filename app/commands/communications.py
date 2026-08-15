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

    def _expand_message_content(self, text: str, mode: str = "whatsapp") -> tuple[str, str]:
        """Expand short prompts (e.g. 'birthday wish', 'absent letter') into full, rich, professional messages."""
        clean = text.strip()
        lower = clean.lower()

        # Birthday wishes
        if any(k in lower for k in ("birthday wish", "happy birthday", "wish birthday", "bday wish", "bday")):
            if mode == "email":
                sub = "Wishing You a Very Happy Birthday! 🎉"
                body = (
                    "Dear Friend,\n\n"
                    "Wishing you a very Happy Birthday! 🎂✨ May this special day bring you immense joy, "
                    "happiness, and wonderful memories. Wishing you good health, prosperity, and great success "
                    "in the year ahead!\n\n"
                    "Have a fantastic celebration!\n\n"
                    "Warmest regards,\n[Your Name]"
                )
                return sub, body
            else:
                return "Happy Birthday", (
                    "🎉 Happy Birthday! 🎂 Wishing you a fantastic day filled with happiness, laughter, "
                    "and success in the year ahead! May all your dreams come true! 🎈✨"
                )

        # Absent / Leave letter
        if any(k in lower for k in ("absent letter", "leave letter", "leave application", "absence letter", "absent", "leave")):
            sub = "Leave Application - Absence Notification"
            body = (
                "Dear Sir/Madam,\n\n"
                "I am writing to formally request a leave of absence and notify you that I will be unable to attend today due to "
                "unforeseen personal circumstances. I will ensure all pending tasks and responsibilities "
                "are prioritized and completed promptly upon my return.\n\n"
                "Thank you very much for your understanding and support.\n\n"
                "Sincerely,\n[Your Name]"
            )
            return sub, body

        # Sick leave
        if any(k in lower for k in ("sick leave", "sick letter", "fever", "unwell", "doctor")):
            sub = "Leave Application - Sick Leave"
            body = (
                "Dear Sir/Madam,\n\n"
                "I am writing to inform you that I am currently unwell and will not be able to attend today. "
                "I am taking the necessary rest/medication and will keep you updated regarding my recovery.\n\n"
                "Thank you for your understanding.\n\n"
                "Sincerely,\n[Your Name]"
            )
            return sub, body

        # Resignation letter
        if "resignation" in lower:
            sub = "Formal Resignation Letter"
            body = (
                "Dear Sir/Madam,\n\n"
                "Please accept this letter as formal notification of my resignation from my position. "
                "I am deeply grateful for the opportunities and experiences during my time with the team.\n\n"
                "I will do everything possible to ensure a smooth transition of my responsibilities.\n\n"
                "Sincerely,\n[Your Name]"
            )
            return sub, body

        # Congratulations
        if any(k in lower for k in ("congratulation", "congrats", "achievement")):
            return "Congratulations", (
                "🎉 Huge congratulations on your wonderful achievement! 🌟 Wishing you continued "
                "success and greatness in all your upcoming endeavors! 🚀✨"
            )

        # Thank you note
        if any(k in lower for k in ("thank you", "thanks note", "appreciation")):
            return "Thank You", (
                "Thank you so much for your assistance and support! It is truly appreciated. "
                "Looking forward to connecting with you again! ✨"
            )

        return "", clean

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
        raw_msg = message.strip() if message else ""

        # Check if message is a short intent that should be expanded into a full rich text/letter
        _, expanded_msg = self._expand_message_content(raw_msg, mode="whatsapp")
        final_msg = expanded_msg if expanded_msg else raw_msg

        encoded_msg = urllib.parse.quote(final_msg)
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

            # Auto-send message reliably with multi-attempt enter key
            if auto_send and final_msg:
                async def _auto_press_enter() -> None:
                    try:
                        # Attempt 1 after 4 seconds (for fast app or existing tab)
                        await asyncio.sleep(4)
                        import pyautogui
                        pyautogui.press("enter")
                        # Attempt 2 after additional 3 seconds (for slower loading web pages)
                        await asyncio.sleep(3)
                        pyautogui.press("enter")
                    except Exception:
                        pass

                asyncio.create_task(_auto_press_enter())

            recipient_display = f"'{target_num}'" if target_num else "recipient"
            preview = final_msg[:60] + "..." if len(final_msg) > 60 else final_msg
            return ActionResult(
                success=True,
                message=f"Sending WhatsApp message to {recipient_display}: \"{preview}\"",
                data={
                    "phone": clean_number,
                    "message": final_msg,
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
        raw_body = body.strip() if body else ""
        raw_sub = subject.strip() if subject else ""

        # Auto-expand template topics if body/subject asks for letter/wish
        auto_sub, expanded_body = self._expand_message_content(f"{raw_sub} {raw_body}".strip(), mode="email")
        if auto_sub and (not raw_sub or any(k in raw_sub.lower() for k in ("absent", "leave", "sick", "birthday", "resignation", "congratulat", "thank"))):
            final_sub = auto_sub
        else:
            final_sub = raw_sub or (auto_sub or "Message from NOVA")

        final_body = expanded_body if (expanded_body and expanded_body != f"{raw_sub} {raw_body}".strip()) else (raw_body or "Hello,")

        if attachment_path:
            att_path = Path(attachment_path)
            if att_path.exists():
                final_body = f"{final_body}\n\n[Attachment: {att_path.name} located at {att_path.resolve()}]".strip()
            else:
                logger.warning("Attachment file does not exist: %s", attachment_path)

        encoded_to = urllib.parse.quote(recipient)
        encoded_sub = urllib.parse.quote(final_sub)
        encoded_body = urllib.parse.quote(final_body)

        mailto_url = f"mailto:{encoded_to}?subject={encoded_sub}&body={encoded_body}"
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
                message=f"Composing professional email{recip_info} with subject '{final_sub}'.",
                data={
                    "to": recipient,
                    "subject": final_sub,
                    "body": final_body,
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
