"""
send_school_emails.py
Sends bulk personalized emails to contacts marked "To send" in the sheet.
Uses Gmail API via oauth_token.pickle — no app password required.

Usage:
  python3 scripts/send_school_emails.py email_template.txt [--dry-run]

  --dry-run   Print rendered emails without sending anything

Output:
  Prints progress to stdout. Updates sheet rows after each send.

Gmail API scope required in oauth_token.pickle:
  https://www.googleapis.com/auth/gmail.send
"""

import base64
import json
import os
import pickle
import subprocess
import sys
import time
import warnings
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

warnings.filterwarnings("ignore")

from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TOKEN_FILE = Path(__file__).parent.parent / "oauth_token.pickle"

RATE_DELAY  = 2    # seconds between emails
BATCH_SIZE  = 50   # pause after this many
BATCH_PAUSE = 30   # seconds


def _load_config():
    cfg = Path(__file__).parent.parent / "school_outreach_config.env"
    if not cfg.exists():
        return
    for line in cfg.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val

_load_config()

GMAIL_USER = os.environ.get("GMAIL_USER", "")
if not GMAIL_USER:
    print("ERROR: GMAIL_USER is not set in school_outreach_config.env", file=sys.stderr)
    sys.exit(1)


def load_creds():
    if not TOKEN_FILE.exists():
        print(f"ERROR: oauth_token.pickle not found at {TOKEN_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(TOKEN_FILE, "rb") as f:
        creds = pickle.load(f)
    if creds.expired and creds.refresh_token:
        print("🔄 Refreshing OAuth token ...", file=sys.stderr)
        creds.refresh(Request())
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    # Check Gmail scope is present
    if hasattr(creds, 'scopes') and creds.scopes:
        if not any('gmail' in s for s in creds.scopes):
            print("ERROR: oauth_token.pickle does not have Gmail send scope.", file=sys.stderr)
            print("       Re-run authentication to add the Gmail scope:", file=sys.stderr)
            print("       python3 scripts/reauth_with_gmail.py", file=sys.stderr)
            sys.exit(1)

    return creds


def load_template(path: str) -> dict:
    result = subprocess.run(
        ["python3", "scripts/load_email_template.py", path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ERROR loading template: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def load_contacts() -> list:
    result = subprocess.run(
        ["python3", "scripts/read_school_contacts.py"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ERROR reading contacts: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def build_message(to: str, subject: str, body: str, sender_name: str) -> dict:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{sender_name} <{GMAIL_USER}>" if sender_name else GMAIL_USER
    msg["To"]      = to
    msg.attach(MIMEText(body, "plain"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}


def mark_sent(row: int, status: str, sent_at: str = "", reason: str = ""):
    subprocess.run(
        ["python3", "scripts/mark_school_sent.py", str(row), status, sent_at, reason],
        capture_output=True
    )


def main():
    dry_run = "--dry-run" in sys.argv

    # Parse --limit N
    limit = 0
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--limit" and i < len(sys.argv):
            try:
                limit = int(sys.argv[i + 1])
            except (IndexError, ValueError):
                print("ERROR: --limit requires a number", file=sys.stderr)
                sys.exit(1)

    args = [a for a in sys.argv[1:] if not a.startswith("--") and not a.isdigit()]

    if not args:
        print("Usage: send_school_emails.py <email_template.txt> [--dry-run] [--limit N]")
        sys.exit(1)

    template_path = args[0]

    # Load template
    print(f"📄 Loading template: {template_path}")
    tmpl = load_template(template_path)
    subject_tpl = tmpl["subject"]
    body_tpl    = tmpl["body"]
    sender_name = tmpl.get("sender_name", "")

    # Load contacts
    print("📋 Reading contacts marked 'To send' from sheet...")
    contacts = load_contacts()

    if not contacts:
        print("\n⚠️  No contacts marked 'To send' in column L.")
        print("   Open the sheet and type 'To send' in column L for rows you want to email.")
        sys.exit(0)

    if limit:
        contacts = contacts[:limit]
        print(f"📬 {len(contacts)} contact(s) to send  (limit: {limit})\n")
    else:
        print(f"📬 {len(contacts)} contact(s) to send\n")

    # Preview first email
    first = contacts[0]
    vars_ = {
        "school_name": first["school_name"],
        "school_type": first["school_type"],
        "city":        first["city"],
        "state":       first["state"],
    }
    print("─" * 60)
    print(f"PREVIEW — email 1 of {len(contacts)}:")
    print(f"  To:      {first['email']}")
    print(f"  Subject: {subject_tpl.format(**vars_)}")
    print(f"  Body:\n")
    print(body_tpl.format(**vars_)[:400] + ("..." if len(body_tpl) > 400 else ""))
    print("─" * 60)

    if dry_run:
        print("\n[DRY RUN] No emails sent.")
        sys.exit(0)

    # Connect to Gmail API
    creds   = load_creds()
    service = build("gmail", "v1", credentials=creds)

    sent_count = 0
    failed     = []

    for i, contact in enumerate(contacts, 1):
        # Safety: skip already-sent rows
        if contact.get("email_sent"):
            print(f"  ⚠️  [{i}/{len(contacts)}] Skipping {contact['email']} — already sent")
            continue

        variables = {
            "school_name": contact["school_name"],
            "school_type": contact["school_type"],
            "city":        contact["city"],
            "state":       contact["state"],
        }

        try:
            subj = subject_tpl.format(**variables)
            body = body_tpl.format(**variables)
        except KeyError as e:
            print(f"  ❌ [{i}/{len(contacts)}] Template variable error: {e} — skipping")
            failed.append({"email": contact["email"], "error": f"Template KeyError: {e}"})
            mark_sent(contact["row"], "failed", "", f"Template KeyError: {e}")
            continue

        msg = build_message(contact["email"], subj, body, sender_name)

        try:
            service.users().messages().send(userId="me", body=msg).execute()
            sent_count += 1
            now = datetime.now(timezone.utc).isoformat()
            mark_sent(contact["row"], "sent", now)
            print(f"  ✅ [{sent_count}/{len(contacts)}] {contact['email']}")

        except Exception as e:
            err = str(e)
            failed.append({"email": contact["email"], "error": err})
            mark_sent(contact["row"], "failed", "", err)
            print(f"  ❌ [{i}/{len(contacts)}] {contact['email']}: {err}")

        time.sleep(RATE_DELAY)
        if sent_count > 0 and sent_count % BATCH_SIZE == 0:
            print(f"⏸️  Batch pause ({BATCH_PAUSE}s) after {sent_count} emails...")
            time.sleep(BATCH_PAUSE)

    # Summary
    print(f"\n{'─' * 60}")
    print(f"✅ Done — {sent_count} sent, {len(failed)} failed")
    if failed:
        print("\nFailed:")
        for f in failed:
            print(f"  - {f['email']}: {f['error']}")


if __name__ == "__main__":
    main()
