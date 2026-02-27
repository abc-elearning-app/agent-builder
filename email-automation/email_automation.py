#!/usr/bin/env python3
"""
Email Automation Pipeline — ABC E-Learning Support System

Polls Gmail for unread support emails via IMAP, processes each via Gemini API
using the email-support-agent prompt, then either:
  - AUTO_REPLY   → send HTML reply via SMTP + apply AUTO_REPLIED label via IMAP
  - NEED_MANUAL_REVIEW → send Discord alert + prompt operator in terminal

Usage:
    cp .env.example .env  # fill in your values
    pip install -r requirements.txt
    python email_automation.py
"""

import email as email_lib
import imaplib
import json
import logging
import os
import re
import smtplib
import socket
import sys
import time

# Prevent any socket (IMAP SSL handshake, SMTP) from hanging indefinitely
socket.setdefaulttimeout(30)
from datetime import datetime, timezone
from email.header import decode_header as decode_email_header
from email.message import Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
AGENTS_DIR = BASE_DIR / "agents"

SUPPORT_GUIDELINE_PATH = AGENTS_DIR / "support_guideline.md"
EMAIL_AGENT_PATH = AGENTS_DIR / "email-support-agent.md"
PROCESSED_IDS_FILE = BASE_DIR / "processed_email_ids.json"

# ── Constants ─────────────────────────────────────────────────────────────────

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
AUTO_REPLIED_LABEL = "AUTO_REPLIED"


# ── Config ────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    load_dotenv()

    required = {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "DISCORD_WEBHOOK_URL": os.getenv("DISCORD_WEBHOOK_URL"),
        "SUPPORT_EMAIL_ADDRESS": os.getenv("SUPPORT_EMAIL_ADDRESS"),
        "GMAIL_APP_PASSWORD": os.getenv("GMAIL_APP_PASSWORD"),
    }

    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"[ERROR] Missing required environment variables: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in the values.")
        sys.exit(1)

    return {
        **required,
        "POLL_INTERVAL_SECONDS": int(os.getenv("POLL_INTERVAL_SECONDS", "60")),
        "MAX_EMAILS_PER_POLL": int(os.getenv("MAX_EMAILS_PER_POLL", "10")),
        "GEMINI_MODEL": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO").upper(),
    }


def setup_logging(level: str = "INFO") -> None:
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format=fmt,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(BASE_DIR / "email_automation.log", encoding="utf-8"),
        ],
    )


# ── State Tracker ─────────────────────────────────────────────────────────────

class StateTracker:
    """Persists processed email UIDs to a JSON file to avoid duplicate processing."""

    def __init__(self):
        self._ids: set[str] = set()
        self._load()

    def _load(self) -> None:
        if PROCESSED_IDS_FILE.exists():
            try:
                data = json.loads(PROCESSED_IDS_FILE.read_text(encoding="utf-8"))
                self._ids = set(data.get("processed_ids", []))
                logging.info("State: loaded %d processed IDs", len(self._ids))
            except (json.JSONDecodeError, OSError) as e:
                logging.warning("State: failed to load, starting fresh: %s", e)
                self._ids = set()

    def _save(self) -> None:
        tmp = PROCESSED_IDS_FILE.with_suffix(".json.tmp")
        try:
            tmp.write_text(
                json.dumps({"processed_ids": sorted(self._ids)}, indent=2),
                encoding="utf-8",
            )
            tmp.replace(PROCESSED_IDS_FILE)
        except OSError as e:
            logging.error("State: failed to save: %s", e)

    def is_processed(self, email_id: str) -> bool:
        return email_id in self._ids

    def mark_processed(self, email_id: str) -> None:
        self._ids.add(email_id)
        self._save()


# ── Support Email Pre-filter ──────────────────────────────────────────────────

# Patterns in From address that indicate automated/system emails
_NO_REPLY_PATTERNS = [
    "no-reply", "no_reply", "noreply", "do-not-reply", "donotreply",
    "notifications@", "notification@", "mailer-daemon", "postmaster@",
    "bounce@", "bounces@", "alerts@", "alert@", "auto@", "automated@",
    "system@", "support-noreply",
]


def is_support_email_candidate(email_data: dict) -> bool:
    """
    Quick header-based pre-filter before calling Gemini.

    Returns False (skip) when the email is clearly NOT a customer support request:
      - From a no-reply / automated sender
      - Contains List-Unsubscribe header (newsletter)
      - Precedence: bulk / list / junk
      - Auto-Submitted header (automated message)

    Returns True for everything else — Gemini does the final classification.
    """
    from_email = email_data.get("from_email", "").lower()

    # No-reply / automated sender
    if any(p in from_email for p in _NO_REPLY_PATTERNS):
        logging.debug("Pre-filter: no-reply sender — %s", from_email)
        return False

    # Newsletter (has List-Unsubscribe header)
    if email_data.get("_list_unsubscribe"):
        logging.debug("Pre-filter: newsletter (List-Unsubscribe) — %s", from_email)
        return False

    # Bulk / mailing-list precedence
    precedence = email_data.get("_precedence", "").lower()
    if precedence in ("bulk", "list", "junk"):
        logging.debug("Pre-filter: bulk mail (Precedence: %s) — %s", precedence, from_email)
        return False

    # Automated message
    auto_submitted = email_data.get("_auto_submitted", "").lower()
    if auto_submitted and auto_submitted != "no":
        logging.debug("Pre-filter: auto-submitted — %s", from_email)
        return False

    return True


# ── Gmail Client (IMAP + SMTP) ────────────────────────────────────────────────

class GmailClient:
    """Gmail client using IMAP for reading and SMTP for sending via App Password."""

    def __init__(self):
        self._email: str = ""
        self._password: str = ""  # App password without spaces

    def authenticate(self, email_address: str, app_password: str) -> None:
        """Validate credentials by connecting to IMAP and immediately logging out."""
        self._email = email_address
        self._password = app_password.replace(" ", "")

        # Test credentials — raises on failure
        imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        imap.login(self._email, self._password)
        imap.logout()
        logging.info("Gmail: authenticated as %s via IMAP/SMTP App Password", email_address)

    def _connect_imap(self) -> imaplib.IMAP4_SSL:
        imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        imap.login(self._email, self._password)
        return imap

    def get_unread_emails(self, max_results: int = 10) -> list[dict]:
        """Fetch unread INBOX emails via IMAP UID search. Returns parsed email dicts."""
        try:
            imap = self._connect_imap()
            imap.select("INBOX")
            _, uid_data = imap.uid("SEARCH", None, "UNSEEN")
            raw_uids = uid_data[0].split() if uid_data[0] else []

            # Take the most recent N UIDs (ascending order → last N = newest)
            raw_uids = raw_uids[-max_results:]

            emails = []
            for uid_bytes in raw_uids:
                uid = uid_bytes.decode() if isinstance(uid_bytes, bytes) else uid_bytes
                try:
                    email_data = self._fetch_message(imap, uid)
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logging.error("Gmail: failed to fetch UID %s: %s", uid, e)

            imap.logout()
            return emails

        except imaplib.IMAP4.error as e:
            logging.error("Gmail: IMAP error fetching unread emails: %s", e)
            return []
        except Exception as e:
            logging.error("Gmail: unexpected error fetching emails: %s", e)
            return []

    def _fetch_message(self, imap: imaplib.IMAP4_SSL, uid: str) -> Optional[dict]:
        # BODY.PEEK[] reads content WITHOUT setting the \Seen flag
        _, msg_data = imap.uid("FETCH", uid, "(BODY.PEEK[])")
        if not msg_data or not msg_data[0]:
            return None

        raw_bytes = msg_data[0][1]
        if not isinstance(raw_bytes, bytes):
            return None

        msg = email_lib.message_from_bytes(raw_bytes)

        from_header = msg.get("From", "")
        raw_subject = msg.get("Subject", "(no subject)")
        message_id_header = msg.get("Message-ID", "")
        subject = self._decode_header_value(raw_subject)
        body = self._extract_body(msg)

        return {
            "email_id": uid,
            "from_email": from_header,
            "subject": subject,
            "body": body,
            "message_id_header": message_id_header,
            # Filtering headers for pre-filter
            "_list_unsubscribe": msg.get("List-Unsubscribe", ""),
            "_precedence": msg.get("Precedence", ""),
            "_auto_submitted": msg.get("Auto-Submitted", ""),
        }

    @staticmethod
    def _decode_header_value(value: str) -> str:
        """Decode RFC2047-encoded header (e.g. =?UTF-8?B?...?=)."""
        parts = decode_email_header(value)
        result = ""
        for part, encoding in parts:
            if isinstance(part, bytes):
                result += part.decode(encoding or "utf-8", errors="replace")
            else:
                result += part
        return result

    @staticmethod
    def _extract_body(msg: Message) -> str:
        """Extract readable text from a MIME email. Prefers plain text over HTML."""
        plain = ""
        html = ""

        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                disposition = part.get("Content-Disposition", "")
                if "attachment" in disposition:
                    continue
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                if ctype == "text/plain" and not plain:
                    plain = text
                elif ctype == "text/html" and not html:
                    html = text
        else:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace") if payload else ""
            if msg.get_content_type() == "text/html":
                html = text
            else:
                plain = text

        if plain:
            return plain.strip()
        if html:
            return re.sub(r"<[^>]+>", " ", html).strip()
        return ""

    def send_reply(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        message_id_header: str = "",
    ) -> bool:
        """Send an HTML reply via SMTP. Threads correctly via In-Reply-To header."""
        try:
            reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"
            plain_body = re.sub(r"<[^>]+>", " ", html_body).strip()

            msg = MIMEMultipart("alternative")
            msg["From"] = self._email
            msg["To"] = to_email
            msg["Subject"] = reply_subject
            if message_id_header:
                msg["In-Reply-To"] = message_id_header
                msg["References"] = message_id_header

            msg.attach(MIMEText(plain_body, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(self._email, self._password)
                smtp.sendmail(self._email, to_email, msg.as_bytes())

            logging.info("Gmail: reply sent to %s", to_email)
            return True

        except smtplib.SMTPException as e:
            logging.error("Gmail: SMTP error sending to %s: %s", to_email, e)
            return False
        except Exception as e:
            logging.error("Gmail: unexpected error sending to %s: %s", to_email, e)
            return False

    def apply_label(self, message_id: str, label_name: str) -> bool:
        """
        Apply a Gmail label by copying the UID to the label's IMAP mailbox.
        Gmail labels appear as IMAP mailboxes; COPY associates the label.
        """
        try:
            imap = self._connect_imap()
            imap.select("INBOX")

            # Create the mailbox if it doesn't exist (Gmail will show it as a label)
            imap.create(label_name)  # Silently fails if already exists

            result, _ = imap.uid("COPY", message_id, label_name)
            imap.logout()

            if result == "OK":
                logging.info("Gmail: label '%s' applied to UID %s", label_name, message_id)
                return True
            logging.warning("Gmail: COPY to '%s' returned %s", label_name, result)
            return False

        except Exception as e:
            logging.warning("Gmail: could not apply label '%s': %s (non-critical)", label_name, e)
            return False

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as \\Seen via IMAP STORE."""
        try:
            imap = self._connect_imap()
            imap.select("INBOX")
            imap.uid("STORE", message_id, "+FLAGS", "\\Seen")
            imap.logout()
            return True
        except Exception as e:
            logging.error("Gmail: failed to mark UID %s as read: %s", message_id, e)
            return False


# ── Gemini Client ─────────────────────────────────────────────────────────────

class GeminiClient:
    """
    Calls Gemini API using the email-support-agent system prompt.
    Passes the support guideline as inline content (Mode A in the agent prompt),
    so no Read tool is needed at runtime.
    """

    def __init__(self, api_key: str, model: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model
        self._system_prompt: Optional[str] = None
        self._guideline_content: Optional[str] = None

    def load_prompts(self) -> None:
        """Load system prompt from email-support-agent.md and guideline content."""
        if not EMAIL_AGENT_PATH.exists():
            raise FileNotFoundError(f"Agent file not found: {EMAIL_AGENT_PATH}")
        if not SUPPORT_GUIDELINE_PATH.exists():
            raise FileNotFoundError(f"Guideline not found: {SUPPORT_GUIDELINE_PATH}")

        raw = EMAIL_AGENT_PATH.read_text(encoding="utf-8")
        self._system_prompt = self._strip_frontmatter(raw)
        self._guideline_content = SUPPORT_GUIDELINE_PATH.read_text(encoding="utf-8")

        logging.info(
            "Gemini: loaded system prompt (%d chars), guideline (%d chars)",
            len(self._system_prompt),
            len(self._guideline_content),
        )

    @staticmethod
    def _strip_frontmatter(text: str) -> str:
        """Remove YAML frontmatter (--- block) from agent markdown file."""
        lines = text.splitlines()
        if lines and lines[0].strip() == "---":
            end = next(
                (i for i, ln in enumerate(lines[1:], 1) if ln.strip() == "---"), None
            )
            if end is not None:
                return "\n".join(lines[end + 1:]).strip()
        return text.strip()

    def process_email(self, email_data: dict) -> dict:
        """
        Send email data to Gemini and return the parsed JSON decision.
        Raises ValueError on bad response, Exception on API failure.
        """
        if not self._system_prompt:
            raise RuntimeError("Prompts not loaded. Call load_prompts() first.")

        user_payload = {
            "email_id": email_data["email_id"],
            "from_email": email_data["from_email"],
            "subject": email_data["subject"],
            "body": email_data["body"],
            "support_guideline": "",
            "support_guideline_content": self._guideline_content,  # Mode A: inline
        }

        logging.info(
            "Gemini: processing '%s' from %s",
            email_data["subject"],
            email_data["from_email"],
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=json.dumps(user_payload, ensure_ascii=False),
            config=genai_types.GenerateContentConfig(
                system_instruction=self._system_prompt,
                max_output_tokens=2048,
                temperature=0.1,
            ),
        )

        raw = response.text.strip()

        # Strip accidental markdown fences (```json ... ```)
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Non-JSON response for email {email_data['email_id']}: {e}\nRaw: {raw[:300]}"
            ) from e

        action = result.get("action")
        if action not in ("AUTO_REPLY", "NEED_MANUAL_REVIEW", "SKIP"):
            raise ValueError(f"Unexpected action '{action}' for email {email_data['email_id']}")

        logging.info("Gemini: decision → %s", action)
        return result


# ── Discord Notifier ──────────────────────────────────────────────────────────

class DiscordNotifier:
    """Sends webhook alerts to Discord for NEED_MANUAL_REVIEW emails."""

    MAX_LEN = 1900  # Discord limit is 2000; leave buffer

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_alert(self, message: str) -> bool:
        if len(message) > self.MAX_LEN:
            message = message[: self.MAX_LEN] + "\n... [truncated]"
        try:
            resp = requests.post(self.webhook_url, json={"content": message}, timeout=10)
            if resp.status_code in (200, 204):
                logging.info("Discord: alert sent")
                return True
            logging.error("Discord: HTTP %d — %s", resp.status_code, resp.text[:200])
            return False
        except requests.RequestException as e:
            logging.error("Discord: request failed: %s", e)
            return False


# ── Terminal UI ───────────────────────────────────────────────────────────────

class TerminalUI:
    """
    Interactive operator prompt for NEED_MANUAL_REVIEW emails.

    Operator options:
      - Type reply + press Enter twice → sends reply via Gmail
      - Type 'skip'                    → leave email in Gmail for manual handling
      - Type 'quit'                    → stop the automation loop
    """

    def prompt_operator(self, email_data: dict, reason: str) -> Optional[str]:
        """
        Returns the reply text, or None if the operator chose to skip.
        Auto-skips in non-interactive (headless) mode.
        """
        if not sys.stdin.isatty():
            logging.warning(
                "Non-interactive mode — auto-skipping email %s", email_data["email_id"]
            )
            return None

        sep = "─" * 68
        print(f"\n{sep}")
        print("  🚨 MANUAL REVIEW REQUIRED")
        print(sep)
        print(f"  From    : {email_data['from_email']}")
        print(f"  Subject : {email_data['subject']}")
        print(f"  Reason  : {reason}")
        print(sep)
        preview = email_data["body"][:500].replace("\n", "\n  ")
        print(f"  {preview}")
        if len(email_data["body"]) > 500:
            print("  ... [truncated]")
        print(sep)
        print("  ✏️  Type your reply then press Enter twice to send.")
        print("  ⏭️  Type 'skip' to handle manually in Gmail.")
        print("  ⛔  Type 'quit' to stop the automation.")
        print(sep)

        lines = []
        try:
            while True:
                line = input()
                cmd = line.strip().lower()
                if cmd == "quit":
                    logging.info("Operator requested quit")
                    raise SystemExit(0)
                if cmd == "skip":
                    print("  ⏭️  Skipped — email left in Gmail inbox.")
                    return None
                if line == "" and lines:
                    break
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            return None

        reply_text = "\n".join(lines).strip()
        if not reply_text:
            return None

        return reply_text

    @staticmethod
    def text_to_html(text: str) -> str:
        """Wrap operator's plain-text reply in minimal HTML for sending."""
        paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        body = "".join(
            f'<p style="margin:0 0 12px 0;">{p.replace(chr(10), "<br>")}</p>'
            for p in paras
        )
        return (
            '<div style="font-family: Arial, sans-serif; font-size:14px; '
            f'line-height:1.6; color:#333;">{body}</div>'
        )


# ── Pipeline Orchestrator ─────────────────────────────────────────────────────

class EmailPipeline:
    """
    Ties everything together.

    Flow per email:
      1. Skip if already processed (StateTracker)
      2. Call Gemini → AUTO_REPLY or NEED_MANUAL_REVIEW
      3a. AUTO_REPLY         → send HTML reply → apply label → mark read
      3b. NEED_MANUAL_REVIEW → Discord alert → operator prompt
            - operator replies → send reply → mark read
            - operator skips  → leave email unread in Gmail
      4. Mark UID as processed
    """

    def __init__(self, config: dict):
        self.config = config
        self.state = StateTracker()
        self.gmail = GmailClient()
        self.gemini = GeminiClient(config["GEMINI_API_KEY"], config["GEMINI_MODEL"])
        self.discord = DiscordNotifier(config["DISCORD_WEBHOOK_URL"])
        self.terminal = TerminalUI()

    def initialize(self) -> None:
        logging.info("Pipeline: initializing...")
        self.gmail.authenticate(
            self.config["SUPPORT_EMAIL_ADDRESS"],
            self.config["GMAIL_APP_PASSWORD"],
        )
        self.gemini.load_prompts()
        logging.info(
            "Pipeline: ready — %s | %d IDs in state",
            self.config["SUPPORT_EMAIL_ADDRESS"],
            len(self.state._ids),
        )

    def run_once(self) -> int:
        """One poll cycle. Returns number of emails processed."""
        emails = self.gmail.get_unread_emails(self.config["MAX_EMAILS_PER_POLL"])
        new_emails = [e for e in emails if not self.state.is_processed(e["email_id"])]

        if not new_emails:
            return 0

        logging.info("Pipeline: %d new email(s) to process", len(new_emails))

        count = 0
        for email_data in new_emails:
            try:
                # Tầng 1: Python pre-filter (headers)
                if not is_support_email_candidate(email_data):
                    logging.info(
                        "Pipeline: skip (pre-filter) — %s | %s",
                        email_data["from_email"], email_data["subject"][:60],
                    )
                    self.state.mark_processed(email_data["email_id"])
                    count += 1
                    continue

                self._process_one(email_data)
                self.state.mark_processed(email_data["email_id"])
                count += 1
            except Exception as e:
                logging.error(
                    "Pipeline: error on email %s: %s", email_data["email_id"], e, exc_info=True
                )
                # Do NOT mark as processed — will retry next cycle

        return count

    def _process_one(self, email_data: dict) -> None:
        logging.info(
            "Pipeline: → [%s] from %s", email_data["subject"], email_data["from_email"]
        )

        try:
            decision = self.gemini.process_email(email_data)
        except Exception as e:
            logging.error("Pipeline: Gemini failed, falling back to manual review: %s", e)
            decision = {
                "action": "NEED_MANUAL_REVIEW",
                "reason": f"AI processing error: {e}",
                "discord_message": (
                    f"🚨 Manual Review Required\n"
                    f"From: {email_data['from_email']}\n"
                    f"Subject: {email_data['subject']}\n"
                    f"Reason: AI processing error\n"
                    f"Preview: {email_data['body'][:500]}"
                ),
            }

        if decision["action"] == "AUTO_REPLY":
            self._handle_auto_reply(email_data, decision)
        elif decision["action"] == "SKIP":
            # Tầng 2: Gemini xác nhận không phải support email
            logging.info(
                "Pipeline: skip (Gemini) — %s", decision.get("reason", "not a support email")
            )
            print(f"  ⏭️  SKIP — {decision.get('reason', 'not a support email')}")
        else:
            self._handle_manual_review(email_data, decision)

    def _handle_auto_reply(self, email_data: dict, decision: dict) -> None:
        html_body = decision.get("reply_html", "")
        if not html_body:
            logging.warning("Pipeline: AUTO_REPLY has no reply_html — skipping send")
            return

        sent = self.gmail.send_reply(
            to_email=email_data["from_email"],
            subject=email_data["subject"],
            html_body=html_body,
            message_id_header=email_data.get("message_id_header", ""),
        )

        if sent:
            self.gmail.apply_label(email_data["email_id"], AUTO_REPLIED_LABEL)
            self.gmail.mark_as_read(email_data["email_id"])
            print(f"  ✅ AUTO_REPLY sent to {email_data['from_email']}")
        else:
            logging.error("Pipeline: send failed for AUTO_REPLY — not labeling")

    def _handle_manual_review(self, email_data: dict, decision: dict) -> None:
        reason = decision.get("reason", "Unknown reason")
        discord_msg = decision.get("discord_message", "")

        if discord_msg:
            self.discord.send_alert(discord_msg)
        print(f"  🚨 NEED_MANUAL_REVIEW — Discord alert sent")
        print(f"     Reason: {reason}")

        reply_text = self.terminal.prompt_operator(email_data, reason)

        if reply_text:
            html_body = TerminalUI.text_to_html(reply_text)
            sent = self.gmail.send_reply(
                to_email=email_data["from_email"],
                subject=email_data["subject"],
                html_body=html_body,
                message_id_header=email_data.get("message_id_header", ""),
            )
            if sent:
                self.gmail.mark_as_read(email_data["email_id"])
                print(f"  ✅ Manual reply sent to {email_data['from_email']}")
        else:
            print("  ⏭️  Email left in Gmail for manual handling.")

    def polling_loop(self) -> None:
        interval = self.config["POLL_INTERVAL_SECONDS"]
        print(f"\n🚀 Email automation started — polling every {interval}s  (Ctrl+C to stop)\n")
        logging.info("Pipeline: polling loop started")

        try:
            while True:
                ts = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                logging.info("Pipeline: poll at %s", ts)

                cycle_start = time.time()
                count = self.run_once()

                if count > 0:
                    logging.info("Pipeline: cycle done — %d email(s) processed", count)
                else:
                    logging.debug("Pipeline: no new emails")

                elapsed = time.time() - cycle_start
                sleep_for = max(0.0, interval - elapsed)
                time.sleep(sleep_for)

        except KeyboardInterrupt:
            print("\n⛔ Stopped by user.")
            logging.info("Pipeline: shutdown via KeyboardInterrupt")
        except SystemExit:
            print("\n⛔ Stopped by operator command.")
            logging.info("Pipeline: shutdown via quit command")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    config = load_config()
    setup_logging(config["LOG_LEVEL"])

    pipeline = EmailPipeline(config)
    pipeline.initialize()
    pipeline.polling_loop()


if __name__ == "__main__":
    main()
