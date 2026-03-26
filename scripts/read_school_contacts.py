"""
read_school_contacts.py
Reads the School Contacts sheet and returns rows ready to send.

Default: returns rows where Sending Status = "To send" (case-insensitive)
--all:   returns every row that has a non-empty email

Usage:
  python3 scripts/read_school_contacts.py          # rows marked "To send"
  python3 scripts/read_school_contacts.py --all    # all rows with an email

Output (stdout): JSON array
  [{"row": 2, "school_name": "...", "email": "...", "city": "...", "state": "...",
    "school_type": "...", "sending_status": "To send", "email_sent": false}, ...]

Sheet columns:
  A School Name | B School Type | C City | D State | E Email | F Phone |
  G Website | H Source URL | I Discovered At | J Email Sent | K Sent At |
  L Sending Status | M Notes
"""

import json
import os
import pickle
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ── Config ─────────────────────────────────────────────────────────────────────
TOKEN_FILE = Path(__file__).parent.parent / "oauth_token.pickle"

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

SHEET_ID = os.environ.get("SCHOOL_OUTREACH_SHEET_ID", "")
if not SHEET_ID:
    print("ERROR: SCHOOL_OUTREACH_SHEET_ID is not set. Copy school_outreach_config.env.example "
          "to school_outreach_config.env and fill in your Sheet ID.", file=sys.stderr)
    sys.exit(1)

# Column indices (0-based)
COL_SCHOOL_NAME    = 0   # A
COL_SCHOOL_TYPE    = 1   # B
COL_CITY           = 2   # C
COL_STATE          = 3   # D
COL_EMAIL          = 4   # E
COL_PHONE          = 5   # F
COL_WEBSITE        = 6   # G
COL_SOURCE_URL     = 7   # H
COL_DISCOVERED     = 8   # I
COL_EMAIL_SENT     = 9   # J
COL_SENT_AT        = 10  # K
COL_SENDING_STATUS = 11  # L  ← "To send" triggers Phase 3
COL_NOTES          = 12  # M


def load_creds():
    if not TOKEN_FILE.exists():
        print(f"ERROR: oauth_token.pickle not found at {TOKEN_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(TOKEN_FILE, "rb") as f:
        creds = pickle.load(f)
    if creds.expired and creds.refresh_token:
        print("Refreshing OAuth token ...", file=sys.stderr)
        creds.refresh(Request())
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
    return creds


def get_cell(row, idx, default=""):
    return row[idx].strip() if len(row) > idx else default


def main():
    return_all = "--all" in sys.argv

    creds = load_creds()
    svc   = build("sheets", "v4", credentials=creds)

    result = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range="A:M"
    ).execute()
    rows = result.get("values", [])

    contacts = []
    for i, row in enumerate(rows[1:], start=2):   # row 1 is header
        email          = get_cell(row, COL_EMAIL)
        sending_status = get_cell(row, COL_SENDING_STATUS).strip().lower()
        email_sent     = get_cell(row, COL_EMAIL_SENT).upper()

        if not email:
            continue

        if not return_all and sending_status != "to send":
            continue

        contacts.append({
            "row":            i,
            "school_name":    get_cell(row, COL_SCHOOL_NAME),
            "school_type":    get_cell(row, COL_SCHOOL_TYPE),
            "city":           get_cell(row, COL_CITY),
            "state":          get_cell(row, COL_STATE),
            "email":          email,
            "phone":          get_cell(row, COL_PHONE),
            "website":        get_cell(row, COL_WEBSITE),
            "source_url":     get_cell(row, COL_SOURCE_URL),
            "discovered":     get_cell(row, COL_DISCOVERED),
            "email_sent":     email_sent == "TRUE",
            "sent_at":        get_cell(row, COL_SENT_AT),
            "sending_status": get_cell(row, COL_SENDING_STATUS),
            "notes":          get_cell(row, COL_NOTES),
        })

    print(json.dumps(contacts, indent=2))


if __name__ == "__main__":
    main()
