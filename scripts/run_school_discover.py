"""
run_school_discover.py
Given a JSON file of schools with website URLs (collected by the agent via WebSearch),
scrapes each school's contact pages for real emails and appends verified contacts
to the Google Sheet.

No LLM involved in data extraction — pure HTTP requests + regex.

Usage:
  python3 scripts/run_school_discover.py --input /tmp/schools.json
  python3 scripts/run_school_discover.py --input /tmp/schools.json --limit 50
  python3 scripts/run_school_discover.py --input /tmp/schools.json --dry-run

Input JSON format (produced by the school-discover agent):
  [
    {
      "school_name": "Lincoln High School",
      "school_type": "High School",
      "city": "San Francisco",
      "state": "CA",
      "website": "https://lincoln.sfusd.edu"
    },
    ...
  ]

Options:
  --input    Path to JSON file with school list (required)
  --limit    Max verified contacts to collect (default: all found)
  --dry-run  Scrape and extract but do NOT write to sheet
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent


def run_extractor(schools: list) -> list:
    """Call extract_school_emails.py; returns verified contacts as a list."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "extract_school_emails.py"),
         json.dumps(schools)],
        text=True,
        stdout=subprocess.PIPE,
        # stderr (live progress per school) prints to terminal — not captured
    )
    if proc.returncode != 0:
        print("  ERROR: extract_school_emails.py failed", file=sys.stderr)
        return []
    try:
        return json.loads(proc.stdout)
    except (json.JSONDecodeError, ValueError):
        print("  ERROR: Could not parse extractor output", file=sys.stderr)
        return []


def run_appender(contacts: list) -> bool:
    """Call append_school_contacts.py to write contacts to the Google Sheet."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "append_school_contacts.py"),
         json.dumps(contacts)],
    )
    return proc.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="School Contact Discovery — scrape emails from agent-provided school URLs"
    )
    parser.add_argument("--input", required=True,
        help="Path to JSON file with school list (produced by school-discover agent)")
    parser.add_argument("--limit", type=int, default=0,
        help="Max verified contacts to collect (default: 0 = no limit)")
    parser.add_argument("--dry-run", action="store_true",
        help="Scrape and extract but do NOT write to sheet")
    args = parser.parse_args()

    # Load school list
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)

    try:
        schools = json.loads(input_path.read_text())
    except (json.JSONDecodeError, ValueError) as e:
        print(f"ERROR: Could not parse input file: {e}")
        sys.exit(1)

    if not schools:
        print("ERROR: Input file is empty — no schools to process")
        sys.exit(1)

    limit = args.limit if args.limit > 0 else len(schools)

    print("=" * 60)
    print("School Contact Discovery")
    print(f"  Input   : {args.input}  ({len(schools)} schools)")
    print(f"  Limit   : {limit}")
    if args.dry_run:
        print(f"  Mode    : DRY RUN — no sheet writes")
    print("=" * 60)

    # Scrape emails from real pages
    print(f"\nScraping contact pages for real emails...")
    contacts = run_extractor(schools[:limit * 3])  # fetch extra to hit the limit

    # Deduplicate by email
    seen    = set()
    unique  = []
    for c in contacts:
        if c["email"] not in seen:
            seen.add(c["email"])
            unique.append(c)
        if args.limit and len(unique) >= args.limit:
            break

    print(f"\n{'=' * 60}")
    print(f"Discovery complete")
    print(f"  Schools scraped   : {len(schools[:limit * 3])}")
    print(f"  Verified contacts : {len(unique)}")

    if not unique:
        print("\n  ⚠️  No emails found on any of the provided school websites.")
        print("  The agent may need to find schools with more accessible contact pages.")
        print("=" * 60)
        return

    if args.dry_run:
        print("\n  DRY RUN — sheet not updated. Contacts found:")
        for c in unique:
            print(f"    {c['school_name']} ({c['state']}) → {c['email']}")
        print("=" * 60)
        return

    print("\n  Writing to Google Sheet...")
    if run_appender(unique):
        print("  ✅ Sheet updated")
        print(f"\n📋 Next step:")
        print(f"   Open the sheet → type 'To send' in column L for rows you want to email")
        print(f"   Then run: python3 scripts/send_school_emails.py email_template.txt")
    else:
        print("  ❌ Sheet write failed — check oauth_token.pickle and school_outreach_config.env")

    print("=" * 60)


if __name__ == "__main__":
    main()
