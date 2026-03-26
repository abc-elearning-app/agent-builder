"""
reauth_with_gmail.py
Re-authenticates OAuth and saves a new oauth_token.pickle that includes
the Gmail send scope alongside the existing Sheets / Docs / Drive scopes.

Run this ONCE after adding GMAIL_USER to school_outreach_config.env.
A browser window will open — log in as dangluu1010@gmail.com and approve.

Usage:
  python3 scripts/reauth_with_gmail.py
"""

import pickle
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.send",   # new scope for email sending
]

TOKEN_FILE = Path(__file__).parent.parent / "oauth_token.pickle"

# Find client_secret file
secrets = list(Path(__file__).parent.parent.glob("client_secret*.json"))
if not secrets:
    print("ERROR: No client_secret_*.json file found in the project root.")
    print("       Download it from Google Cloud Console → APIs & Services → Credentials.")
    raise SystemExit(1)

secret_file = str(secrets[0])
print(f"Using credentials file: {secret_file}")
print(f"Scopes: {', '.join(SCOPES)}")
print("\nA browser window will open. Log in as dangluu1010@gmail.com and approve all scopes.\n")

flow  = InstalledAppFlow.from_client_secrets_file(secret_file, SCOPES)
creds = flow.run_local_server(port=0)

with open(TOKEN_FILE, "wb") as f:
    pickle.dump(creds, f)

print(f"\n✅ oauth_token.pickle updated with Gmail send scope.")
print(f"   Saved to: {TOKEN_FILE}")
