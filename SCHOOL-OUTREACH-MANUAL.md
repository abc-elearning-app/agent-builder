# School Email Outreach — Manual

Discover contact emails for US secondary schools, high schools, and education centers, then send personalized bulk emails via Gmail.

---

## How It Works

| Phase | Command | What it does |
|-------|---------|-------------|
| 1 | `/school-discover` | Uses web search to find school websites, scrapes contact pages for real emails, writes verified contacts to your Google Sheet |
| 2 | `/school-send` | Reads rows you marked "To send" in the sheet and sends your email template via Gmail |

**No LLM is involved in email extraction** — all contact data comes from real HTTP requests to school websites.

---

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/abc-elearning-app/agent-factory/project/school-email-outreach/install-school-outreach.sh | bash
```

The installer handles everything: cloning the repo, installing Python packages, Google OAuth setup, and config.

---

## First-Time Setup (after install)

### 1. Edit your email template

```bash
nano ~/school-outreach/email_template.txt
```

Template format:
```
SUBJECT: Your subject line with {school_name}

SENDER_NAME: Your Full Name

---

Email body here. Available variables:
  {school_name}   — e.g. "Lincoln High School"
  {school_type}   — e.g. "High School"
  {city}          — e.g. "Austin"
  {state}         — e.g. "TX"

Your Name
Your Company
Your Address (required by CAN-SPAM)

---
To unsubscribe, reply with "unsubscribe" in the subject.
```

### 2. Run the AI agent

Open Gemini CLI or Claude Code from the install directory:

```bash
cd ~/school-outreach
gemini   # or: claude
```

---

## Phase 1 — Discover Contacts

Run `/school-discover` in the AI chat. The agent will ask:

```
🔍 School discovery parameters:
1. Target states (e.g. TX,CA,FL — or "all"):
2. School types: high / secondary / other / all  (default: high)
3. Max contacts to collect (default: 100):
4. Dry run? yes / no  (default: no)
```

**What happens:**
1. Agent uses web search to find 20–50 school websites per state
2. Python script visits each school's contact pages (`/contact`, `/about`, `/staff`, etc.)
3. Extracts emails matching `.edu`, `.org`, `.us`, `.gov`, `k12.*.us` domains
4. Filters out noreply/webmaster/privacy addresses
5. Writes verified contacts to your Google Sheet (appends new rows each run)

**Each row in the sheet:**

| Column | Contents |
|--------|----------|
| A | School Name |
| B | School Type |
| C | City |
| D | State |
| E | Email |
| F | Phone |
| G | Website |
| H | Source URL |
| I | Discovered At |
| J | Email Sent (TRUE/FALSE) |
| K | Sent At |
| L | **Sending Status** ← you fill this |
| M | Notes |

---

## Phase 2 — Send Emails

### Step 1: Mark rows in the sheet

Open your Google Sheet. For each row you want to email, type **`To send`** in column L (Sending Status). Leave blank to skip.

### Step 2: Run `/school-send`

The agent previews the first rendered email and asks for confirmation before sending.

**The script automatically:**
- Sends only rows where column L = "To send"
- Skips rows where Email Sent = TRUE (safety guard against re-sending)
- Waits 2 seconds between emails
- Pauses 30 seconds every 50 emails (Gmail rate limit)
- Updates Email Sent = TRUE, Sent At timestamp, and clears Sending Status after each send

---

## Day-to-Day Usage

Each `/school-discover` run **appends new rows** to the same sheet — previous runs are identifiable by the "Discovered At" timestamp. You can run discovery daily and accumulate contacts over time.

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `oauth_token.pickle not found` | Delete it and re-run `install-school-outreach.sh` |
| `SCHOOL_OUTREACH_SHEET_ID not set` | Check `school_outreach_config.env` — paste your sheet ID |
| `requests not installed` | Run `pip3 install requests` |
| `Token has been expired or revoked` | Delete `oauth_token.pickle` and re-run installer to re-auth |
| 0 contacts found | Try different states or broader school types |
| 0 rows marked "To send" | Open sheet, type "To send" in column L, then run `/school-send` again |
| Gmail daily limit (500/day) | Stop sending, note the count, resume next session |

---

## Config File

`school_outreach_config.env` (in your install directory):

```
SCHOOL_OUTREACH_SHEET_ID=1AbCxyz...   ← from your Sheet URL
GMAIL_USER=you@gmail.com              ← must match your OAuth account
```

Never commit this file — it is gitignored.

---

## Re-authentication

If your OAuth token expires or you need to re-auth:

```bash
cd ~/school-outreach
python3 scripts/reauth_with_gmail.py
```

---

## Files

```
install-school-outreach.sh       ← installer
agents/
  school-discover.md             ← /school-discover agent
  school-send.md                 ← /school-send agent
scripts/
  run_school_discover.py         ← Phase 1 entry point
  extract_school_emails.py       ← HTTP scraper (no LLM)
  send_school_emails.py          ← Gmail API sender
  append_school_contacts.py      ← writes to Google Sheet
  read_school_contacts.py        ← reads "To send" rows
  mark_school_sent.py            ← updates sent status
  load_email_template.py         ← validates template file
  reauth_with_gmail.py           ← re-auth OAuth
email_template.example.txt       ← template format reference
email_template.txt               ← your actual template (edit this)
school_outreach_config.env       ← your Sheet ID + Gmail (gitignored)
oauth_token.pickle               ← OAuth credentials (gitignored)
```
