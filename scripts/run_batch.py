"""
run_batch.py
Batch runner for the GEO Blog Post Optimizer.

Reads rows with Status="optimize" from the Google Sheet, optimizes each post,
creates a Google Doc, and writes the result back to the sheet.

Usage:
  # Run next 10 rows (default)
  python3 scripts/run_batch.py

  # Run only 3 rows
  python3 scripts/run_batch.py --limit 3

  # Run a specific range of sheet rows (e.g. rows 71-80)
  python3 scripts/run_batch.py --start-row 71 --end-row 80

  # Dry run — fetch and optimize but do NOT write to sheet or create docs
  python3 scripts/run_batch.py --limit 3 --dry-run
"""

import argparse
import os
import pickle
import re
import subprocess
import sys
import time
import urllib.request
import warnings
from datetime import date
from pathlib import Path

warnings.filterwarnings("ignore")

from googleapiclient.discovery import build

# ── Config ────────────────────────────────────────────────────────────────────
SCRIPTS_DIR   = Path(__file__).parent
TOKEN_FILE    = SCRIPTS_DIR.parent / "oauth_token.pickle"
SHEET_ID      = "1BhPNndHkZNf4xwJz1_AQUQcWo9awjt41swnVlrefj6c"
FOLDER_ID     = "16kPgjFPeahDJ_Acy00l7KLVGzR6VxkHZ"
TMP_DIR       = Path("/tmp/geo_batch")
DELAY_SECONDS = 5        # polite delay between rows to avoid rate limits

# Column indices (0-based)
COL_URL            = 0
COL_STATUS         = 1
COL_WRITER         = 2
COL_OPTIMIZED_DOC  = 3
COL_FAIL_REASON    = 4
COL_PROCESSED_DATE = 5
COL_POST_TITLE     = 6


# ── Google API helpers ────────────────────────────────────────────────────────

def load_creds():
    with open(TOKEN_FILE, "rb") as f:
        return pickle.load(f)

def get_sheet_rows(sheets_svc) -> list[tuple[int, list]]:
    """Return list of (sheet_row_number, row_data) for all rows with status='optimize'."""
    result = sheets_svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range="A:G"
    ).execute()
    rows = result.get("values", [])
    out = []
    for i, row in enumerate(rows[1:], start=2):   # row 1 is header
        status = row[COL_STATUS].strip().lower() if len(row) > COL_STATUS else ""
        if status == "optimize":
            out.append((i, row))
    return out

def update_sheet_row(sheets_svc, row_num: int, doc_url: str):
    sheets_svc.spreadsheets().values().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"valueInputOption": "RAW", "data": [
            {"range": f"B{row_num}", "values": [["Done ✅"]]},
            {"range": f"D{row_num}", "values": [[doc_url]]},
            {"range": f"F{row_num}", "values": [[str(date.today())]]},
        ]}
    ).execute()

def fail_sheet_row(sheets_svc, row_num: int, reason: str):
    sheets_svc.spreadsheets().values().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"valueInputOption": "RAW", "data": [
            {"range": f"B{row_num}", "values": [["Failed ❌"]]},
            {"range": f"E{row_num}", "values": [[reason[:500]]]},
            {"range": f"F{row_num}", "values": [[str(date.today())]]},
        ]}
    ).execute()


# ── Blog post fetcher ─────────────────────────────────────────────────────────

def fetch_blog_post(url: str) -> str:
    """Fetch and clean blog post HTML → markdown text."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        raise RuntimeError(f"Fetch failed: {e}")

    # Strip scripts, styles, comments
    html = re.sub(r"<!--.*?-->",               "", html, flags=re.DOTALL)
    html = re.sub(r"<script[^>]*>.*?</script>","", html, flags=re.DOTALL)
    html = re.sub(r"<style[^>]*>.*?</style>",  "", html, flags=re.DOTALL)

    # Convert key tags to markdown
    html = re.sub(r"<h1[^>]*>(.*?)</h1>", r"\n# \1\n",  html, flags=re.DOTALL)
    html = re.sub(r"<h2[^>]*>(.*?)</h2>", r"\n## \1\n", html, flags=re.DOTALL)
    html = re.sub(r"<h3[^>]*>(.*?)</h3>", r"\n### \1\n",html, flags=re.DOTALL)
    html = re.sub(r"<li[^>]*>(.*?)</li>", r"\n- \1",    html, flags=re.DOTALL)
    html = re.sub(r"<p[^>]*>(.*?)</p>",   r"\1\n\n",    html, flags=re.DOTALL)
    html = re.sub(r"<br\s*/?>",           "\n",          html)
    html = re.sub(r"<[^>]+>",             "",            html)

    # Decode HTML entities
    for ent, ch in [("&amp;","&"),("&nbsp;"," "),("&lt;","<"),
                    ("&gt;",">"),("&#39;","'"),("&quot;",'"')]:
        html = html.replace(ent, ch)

    html = re.sub(r"[ \t]+", " ", html)
    html = re.sub(r"\n{3,}", "\n\n", html).strip()

    # Cut off footer / related posts noise
    for marker in ["Copyright", "Privacy Policy", "SUBSCRIBE",
                   "RESOURCE\n", "COMPANY\n", "Read more\n"]:
        idx = html.find(marker)
        if idx > 5000:
            html = html[:idx].strip()
            break

    # Also cut trailing stray ## headings with no content
    html = re.sub(r"\n##\s*$", "", html).strip()

    if len(html) < 500:
        raise RuntimeError("Fetched content too short — page may be blocked or empty")

    return html


# ── Optimizer call ────────────────────────────────────────────────────────────

def run_optimizer(input_path: Path, output_path: Path, post_url: str, writer: str):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "optimize_post.py"),
         "--input",  str(input_path),
         "--output", str(output_path),
         "--url",    post_url,
         "--writer", writer.lower()],
        capture_output=True, text=True, timeout=360
    )
    if result.returncode != 0:
        raise RuntimeError(f"Optimizer failed:\n{result.stderr[-500:]}")
    # Print optimizer's stderr (progress info) to our stdout
    if result.stderr:
        for line in result.stderr.strip().splitlines():
            print(f"    {line}")


# ── Doc creator call ──────────────────────────────────────────────────────────

def run_doc_creator(input_path: Path, title: str) -> str:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "create_geo_doc.py"),
         str(input_path), title, FOLDER_ID],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(f"Doc creator failed:\n{result.stderr[-500:]}")
    if result.stderr:
        for line in result.stderr.strip().splitlines():
            print(f"    {line}")
    doc_url = result.stdout.strip()
    if not doc_url.startswith("https://"):
        raise RuntimeError(f"Unexpected doc creator output: {doc_url[:200]}")
    return doc_url


# ── Row processor ─────────────────────────────────────────────────────────────

def process_row(row_num: int, row: list, sheets_svc, dry_run: bool) -> bool:
    url    = row[COL_URL].strip()    if len(row) > COL_URL    else ""
    writer = row[COL_WRITER].strip() if len(row) > COL_WRITER else "gemini"
    title  = row[COL_POST_TITLE].strip() if len(row) > COL_POST_TITLE else ""

    if not url:
        print(f"  ⚠️  Skipped — empty URL")
        return False

    writer = writer.lower() if writer.lower() in ("gemini", "claude") else "gemini"

    original_path  = TMP_DIR / f"row{row_num}_original.md"
    optimized_path = TMP_DIR / f"row{row_num}_optimized.md"

    try:
        # Step 1: Fetch blog post
        print(f"  [1/4] Fetching {url}")
        content = fetch_blog_post(url)

        # Extract title from content if missing in sheet
        if not title:
            m = re.search(r"^#\s+(.+)", content, re.MULTILINE)
            title = m.group(1).strip() if m else url.rstrip("/").split("/")[-1].replace("-", " ").title()

        original_path.write_text(content, encoding="utf-8")
        print(f"  [1/4] ✅ {len(content):,} chars — \"{title[:60]}\"")

        # Step 2: Optimize
        print(f"  [2/4] Optimizing via {writer.title()} ...")
        run_optimizer(original_path, optimized_path, url, writer)
        print(f"  [2/4] ✅ Optimized ({optimized_path.stat().st_size:,} chars)")

        if dry_run:
            print(f"  [3/4] ⏭️  Dry run — skipping doc creation")
            print(f"  [4/4] ⏭️  Dry run — skipping sheet update")
            return True

        # Step 3: Create Google Doc
        doc_title = f"{title} — GEO Optimized"
        print(f"  [3/4] Creating Google Doc ...")
        doc_url = run_doc_creator(optimized_path, doc_title)
        print(f"  [3/4] ✅ {doc_url}")

        # Step 4: Update sheet
        print(f"  [4/4] Updating sheet row {row_num} ...")
        update_sheet_row(sheets_svc, row_num, doc_url)
        print(f"  [4/4] ✅ Sheet updated")

        return True

    except Exception as e:
        err = str(e)
        print(f"  ❌ FAILED: {err[:200]}")
        if not dry_run:
            try:
                fail_sheet_row(sheets_svc, row_num, err)
            except Exception as sheet_err:
                print(f"  ⚠️  Could not update sheet with failure: {sheet_err}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="GEO Blog Post Optimizer — Batch Runner")
    parser.add_argument("--limit",     type=int, default=10,
                        help="Max rows to process in this run (default: 10)")
    parser.add_argument("--start-row", type=int, default=None,
                        help="Only process rows >= this sheet row number")
    parser.add_argument("--end-row",   type=int, default=None,
                        help="Only process rows <= this sheet row number")
    parser.add_argument("--dry-run",   action="store_true",
                        help="Optimize but skip doc creation and sheet updates")
    args = parser.parse_args()

    TMP_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("GEO Batch Optimizer")
    print(f"  Limit     : {args.limit} rows")
    if args.start_row: print(f"  Start row : {args.start_row}")
    if args.end_row:   print(f"  End row   : {args.end_row}")
    if args.dry_run:   print(f"  Mode      : DRY RUN (no writes)")
    print("=" * 60)

    creds      = load_creds()
    sheets_svc = build("sheets", "v4", credentials=creds)

    print("Reading sheet ...")
    all_rows = get_sheet_rows(sheets_svc)
    print(f"Found {len(all_rows)} rows with status='optimize'")

    # Apply row range filter
    if args.start_row or args.end_row:
        all_rows = [
            (r, row) for r, row in all_rows
            if (args.start_row is None or r >= args.start_row) and
               (args.end_row   is None or r <= args.end_row)
        ]
        print(f"After range filter: {len(all_rows)} rows")

    # Apply limit
    batch = all_rows[:args.limit]
    print(f"Processing {len(batch)} rows this run\n")

    succeeded = 0
    failed    = 0

    for i, (row_num, row) in enumerate(batch, start=1):
        url = row[COL_URL] if len(row) > COL_URL else "?"
        print(f"── Row {row_num}  [{i}/{len(batch)}]  {url}")

        ok = process_row(row_num, row, sheets_svc, dry_run=args.dry_run)
        if ok:
            succeeded += 1
        else:
            failed += 1

        if i < len(batch):
            print(f"  ⏳ Waiting {DELAY_SECONDS}s before next row ...\n")
            time.sleep(DELAY_SECONDS)

    print("\n" + "=" * 60)
    print(f"Batch complete")
    print(f"  ✅ Succeeded : {succeeded}")
    print(f"  ❌ Failed    : {failed}")
    print(f"  📊 Sheet     : https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    print("=" * 60)


if __name__ == "__main__":
    main()
