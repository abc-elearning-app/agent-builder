"""
build_sitemap_cache.py
Dynamically fetches worksheetzone.org sitemaps from the sitemap index
and saves a local URL index for internal linking.

Run once (and re-run when new content is added):
  python3 scripts/build_sitemap_cache.py

Sitemap root:
  sitemap-index.xml  →  122 sub-sitemaps (flat, no nested indexes)

Included sitemaps:
  sitemap-blog.xml                   → ~597  blog posts
  sitemap-coloring-pages-*.xml       → ~13,000 coloring pages + categories
  sitemap-lesson-plan-categories.xml → ~73   lesson plan categories
  sitemap-lesson-plans-*.xml         → ~459  lesson plan pages
  sitemap-pages.xml                  → ~14   static pages
  sitemap-post-categories.xml        → ~20   blog post categories
  sitemap-tools.xml                  → ~27   tool pages
  sitemap-worksheet-categories.xml   → ~24,120 worksheet category pages

Excluded:
  sitemap-authors.xml       → author profile pages (no internal linking value)
  sitemap-worksheets-*.xml  → individual worksheet pages (~97,000, too many for linking)
"""

import json, re, time, urllib.request
from datetime import date
from pathlib import Path

CACHE_FILE  = str(Path(__file__).parent / "wzorg_link_cache.json")
BASE        = "https://worksheetzone.org"
INDEX_URL   = f"{BASE}/sitemap-index.xml"

RETRY_ATTEMPTS = 3
RETRY_DELAY    = 2   # seconds (multiplied by attempt number)

# ── Sitemap inclusion filter ───────────────────────────────────────────────────
def should_include_sitemap(name: str) -> bool:
    """Return True if this sub-sitemap should be crawled."""
    # Skip author profile pages
    if name == "sitemap-authors.xml":
        return False
    # Skip individual worksheet pages — too many (~97k), low linking value per post
    # Note: "sitemap-worksheet-categories.xml" is kept (no trailing 's' before '-categories')
    if re.match(r"sitemap-worksheets-", name):
        return False
    return True

# ── URL type mapping ───────────────────────────────────────────────────────────
def classify(url: str) -> str:
    if "/blog/" in url:              return "blog"
    if "/worksheets/" in url:        return "worksheet"
    if "/coloring-page" in url:      return "coloring"
    if "/coloring-pages/" in url:    return "coloring"
    if "/lesson-plan" in url:        return "lesson"
    if "/category/" in url:          return "category"
    # Tool pages: worksheet makers, generators, search tools
    if re.search(r"-(maker|generator|creator|builder|tool|search|solver|checker)$", url):
        return "tool"
    if "/worksheet-" in url:         return "tool"
    if "printable-lesson-plan" in url: return "lesson"
    if "printable-interactive" in url: return "coloring"
    return "page"

# ── Slug helpers ───────────────────────────────────────────────────────────────
def strip_hash_suffix(slug: str) -> str:
    """Remove trailing 20+ char hex hash from slugs like 'some-title-65b1c94ea8ee2c003ffbb56a'."""
    return re.sub(r"-[0-9a-f]{20,}$", "", slug)

def slug_to_title(url: str) -> str:
    path = url.rstrip("/").split("/")[-1]
    path = strip_hash_suffix(path)
    return path.replace("-", " ").replace("_", " ").title()

def slug_keywords(url: str) -> list:
    path = url.rstrip("/").split("/")[-1]
    path = strip_hash_suffix(path)
    return [w.lower() for w in re.split(r"[-_]", path) if len(w) > 2]

# ── Filters ────────────────────────────────────────────────────────────────────
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
    if "/team-member/" in url or "/author/" in url:
        return False
    # Skip URLs where the hash IS the only identifier (pure hash slug, no descriptive prefix)
    # e.g. /coloring-pages/62a026a2ee7b001ec52eb910 — kept: /some-title-62a026a2ee7b001ec52eb910
    path_segment = url.rstrip("/").split("/")[-1]
    hash_match = re.search(r"-([0-9a-f]{20,})$", path_segment)
    if hash_match:
        prefix = path_segment[:hash_match.start()]
        # Block if there's no meaningful prefix (fewer than 3 real words before the hash)
        words = [w for w in re.split(r"[-_]", prefix) if len(w) > 2]
        if len(words) < 2:
            return False
    return True

# ── Fetcher with retry ─────────────────────────────────────────────────────────
def fetch_xml(url: str) -> str:
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read().decode("utf-8")
        except Exception as e:
            if attempt < RETRY_ATTEMPTS:
                print(f" (retry {attempt}/{RETRY_ATTEMPTS - 1})...", end="", flush=True)
                time.sleep(RETRY_DELAY * attempt)
            else:
                raise

def extract_locs(xml: str) -> list:
    return re.findall(r"<loc>([^<]+)</loc>", xml)

# ── Infer content type from sitemap filename ───────────────────────────────────
def infer_type(sitemap_name: str) -> str:
    if "blog" in sitemap_name:         return "blog"
    if "coloring" in sitemap_name:     return "coloring"
    if "lesson-plan" in sitemap_name:  return "lesson"
    if "tools" in sitemap_name:        return "tool"
    if "categories" in sitemap_name:   return "category"
    if "pages" in sitemap_name:        return "page"
    return "worksheet"

# ── Crawler ────────────────────────────────────────────────────────────────────
def crawl_sitemap(url: str, content_type: str, seen: set) -> list:
    name = url.replace(BASE + "/", "")
    print(f"  → {name} ", end="", flush=True)

    try:
        xml = fetch_xml(url)
        time.sleep(0.1)   # polite crawl
    except Exception as e:
        print(f"ERROR: {e}")
        return []

    locs = extract_locs(xml)
    entries = []
    added = 0
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

# ── Main ───────────────────────────────────────────────────────────────────────
def build_cache():
    print(f"Fetching sitemap index: {INDEX_URL}")
    index_xml = fetch_xml(INDEX_URL)
    all_sitemaps = extract_locs(index_xml)
    print(f"Found {len(all_sitemaps)} sub-sitemaps in index\n")

    included = [s for s in all_sitemaps
                if should_include_sitemap(s.replace(BASE + "/", ""))]
    skipped  = len(all_sitemaps) - len(included)
    print(f"Including: {len(included)} sitemaps | Skipping: {skipped} (authors + individual worksheets)\n")

    seen        = set()
    all_entries = []

    for sitemap_url in included:
        name         = sitemap_url.replace(BASE + "/", "")
        content_type = infer_type(name)
        entries      = crawl_sitemap(sitemap_url, content_type, seen)
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
