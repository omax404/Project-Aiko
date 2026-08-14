"""
AIKO EMAIL ENGINE v1.0
Async SMTP/IMAP Email Client with Proactive Inbox Monitoring & Reasoning Capabilities.
Allows Aiko to send, read, summarize, and reply to emails autonomously or on request.
"""

import asyncio
import email
import imaplib
import logging
import smtplib
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from core.config_manager import config

logger = logging.getLogger("EmailEngine")


class EmailEngine:
    """
    Asynchronous Email Interface for Aiko Desktop.
    Supports secure SSL/TLS SMTP sending and IMAP inbox fetching.
    """

    def __init__(self):
        self.reload_config()

    def reload_config(self):
        """Reload email configuration parameters from user_settings.json."""
        email_cfg = config.get("email") or {}
        self.enabled = email_cfg.get("enabled", False)
        self.address = email_cfg.get("address") or email_cfg.get("username") or ""
        self.username = email_cfg.get("username") or self.address
        self.password = email_cfg.get("password") or ""
        self.smtp_host = email_cfg.get("smtp_host", "smtp.gmail.com")
        self.smtp_port = int(email_cfg.get("smtp_port", 587))
        self.imap_host = email_cfg.get("imap_host", "imap.gmail.com")
        self.imap_port = int(email_cfg.get("imap_port", 993))
        self.use_tls = email_cfg.get("use_tls", True)

    @property
    def is_configured(self) -> bool:
        return bool(self.address and self.password)

    async def send_email(
        self,
        to_address: str,
        subject: str,
        body: str,
        html: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Send an email using SMTP in an executor thread."""
        if not self.is_configured:
            return False, "Email account credentials not configured in user_settings.json."

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._send_email_sync, to_address, subject, body, html
        )

    def _send_email_sync(
        self,
        to_address: str,
        subject: str,
        body: str,
        html: Optional[str] = None
    ) -> Tuple[bool, str]:
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"Aiko <{self.address}>"
            msg["To"] = to_address
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain", "utf-8"))
            if html:
                msg.attach(MIMEText(html, "html", "utf-8"))

            if self.smtp_port == 465:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=15) as server:
                    server.login(self.username, self.password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                    if self.use_tls:
                        server.starttls()
                    server.login(self.username, self.password)
                    server.send_message(msg)

            logger.info(f"[EmailEngine] Email sent successfully to {to_address} (Subject: {subject})")
            return True, f"Email sent to {to_address} successfully!"

        except Exception as e:
            logger.error(f"[EmailEngine] Failed to send email: {e}")
            return False, f"Email delivery failed: {str(e)}"

    async def fetch_inbox(
        self,
        unread_only: bool = True,
        limit: int = 5
    ) -> Tuple[bool, Union[List[Dict], str]]:
        """Fetch recent emails from IMAP inbox."""
        if not self.is_configured:
            return False, "Email credentials missing."

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._fetch_inbox_sync, unread_only, limit
        )

    def _fetch_inbox_sync(
        self,
        unread_only: bool = True,
        limit: int = 5
    ) -> Tuple[bool, Union[List[Dict], str]]:
        try:
            mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            mail.login(self.username, self.password)
            mail.select("inbox")

            search_criterion = "UNSEEN" if unread_only else "ALL"
            status, messages = mail.search(None, search_criterion)

            if status != "OK":
                mail.logout()
                return False, "Failed to search IMAP inbox."

            email_ids = messages[0].split()
            if not email_ids:
                mail.logout()
                return True, []

            # Get latest 'limit' messages
            target_ids = email_ids[-limit:]
            emails_list = []

            for eid in reversed(target_ids):
                _, msg_data = mail.fetch(eid, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        raw_msg = email.message_from_bytes(response_part[1])
                        subject = self._decode_header_text(raw_msg.get("Subject", ""))
                        sender = self._decode_header_text(raw_msg.get("From", ""))
                        date = raw_msg.get("Date", "")
                        body = self._extract_email_body(raw_msg)

                        emails_list.append({
                            "id": eid.decode(),
                            "subject": subject,
                            "sender": sender,
                            "date": date,
                            "snippet": body[:200] + "..." if len(body) > 200 else body,
                            "body": body
                        })

            mail.logout()
            return True, emails_list

        except Exception as e:
            logger.error(f"[EmailEngine] IMAP fetch error: {e}")
            return False, f"IMAP Fetch Error: {str(e)}"

    def _decode_header_text(self, text: str) -> str:
        if not text:
            return ""
        decoded_fragments = decode_header(text)
        header_str = ""
        for fragment, encoding in decoded_fragments:
            if isinstance(fragment, bytes):
                header_str += fragment.decode(encoding or "utf-8", errors="ignore")
            else:
                header_str += str(fragment)
        return header_str

    def _extract_email_body(self, msg) -> str:
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body += payload.decode("utf-8", errors="ignore")
                    except Exception:
                        pass
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode("utf-8", errors="ignore")
            except Exception:
                pass

        return body.strip()


# Global Singleton Instance
email_engine = EmailEngine()
