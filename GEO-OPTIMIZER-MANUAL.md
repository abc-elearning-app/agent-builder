# GEO Blog Post Optimizer — Complete Setup & Usage Manual

This tool automatically optimizes blog posts for AI search visibility (Google AI Overviews, ChatGPT, Perplexity) and generates schema markup. It reads a Google Sheet, rewrites each post using Gemini or Claude, creates formatted Google Docs, and writes the results back to the sheet.

Two independent pipelines share the same sheet and scripts folder:

| Pipeline | Trigger column | What it does |
|----------|---------------|-------------|
| **GEO Optimizer** | `Status = "optimize"` | Rewrites post content, creates Optimized Doc |
| **Schema Generator** | `Schema Status = "Generate Schema"` | Scans live post, generates missing JSON-LD, creates Schema Doc |

---

## Quick Install (Mac / Linux)

Open Terminal and run this single command:

```bash
curl -fsSL https://raw.githubusercontent.com/abc-elearning-app/agent-factory/project/geo-blog-post-optimizer/install-geo-optimizer.sh | bash
```

The installer guides you through every step interactively — checking prerequisites, downloading the tool, installing dependencies, connecting to Google, and building the link cache. **Estimated time: 5–15 minutes.**

> The only part that cannot be automated is creating your Google Cloud credentials (Step 2 below). The installer will pause and walk you through it when the time comes.

---

## Table of Contents

1. [What You Need Before Starting](#1-what-you-need-before-starting)
2. [Step 1 — Run the Installer](#2-step-1--run-the-installer)
3. [Step 2 — Set Up Google Cloud (one-time)](#3-step-2--set-up-google-cloud-one-time)
4. [Step 3 — Set Up Your AI Writer](#4-step-3--set-up-your-ai-writer)
5. [Step 4 — Get Access to the Google Sheet](#5-step-4--get-access-to-the-google-sheet)
6. [Running the GEO Optimizer](#6-running-the-geo-optimizer)
7. [Running the Schema Generator](#7-running-the-schema-generator)
8. [Understanding the Results](#8-understanding-the-results)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. What You Need Before Starting

Make sure you have all of the following before starting:

| Requirement | How to check |
|-------------|-------------|
| A Mac or Linux computer | — |
| Python 3.9 or newer | Open Terminal, type `python3 --version` |
| Git | Open Terminal, type `git --version` |
| A Google account | — |
| Access to the team Google Sheet | Ask the team lead to share it with you |
| Either Gemini CLI **or** Claude CLI installed | See Step 3 |

> **Windows users:** These instructions assume Mac/Linux. On Windows, use [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) (Windows Subsystem for Linux) and follow the same steps inside a WSL terminal.

---

## 2. Step 1 — Run the Installer

Open **Terminal** and paste this command:

```bash
curl -fsSL https://raw.githubusercontent.com/abc-elearning-app/agent-factory/project/geo-blog-post-optimizer/install-geo-optimizer.sh | bash
```

The installer runs 7 steps automatically:

| Step | What it does |
|------|-------------|
| 1 | Checks Python 3.9+, Git, pip3 — prints install hints if anything is missing |
| 2 | Asks where to install (press Enter to use the default: `~/geo-optimizer`) |
| 3 | Downloads the tool from GitHub |
| 4 | Installs all Python packages |
| 5 | **Pauses here** — guides you to create Google Cloud credentials (see Step 2 below) |
| 6 | Opens a browser to connect your Google account |
| 7 | Builds the internal link cache (~33,000 URLs) |

When it finishes, it prints exactly which commands to run next.

> **Re-running the installer is safe.** It updates the code and skips steps already completed (existing credentials, existing cache).

---

## 3. Step 2 — Set Up Google Cloud (one-time)

This is the most involved step. You need to create your own Google Cloud project and OAuth credentials. This is free and takes about 10 minutes.

**The installer will pause and wait for you at this step.** Follow the instructions below, then return to the Terminal and press Enter.

### 3a. Create a Google Cloud Project

1. Go to [https://console.cloud.google.com](https://console.cloud.google.com) and sign in with your Google account.
2. At the top of the page, click the project dropdown (it may say "Select a project").
3. Click **New Project**.
4. Give it any name (e.g. `geo-optimizer`) and click **Create**.
5. Make sure your new project is selected in the dropdown before continuing.

### 3b. Enable Required APIs

You need to enable three APIs. For each one:

1. In the left sidebar, go to **APIs & Services → Library**.
2. Search for the API name, click it, then click **Enable**.

Enable these three APIs:
- **Google Sheets API**
- **Google Docs API**
- **Google Drive API**

### 3c. Create OAuth Credentials

1. In the left sidebar, go to **APIs & Services → Credentials**.
2. Click **+ Create Credentials** → **OAuth client ID**.
3. If prompted to configure the OAuth consent screen first:
   - Click **Configure Consent Screen**
   - Choose **External** → click **Create**
   - Fill in **App name** (any name, e.g. "GEO Optimizer"), **User support email** (your email), **Developer contact** (your email)
   - Click **Save and Continue** through all steps until done
   - Go back to **Credentials → + Create Credentials → OAuth client ID**
4. For **Application type**, choose **Desktop app**.
5. Give it any name and click **Create**.
6. A dialog will appear — click **Download JSON**.
7. Rename the downloaded file to `client_secret.json`.
8. Move it into the install folder (default: `~/geo-optimizer/`).

Once the file is in place, return to the Terminal and press **Enter** — the installer will continue automatically.

---

## 4. Step 3 — Set Up Your AI Writer

The tool supports two AI writers: **Gemini** (free, uses your Google account) and **Claude** (requires Anthropic subscription). You only need one.

### Option A: Gemini CLI (recommended — free)

1. Install Gemini CLI: [https://github.com/google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli)
2. Run `gemini --version` in Terminal to confirm it works.
3. Run `gemini` once and sign in with your Google account when prompted.

### Option B: Claude CLI

1. Install Claude Code: [https://claude.ai/code](https://claude.ai/code)
2. Sign in with your Anthropic account.
3. Run `claude --version` in Terminal to confirm it works.

> **Which writer to use?** Check the **Writer** column in the Google Sheet — it will say either `Gemini` or `Claude`. Set up whichever is assigned to your rows.

---

## 5. Step 4 — Get Access to the Google Sheet

Ask the team lead to:
- Share the **Google Sheet** with your Google account (Editor access)
- Share the **"GEO Optimized Posts"** Google Drive folder with your account

Use the same Google account you authenticated with in the installer.

---

## 6. Running the GEO Optimizer

Once setup is complete, go to your install folder and run:

```bash
cd ~/geo-optimizer
```

### Basic usage

```bash
# Process the next 10 rows (default)
python3 scripts/run_batch.py
```

### Process a specific number of rows

```bash
python3 scripts/run_batch.py --limit 50
```

### Process a specific range of rows

```bash
# Only process rows 72 to 150 in the sheet
python3 scripts/run_batch.py --start-row 72 --end-row 150
```

### Test run without writing anything

```bash
# Optimizes posts but does NOT create Docs or update the sheet
python3 scripts/run_batch.py --limit 3 --dry-run
```

> **Recommended pace:** Process 50–80 rows per week to avoid triggering Google's spam filters.

---

## 7. Running the Schema Generator

The schema generator is a **separate pipeline** that runs independently from the GEO optimizer. It reads rows where **Schema Status (column H) = "Generate Schema"**, inspects each live blog post for existing JSON-LD schema already injected by WordPress, and generates only the missing entities.

### What it generates

| Schema entity | When added |
|---------------|-----------|
| `BreadcrumbList` | Always (if not already present) |
| `FAQPage` | Only if the post has a FAQ section |
| `ItemList` | Only if the post is a listicle (e.g. "45 Activities for Kids") |

Base entities (`Organization`, `WebSite`, `WebPage`, `Person`, `BlogPosting`) are already handled by WordPress — the tool never duplicates them.

### How to trigger it

In the Google Sheet, set column H (**Schema Status**) to `Generate Schema` for any row you want processed. Then run:

```bash
cd ~/geo-optimizer

# Process the next 10 rows with Schema Status = "Generate Schema"
bash scripts/run_schema_batch.sh

# Process a specific number of rows
bash scripts/run_schema_batch.sh --limit 5

# Process a specific row range
bash scripts/run_schema_batch.sh --start-row 2 --end-row 20

# Test run — generates docs but does NOT update the sheet
bash scripts/run_schema_batch.sh --dry-run
```

### What you'll see while it runs

```
============================================================
Schema Generator
  Limit     : 10 rows
============================================================
Reading sheet for schema rows ...
Found 4 rows with Schema Status='Generate Schema'
Processing 1 rows this run

── Row 2  [1/1]  https://worksheetzone.org/blog/enrichment-activities-for-kids
  [1/2] Generating schema for https://worksheetzone.org/blog/enrichment-activities-for-kids
    [schema] Found: BlogPosting, ImageObject, Organization, Person, WebPage, WebSite
    [schema] Article type : listicle
    [schema] FAQ pairs    : 4
    [schema] Listicle items: 10
    [schema] Missing types: BreadcrumbList, FAQPage, ItemList
    [schema] Doc: https://docs.google.com/document/d/...
  [2/2] ✅ Sheet updated

============================================================
Schema batch complete
  ✅ Succeeded : 1
  ❌ Failed    : 0
```

### What the schema doc contains

Each schema Google Doc is an audit report with three sections:

```
Schema Markup Audit
URL: https://worksheetzone.org/blog/...
Date: 2026-03-18
Article type: listicle

━━━ Already Present in WordPress ━━━
  ✅ BlogPosting
  ✅ Organization
  ✅ Person
  ✅ WebPage
  ✅ WebSite

━━━ Missing — Added Below ━━━
  ➕ BreadcrumbList
  ➕ FAQPage (4 Q&A pairs)
  ➕ ItemList

━━━ Paste This Into Your WordPress Page ━━━

<script type="application/ld+json">
{ ... }
</script>
```

Copy the `<script>` block and paste it into the WordPress page's custom HTML or theme header for that post.

> **The two pipelines are independent.** A row can have `Status = "optimize"` and `Schema Status = "Generate Schema"` at the same time. Run them in any order.

### What you'll see while it runs

```
============================================================
GEO Batch Optimizer
  Limit     : 10 rows
============================================================
Reading sheet ...
Found 528 rows with status='optimize'
Processing 10 rows this run

── Row 71  [1/10]  https://worksheetzone.org/blog/adjectives-that-start-with-n
  [1/4] Fetching https://worksheetzone.org/blog/adjectives-that-start-with-n
  [1/4] ✅ 8,432 chars — "Adjectives That Start With N"
  [2/4] Optimizing via Gemini ...
  [2/4] ✅ Optimized (11,204 chars)
  [3/4] Creating Google Doc ...
  [3/4] ✅ https://docs.google.com/document/d/...
  [4/4] Updating sheet row 71 ...
  [4/4] ✅ Sheet updated
  ⏳ Waiting 5s before next row ...
```

---

## 8. Understanding the Results

After the tool runs, open the Google Sheet. Each processed row will be updated:

### GEO Optimizer columns (A–G)

| Column | What it shows |
|--------|--------------|
| **B — Status** | `Done ✅` if successful, `Failed ❌` if something went wrong |
| **D — Optimized Doc** | Link to the Google Doc with the optimized post |
| **E — Fail Reason** | If status is `Failed ❌`, this explains what went wrong |
| **F — Processed Date** | The date the row was processed |

### Schema Generator columns (H–I)

| Column | What it shows |
|--------|--------------|
| **H — Schema Status** | Set to `Generate Schema` to trigger; updated to `Done ✅` or `Failed ❌` after processing |
| **I — Schema file** | Link to the Google Doc with the schema audit and `<script>` block to paste into WordPress |

### What the optimized post contains

Each optimized post is a ready-to-copy Google Doc with:
- Original title preserved exactly
- Rewritten opening paragraph (sapo) — 40–60 words
- All headings improved to be specific and descriptive
- Definitions for key terms
- Bullet/numbered lists where appropriate
- A comparison table (if the post covers multiple categories)
- Exactly 4 FAQ pairs at the end
- 3–4 verified internal links to worksheetzone.org pages
- Proper heading styles (H1/H2/H3) and table borders — ready to paste into WordPress

---

## 9. Troubleshooting

| Error message | Cause | Fix |
|---------------|-------|-----|
| `oauth_token.pickle not found` | Authentication not completed | Re-run the installer |
| `Token expired` | Refresh token revoked (rare) | Re-run the installer to re-authenticate |
| `No client_secret*.json found` | Credentials file missing or misnamed | Re-download from Google Cloud Console, rename to `client_secret.json`, place in install folder |
| `Gemini error` | Gemini CLI not logged in | Run `gemini` in Terminal and sign in |
| `Claude error` | Claude CLI not authenticated | Run `claude` in Terminal and sign in |
| `Fetch failed` | Blog post URL blocked or offline | Row is skipped automatically; check the URL manually |
| `wzorg_link_cache.json not found` | Cache not built | Run: `python3 scripts/build_sitemap_cache.py` |
| `Doc creator failed` | Docs/Drive API issue | Check [Google Cloud Console](https://console.cloud.google.com) — all three APIs must be enabled |
| `403 The caller does not have permission` | Drive folder not shared with your account | Ask team lead to share "GEO Optimized Posts" folder with your Google account |
| `Schema generator failed` | Error in `create_schema_doc.py` | Run `python3 scripts/create_schema_doc.py --url <url> --title "<title>" --folder-id <id>` directly for the full traceback |
| `wzorg_schema_config.json not found` | Static schema config missing | File must exist at `scripts/wzorg_schema_config.json` — re-clone the repo or restore from git |

### Auto-refresh (no action needed)

Both the OAuth token and the link cache are refreshed automatically every time you run `python3 scripts/run_batch.py`:

| What | How it works |
|------|-------------|
| **OAuth token** | If expired, refreshed silently using the stored refresh token — no browser, no action needed |
| **Link cache** | If older than 7 days, rebuilt automatically before the first row is processed (~60s) |

The only time manual action is needed is if the `oauth_token.pickle` file is missing entirely (first install) or if the refresh token was revoked by Google (very rare — happens if you revoke app access in your Google account settings). In either case, re-run the installer:

```bash
curl -fsSL https://raw.githubusercontent.com/abc-elearning-app/agent-factory/project/geo-blog-post-optimizer/install-geo-optimizer.sh | bash
```

---

## Quick Reference

```bash
# --- Install (run once) ---
curl -fsSL https://raw.githubusercontent.com/abc-elearning-app/agent-factory/project/geo-blog-post-optimizer/install-geo-optimizer.sh | bash

# --- GEO Optimizer (from ~/geo-optimizer) ---
# Trigger: Status column = "optimize"
python3 scripts/run_batch.py               # process next 10 rows
python3 scripts/run_batch.py --limit 50    # process 50 rows
python3 scripts/run_batch.py --dry-run     # test without writing

# --- Schema Generator (from ~/geo-optimizer) ---
# Trigger: Schema Status column = "Generate Schema"
bash scripts/run_schema_batch.sh           # process next 10 rows
bash scripts/run_schema_batch.sh --limit 5
bash scripts/run_schema_batch.sh --dry-run # test without writing
```

---

*Questions? Contact the team lead or refer to `agents/geo-blog-post-optimizer.md` and `agents/geo-schema-generator.md` in the repository for the full technical reference.*
