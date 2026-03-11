"""
run_pinterest_batch.py
Standalone batch runner for the Pinterest Pin CSV Generator.

Reads "to do" rows from your Google Sheet, fetches items from each listing
page via Gemini CLI, generates Pinterest-optimized titles and descriptions,
writes bulk-upload CSV files (200-row limit, auto-split), uploads each CSV
to Google Drive, and updates the sheet — all without needing Claude Code.

Usage:
  python3 scripts/run_pinterest_batch.py                    # process all pending tasks
  python3 scripts/run_pinterest_batch.py --limit 3          # process at most 3 tasks
  python3 scripts/run_pinterest_batch.py --dry-run          # skip CSV write / upload / sheet update
  python3 scripts/run_pinterest_batch.py --reset-registry   # clear entire dedup registry, then run
  python3 scripts/run_pinterest_batch.py --reset-url URL    # clear registry entries for one URL, then run
"""

import argparse
import csv
import json
import os
import pickle
import re
import subprocess
import sys
import tempfile
import urllib.request
import warnings
from datetime import date
from pathlib import Path

warnings.filterwarnings("ignore")

from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPTS_DIR = Path(__file__).parent
REPO_ROOT   = SCRIPTS_DIR.parent
TOKEN_FILE  = REPO_ROOT / "oauth_token.pickle"
SEEN_FILE   = REPO_ROOT / "pinterest_pins_seen_urls.json"
CSV_MAX_ROWS = 200

# ── Column indices (0-based) ───────────────────────────────────────────────────
COL_SOURCE_URL  = 0   # A
COL_STATUS      = 1   # B
COL_BOARD       = 2   # C
COL_CSV         = 3   # D
COL_DATE        = 4   # E
COL_FAIL_REASON = 5   # F

TODO_STATUS = "to do"

# ── Gemini prompts ─────────────────────────────────────────────────────────────
# Items are now fetched directly from the listing page __NEXT_DATA__ (no Gemini).
# Gemini is only used for Step 3: generating Pinterest-optimized metadata.

METADATA_PROMPT = """\
You are a Pinterest copy specialist. Generate optimized Pinterest metadata for each item below.

## Content type detection
Detect from page_url, title, and tags:
- URL contains /coloring-pages/   → coloring-page
- URL contains /worksheets/       → worksheet
- URL contains /lesson-plan/      → lesson-plan
- URL contains /activities/       → activity
- Title starts with "How to"      → tutorial
- Title has number + plural noun  → listicle
- URL contains /blog/             → blog (detect subtype)
- Anything else                   → resource

## Title rules
- 30–60 characters, hard max 100
- Front-load primary keyword (topic + content type)
- Add one modifier: audience, style, or season
- DO NOT copy the raw item title verbatim — rewrite it
- Templates:
    coloring-page → "[Topic] Coloring Page | [Modifier]"
    worksheet     → "[Topic] Worksheet | [Grade or Skill]"
    lesson-plan   → "[Topic] Lesson Plan | [Grade Level]"
    tutorial      → "How to [Outcome] | [Audience]"
    listicle      → "[N] [Adjective] [Topic] | [Modifier]"
    activity      → "[Topic] Activity | [Modifier]"
    blog          → apply subtype template
    resource      → "[Topic] Printable | [Modifier]"
- If > 60 chars: drop modifier or shorten base
- If < 30 chars: add "Free Printable", "for Kids", or grade level

## Description rules
- 200–232 characters target, min 150, max 250
- Sentence 1: what user gets + why it matters, 2–3 keywords woven in naturally
- Sentence 2: clear CTA directing to the page
- End with 2–3 hashtags: #topic #contenttype #audience
- Natural conversational tone, no keyword stuffing, no repetition

## Keywords rules
- Strip # from description hashtags, append normalized grade codes
- Normalize grade levels: Preschool → Pre, Kindergarten/KG → KG, Grade 1/1st → 1st, \
Grade 2/2nd → 2nd, Grade 3/3rd → 3rd, Grade 4/4th → 4th, Grade 5/5th → 5th, Grade 6+ → 6th
- If worksheet spans multiple grades, include only the lowest and highest code as range \
endpoints (e.g. Pre,5th — NOT Pre,KG,1st,2nd,3rd,4th,5th)
- No duplicate keywords. Comma-separated, no spaces after commas. Hashtag-derived keywords lowercase.

## Input items
{items_json}

## Output format
Return ONLY a valid JSON array. Each object must have exactly:
{{"title": "...", "description": "...", "keywords": "..."}}
No explanation, no markdown, no code block fences.\
"""


# ── Config loader ──────────────────────────────────────────────────────────────
def _load_config():
    cfg = REPO_ROOT / "pinterest_config.env"
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

SHEET_ID  = os.environ.get("PINTEREST_SHEET_ID", "")
FOLDER_ID = os.environ.get("PINTEREST_DRIVE_FOLDER_ID", "")


# ── OAuth ──────────────────────────────────────────────────────────────────────
def load_creds():
    if not TOKEN_FILE.exists():
        raise FileNotFoundError(
            f"oauth_token.pickle not found at {TOKEN_FILE}\n"
            f"Re-run the installer:  bash {REPO_ROOT}/install-pinterest-generator.sh"
        )
    with open(TOKEN_FILE, "rb") as f:
        creds = pickle.load(f)
    if creds.expired and creds.refresh_token:
        print("🔄 OAuth token expired — refreshing automatically...")
        creds.refresh(Request())
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
        print("✅ Token refreshed")
    return creds


# ── Deduplication registry ─────────────────────────────────────────────────────
def load_seen() -> dict:
    """Load the dedup registry as {hex_id: source_url}.

    Automatically migrates the old flat-list format:
      ["abc123", ...]  →  {"abc123": "", ...}
    """
    if SEEN_FILE.exists():
        data = json.loads(SEEN_FILE.read_text())
        if isinstance(data, list):
            # Migrate old format — source URL unknown for legacy entries
            return {hex_id: "" for hex_id in data}
        return data  # Already a dict
    return {}

def save_seen(seen: dict):
    SEEN_FILE.write_text(json.dumps(seen, indent=2, sort_keys=True))


# ── Gemini CLI wrapper ─────────────────────────────────────────────────────────
def gemini_run(prompt: str, timeout: int = 360) -> str:
    """Write prompt to a temp file, run gemini --yolo, return stdout."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="/tmp/pinterest_prompt_"
    ) as f:
        f.write(prompt)
        prompt_file = f.name
    try:
        result = subprocess.run(
            f'gemini -p "$(cat {prompt_file})" --yolo 2>/dev/null',
            shell=True, capture_output=True, text=True, timeout=timeout
        )
        output = result.stdout.strip()
        if not output:
            raise RuntimeError(
                f"Gemini returned no output (exit {result.returncode}). "
                f"Make sure Gemini CLI is installed and logged in: run `gemini` once."
            )
        return output
    finally:
        Path(prompt_file).unlink(missing_ok=True)


def parse_json(raw: str) -> list:
    """Parse a JSON array from Gemini output, stripping any accidental markdown fences."""
    text = raw.strip()
    # Strip ```json ... ``` or ``` ... ``` fences
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```\s*$",       "", text, flags=re.MULTILINE)
    text = text.strip()
    # Find the outermost JSON array if there's surrounding text
    start = text.find("[")
    end   = text.rfind("]")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


# ── Step 1: Fetch items from listing page via __NEXT_DATA__ ───────────────────
def fetch_items(url: str) -> list:
    """Extract all worksheet items directly from the listing page __NEXT_DATA__ JSON.

    No Gemini needed — Worksheetzone embeds the full worksheet array (including
    thumbnail URLs, grades, and slugs) in the page's __NEXT_DATA__ script tag.
    One HTTP request, no LLM timeout risk.
    """
    req  = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; Bot/1.0)"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")

    m = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html, re.DOTALL
    )
    if not m:
        raise ValueError(
            "No __NEXT_DATA__ found on listing page. "
            "Make sure the URL is a listing/category page, not a single worksheet."
        )

    data = json.loads(m.group(1))
    try:
        worksheets = (
            data["props"]["pageProps"]["initialState"]
            ["homeV2State"]["currentPageData"]["worksheets"]
        )
    except KeyError:
        raise ValueError(
            "Unexpected page structure — could not find worksheets list in __NEXT_DATA__. "
            "Make sure the URL is a Worksheetzone listing/category page."
        )

    if not isinstance(worksheets, list) or not worksheets:
        raise ValueError("No worksheets found on the listing page.")

    items = []
    for w in worksheets:
        slug     = w.get("slug", "")
        page_url = f"https://worksheetzone.org/{slug}" if slug else ""
        grades   = (w.get("moreInfo") or {}).get("grades", [])
        desc     = ((w.get("seoInfo") or {}).get("description") or "").strip()
        tags     = [t.get("name", "") for t in (w.get("tags") or []) if t.get("name")]
        items.append({
            "title":         w.get("title", "").strip(),
            "page_url":      page_url,
            "thumbnail_url": w.get("thumbnail", "").strip(),
            "description":   desc,
            "grade_levels":  grades,
            "tags":          tags,
        })

    return items


# ── Step 2b: Deduplicate ───────────────────────────────────────────────────────
def dedup(items: list, seen: dict, source_url: str = "") -> tuple:
    """Return (clean, dupes). Adds new hex IDs to seen as {hex_id: source_url}."""
    clean, dupes = [], []
    for item in items:
        url   = item.get("page_url", "")
        match = re.search(r"[0-9a-f]{24}", url)
        key   = match.group(0) if match else url
        if key in seen:
            dupes.append(item.get("title", url))
        else:
            seen[key] = source_url
            clean.append(item)
    return clean, dupes


# ── Step 3: Generate metadata ──────────────────────────────────────────────────
def generate_metadata(items: list) -> list:
    items_json = json.dumps(items, indent=2, ensure_ascii=False)
    raw        = gemini_run(METADATA_PROMPT.format(items_json=items_json), timeout=420)
    metadata   = parse_json(raw)
    if not isinstance(metadata, list):
        raise ValueError(f"Expected a JSON array from metadata step, got {type(metadata).__name__}")
    return metadata


# ── Step 4: Validate ───────────────────────────────────────────────────────────
CTA_VERBS = ("download", "get", "grab", "click", "print", "try", "explore",
             "discover", "check", "find", "start", "learn")

def validate(items: list, metadata: list, board: str) -> tuple:
    rows, errors, warns = [], 0, 0

    for i, (item, meta) in enumerate(zip(items, metadata), start=1):
        title       = meta.get("title",       "").strip()
        description = meta.get("description", "").strip()
        keywords    = meta.get("keywords",    "").strip()
        media_url   = (item.get("thumbnail_url") or "").strip()
        page_url    = item.get("page_url", "").strip()

        if not title:
            print(f"    ⚠️  Row {i}: empty title — skipped"); errors += 1; continue
        if len(title) > 100:
            title = title[:100]
        if len(title) < 30:
            print(f"    ⚠️  Row {i}: title too short ({len(title)} chars): {title}"); warns += 1

        if not media_url or media_url.lower() == "null":
            print(f"    ⚠️  Row {i}: no thumbnail_url — skipped: {title[:50]}"); errors += 1; continue
        if not media_url.startswith("https://storage.googleapis.com/worksheetzone/"):
            print(f"    ❌ Row {i}: wrong thumbnail domain — skipped: {media_url[:80]}"); errors += 1; continue

        if len(description) < 150:
            print(f"    ⚠️  Row {i}: description {len(description)} chars (< 150)"); warns += 1
        if len(description) > 500:
            description = description[:500]
        if "#" not in description:
            print(f"    ⚠️  Row {i}: description has no hashtags"); warns += 1
        if not any(v in description.lower() for v in CTA_VERBS):
            print(f"    ⚠️  Row {i}: description may be missing a CTA"); warns += 1

        rows.append({
            "title":       title,
            "media_url":   media_url,
            "board":       board,
            "description": description,
            "link":        page_url,
            "keywords":    keywords,
        })

    return rows, errors, warns


# ── Step 5: CSV writer (with auto-split at 200 rows) ──────────────────────────
CSV_HEADER = ["Title", "Media URL", "Pinterest board", "Thumbnail",
              "Description", "Link", "Publish date", "Keywords"]

class CsvWriter:
    def __init__(self, base_path: Path):
        self._base      = base_path
        self.part       = 1
        self.part_rows  = 0
        self.total_rows = 0
        self._closed    = []   # list of (Path, row_count)
        self._open()

    def _open(self):
        self.path = Path(f"{self._base}_part{self.part}.csv")
        self._fh  = open(self.path, "w", newline="", encoding="utf-8")
        self._w   = csv.writer(self._fh, quoting=csv.QUOTE_ALL)
        self._w.writerow(CSV_HEADER)
        self.part_rows = 0

    def write(self, row: dict) -> Path:
        """Write one row. Auto-splits at CSV_MAX_ROWS. Returns path written to."""
        if self.part_rows >= CSV_MAX_ROWS:
            self._seal()
            self.part += 1
            self._open()
            print(f"  ⚠️  200-row limit reached — new file: {self.path.name}")
        self._w.writerow([
            row["title"], row["media_url"], row["board"], "",
            row["description"], row["link"], "", row["keywords"],
        ])
        self.part_rows  += 1
        self.total_rows += 1
        return self.path

    def _seal(self):
        self._fh.close()
        self._closed.append((self.path, self.part_rows))

    def close(self):
        self._fh.close()
        if self.part_rows > 0:
            self._closed.append((self.path, self.part_rows))

    @property
    def sealed_files(self):
        return list(self._closed)


# ── Drive upload (delegates to existing script) ────────────────────────────────
def upload_csv(csv_path: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "upload_csv_to_drive.py"), str(csv_path)],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(f"Drive upload failed: {result.stderr[:300]}")
    link = result.stdout.strip()
    if not link.startswith("https://"):
        raise RuntimeError(f"Unexpected upload output: {link[:200]}")
    return link


# ── Sheet helpers (delegates to existing script) ───────────────────────────────
def mark_done(row_num: int, board: str, csv_link: str, today: str):
    subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "update_pinterest_task.py"),
         str(row_num), "done", board, csv_link, today, ""],
        check=True, capture_output=True, text=True
    )

def mark_failed(row_num: int, today: str, reason: str):
    subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "update_pinterest_task.py"),
         str(row_num), "failed", "", "", today, reason[:300]],
        check=True, capture_output=True, text=True
    )


# ── Board name ─────────────────────────────────────────────────────────────────
def derive_board(source_url: str, override: str) -> str:
    if override:
        return override
    slug = source_url.rstrip("/").split("/")[-1]
    return slug.replace("-", " ").title()


# ── Per-task processor ─────────────────────────────────────────────────────────
def process_task(task: dict, csv_writer: "CsvWriter | None",
                 seen: set, dry_run: bool) -> dict:
    row_num    = task["row"]
    source_url = task["source_url"]
    board      = derive_board(source_url, task.get("board_override", ""))

    result = {
        "row": row_num, "board": board, "source_url": source_url,
        "status": "failed", "csv_path": "", "pins": 0, "error": ""
    }

    try:
        # Step 1 — fetch items + thumbnails directly from listing page __NEXT_DATA__
        print(f"  [1/3] Fetching items from listing page...")
        items = fetch_items(source_url)
        thumb_count = sum(1 for it in items if it.get("thumbnail_url"))
        print(f"  [1/3] ✅ {len(items)} item(s) found, {thumb_count} with thumbnails")

        # Step 2 — dedup
        clean, dupes = dedup(items, seen, source_url)
        if dupes:
            print(f"  [2/3] 🔍 {len(clean)} unique, {len(dupes)} duplicate(s) skipped")
        else:
            print(f"  [2/3] 🔍 {len(clean)}/{len(items)} unique")

        if not clean:
            print(f"  ℹ️  All items already seen — skipping task")
            result["status"] = "skipped"
            return result

        # Step 3 — generate Pinterest metadata via Gemini
        print(f"  [3/3] Generating Pinterest metadata via Gemini...")
        metadata = generate_metadata(clean)
        print(f"  [3/3] ✅ Metadata ready for {len(metadata)} item(s)")

        # Step 4 — validate
        rows, errors, warns = validate(clean, metadata, board)
        suffix = f"({errors} error(s), {warns} warning(s))" if (errors or warns) else ""
        print(f"  [✓] {len(rows)}/{len(clean)} rows passed validation {suffix}".rstrip())

        if not rows:
            raise RuntimeError("No valid rows remained after validation")

        if dry_run:
            print(f"  ⏭️  Dry run — skipping CSV write, upload, sheet update")
            result["status"] = "dry-run"
            result["pins"]   = len(rows)
            return result

        # Write rows; record which CSV file this task ends in
        last_path = None
        for row in rows:
            last_path = csv_writer.write(row)

        result["status"]   = "done"
        result["pins"]     = len(rows)
        result["csv_path"] = str(last_path)

    except Exception as exc:
        err = str(exc)[:400]
        print(f"  ❌ FAILED: {err}")
        result["error"] = err

    return result


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Pinterest Pin CSV Generator — Batch Runner"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Run without writing CSVs, uploading, or updating the sheet")
    parser.add_argument("--limit", type=int, default=None,
                        help="Maximum number of tasks (sheet rows) to process")
    parser.add_argument("--reset-registry", action="store_true",
                        help="Clear the entire dedup registry before running")
    parser.add_argument("--reset-url", metavar="URL",
                        help="Remove all registry entries for this source URL before running")
    args = parser.parse_args()

    # ── Preflight checks ──────────────────────────────────────────────────────
    if not SHEET_ID:
        print("❌ PINTEREST_SHEET_ID is not set.\n"
              "   Copy pinterest_config.env.example → pinterest_config.env and fill it in.",
              file=sys.stderr)
        sys.exit(1)

    if not FOLDER_ID and not args.dry_run:
        print("❌ PINTEREST_DRIVE_FOLDER_ID is not set.\n"
              "   Check pinterest_config.env.",
              file=sys.stderr)
        sys.exit(1)

    if subprocess.run(["which", "gemini"], capture_output=True).returncode != 0:
        print("❌ Gemini CLI not found. Install: npm install -g @google/gemini-cli",
              file=sys.stderr)
        sys.exit(1)

    # ── Banner ────────────────────────────────────────────────────────────────
    print("=" * 60)
    print("Pinterest Pin CSV Generator — Batch Runner")
    if args.dry_run: print("  Mode : DRY RUN (no writes)")
    if args.limit:   print(f"  Limit: {args.limit} task(s)")
    print("=" * 60)

    # ── Registry management ───────────────────────────────────────────────────
    if args.reset_registry:
        if SEEN_FILE.exists():
            SEEN_FILE.unlink()
            print("🗑️  Dedup registry cleared (all entries removed).")
        else:
            print("ℹ️  Dedup registry was already empty.")
        print()

    if args.reset_url:
        target = args.reset_url.rstrip("/")
        reg = load_seen()
        before = len(reg)
        # Remove entries whose stored source_url matches target
        reg = {k: v for k, v in reg.items() if v.rstrip("/") != target}
        removed = before - len(reg)
        if removed:
            save_seen(reg)
            print(f"🗑️  Removed {removed} registry entry(ies) for: {target}")
        else:
            print(f"ℹ️  No registry entries found for: {target}")
            if before > 0:
                print(f"   (Note: {before} entries exist but may have been migrated from the old "
                      f"format and lack source URL info. Use --reset-registry to clear all.)")
        print()

    # ── Auth ──────────────────────────────────────────────────────────────────
    try:
        creds = load_creds()
    except FileNotFoundError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        sys.exit(1)

    sheets_svc = build("sheets", "v4", credentials=creds)

    # ── Read pending tasks ────────────────────────────────────────────────────
    print("\nReading sheet...")
    sheet_data = sheets_svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range="A:F"
    ).execute()
    all_rows = sheet_data.get("values", [])

    tasks = []
    for i, row in enumerate(all_rows[1:], start=2):
        status = row[COL_STATUS].strip().lower() if len(row) > COL_STATUS else ""
        if status == TODO_STATUS:
            source_url     = row[COL_SOURCE_URL].strip() if len(row) > COL_SOURCE_URL else ""
            board_override = row[COL_BOARD].strip()      if len(row) > COL_BOARD      else ""
            if source_url:
                tasks.append({"row": i, "source_url": source_url,
                               "board_override": board_override})

    if not tasks:
        print("📋 No pending tasks. All rows are already done or failed.")
        print(f"   Sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
        return

    if args.limit:
        tasks = tasks[:args.limit]

    print(f"📋 Found {len(tasks)} pending task(s):")
    for t in tasks:
        board = derive_board(t["source_url"], t.get("board_override", ""))
        print(f"   Row {t['row']:>3} │ {t['source_url']}  → Board: {board!r}")

    # ── Dedup registry ────────────────────────────────────────────────────────
    seen = load_seen()
    print(f"\n🔍 Dedup registry: {len(seen)} URLs already seen\n{'─' * 60}")

    # ── CSV state ─────────────────────────────────────────────────────────────
    today      = str(date.today())
    base_path  = REPO_ROOT / f"pinterest_pins_{today}"
    csv_writer = CsvWriter(base_path) if not args.dry_run else None

    # ── Process tasks ─────────────────────────────────────────────────────────
    results = []
    for idx, task in enumerate(tasks, start=1):
        print(f"\n── Task {idx}/{len(tasks)}  Row {task['row']} │ {task['source_url']}")
        board = derive_board(task["source_url"], task.get("board_override", ""))
        print(f"   Board: {board!r}")

        r = process_task(task, csv_writer, seen, dry_run=args.dry_run)
        results.append(r)
        save_seen(seen)

    # ── Upload CSVs + update sheet ────────────────────────────────────────────
    drive_links: dict[str, str] = {}   # csv_path → drive_link

    if not args.dry_run:
        csv_writer.close()

        # Upload each sealed CSV file once
        all_files = csv_writer.sealed_files
        print(f"\n{'─' * 60}")
        for csv_path, row_count in all_files:
            if csv_path.exists() and row_count > 0:
                try:
                    print(f"📤 Uploading {csv_path.name} ({row_count} pins)...")
                    link = upload_csv(csv_path)
                    drive_links[str(csv_path)] = link
                    print(f"   ✅ {link}")
                except Exception as exc:
                    print(f"   ❌ Upload failed: {exc}")

        # Update sheet rows
        print()
        for r in results:
            if r["status"] == "done":
                link = drive_links.get(r["csv_path"], "")
                try:
                    mark_done(r["row"], r["board"], link, today)
                    print(f"✅ Row {r['row']} → done  (board: {r['board']!r}, {r['pins']} pins)")
                except Exception as exc:
                    print(f"⚠️  Could not update sheet row {r['row']}: {exc}")
            elif r["status"] == "skipped":
                try:
                    mark_done(r["row"], r["board"], "", today)
                    print(f"✅ Row {r['row']} → done  (board: {r['board']!r}, all items already seen — no new pins)")
                except Exception as exc:
                    print(f"⚠️  Could not update sheet row {r['row']}: {exc}")
            elif r["status"] == "failed":
                try:
                    mark_failed(r["row"], today, r["error"])
                    print(f"❌ Row {r['row']} → failed: {r['error'][:80]}")
                except Exception as exc:
                    print(f"⚠️  Could not update sheet row {r['row']}: {exc}")

    # ── Summary ───────────────────────────────────────────────────────────────
    done_count    = sum(1 for r in results if r["status"] == "done")
    failed_count  = sum(1 for r in results if r["status"] == "failed")
    skipped_count = sum(1 for r in results if r["status"] == "skipped")
    total_pins    = sum(r["pins"] for r in results)
    boards        = sorted({r["board"] for r in results if r["status"] == "done"})

    print(f"\n{'=' * 60}")
    print("All done!" if not args.dry_run else "Dry run complete.")
    print()

    if not args.dry_run and drive_links:
        print("📁 CSV files on Google Drive:")
        for csv_path, row_count in (csv_writer.sealed_files if csv_writer else []):
            link = drive_links.get(str(csv_path), "(upload failed)")
            print(f"   {csv_path.name:<45}  {row_count:>3} pins  → {link}")
        print()

    print(f"📌 Total pins     : {total_pins}")
    print(f"🔗 Tasks          : {len(results)} total  "
          f"({done_count} done, {failed_count} failed, {skipped_count} skipped)")
    if boards:
        print(f"🗂️  Boards         : {', '.join(boards)}")
    print(f"📖 Dedup registry : {len(seen)} URLs tracked")

    if not args.dry_run and SHEET_ID:
        print()
        print(f"📊 Sheet : https://docs.google.com/spreadsheets/d/{SHEET_ID}")
        print(f"📂 Drive : https://drive.google.com/drive/folders/{FOLDER_ID}")
        print()
        print("Next steps:")
        print("  1. Go to Pinterest Business → Create → Bulk create Pins")
        print("  2. Download each CSV from the Drive links above")
        print("  3. Upload each CSV (200-pin limit per upload)")
        print("  4. Review the preview → Publish")

    print("=" * 60)


if __name__ == "__main__":
    main()
