"""
optimize_post.py
Optimizes a blog post using Gemini CLI or Claude with:
  - Temperature 0.3 (consistent structure, varied phrasing)
  - Strict format contract (Option B)
  - Rotating expertise signal phrases (prevents uniformity across 500+ posts)
  - Verified internal links injected from local sitemap cache

Usage:
  python3 scripts/optimize_post.py \
    --input  /tmp/original.md \
    --output /tmp/optimized.md \
    --url    https://worksheetzone.org/blog/post-slug \
    --writer gemini|claude
"""

import argparse, random, re, subprocess, sys, json
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))
from find_internal_links import find_links

# ── Rotating expertise signal phrase pool ─────────────────────────────────────
# 4 groups × 4 variants = 16 phrases.
# Each post gets 2 phrases drawn from different groups → ~144 unique combinations.

EXPERTISE_PHRASES = {
    "classroom_setting": [
        "In a classroom setting, this works best when students encounter the words in context before being asked to memorise definitions.",
        "Across the classrooms we have observed, introducing these terms through short reading passages before drilling definitions produces the strongest retention.",
        "Based on our classroom experience, students grasp these distinctions faster when teachers model one example aloud before asking learners to work independently.",
        "Teachers we have worked with consistently report that pairing this content with a quick think-pair-share warm-up measurably improves participation.",
    ],
    "common_mistakes": [
        "A common mistake students make is treating all items in this category as interchangeable — to address this, ask them to substitute one for another in a sentence and notice whether the meaning shifts.",
        "One pitfall learners often encounter is skipping the examples and jumping straight to the list — the fix is to require them to write one original sentence per term before moving on.",
        "We have noticed that beginners frequently confuse the more formal variants with their everyday equivalents; the clearest way to address this is through side-by-side sentence comparisons.",
        "Students regularly underestimate how much context shapes meaning here — a practical solution is to present each term in two contrasting sentences so the nuance becomes visible.",
    ],
    "recommendations": [
        "We recommend pairing this material with a short writing prompt so students apply the vocabulary immediately rather than passively reading the list.",
        "For best results, we suggest combining this resource with a peer-review activity where students highlight each other's word choices — accountability accelerates retention.",
        "In our practice, supplementing this content with a simple sorting game (positive / negative / neutral) yields the strongest outcomes for students who are visual learners.",
        "We have found that giving students a personal connection task — asking them to link each word to a memory or a person they know — significantly deepens long-term recall.",
    ],
    "curriculum_context": [
        "From a curriculum standpoint, this content aligns well with vocabulary acquisition standards that call for learning words in rich semantic networks rather than in isolation.",
        "In our experience reviewing curriculum maps, the most effective placement for this type of content is immediately after a reading unit, when students have fresh contextual exposure.",
        "Educators following a structured literacy approach will find this material slots naturally into the word study block, particularly at the morphology and semantics stage.",
        "When we map this content against Common Core ELA vocabulary standards, it most directly supports the strand on acquiring and using grade-appropriate general academic words.",
    ],
}


def pick_expertise_phrases() -> tuple[str, str]:
    """Pick 2 phrases from 2 different groups — ensures variety per post."""
    groups = list(EXPERTISE_PHRASES.keys())
    chosen_groups = random.sample(groups, 2)
    phrase_a = random.choice(EXPERTISE_PHRASES[chosen_groups[0]])
    phrase_b = random.choice(EXPERTISE_PHRASES[chosen_groups[1]])
    return phrase_a, phrase_b


# ── Format contract ───────────────────────────────────────────────────────────

FORMAT_CONTRACT = """
OUTPUT STRUCTURE — follow this order exactly, every time:
1. # [H1 title — preserve the original title word for word]
2. [Opening paragraph — sapo, 40–60 words, answers the title, defines the key term, names the audience]
3. [Body sections — preserve the exact number and hierarchy of H2/H3 headings from the original; only rewrite heading text when Rule 3 requires it]
4. [Comparison table — only if the post covers multiple categories AND no table exists yet]
5. ## Frequently Asked Questions
   [Exactly 4 Q&A pairs in this format:]
   ### Q: [question derived from the post content]
   [40–80 word self-contained answer]
6. ## References
   [Only include this section if Rule 4 added at least one citation; omit entirely otherwise]

FORMATTING RULES:
- Use clean markdown only: # H1, ## H2, ### H3, - bullet, 1. numbered, | table |
- No HTML comments, no annotation markers, no GEO-EDIT tags, no meta-commentary
- Bold key terms with **double asterisks** where it aids readability
- Every markdown table must have a separator row (|---|---|)
""".strip()


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_link_candidates(content: str, post_url: str) -> str:
    """
    Run one find_links query per H2 section heading (plus the post title),
    collect unique candidates, and return a structured block for the prompt.

    Each candidate line includes type + score + matched_on so the AI can
    apply the No-Reach Rule, intent-type matching, and the 1% doubt rule.
    """
    title_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
    headings    = re.findall(r"^##\s+(.+)", content, re.MULTILINE)

    queries = []
    if title_match:
        queries.append(title_match.group(1).strip())
    queries.extend(h.strip() for h in headings[:6])   # up to 6 H2 sections

    seen_urls  = {post_url}
    candidates = []

    for q in queries:
        try:
            results = find_links(q, exclude_url=post_url, top_n=8)
            for r in results:
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    candidates.append(r)
        except Exception as e:
            print(f"  ⚠️  find_links failed for query '{q[:50]}': {e}", file=sys.stderr)
            break  # don't repeat for every query if cache is missing

    if not candidates:
        return "(no candidates found)"

    lines = []
    for c in candidates[:20]:   # hard cap: 20 candidates total
        matched = ",".join(c.get("matched_on", []))
        lines.append(
            f"- type:{c['type']} score:{c['score']} "
            f"[{c['title']}]({c['url']}) matched:{matched}"
        )
    return "\n".join(lines)


def build_prompt(content: str, post_url: str) -> str:
    # 1. Find verified internal links (per-section queries)
    links_block = build_link_candidates(content, post_url)

    # 2. Pick rotating expertise phrases
    phrase_a, phrase_b = pick_expertise_phrases()

    return f"""You are a GEO editor for Worksheetzone.org. Apply the 10 GEO optimization rules to the blog post below.

CONSISTENCY INSTRUCTION: Follow the OUTPUT STRUCTURE below with strict discipline on every run — same section order, same heading levels, same FAQ format. For narrative prose (sapo, paragraph openers, expertise signals) use natural, varied phrasing rather than repeating fixed templates. Structure must be identical across posts; sentence-level wording must feel human and fresh.

CRITICAL OUTPUT RULES:
1. Return ONLY the complete optimized blog post — no annotations, no HTML comments, no explanations.
2. Preserve the author's voice. Make the minimum change needed for each rule. Never rewrite a sentence that already meets the criteria.
3. For Rule 9 (expertise signals), insert these two sentences exactly as written, placed naturally in two separate body sections — do not cluster them together:
   Sentence A: "{phrase_a}"
   Sentence B: "{phrase_b}"
4. For Rule 10 (internal links), you MUST ONLY use URLs from the VERIFIED CANDIDATES below. Do not invent, guess, or modify any URL. Insert fewer links rather than force an unnatural one.

{FORMAT_CONTRACT}

VERIFIED INTERNAL LINK CANDIDATES (use only these for Rule 10):
Each line: type:<intent> score:<relevance> [Title](URL) matched:<keywords>
{links_block}

GEO OPTIMIZATION RULES:
Rule 1 - Sapo: Rewrite the opening paragraph only if needed so it answers the title in sentence 1, contains an explicit "X is..." definition, names the target audience, is 40-60 words, and does not open with meta-commentary. Leave unchanged if it already passes all five.
Rule 2 - Paragraph opening sentences: Rewrite only the first sentence of each body paragraph if it lacks a direct declarative statement, a concrete detail (grade level / time / quantity / named framework), or is not independently meaningful out of context. Leave all other sentences untouched.
Rule 3 - Headings: Leave specific descriptive headings unchanged. Rewrite vague label-style headings (Benefits, Tips, Overview) to be specific. Add an H3 for sections over 300 words that have no subheading.
Rule 4 - In-text citations: For any statistic, research finding, or curriculum standard already in the post, search for the authoritative source and embed a verified markdown link. Append a ## References section. Flag unverifiable claims as [VERIFY: description].
Rule 5 - Definitions: For each key term's first mention lacking a nearby definition, insert one sentence "A [term] is..." under 25 words. Do not touch surrounding text.
Rule 6 - Inline lists to structured lists: Convert sentences packing 3 or more items in running text into bulleted or numbered lists. Keep the lead-in sentence.
Rule 7 - Comparison table: Add a markdown table only if the post covers multiple categories AND no table already exists. Max 3-5 columns.
Rule 8 - FAQ: If no FAQ exists, append exactly 4 Q&A pairs as specified in the OUTPUT STRUCTURE above. If FAQ exists, audit: adjust answers outside 40-80 words; do not replace existing questions.
Rule 9 - Expertise signals: Insert the two sentences provided above (Sentence A and Sentence B) into separate body sections where they fit naturally.
Rule 10 - Internal links: From VERIFIED CANDIDATES above, embed 3-5 links in paragraph/body text only — never inside headings. Apply all of these checks before placing each link:
  a) Intent match: type:tool → anchor must contain "maker/generator/builder/creator"; type:worksheet or type:category → anchor must be "worksheets/printables/resources"; type:blog → anchor must be an informational phrase ("tips/strategies/how to/ideas")
  b) No-Reach Rule: never link a broad anchor to a narrow URL. Invalid: "activities" → /blog/100th-day-of-school-ideas. Valid: "activities" → /worksheets or /blog/ela-activities
  c) Semantic fit: replace the anchor mentally with its definition — if the sentence breaks, reject the link
  d) Context check: 3 words before and after must be instructional (practice/students/use/try/download). Reject if context is conversational (however/also/by the way)
  e) 1% doubt rule: any uncertainty → skip. Accuracy is 100x more important than density
  Hard cap: 5 new links. Never modify or remove existing links.

ORIGINAL POST:
{content}"""


# ── Run optimizer ─────────────────────────────────────────────────────────────

def run_gemini(prompt: str, output_path: str):
    result = subprocess.run(
        ["gemini", "-p", prompt],
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        raise RuntimeError(f"Gemini error: {result.stderr[:500]}")
    # Strip Gemini CLI header lines (e.g. "Loaded cached credentials.")
    output = re.sub(r"^Loaded cached credentials\.\s*\n", "", result.stdout, flags=re.MULTILINE)
    with open(output_path, "w") as f:
        f.write(output)


def run_claude(prompt: str, output_path: str):
    result = subprocess.run(
        ["claude", "--model", "claude-opus-4-5", "-p", prompt],
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        raise RuntimeError(f"Claude error: {result.stderr[:500]}")
    with open(output_path, "w") as f:
        f.write(result.stdout)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  required=True, help="Path to original markdown file")
    parser.add_argument("--output", required=True, help="Path to save optimized markdown")
    parser.add_argument("--url",    required=True, help="Post URL (used to exclude self from links)")
    parser.add_argument("--writer", required=True, choices=["gemini", "claude"])
    args = parser.parse_args()

    content = Path(args.input).read_text(encoding="utf-8")
    prompt  = build_prompt(content, args.url)

    print(f"  Writer  : {args.writer}", file=sys.stderr)
    print(f"  Temp    : prompt-controlled (consistency instruction + rotating phrases)", file=sys.stderr)
    print(f"  Input   : {len(content):,} chars", file=sys.stderr)

    if args.writer == "gemini":
        run_gemini(prompt, args.output)
    else:
        run_claude(prompt, args.output)

    output_size = Path(args.output).stat().st_size
    print(f"  Output  : {output_size:,} chars → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
