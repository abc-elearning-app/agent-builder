# Pinterest Pin CSV Generator — Complete Setup & Usage Manual

This tool automatically creates Pinterest bulk-upload CSV files from Worksheetzone.org listing pages. You give it a Google Sheet of worksheet URLs, and it fetches every item on each page, writes Pinterest-optimized titles and descriptions using Gemini AI, and uploads ready-to-import CSV files directly to your Google Drive.

---

## Quick Install

Open a terminal and paste the command for your platform:

**Mac / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/abc-elearning-app/agent-factory/project/pinterest-pin-csv-generator/install-pinterest-generator.sh | bash
```

**Windows** — open **Git Bash** or **WSL**, then run the same command above.

> The only part that cannot be automated is creating your Google Cloud credentials. The installer pauses and walks you through it step by step.
>
> **Estimated time: 5–15 minutes.**

---

## Table of Contents

1. [What You Need Before Starting](#1-what-you-need-before-starting)
2. [Step 1 — Run the Installer](#2-step-1--run-the-installer)
3. [Step 2 — Set Up Google Cloud (one-time)](#3-step-2--set-up-google-cloud-one-time)
4. [Step 3 — Install Gemini CLI](#4-step-3--install-gemini-cli)
5. [Step 4 — Prepare Your Google Sheet](#5-step-4--prepare-your-google-sheet)
6. [Step 5 — Create a Google Drive Folder](#6-step-5--create-a-google-drive-folder)
7. [Running the Agent](#7-running-the-agent)
8. [Understanding the Output](#8-understanding-the-output)
9. [Uploading to Pinterest](#9-uploading-to-pinterest)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. What You Need Before Starting

| Requirement | How to check |
|---|---|
| Mac, Linux, or Windows (with Git Bash or WSL) | — |
| Python 3.9 or newer | Terminal → `python3 --version` |
| Git | Terminal → `git --version` |
| Node.js + npm (for Gemini CLI) | Terminal → `node --version` |
| Claude Code | Terminal → `claude --version` |
| A Google account | — |
| A Pinterest Business account | [business.pinterest.com](https://business.pinterest.com) |

> **Windows users:** The installer is a bash script. You need either **Git Bash** (bundled with [Git for Windows](https://git-scm.com/download/win)) or **WSL** (Windows Subsystem for Linux). Both give you a bash terminal where the install command works identically to Mac/Linux.

---

## 2. Step 1 — Run the Installer

Open a terminal and run:

**Mac / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/abc-elearning-app/agent-factory/project/pinterest-pin-csv-generator/install-pinterest-generator.sh | bash
```

**Windows (Git Bash or WSL):**
```bash
curl -fsSL https://raw.githubusercontent.com/abc-elearning-app/agent-factory/project/pinterest-pin-csv-generator/install-pinterest-generator.sh | bash
```

The installer runs 7 steps:

| Step | What it does |
|---|---|
| 1 | Checks Python 3.9+, pip3, git, Gemini CLI, Claude Code — prints hints if anything is missing |
| 2 | Asks where to install (press Enter for the default: `~/pinterest-generator`) |
| 3 | Downloads the tool from GitHub |
| 4 | Installs Python packages (`google-auth`, `google-api-python-client`, etc.) |
| 5 | **Pauses here** — guides you to create Google Cloud credentials (see Step 2 below) |
| 6 | Opens a browser to connect your Google account (Sheets + Drive access) |
| 7 | Asks for your Sheet ID and Drive folder ID — writes your personal config file |

When it finishes, it prints the exact commands to run the agent.

> **Re-running is safe.** It updates the code and skips steps already completed (existing credentials, existing config).

---

## 3. Step 2 — Set Up Google Cloud (one-time)

You need your own Google Cloud project and OAuth credentials. This is free and takes about 10 minutes. The installer pauses and waits for you during this step.

### 3a. Create a Google Cloud project

1. Go to [https://console.cloud.google.com](https://console.cloud.google.com) and sign in.
2. Click the project dropdown at the top → **New Project**.
3. Name it anything (e.g. `pinterest-generator`) → **Create**.
4. Make sure your new project is selected before continuing.

### 3b. Enable the required APIs

You need to enable two APIs. For each one:

1. In the left sidebar, go to **APIs & Services → Library**.
2. Search by name, click the result, click **Enable**.

Enable these two APIs:
- **Google Sheets API**
- **Google Drive API**

### 3c. Configure the OAuth consent screen

1. Go to **APIs & Services → OAuth consent screen**.
2. User Type: **External** → click **Create**.
3. Fill in:
   - **App name**: anything (e.g. `Pinterest Generator`)
   - **User support email**: your email
   - **Developer contact information**: your email
4. Click **Save and Continue** through all remaining screens until done.

### 3d. Create OAuth credentials

1. Go to **APIs & Services → Credentials**.
2. Click **+ Create Credentials → OAuth client ID**.
3. Application type: **Desktop app** → give it any name → **Create**.
4. A dialog appears — click **Download JSON**.
5. Rename the downloaded file to `client_secret.json`.
6. Move it into the install folder (default: `~/pinterest-generator/`).

Return to the terminal and press **Enter** — the installer will continue automatically.

---

## 4. Step 3 — Install Gemini CLI

The agent uses Gemini CLI to browse Worksheetzone pages and generate pin content. You need it installed and logged in.

### Install

Gemini CLI requires Node.js. Install Node.js first if you don't have it: [https://nodejs.org](https://nodejs.org)

Then install Gemini CLI:

```bash
npm install -g @google/gemini-cli
```

Verify it installed:
```bash
gemini --version
```

### Log in

Run Gemini once to complete authentication:
```bash
gemini
```

A browser window opens — sign in with your Google account. Once logged in, type `/quit` or press `Ctrl+C` to exit. You only need to do this once.

> **Free tier:** Gemini CLI uses the Gemini API. The free tier is sufficient for this tool's usage. No billing required.

---

## 5. Step 4 — Prepare Your Google Sheet

You manage all your Pin tasks in a Google Sheet. The agent reads pending rows, processes them, and writes results back.

### Create the sheet

1. Go to [https://sheets.google.com](https://sheets.google.com) and create a new spreadsheet.
2. Name it anything (e.g. `Pinterest Pin Tasks`).
3. Set up **row 1** as headers exactly as shown:

| A | B | C | D | E | F |
|---|---|---|---|---|---|
| Source URL | Status | Pin board | CSV link | Date | Reason |

### Set up the Status dropdown

Column B must use a dropdown with exactly these three values (the agent checks for them):

1. Click the column B header to select the whole column.
2. **Data → Data validation → Add a rule**.
3. Criteria: **Dropdown** → add three items:
   - `to do`
   - `done`
   - `failed`
4. Click **Done**.

### Add your first task

In row 2, enter a Worksheetzone listing page URL in column A and set Status to `to do`:

| A | B |
|---|---|
| `https://worksheetzone.org/coloring-pages/fruit-coloring-pages/watermelon` | `to do` |

> **Listing pages only.** The URL must be a category or listing page that shows multiple worksheets in a grid — not a single worksheet detail page. The agent will tell you if you give it the wrong type.

### Find your Sheet ID

The Sheet ID is in the URL when you open the sheet:
```
https://docs.google.com/spreadsheets/d/← SHEET_ID →/edit
```

Copy everything between `/d/` and `/edit`. You'll paste this into the installer at Step 7.

---

## 6. Step 5 — Create a Google Drive Folder

The agent uploads generated CSV files to a Google Drive folder you own.

1. Go to [https://drive.google.com](https://drive.google.com).
2. Click **+ New → Folder**, name it (e.g. `Pinterest CSVs`).
3. Open the folder — the URL looks like:
   ```
   https://drive.google.com/drive/folders/← FOLDER_ID →
   ```
4. Copy the Folder ID (everything after `/folders/`).

You'll paste this into the installer at Step 7.

---

## 7. Running the Tool

There are two ways to run the tool. Both do exactly the same work.

### Option A — Terminal script (recommended for daily use)

No need to open Claude Code. Run directly from any terminal:

```bash
cd ~/pinterest-generator

# Process all pending tasks
python3 scripts/run_pinterest_batch.py

# Process at most 3 tasks
python3 scripts/run_pinterest_batch.py --limit 3

# Dry run — fetch and generate but skip CSV write, upload, and sheet update
python3 scripts/run_pinterest_batch.py --dry-run

# Clear the entire dedup registry, then process all pending tasks
python3 scripts/run_pinterest_batch.py --reset-registry

# Remove registry entries for one specific listing URL, then process
python3 scripts/run_pinterest_batch.py --reset-url https://worksheetzone.org/coloring-pages/fruit-coloring-pages/orange
```

Sample output:

```
============================================================
Pinterest Pin CSV Generator — Batch Runner
============================================================
Reading sheet...
📋 Found 2 pending task(s):
   Row 2 │ https://worksheetzone.org/.../watermelon  → Board: 'Watermelon'
   Row 3 │ https://worksheetzone.org/.../banana      → Board: 'Banana'

🔍 Dedup registry: 0 URLs already seen

── Task 1/2  Row 2 │ https://worksheetzone.org/.../watermelon
  [1/3] Fetching items from listing page...
  [1/3] ✅ 14 item(s) found, 14 with thumbnails
  [2/3] 🔍 14/14 unique
  [3/3] Generating Pinterest metadata via Gemini...
  [3/3] ✅ Metadata ready for 14 item(s)
  [✓] 14/14 rows passed validation

📤 Uploading pinterest_pins_2026-03-11_part1.csv (14 pins)...
   ✅ https://drive.google.com/file/d/.../view
✅ Row 2 → done  (board: 'Watermelon', 14 pins)
============================================================
```

> **How item and thumbnail fetching works:** The tool fetches the listing page once and extracts all worksheet items — including titles, grade levels, and thumbnail URLs — directly from the page's embedded JSON (`__NEXT_DATA__`). No child page visits are needed. Only Gemini (for metadata generation) requires an LLM call.

### Option B — Claude Code agent (interactive, with review step)

Use this when you want to review the generated metadata before writing the CSV, or when you want to adjust the content interactively.

```bash
cd ~/pinterest-generator
claude
```

In Claude Code, type:

```
@pinterest-pin-csv-generator
```

Or press `@` and type `pinterest` to find it in the agent picker. The agent pauses after Step 3 to show you a preview and ask for approval before writing the CSV.

### Board names

The agent auto-derives the Pinterest board name from the last path segment of the URL:

| Source URL | Board |
|---|---|
| `.../fruit-coloring-pages/watermelon` | `Watermelon` |
| `.../math-worksheets/fractions` | `Fractions` |
| `.../animals/dogs` | `Dogs` |

To override, put the board name in column C of the sheet before running.

---

## 8. Understanding the Output

### Google Sheet — after processing

| Column | What it shows |
|---|---|
| **Status** (B) | `done` — CSV uploaded successfully<br>`failed` — something went wrong |
| **Pin board** (C) | The Pinterest board name that was used |
| **CSV link** (D) | Google Drive link to the generated CSV file |
| **Date** (E) | Date the row was processed (YYYY-MM-DD) |
| **Reason** (F) | If `failed`, explains what went wrong |

### The CSV file

Each CSV file contains up to 200 rows. If a listing page has more items than that, the agent automatically creates numbered files (`_part1.csv`, `_part2.csv`).

The CSV columns match Pinterest's bulk upload format exactly:

| Column | Content |
|---|---|
| `Title` | Pinterest-optimized title (30–60 chars, keyword-first) |
| `Media URL` | Direct link to the worksheet thumbnail image |
| `Pinterest board` | Board name (auto-derived or your override) |
| `Thumbnail` | Empty (image pins — no video thumbnail needed) |
| `Description` | 200–232 char description with CTA and hashtags |
| `Link` | Worksheetzone page URL |
| `Publish date` | Empty (publish immediately) or scheduled date |
| `Keywords` | Comma-separated search keywords: topic words derived from the description hashtags (lowercase), followed by grade range codes. Grade levels are normalized to short codes (`Pre`, `KG`, `1st`–`6th`); when a worksheet spans multiple grades only the lowest and highest appear (e.g. `watermelon,coloringpages,preschool,Pre,5th`) |

### Deduplication

The agent keeps a local registry (`pinterest_pins_seen_urls.json`) of every worksheet it has already processed. If you run the same listing URL again, items that were already pinned are automatically skipped. This prevents duplicate pins across multiple sessions.

When all items on a listing page are already in the registry, the row is marked **done** in the sheet automatically (not left as "To Do" indefinitely).

To reset the registry:

| Command | Effect |
|---|---|
| `--reset-registry` | Clears the entire registry (all sources) |
| `--reset-url URL` | Removes only the entries from that specific listing URL |

Use `--reset-url` when you want to re-pin items from one category without affecting other categories. Use `--reset-registry` for a full fresh start.

---

## 9. Uploading to Pinterest

After the agent finishes:

1. Open your Google Sheet — column D has the Drive link for each CSV.
2. Click the Drive link → download the CSV file.
3. Go to [Pinterest Business](https://business.pinterest.com) → **Create → Create multiple Pins**.
4. Upload the CSV file.
5. Pinterest shows a preview of all pins — review and click **Publish**.

> **200-pin limit:** Pinterest allows a maximum of 200 pins per bulk upload. The agent enforces this automatically — larger batches are split into multiple files.

> **Pinterest review time:** After uploading, Pinterest may take a few minutes to process images. If a pin shows a broken image, reset the sheet row to `to do` and re-run to regenerate the CSV with fresh thumbnail URLs.

---

## 10. Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `PINTEREST_SHEET_ID is not set` | `pinterest_config.env` is missing or has placeholder value | Run the installer again, or edit `pinterest_config.env` manually |
| `oauth_token.pickle not found` | Authentication not completed | Re-run the installer |
| `Token expired` | Refresh token revoked (rare) | Delete `oauth_token.pickle` and re-run the installer |
| `No client_secret*.json found` | Credentials file missing or misnamed | Re-download from Google Cloud Console, rename to `client_secret.json`, move to install folder |
| `403 The caller does not have permission` | Sheet or Drive folder not accessible | Make sure your Google account owns the sheet and Drive folder you configured |
| `Gemini error` / `gemini: command not found` | Gemini CLI not installed or not in PATH | Run: `npm install -g @google/gemini-cli`, then `gemini` to log in |
| `Gemini timed out` | Metadata generation took too long (large batch) | Re-run — the sheet row will be retried |
| `No __NEXT_DATA__ found` | URL is not a Worksheetzone listing page | Use a category/listing URL (shows a grid of worksheets, not a single worksheet) |
| `No worksheets found` | Listing page returned 0 items | Check that the URL is a category page with worksheets visible |
| `All items were already pinned` | Every item on that page was processed before | Add new listing page URLs, or use `--reset-url URL` to reprocess one page |
| `Sheet connection failed` | Sheet ID is wrong or sheet not shared | Double-check the Sheet ID in `pinterest_config.env`; make sure the sheet is owned by the authenticated Google account |
| CSV uploads to wrong Drive folder | Wrong `PINTEREST_DRIVE_FOLDER_ID` | Edit `pinterest_config.env` and correct the folder ID |

### Re-run the installer to fix any setup issue

```bash
bash ~/pinterest-generator/install-pinterest-generator.sh
```

The installer skips steps already completed — it only re-runs what needs fixing.

### Edit your config manually

If you need to change your Sheet ID or Drive folder ID without re-running the full installer:

```bash
nano ~/pinterest-generator/pinterest_config.env
```

The file looks like this:
```
PINTEREST_SHEET_ID=your_sheet_id
PINTEREST_DRIVE_FOLDER_ID=your_folder_id
PINTEREST_SCRIPTS_DIR=/home/you/pinterest-generator/scripts
```

Save the file and run the agent again — no restart needed.

### Token auto-refresh

The OAuth token refreshes automatically in the background every time the agent runs. You never need to re-authenticate unless:
- `oauth_token.pickle` was deleted
- You revoked app access in your Google account settings ([myaccount.google.com/permissions](https://myaccount.google.com/permissions))

---

## Quick Reference

```bash
# ── Install (run once) ────────────────────────────────────────────────────────
curl -fsSL https://raw.githubusercontent.com/abc-elearning-app/agent-factory/project/pinterest-pin-csv-generator/install-pinterest-generator.sh | bash

# ── Daily use — terminal script (no Claude Code needed) ───────────────────────
cd ~/pinterest-generator
python3 scripts/run_pinterest_batch.py                         # process all pending tasks
python3 scripts/run_pinterest_batch.py --limit 3               # process at most 3 tasks
python3 scripts/run_pinterest_batch.py --dry-run               # test without writing anything
python3 scripts/run_pinterest_batch.py --reset-registry        # clear all dedup history, then run
python3 scripts/run_pinterest_batch.py --reset-url <URL>       # clear history for one URL, then run

# ── Daily use — Claude Code agent (interactive) ───────────────────────────────
cd ~/pinterest-generator
claude                          # open Claude Code
# then in Claude Code:
@pinterest-pin-csv-generator    # start the agent

# ── Update to the latest version ──────────────────────────────────────────────
bash ~/pinterest-generator/install-pinterest-generator.sh

# ── Edit config ───────────────────────────────────────────────────────────────
nano ~/pinterest-generator/pinterest_config.env
```

---

*Questions or issues? Refer to `agents/pinterest-pin-csv-generator.md` in the repository for the full technical reference.*
