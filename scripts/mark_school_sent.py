"""
mark_school_sent.py
Marks a single contact row as sent (or failed) after email dispatch.
Also clears the Sending Status cell so it won't be picked up again.

Usage:
  # Mark as sent
  python3 scripts/mark_school_sent.py <row> sent "<iso_timestamp>"

  # Mark as failed
  python3 scripts/mark_school_sent.py <row> failed "" "<error_reason>"

Arguments:
  row        — sheet row number (integer, e.g. 2)
  status     — "sent" or "failed"
  sent_at    — ISO 8601 timestamp (column K); empty string for failed rows
  reason     — failure reason written to Notes column M; only for failed rows

Sheet columns updated:
  J Email Sent     → TRUE (sent) or FALSE (failed)
  K Sent At        → iso timestamp (sent only)
  L Sending Status → cleared (so row is not re-processed)
  M Notes          → error reason (failed only)
"""

import os
import pickle
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

from google.auth.transport.requests import Request
from googleapiclient.discovery import build

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
    if len(sys.argv) < 4:
        print("Usage: mark_school_sent.py <row> <status> <sent_at> [reason]")
        sys.exit(1)

    row     = int(sys.argv[1])
    status  = sys.argv[2].strip()   # "sent" or "failed"
    sent_at = sys.argv[3].strip()
    reason  = sys.argv[4].strip() if len(sys.argv) > 4 else ""

    email_sent_value = "TRUE" if status == "sent" else "FALSE"

    creds = load_creds()
    svc   = build("sheets", "v4", credentials=creds)

    data = [
        {"range": f"J{row}", "values": [[email_sent_value]]},  # Email Sent
        {"range": f"K{row}", "values": [[sent_at]]},           # Sent At
        {"range": f"L{row}", "values": [[""]]},                # Sending Status — cleared
        {"range": f"M{row}", "values": [[reason]]},            # Notes
    ]

    svc.spreadsheets().values().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"valueInputOption": "RAW", "data": data}
    ).execute()

    print(f"✅ Row {row} marked as {status}")


if __name__ == "__main__":
    main()
