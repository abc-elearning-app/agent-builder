# School Email Outreach — Manual

Discover contact emails for US secondary schools, high schools, and education centers, then send personalized bulk emails via Gmail.

---

## How It Works

| Phase | Script | What it does |
|-------|--------|-------------|
| 1 — Discover | `bash run-discover.sh` | Searches the web for school websites, scrapes contact pages for real emails, writes verified contacts to your Google Sheet |
| 2 — Send | `bash run-send.sh` | Reads rows you marked "To send" in the sheet and sends your email template via Gmail |

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
Your Title, Your Company
https://yourwebsite.org

---

Your Company Name
Your Street Address, City, State ZIP

If you'd prefer not to receive future emails, simply ignore this message and you will not be contacted again.
```

- No blank lines between `SUBJECT:`, `SENDER_NAME:`, and the first `---`
- Second `---` (optional) separates the email body from the footer; the footer (address + unsubscribe) is included in the sent email
- Variables are substituted automatically per recipient when the email is sent

---

## Phase 1 — Discover Contacts

### Run

```bash
cd ~/school-outreach
bash run-discover.sh
```

This launches the AI agent in fully autonomous mode. No prompts or approvals — it runs start to finish and writes results directly to your Google Sheet.

### What happens

1. Agent searches the web for real school website URLs across all US states
2. Python script visits each school's contact pages (`/contact`, `/about/contact`, `/staff`, `/administration`, etc.)
3. Extracts emails matching `.edu`, `.org`, `.us`, `.gov`, `k12.*.us` domains using regex
4. Filters out noreply, webmaster, and privacy addresses
5. Skips any email already in the sheet (deduplication — safe to run daily)
6. Writes up to 100 new verified contacts to your Google Sheet

### Default parameters (no input needed)

| Parameter | Default |
|-----------|---------|
| Target states | All US states |
| School types | All (high school, secondary, education centers) |
| Max contacts per run | 100 |
| Dry run | No |

### Sheet columns

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
| J | Email Sent (TRUE / FALSE) |
| K | Sent At |
| L | **Sending Status** ← you fill this |
| M | Notes |

---

## Phase 2 — Send Emails

### Step 1: Mark rows in the sheet

Open your Google Sheet. For each row you want to email, type **`To send`** in column L (Sending Status). Leave column L blank for rows you want to skip.

### Step 2: Run the send script

**Send to all rows marked "To send":**
```bash
cd ~/school-outreach
bash run-send.sh
```

**Send to only the first N rows marked "To send":**
```bash
bash run-send.sh --limit 10    # process 10 rows
bash run-send.sh --limit 50    # process 50 rows
```

Use `--limit` when you want to pace your outreach across multiple sessions (e.g. 50 emails/day).

### What happens automatically

- Loads only rows where column L = `"To send"`
- Skips any row where column J = `TRUE` (already sent — safety guard against re-sending)
- Substitutes `{school_name}`, `{school_type}`, `{city}`, `{state}` into your template per recipient
- Shows a preview of the first rendered email before sending
- Waits 2 seconds between emails
- Pauses 30 seconds every 50 emails (Gmail rate limit protection)
- After each send: sets column J → `TRUE`, sets column K → timestamp, clears column L

---

## Day-to-Day Workflow

```
Day 1:  bash run-discover.sh          → 100 new contacts in sheet
Day 2:  bash run-discover.sh          → more new contacts appended (no duplicates)
        [open sheet, mark rows "To send" in column L]
        bash run-send.sh --limit 50   → send to first 50
Day 3:  bash run-send.sh --limit 50   → send to next 50
        bash run-discover.sh          → discover more
```

Each discovery run appends new rows — previous rows stay intact and are identifiable by their "Discovered At" timestamp. The same email is never written to the sheet twice.

---

## Deduplication

The system prevents duplicates at every layer:

| Layer | Where | What it catches |
|-------|-------|-----------------|
| Within a scrape run | `run_school_discover.py` | Same email from multiple schools in one session |
| Within an incoming batch | `append_school_contacts.py` | Duplicates in the same batch being written |
| Cross-run | `append_school_contacts.py` | Emails already in the sheet from previous runs |
| Send-time | `send_school_emails.py` | Rows already marked `Email Sent = TRUE` |

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `oauth_token.pickle not found` | Delete it and re-run `install-school-outreach.sh` |
| `SCHOOL_OUTREACH_SHEET_ID not set` | Check `school_outreach_config.env` — paste your sheet ID |
| `requests not installed` | Run `pip3 install requests` |
| `Token has been expired or revoked` | Delete `oauth_token.pickle` and re-run installer to re-auth |
| 0 contacts found | Run again — web search results vary per session |
| 0 rows marked "To send" | Open sheet, type "To send" in column L, then re-run |
| Gmail daily limit (500/day) | Stop sending, note the count, resume next session |

---

## Config File

`school_outreach_config.env` (in your install directory):

```
SCHOOL_OUTREACH_SHEET_ID=1AbCxyz...   ← the ID from your Google Sheet URL
GMAIL_USER=you@gmail.com              ← must match your OAuth account
```

The Sheet ID is the long string between `/d/` and `/edit` in your Sheet URL. This file is gitignored — never committed.

---

## Re-authentication

If your OAuth token expires or you need to add Gmail scope:

```bash
cd ~/school-outreach
python3 scripts/reauth_with_gmail.py
```

---

## Files

```
run-discover.sh                  ← Phase 1 entry point (bash run-discover.sh)
run-send.sh                      ← Phase 2 entry point (bash run-send.sh [--limit N])
install-school-outreach.sh       ← one-command installer
SCHOOL-OUTREACH-MANUAL.md        ← this file
agents/
  school-discover.md             ← /school-discover AI agent definition
  school-send.md                 ← /school-send AI agent definition
scripts/
  run_school_discover.py         ← Phase 1 orchestrator
  extract_school_emails.py       ← HTTP scraper — no LLM, regex only
  send_school_emails.py          ← Gmail API sender (supports --limit N)
  append_school_contacts.py      ← writes to Google Sheet, deduplicates
  read_school_contacts.py        ← reads "To send" rows from sheet
  mark_school_sent.py            ← updates sent status per row
  load_email_template.py         ← validates template file format
  reauth_with_gmail.py           ← re-auth OAuth with Gmail scope
email_template.example.txt       ← template format reference
email_template.txt               ← your actual template (edit this, gitignored)
school_outreach_config.env       ← your Sheet ID + Gmail address (gitignored)
oauth_token.pickle               ← OAuth credentials (gitignored)
```
