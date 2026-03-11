"""
find_internal_links.py
Local TF-IDF-weighted link finder against the cached worksheetzone.org URL index.

Usage:
  python3 scripts/find_internal_links.py "query text" [exclude_url] [top_n]

Returns JSON list of {url, title, type, score, matched_on}.
Zero tokens, instant.
"""
import sys, json, re, math
from collections import Counter

CACHE_FILE = "/Users/dangluu/Projects/agent-factory/scripts/wzorg_link_cache.json"

STOP_WORDS = {
    "a","an","the","and","or","but","in","on","at","to","for","of","with",
    "by","from","is","are","was","were","be","been","that","this","it",
    "as","not","have","has","had","do","does","did","will","would","could",
    "should","may","might","can","so","if","than","then","when","how",
    "what","which","who","its","our","your","their","we","you","they",
    "he","she","his","her","all","any","each","more","also","into",
    "about","after","before","up","down","out","over","under","very",
    "just","no","yes","get","got","use","used","using","make","makes",
    "made","take","takes","took","give","gives","gave","help","helps",
    "way","ways","time","need","work","works","new","best","top","great",
}


def tokenize(text: str) -> list:
    tokens = re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 2]


def url_tokens(entry: dict) -> list:
    """Extract tokens from every segment of the URL path (not just slug)."""
    path = entry["url"].replace("https://worksheetzone.org", "").strip("/")
    raw = re.sub(r"[^a-z0-9 ]", " ", path.replace("/", " ").replace("-", " ").lower()).split()
    return [t for t in raw if t not in STOP_WORDS and len(t) > 2]


def build_idf(entries: list) -> dict:
    """
    Compute inverse document frequency for each token across the full URL corpus.
    Rare terms (like 'thanksgiving') score high; common terms ('activities') score low.
    """
    N = len(entries)
    df = Counter()
    for entry in entries:
        tokens = set(url_tokens(entry))
        for t in tokens:
            df[t] += 1
    return {t: math.log(N / (1 + df[t])) for t in df}


def find_links(query: str, exclude_url: str = "", top_n: int = 5) -> list:
    with open(CACHE_FILE) as f:
        cache = json.load(f)

    entries = cache["entries"]
    idf = build_idf(entries)

    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    # Compute weighted query vector
    query_tf = Counter(query_tokens)
    query_vec = {t: query_tf[t] * idf.get(t, 0) for t in query_tf}

    results = []
    for entry in entries:
        url = entry["url"]
        if exclude_url and url == exclude_url:
            continue

        doc_tokens = url_tokens(entry)
        if not doc_tokens:
            continue

        doc_tf = Counter(doc_tokens)
        doc_vec = {t: doc_tf[t] * idf.get(t, 0) for t in doc_tf}

        # Cosine similarity
        common = set(query_vec) & set(doc_vec)
        if not common:
            continue

        dot = sum(query_vec[t] * doc_vec[t] for t in common)
        norm_q = math.sqrt(sum(v ** 2 for v in query_vec.values()))
        norm_d = math.sqrt(sum(v ** 2 for v in doc_vec.values()))

        if norm_q == 0 or norm_d == 0:
            continue

        score = dot / (norm_q * norm_d)

        results.append({
            "url":        url,
            "title":      entry["title"],
            "type":       entry["type"],
            "score":      round(score, 4),
            "matched_on": sorted(common),
        })

    # Sort by score descending
    results.sort(key=lambda x: (-x["score"], x["url"]))

    # Deduplicate: avoid returning multiple URLs that differ only by
    # a suffix letter (e.g. adjectives-that-start-with-a/b/c/d...)
    # Keep the single highest-scoring one per "topic root"
    seen_roots = set()
    deduped = []
    for r in results:
        slug = r["url"].rstrip("/").split("/")[-1]
        # Root = slug with trailing single letter stripped (e.g. "adjectives-that-start-with-a" → "adjectives-that-start-with")
        root = re.sub(r"-[a-z]$", "", slug)
        if root not in seen_roots:
            seen_roots.add(root)
            deduped.append(r)
        if len(deduped) >= top_n:
            break

    return deduped


if __name__ == "__main__":
    query   = sys.argv[1] if len(sys.argv) > 1 else ""
    exclude = sys.argv[2] if len(sys.argv) > 2 else ""
    top_n   = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    results = find_links(query, exclude, top_n)
    print(json.dumps(results, indent=2))
