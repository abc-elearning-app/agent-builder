"""
append_school_contacts.py
Appends a batch of discovered school contacts to the School Contacts sheet.
Creates the header row automatically if the sheet is empty.

Usage:
  python3 scripts/append_school_contacts.py '<json_array>'

  The JSON array must be a list of objects with these keys (all strings):
    school_name, school_type, city, state, email,
    phone, website, source_url, discovered_at

Output (stdout): number of rows appended

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

TOKEN_FILE = Path(__file__).parent.parent / "oauth_token.pickle"

HEADERS = [
    "School Name", "School Type", "City", "State",
    "Email", "Phone", "Website", "Source URL",
    "Discovered At", "Email Sent", "Sent At", "Sending Status", "Notes"
]

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
    print("ERROR: SCHOOL_OUTREACH_SHEET_ID is not set.", file=sys.stderr)
    sys.exit(1)


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


def main():
    if len(sys.argv) < 2:
        print("Usage: append_school_contacts.py '<json_array>'")
        sys.exit(1)

    records = json.loads(sys.argv[1])

    creds = load_creds()
    svc   = build("sheets", "v4", credentials=creds)

    # Check if header row exists
    existing = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range="A1:M1"
    ).execute().get("values", [])

    rows_to_write = []
    if not existing or existing[0][0] != "School Name":
        rows_to_write.append(HEADERS)

    for r in records:
        rows_to_write.append([
            r.get("school_name", ""),
            r.get("school_type", ""),
            r.get("city", ""),
            r.get("state", ""),
            r.get("email", ""),
            r.get("phone", ""),
            r.get("website", ""),
            r.get("source_url", ""),
            r.get("discovered_at", ""),
            "FALSE",        # J — Email Sent
            "",             # K — Sent At
            "",             # L — Sending Status (blank — user fills in "To send")
            r.get("notes", ""),  # M — Notes
        ])

    svc.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range="A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows_to_write}
    ).execute()

    data_rows = len(rows_to_write) - (1 if rows_to_write[0] == HEADERS else 0)
    print(f"✅ Appended {data_rows} contacts to sheet")
    print(f"   https://docs.google.com/spreadsheets/d/{SHEET_ID}")


if __name__ == "__main__":
    main()
