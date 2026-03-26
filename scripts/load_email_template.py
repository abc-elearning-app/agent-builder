"""
load_email_template.py
Reads and validates an email template file, returns subject + body as JSON.

Template file format (plain .txt):
  Line 1:   SUBJECT: <subject line with optional {variables}>
  Line 2:   SENDER_NAME: <display name>  (optional)
  Line 3:   ---                          (separator)
  Lines 4+: email body

Usage:
  python3 scripts/load_email_template.py email_template.txt

Output (stdout):
  {"subject": "...", "sender_name": "...", "body": "..."}
"""

import json
import re
import sys
from pathlib import Path

REQUIRED_VARIABLES = []   # none required — all optional
VALID_VARIABLES    = {'{school_name}', '{school_type}', '{city}', '{state}'}


def parse(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()

    subject     = ""
    sender_name = ""
    body_start  = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.upper().startswith("SUBJECT:"):
            subject = line.split(":", 1)[1].strip()
        elif stripped.upper().startswith("SENDER_NAME:"):
            sender_name = line.split(":", 1)[1].strip()
        elif stripped == "---":
            body_start = i + 1
            break

    if not subject:
        raise ValueError("Template is missing a SUBJECT: line")
    if body_start == 0:
        raise ValueError("Template is missing the --- separator between headers and body")

    body = "\n".join(lines[body_start:]).strip()

    if not body:
        raise ValueError("Template body is empty (nothing after the --- separator)")

    # Warn about unknown variables
    found_vars = set(re.findall(r'\{[^}]+\}', subject + body))
    unknown = found_vars - VALID_VARIABLES
    if unknown:
        print(f"WARNING: Unknown variable(s) in template: {', '.join(sorted(unknown))}", file=sys.stderr)
        print(f"  Valid variables: {', '.join(sorted(VALID_VARIABLES))}", file=sys.stderr)

    return {"subject": subject, "sender_name": sender_name, "body": body}


def main():
    if len(sys.argv) < 2:
        print("Usage: load_email_template.py <template_file.txt>")
        sys.exit(1)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"ERROR: Template file not found: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        result = parse(path)
        print(json.dumps(result, indent=2))
        print(f"✅ Template loaded: subject='{result['subject']}', "
              f"sender='{result['sender_name']}', body={len(result['body'])} chars",
              file=sys.stderr)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
