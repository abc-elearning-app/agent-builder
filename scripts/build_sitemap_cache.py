"""
build_sitemap_cache.py
Recursively fetches ALL worksheetzone.org sitemaps and saves a local URL index.

Run once (and re-run when new content is added):
  python3 scripts/build_sitemap_cache.py

Sitemap tree:
  sitemap.xml (index)
  ├── page-sitemap.xml              → 14  static pages
  ├── worksheet-generator.xml       → 27  tool pages
  ├── post-category.xml             → 20  blog categories
  ├── post-sitemap.xml              → 596 blog posts
  ├── worksheets-detail.xml         → 65  worksheet detail pages
  ├── lesson-plans-detail.xml       → 3   lesson plan detail pages
  ├── worksheets.xml (index)        → 24 sub-sitemaps → worksheet categories
  ├── coloring-pages.xml (index)    → 43 sub-sitemaps → coloring page categories
  └── lesson-plans.xml (index)      → 3  sub-sitemaps → lesson plan categories
  [team-members-sitemap.xml skipped — not content pages]
  [coloring-pages-detail.xml skipped — hash-slug IDs, no semantic value]
"""

import json, re, time, urllib.request
from datetime import date

CACHE_FILE = "/Users/dangluu/Projects/agent-factory/scripts/wzorg_link_cache.json"
BASE = "https://worksheetzone.org"

# ── URL type mapping ─────────────────────────────────────────────────────────
def classify(url: str) -> str:
    if "/blog/" in url:              return "blog"
    if "/worksheets/" in url:        return "worksheet"
    if "/worksheet-" in url:         return "tool"
    if "/word-search" in url:        return "tool"
    if "/coloring-page" in url:      return "coloring"
    if "/coloring-pages/" in url:    return "coloring"
    if "/lesson-plan" in url:        return "lesson"
    if "/category/" in url:          return "category"
    return "page"

# ── Slug helpers ──────────────────────────────────────────────────────────────
def slug_to_title(url: str) -> str:
    path = url.rstrip("/").split("/")[-1]
    return path.replace("-", " ").replace("_", " ").title()

def slug_keywords(url: str) -> list:
    path = url.rstrip("/").split("/")[-1]
    return [w.lower() for w in re.split(r"[-_]", path) if len(w) > 2]

# ── Filters ───────────────────────────────────────────────────────────────────
SKIP_PATHS = {
    "/privacy-policy", "/terms-of-service", "/refund-policy",
    "/editorial-policy", "/about-us", "/contact-us", "/reviews",
    "/blog",  # bare /blog index page, not useful
}

def is_useful(url: str) -> bool:
    """Return True if the URL is worth indexing for internal linking."""
    if not url.startswith(BASE):
        return False
    if url.endswith(".xml"):
        return False
    path = url[len(BASE):]
    if path in SKIP_PATHS:
        return False
    # Skip team member profile pages
    if "/team-member/" in url or "/author/" in url:
        return False
    # Skip hash-slug coloring page detail IDs
    # (pattern: ends with -HEXID like -62a026a2ee7b001ec52eb910)
    if re.search(r"-[0-9a-f]{20,}$", url):
        return False
    return True

# ── Fetcher ───────────────────────────────────────────────────────────────────
def fetch_xml(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")

def extract_locs(xml: str) -> list:
    return re.findall(r"<loc>([^<]+)</loc>", xml)

def is_sitemap_index(locs: list) -> bool:
    """True if the locs are XML sub-sitemaps, not actual page URLs."""
    return bool(locs) and all(l.endswith(".xml") for l in locs[:3])

def crawl_sitemap(url: str, content_type: str, seen: set, depth: int = 0) -> list:
    """Recursively fetch a sitemap and return all real page entries."""
    if depth > 3:
        return []
    indent = "  " * depth
    print(f"{indent}→ {url.replace(BASE, '')} ", end="", flush=True)

    try:
        xml = fetch_xml(url)
        time.sleep(0.1)  # polite crawl
    except Exception as e:
        print(f"ERROR: {e}")
        return []

    locs = extract_locs(xml)

    if is_sitemap_index(locs):
        print(f"(index, {len(locs)} sub-sitemaps)")
        entries = []
        for sub in locs:
            entries.extend(crawl_sitemap(sub, content_type, seen, depth + 1))
        return entries

    # Actual URL list
    added = 0
    entries = []
    for loc in locs:
        loc = loc.strip()
        if loc in seen or not is_useful(loc):
            continue
        seen.add(loc)
        entries.append({
            "url":      loc,
            "title":    slug_to_title(loc),
            "keywords": slug_keywords(loc),
            "type":     classify(loc) or content_type,
        })
        added += 1
    print(f"({added} URLs)")
    return entries

# ── Top-level sitemaps to crawl ───────────────────────────────────────────────
SITEMAPS = [
    ("blog",      f"{BASE}/post-sitemap.xml"),
    ("category",  f"{BASE}/post-category.xml"),
    ("worksheet", f"{BASE}/worksheets-detail.xml"),
    ("worksheet", f"{BASE}/worksheets.xml"),
    ("tool",      f"{BASE}/worksheet-generator.xml"),
    ("lesson",    f"{BASE}/lesson-plans-detail.xml"),
    ("lesson",    f"{BASE}/lesson-plans.xml"),
    ("coloring",  f"{BASE}/coloring-pages.xml"),
    ("page",      f"{BASE}/page-sitemap.xml"),
]

# ── Main ──────────────────────────────────────────────────────────────────────
def build_cache():
    seen = set()
    all_entries = []

    for content_type, sitemap_url in SITEMAPS:
        entries = crawl_sitemap(sitemap_url, content_type, seen, depth=0)
        all_entries.extend(entries)

    cache = {
        "last_updated": str(date.today()),
        "total":        len(all_entries),
        "by_type": {
            t: sum(1 for e in all_entries if e["type"] == t)
            for t in sorted({e["type"] for e in all_entries})
        },
        "entries": all_entries,
    }

    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

    print(f"\n✅  Cache saved → {CACHE_FILE}")
    print(f"   Total URLs : {len(all_entries)}")
    for t, n in cache["by_type"].items():
        print(f"   {t:<12}: {n}")

if __name__ == "__main__":
    build_cache()
