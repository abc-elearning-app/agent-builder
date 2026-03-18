"""
create_schema_doc.py
Scans a live blog post for existing JSON-LD schema, identifies missing entities
(BreadcrumbList, FAQPage, ItemList), generates only the missing markup, and
uploads an audit Google Doc.

Usage:
  python3 scripts/create_schema_doc.py \
      --url <post_url> \
      --title <post_title> \
      --author <author_name> \
      --folder-id <gdrive_folder_id>

Outputs (stdout): Google Doc URL
"""

import argparse
import json
import re
import sys
import urllib.request
import warnings
from datetime import date
from pathlib import Path

warnings.filterwarnings("ignore")

SCRIPTS_DIR        = Path(__file__).parent
TOKEN_FILE         = SCRIPTS_DIR.parent / "oauth_token.pickle"
SCHEMA_CONFIG_FILE = SCRIPTS_DIR / "wzorg_schema_config.json"
SITE_URL           = "https://worksheetzone.org"


# ── Auth ──────────────────────────────────────────────────────────────────────

def load_creds():
    import pickle
    with open(TOKEN_FILE, "rb") as f:
        creds = pickle.load(f)
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
    return creds


# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch_raw_html(url: str) -> str:
    """Fetch raw HTML — preserves <script> blocks needed for schema extraction."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        raise RuntimeError(f"Fetch failed: {e}")


# ── Schema extraction ─────────────────────────────────────────────────────────

def extract_existing_schema(html: str) -> tuple:
    """
    Parse all JSON-LD <script> blocks.
    Returns (set_of_@types, list_of_raw_entity_dicts).
    """
    found_types    = set()
    found_entities = []

    blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE
    )
    for block in blocks:
        try:
            data  = json.loads(block.strip())
            graph = data.get("@graph", [data])
            if not isinstance(graph, list):
                graph = [graph]
            for entity in graph:
                t = entity.get("@type")
                if not t:
                    continue
                # @type can be a string or a list in WordPress JSON-LD
                types = t if isinstance(t, list) else [t]
                for typ in types:
                    found_types.add(typ)
                found_entities.append(entity)
        except json.JSONDecodeError:
            pass

    return found_types, found_entities


# ── Metadata extraction ───────────────────────────────────────────────────────

def _meta_tag(html: str, attr: str, name: str) -> str:
    """Extract a <meta> tag value by attribute name."""
    for pattern in [
        rf'<meta[^>]+{attr}=["\'][^"\']*{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+{attr}=["\'][^"\']*{re.escape(name)}["\']',
    ]:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def extract_metadata(html: str, url: str, existing_entities: list) -> dict:
    """
    Build a metadata dict from existing JSON-LD entities (priority 1),
    HTML meta tags (priority 2), and H1 (priority 3).
    """
    meta = {
        "url": url, "headline": "", "description": "",
        "keywords": "", "date_published": "", "date_modified": "",
        "image": "", "author_name": "", "category_name": "", "category_url": "",
    }

    for entity in existing_entities:
        t = entity.get("@type", "")

        if t in ("BlogPosting", "Article", "NewsArticle"):
            meta["headline"]       = meta["headline"]       or entity.get("headline", "")
            meta["description"]    = meta["description"]    or entity.get("description", "")
            meta["keywords"]       = meta["keywords"]       or entity.get("keywords", "")
            meta["date_published"] = meta["date_published"] or entity.get("datePublished", "")
            meta["date_modified"]  = meta["date_modified"]  or entity.get("dateModified", "")
            img = entity.get("image", "")
            if isinstance(img, dict):
                img = img.get("url", "")
            meta["image"] = meta["image"] or (img if isinstance(img, str) else "")
            author = entity.get("author", {})
            if isinstance(author, dict):
                meta["author_name"] = meta["author_name"] or author.get("name", "")
            elif isinstance(author, str):
                meta["author_name"] = meta["author_name"] or author

        elif t == "BreadcrumbList":
            items = entity.get("itemListElement", [])
            if len(items) >= 2:
                second = items[1] if isinstance(items[1], dict) else {}
                meta["category_name"] = meta["category_name"] or second.get("name", "")
                meta["category_url"]  = meta["category_url"]  or second.get("item", "")

        elif t in ("WebPage",):
            meta["headline"] = meta["headline"] or entity.get("name", "")

    # Fallback: HTML meta tags
    meta["headline"]    = meta["headline"]    or _meta_tag(html, "property", "og:title")    or _meta_tag(html, "name", "title")
    meta["description"] = meta["description"] or _meta_tag(html, "property", "og:description") or _meta_tag(html, "name", "description")
    meta["image"]       = meta["image"]       or _meta_tag(html, "property", "og:image")

    # Fallback: H1
    if not meta["headline"]:
        m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
        if m:
            meta["headline"] = re.sub(r"<[^>]+>", "", m.group(1)).strip()

    return meta


# ── Article type detection ────────────────────────────────────────────────────

def detect_article_type(headline: str) -> str:
    """Return 'listicle' or 'knowledge'."""
    h = headline.lower().strip()
    listicle_patterns = [
        r"^\d+[\+\s]",
        r"^(top|best|worst|greatest|most)\s+\d+",
        r"^\d+\s+(ways|tips|tricks|ideas|activities|reasons|examples|types|"
        r"tools|resources|facts|games|poems|jokes|quotes|books|strategies|"
        r"techniques|methods|things|signs|steps|questions)",
    ]
    for p in listicle_patterns:
        if re.search(p, h):
            return "listicle"
    return "knowledge"


# ── FAQ extraction ────────────────────────────────────────────────────────────

def extract_faq_pairs(html: str) -> list:
    """
    Extract Q&A pairs from the FAQ section.

    WordPress wraps heading text in inline tags like <b> and <span>, so the
    FAQ heading appears as e.g. <h2><b>Frequently Asked Questions (FAQ)</b></h2>.
    We iterate over all h2/h3 tags, strip their inner HTML, then match on plain
    text — this is robust to any inline tag nesting inside headings.
    """
    pairs = []

    # Step 1: locate the FAQ heading by stripping inner HTML from each h2/h3
    faq_start_pos = None
    for m in re.finditer(r'<h[23][^>]*>(.*?)</h[23]>', html, re.DOTALL | re.IGNORECASE):
        heading_text = re.sub(r'<[^>]+>', '', m.group(1)).strip().lower()
        if 'frequently asked' in heading_text or re.match(r'^faq[\s\b(]', heading_text):
            faq_start_pos = m.end()
            break

    if faq_start_pos is None:
        return pairs

    faq_html = html[faq_start_pos:]

    # Step 2: split into chunks at each h3/h4 (the individual questions)
    # .*? with DOTALL handles <b>/<span> tags inside the heading
    chunks = re.split(r'(<h[34][^>]*>.*?</h[34]>)', faq_html, flags=re.DOTALL | re.IGNORECASE)

    i = 1  # index 0 is text before the first question heading
    while i < len(chunks) - 1:
        heading_raw = chunks[i]
        body_raw    = chunks[i + 1]

        # Strip all inner HTML tags to get the plain question text
        question = re.sub(r'<[^>]+>', '', heading_raw).strip()
        question = re.sub(r'^(Q:|Question:)\s*', '', question, flags=re.IGNORECASE).strip()

        # Stop if we've drifted out of the FAQ section
        if re.search(r'^(references|conclusion|summary|related|see also)', question, re.IGNORECASE):
            break

        # Answer: first <p> block after the heading (strip inner tags like <span>)
        p_match = re.search(r'<p[^>]*>(.*?)</p>', body_raw, re.DOTALL | re.IGNORECASE)
        if p_match:
            answer = re.sub(r'<[^>]+>', '', p_match.group(1)).strip()
            answer = re.sub(r'\s+', ' ', answer)
            if question and answer and len(answer) > 10:
                pairs.append({"question": question, "answer": answer[:600]})

        i += 2

    return pairs[:6]


# ── Listicle item extraction ──────────────────────────────────────────────────

def extract_listicle_items(html: str, url: str) -> list:
    """
    Extract the actual list items for ItemList schema.

    Strategy:
      1. Isolate the main article body (after H1, before FAQ/References).
      2. PRIMARY: collect <li> elements — these are the real enumerated items.
         Extract a concise name from "Label: description..." patterns.
      3. FALLBACK: if fewer than 3 <li> items found, use H3 headings instead
         (some listicles use H3 per item rather than bullet points).

    H2 headings are deliberately NOT used — they are section groupings, not items.
    """
    items = []

    # Isolate body: after the first </h1>, before the FAQ or References section
    # Also need to handle inner HTML in headings (e.g. <h2><b>FAQ</b></h2>)
    body_start = re.search(r'</h1>', html, re.IGNORECASE)
    faq_start  = None
    for m in re.finditer(r'<h[23][^>]*>(.*?)</h[23]>', html, re.DOTALL | re.IGNORECASE):
        t = re.sub(r'<[^>]+>', '', m.group(1)).strip().lower()
        if re.search(r'frequently asked|^faq[\s(]|^references$|^conclusion$|^summary$', t):
            faq_start = m.start()
            break

    body_html = html[
        (body_start.end() if body_start else 0) :
        (faq_start if faq_start else len(html))
    ]

    # ── Primary: <li> items ────────────────────────────────────────────────────
    raw_lis = re.findall(r'<li[^>]*>(.*?)</li>', body_html, re.DOTALL | re.IGNORECASE)
    for li_html in raw_lis:
        text = re.sub(r'<[^>]+>', '', li_html)          # strip all tags
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&#\d+;|&\w+;', '', text)        # strip remaining entities
        text = re.sub(r'\s+', ' ', text).strip()

        # Skip navigation/UI items (too short, or contain CSS/JS artefacts)
        if len(text) < 15 or re.search(r'@media|\.v4-|javascript', text):
            continue

        # Extract a concise name: take the part before the first colon or
        # first sentence boundary, capped at 80 chars
        colon_idx = text.find(':')
        if 0 < colon_idx < 80:
            name = text[:colon_idx].strip()
        else:
            name = text[:80].strip()
            # Trim at last word boundary if cut mid-word
            if len(text) > 80 and ' ' in name:
                name = name.rsplit(' ', 1)[0]

        if not name:
            continue

        items.append({"position": len(items) + 1, "name": name, "url": url})
        if len(items) >= 10:
            break

    # ── Fallback: H3 headings (for listicles structured as one H3 per item) ───
    if len(items) < 3:
        items = []
        skip = re.compile(
            r'^(introduction|overview|conclusion|summary|references|'
            r'what is|why|how to|about|faq|frequently)',
            re.IGNORECASE
        )
        h3s = re.findall(r'<h3[^>]*>(.*?)</h3>', body_html, re.DOTALL | re.IGNORECASE)
        for h in h3s:
            text = re.sub(r'<[^>]+>', '', h)
            text = re.sub(r'&amp;', '&', text)
            text = re.sub(r'\s+', ' ', text).strip()
            if not text or skip.match(text):
                continue
            items.append({"position": len(items) + 1, "name": text, "url": url})
            if len(items) >= 10:
                break

    return items


# ── Schema builder ────────────────────────────────────────────────────────────

def build_missing_entities(
    existing_types: set,
    meta: dict,
    config: dict,
    article_type: str,
    faq_pairs: list,
    listicle_items: list,
) -> list:
    """Return only the schema entities that are absent and required."""
    url      = meta["url"]
    entities = []

    # BreadcrumbList — always required
    if "BreadcrumbList" not in existing_types:
        category_name = meta["category_name"] or "Blog"
        category_url  = meta["category_url"]  or config["category_map"].get(
            category_name, f"{SITE_URL}/blog"
        )
        entities.append({
            "@type": "BreadcrumbList",
            "@id":   f"{url}#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home",         "item": SITE_URL},
                {"@type": "ListItem", "position": 2, "name": category_name,  "item": category_url},
                {"@type": "ListItem", "position": 3, "name": meta["headline"], "item": url},
            ],
        })

    # FAQPage — only when FAQ content is present
    if "FAQPage" not in existing_types and faq_pairs:
        entities.append({
            "@type": "FAQPage",
            "@id":   f"{url}#faq",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name":  pair["question"],
                    "acceptedAnswer": {"@type": "Answer", "text": pair["answer"]},
                }
                for pair in faq_pairs
            ],
        })

    # ItemList — only for listicles
    if "ItemList" not in existing_types and article_type == "listicle" and listicle_items:
        entities.append({
            "@type": "ItemList",
            "@id":   f"{url}#itemlist",
            "itemListElement": [
                {
                    "@type":    "ListItem",
                    "position": item["position"],
                    "name":     item["name"],
                    "url":      item["url"],
                }
                for item in listicle_items
            ],
        })

    return entities


# ── Doc content builder ───────────────────────────────────────────────────────

def build_doc_text(
    url: str,
    existing_types: set,
    missing_entities: list,
    faq_pairs: list,
    article_type: str,
) -> str:
    """Compose the plain-text content for the schema audit Google Doc."""
    lines = [
        "Schema Markup Audit",
        f"URL: {url}",
        f"Date: {date.today().isoformat()}",
        f"Article type: {article_type}",
        "",
        "━━━ Already Present in WordPress ━━━",
    ]

    if existing_types:
        for t in sorted(existing_types):
            lines.append(f"  ✅ {t}")
    else:
        lines.append("  (none detected)")

    lines += ["", "━━━ Missing — Added Below ━━━"]

    if missing_entities:
        for e in missing_entities:
            note = f" ({len(faq_pairs)} Q&A pairs)" if e["@type"] == "FAQPage" else ""
            lines.append(f"  ➕ {e['@type']}{note}")
        lines += [
            "",
            "━━━ Paste This Into Your WordPress Page ━━━",
            "",
            '<script type="application/ld+json">',
            json.dumps(
                {"@context": "https://schema.org", "@graph": missing_entities},
                indent=2, ensure_ascii=False
            ),
            "</script>",
        ]
    else:
        lines.append("  ✅ Nothing missing — all required schema already present")

    return "\n".join(lines)


# ── Google Doc creation ───────────────────────────────────────────────────────

def create_schema_doc(text_content: str, title: str, folder_id: str, creds) -> str:
    """Create a plain-text Google Doc and return its URL."""
    from googleapiclient.discovery import build as gbuild

    docs_svc  = gbuild("docs",  "v1", credentials=creds)
    drive_svc = gbuild("drive", "v3", credentials=creds)

    doc    = docs_svc.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]

    docs_svc.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": [
            {"insertText": {"location": {"index": 1}, "text": text_content}}
        ]},
    ).execute()

    drive_svc.files().update(
        fileId=doc_id,
        addParents=folder_id,
        removeParents="root",
        fields="id, parents",
    ).execute()

    drive_svc.permissions().create(
        fileId=doc_id,
        body={"role": "reader", "type": "anyone"},
    ).execute()

    return f"https://docs.google.com/document/d/{doc_id}/edit"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Schema markup generator for worksheetzone.org blog posts")
    parser.add_argument("--url",       required=True, help="Blog post URL")
    parser.add_argument("--title",     required=True, help="Post title (used for doc naming)")
    parser.add_argument("--author",    default="",    help="Author display name (optional hint)")
    parser.add_argument("--folder-id", required=True, help="Google Drive folder ID")
    args = parser.parse_args()

    print(f"  [schema] Fetching {args.url}", file=sys.stderr)
    html = fetch_raw_html(args.url)

    print("  [schema] Scanning existing JSON-LD ...", file=sys.stderr)
    existing_types, existing_entities = extract_existing_schema(html)
    print(f"  [schema] Found: {', '.join(sorted(existing_types)) or 'none'}", file=sys.stderr)

    meta = extract_metadata(html, args.url, existing_entities)
    if not meta["headline"] and args.title:
        meta["headline"] = args.title

    article_type   = detect_article_type(meta["headline"])
    faq_pairs      = extract_faq_pairs(html)
    listicle_items = extract_listicle_items(html, args.url) if article_type == "listicle" else []

    print(f"  [schema] Article type : {article_type}", file=sys.stderr)
    print(f"  [schema] FAQ pairs    : {len(faq_pairs)}", file=sys.stderr)
    if listicle_items:
        print(f"  [schema] Listicle items: {len(listicle_items)}", file=sys.stderr)

    config  = json.loads(SCHEMA_CONFIG_FILE.read_text(encoding="utf-8"))
    missing = build_missing_entities(existing_types, meta, config, article_type, faq_pairs, listicle_items)

    if missing:
        print(f"  [schema] Missing types: {', '.join(e['@type'] for e in missing)}", file=sys.stderr)
    else:
        print("  [schema] All required schema already present", file=sys.stderr)

    doc_text = build_doc_text(args.url, existing_types, missing, faq_pairs, article_type)
    doc_title = f"{args.title} — Schema Markup"

    creds   = load_creds()
    doc_url = create_schema_doc(doc_text, doc_title, args.folder_id, creds)
    print(f"  [schema] Doc: {doc_url}", file=sys.stderr)
    print(doc_url)


if __name__ == "__main__":
    main()
