# GEO Blog Post Optimizer — Team Manual

Optimize Worksheetzone blog posts for AI-powered search (Google AI Overviews, ChatGPT, Perplexity) using a Claude or Gemini AI agent. You manage everything from a Google Sheet — paste URLs, set a status, and the agent does the rest.

---

## What the Agent Does

- Reads blog post URLs from your Google Sheet
- Applies surgical GEO edits (rewrites only the sapo and opening sentences — not the whole post)
- Adds/rewrites headings only when needed, embeds hyperlinked citations, adds a FAQ
- Saves each optimized post as a Google Doc in a shared Drive folder
- Writes results (Doc link, status, date) back to the sheet automatically

---

## One-Time Setup (per machine)

Do this once. Takes about 10–15 minutes.

### Step 1 — Install the Google Cloud CLI

Open **Terminal** and run:

```bash
brew install --cask google-cloud-sdk
```

Close and reopen Terminal when it finishes.

### Step 2 — Connect your Google account

Run this single command (copy and paste it exactly):

```bash
mkdir -p ~/.config/geo-optimizer && \
gcloud auth application-default login \
  --client-id-file=/Users/YOUR_USERNAME/Desktop/client_secret.json \
  --scopes="https://www.googleapis.com/auth/drive.file,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/cloud-platform"
```

Replace `YOUR_USERNAME` with your Mac username (e.g. `/Users/janedoe/Desktop/client_secret.json`).

> **Need the `client_secret.json` file?** Ask your team lead — it is the OAuth credential file downloaded from Google Cloud Console. Each team member uses the same file.

A browser window will open. Sign in with your Google work account and click **Allow**.

### Step 3 — Save your Gemini API key

Run (paste your actual key):

```bash
echo 'YOUR_GEMINI_API_KEY_HERE' > ~/.config/geo-optimizer/gemini_api_key
```

> **Need the Gemini API key?** Ask your team lead. One key can be shared across the team.

### Step 4 — Install the agent into Claude Code

```bash
cp geo-blog-post-optimizer.md ~/.claude/agents/geo-blog-post-optimizer.md
```

That's it. The agent is ready.

---

## Google Sheet Setup

The agent works with a shared Google Sheet. **Your team lead will share the sheet with you** — you do not need to create it.

The sheet has these columns:

| Column | Name | Your role |
|--------|------|-----------|
| A | URL | Paste the blog post URL here |
| B | Status | Set to `Optimize` to trigger the agent |
| C | Writer | Choose from dropdown: `Claude` or `Gemini` |
| D | Optimized Doc | Agent fills this in (Google Doc link) |
| E | Fail Reason | Agent fills this in if something goes wrong |
| F | Processed Date | Agent fills this in automatically |
| G | Post Title | Agent fills this in automatically |

---

## Daily Workflow

### 1. Add a post to the queue

Open the Google Sheet. In a new row:
- **Column A** — paste the blog post URL (e.g. `https://worksheetzone.org/blog/my-post`)
- **Column B** — type `Optimize`
- **Column C** — select `Claude` or `Gemini` from the dropdown

You can add as many rows as you like at once.

### 2. Run the agent

In Claude Code, type:

```
/geo-blog-post-optimizer
```

Then paste the Google Sheet URL when asked, or simply paste it directly into the chat:

```
https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
```

### 3. Watch the progress

The agent will:
1. Find all rows where Status = `Optimize`
2. Change Status to `In Progress ⏳` as it starts each row
3. Fetch and optimize the post
4. Save a Google Doc to the shared **GEO Optimized Posts** folder in Drive
5. Update Status to `Done ✅` and fill in the Doc link and date

### 4. Review before publishing

Open the Google Doc link in column D. Before copying into WordPress:

- Check any `[VERIFY: suggested source]` tags — these are claims the agent could not source automatically. Verify them and replace with the correct source, or remove the tag if the claim is not needed.
- Review any fact-check notes the agent mentions in its summary.

---

## Status Reference

| Status | Set by | Meaning |
|--------|--------|---------|
| `Optimize` | You | Queued for processing |
| `In Progress ⏳` | Agent | Currently being optimized |
| `Done ✅` | Agent | Complete — check column D for the Doc link |
| `Failed ❌` | Agent | Something went wrong — see column E for the reason |

**To retry a failed row:** change column B back to `Optimize` and run the agent again.

---

## Writer Reference

| Option | Model used | Best for |
|--------|-----------|---------|
| `Claude` | Claude Sonnet (Anthropic) | Default — strong reasoning and citation quality |
| `Gemini` | Gemini 2.0 Flash (Google) | Speed, or when you want a second opinion |

Both writers follow the same GEO rules and produce output in the same format. Results are saved to the same Drive folder regardless of which writer is used.

---

## What the Agent Edits (and What It Leaves Alone)

The agent makes **surgical edits only** — it does not rewrite the whole post.

| What changes | What stays the same |
|---|---|
| First paragraph (sapo) — fully rewritten | All other paragraph body text |
| First sentence of each paragraph | Sentences 2+ in every paragraph |
| Vague or label-style headings | Clear, specific headings |
| In-text citations added as hyperlinks | Post conclusions and opinions |
| Run-on lists → bullet/numbered lists | Post structure and order |
| FAQ section added at the end (4 questions) | Internal links and image references |
| 2 practitioner-voice sentences inserted | Original tone and voice |

---

## Troubleshooting

**"No rows with Status 'Optimize' found"**
Make sure column B says exactly `Optimize` (capital O, no extra spaces).

**Status stuck on `In Progress ⏳`**
The agent may have crashed mid-run. Change column B back to `Optimize` and run again.

**`Failed ❌` — "Could not fetch page"**
The URL may be behind a login or returning a 404. Check the URL is publicly accessible, then retry.

**`Failed ❌` — "Gemini API error"**
Your Gemini API key may have expired or hit a quota. Ask your team lead for an updated key, then re-save it:
```bash
echo 'NEW_KEY_HERE' > ~/.config/geo-optimizer/gemini_api_key
```

**Google auth expired (every few months)**
Re-run the Step 2 login command and sign in again.

---

## Output Location

All optimized posts are saved as Google Docs in:
**My Drive → GEO Optimized Posts**

The folder is created automatically on the first run. Each Doc is named:
`[GEO Optimized] {post title}`

---

## Questions?

Contact your team lead or open an issue in the project repository.
