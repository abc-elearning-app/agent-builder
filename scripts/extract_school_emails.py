"""
extract_school_emails.py
Given a list of school website URLs, actually fetches each page and extracts
real contact emails using HTTP requests + regex. No LLM involved — zero hallucination.

Usage:
  python3 scripts/extract_school_emails.py '<json_array_of_schools>'

Input JSON: list of objects with at minimum:
  {"school_name": "...", "school_type": "...", "city": "...", "state": "...", "website": "..."}

Output (stdout): JSON array of successfully resolved contacts (only rows where a real
  email was found on a real page). Rows with no email found are omitted.

Example:
  python3 scripts/extract_school_emails.py '[{"school_name":"Lincoln High","school_type":"High School","city":"San Jose","state":"CA","website":"https://lhs.sjusd.org"}]'
"""

import json
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

try:
    import requests
    from requests.exceptions import RequestException
except ImportError:
    print("ERROR: requests not installed. Run: pip3 install requests", file=sys.stderr)
    sys.exit(1)

# ── Config ──────────────────────────────────────────────────────────────────
REQUEST_TIMEOUT = 10      # seconds per HTTP request
DELAY_BETWEEN   = 1.5     # seconds between requests (polite scraping)
MAX_RETRIES     = 2

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Contact page path candidates — tried in order
CONTACT_PATHS = [
    "/contact",
    "/contact-us",
    "/about/contact",
    "/about",
    "/administration",
    "/staff",
    "/staff-directory",
    "/faculty",
    "/our-school/contact",
    "/school-info/contact",
    "/",   # homepage as last resort
]

# Email pattern — matches edu, org, us, gov, k12.*.us domains only
# Avoids generic noreply / webmaster / privacy addresses
EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.(edu|org|us|gov|k12\.[a-z]{2}\.us)',
    re.IGNORECASE
)

SKIP_PREFIXES = (
    "noreply", "no-reply", "donotreply", "webmaster", "privacy",
    "unsubscribe", "bounce", "mailer-daemon", "postmaster",
)

PRIORITY_KEYWORDS = [
    "principal", "contact", "admin", "office", "school",
    "superintendent", "info", "secretary", "registrar",
]


def fetch(url: str, session: requests.Session) -> str:
    """Fetch a URL and return text content, or None on failure."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT,
                               allow_redirects=True)
            if resp.status_code == 200:
                return resp.text
            if resp.status_code in (403, 404, 410):
                return None   # not retryable
        except RequestException:
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
    return None


def extract_emails(html: str) -> list[str]:
    """Extract and deduplicate emails from HTML, filtering obvious noise."""
    found = []
    seen  = set()
    for match in EMAIL_PATTERN.finditer(html):
        email = match.group(0).lower()
        local = email.split("@")[0]
        if any(local.startswith(skip) for skip in SKIP_PREFIXES):
            continue
        if email not in seen:
            seen.add(email)
            found.append(email)
    return found


def pick_best_email(emails: list[str]) -> str:
    """Pick the most likely school-contact email from a list."""
    if not emails:
        return None
    for keyword in PRIORITY_KEYWORDS:
        for email in emails:
            if keyword in email.split("@")[0]:
                return email
    return emails[0]


def discover_email(school: dict, session: requests.Session) -> dict:
    """
    Try contact sub-pages of the school website, return a contact record
    with a verified email, or None if nothing found.
    """
    base = school.get("website", "").strip().rstrip("/")
    if not base:
        print(f"  ⚠️  {school['school_name']}: no website URL provided — skipping",
              file=sys.stderr)
        return None

    # Normalise base URL
    parsed = urlparse(base)
    if not parsed.scheme:
        base = "https://" + base

    for path in CONTACT_PATHS:
        url = urljoin(base, path)
        html = fetch(url, session)
        time.sleep(DELAY_BETWEEN)

        if not html:
            continue

        emails = extract_emails(html)
        best   = pick_best_email(emails)

        if best:
            print(f"  ✅ {school['school_name']}: {best}  (from {url})",
                  file=sys.stderr)
            return {
                "school_name":  school.get("school_name", ""),
                "school_type":  school.get("school_type", ""),
                "city":         school.get("city", ""),
                "state":        school.get("state", ""),
                "email":        best,
                "phone":        school.get("phone", ""),
                "website":      base,
                "source_url":   url,
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "notes":        "",
            }

    print(f"  ❌ {school['school_name']}: no email found on any contact page",
          file=sys.stderr)
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: extract_school_emails.py '<json_array>'")
        sys.exit(1)

    schools = json.loads(sys.argv[1])
    print(f"🔍 Processing {len(schools)} schools...", file=sys.stderr)

    results = []
    with requests.Session() as session:
        for i, school in enumerate(schools, 1):
            print(f"[{i}/{len(schools)}] {school.get('school_name','?')} ({school.get('state','?')})",
                  file=sys.stderr)
            record = discover_email(school, session)
            if record:
                results.append(record)

    print(f"\n📊 Found emails: {len(results)}/{len(schools)}", file=sys.stderr)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
