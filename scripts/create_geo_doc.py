"""
create_geo_doc.py
Helper script for geo-blog-post-optimizer agent.
Usage: python3 create_geo_doc.py <markdown_file> <doc_title> <folder_id>
Outputs: Google Doc URL
"""
import sys, re, io, pickle, warnings
warnings.filterwarnings("ignore")

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

TOKEN_FILE = "/Users/dangluu/Projects/agent-factory/oauth_token.pickle"


# ── 1. Markdown → HTML ────────────────────────────────────────────────────────

def markdown_to_html(md: str) -> str:
    lines = md.split("\n")
    out = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # ── Table block ──────────────────────────────────────────────────────
        if re.match(r"^\s*\|", line):
            table_lines = []
            while i < len(lines) and re.match(r"^\s*\|", lines[i]):
                table_lines.append(lines[i])
                i += 1
            # Filter out separator rows (---|---|---)
            data_rows = [l for l in table_lines
                         if not re.match(r"^\s*\|[\s\-\|:]+\|\s*$", l)]
            if data_rows:
                out.append("<table>")
                for row_i, row in enumerate(data_rows):
                    cells = [c.strip() for c in row.strip().strip("|").split("|")]
                    tag = "th" if row_i == 0 else "td"
                    out.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in cells) + "</tr>")
                out.append("</table>")
            continue

        # ── Headings ─────────────────────────────────────────────────────────
        m = re.match(r"^(#{1,4})\s+(.+)", line)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # ── Unordered list item ───────────────────────────────────────────────
        if re.match(r"^[-*]\s+", line):
            out.append("<ul>")
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i]):
                content = re.sub(r"^[-*]\s+", "", lines[i])
                out.append(f"<li>{inline(content)}</li>")
                i += 1
            out.append("</ul>")
            continue

        # ── Ordered list item ─────────────────────────────────────────────────
        if re.match(r"^\d+\.\s+", line):
            out.append("<ol>")
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i]):
                content = re.sub(r"^\d+\.\s+", "", lines[i])
                out.append(f"<li>{inline(content)}</li>")
                i += 1
            out.append("</ol>")
            continue

        # ── Blank line ────────────────────────────────────────────────────────
        if not line.strip():
            out.append("")
            i += 1
            continue

        # ── Regular paragraph ─────────────────────────────────────────────────
        out.append(f"<p>{inline(line)}</p>")
        i += 1

    body = "\n".join(out)
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>{body}</body></html>"


def inline(text: str) -> str:
    """Convert inline markdown (bold, italic, links, code) to HTML."""
    # Strip HTML comments (GEO-EDIT annotations)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Links [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Italic
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    # Inline code
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text.strip()


# ── 2. Strip annotation comments from raw markdown ────────────────────────────

def strip_comments(md: str) -> str:
    """Remove all <!-- ... --> comments Gemini may have added."""
    return re.sub(r"<!--.*?-->", "", md, flags=re.DOTALL).strip()


# ── 3. Ensure FAQ section exists ──────────────────────────────────────────────

def has_faq(md: str) -> bool:
    return bool(re.search(r"(FAQ|Frequently Asked Questions)", md, re.IGNORECASE))


# ── 4. Create Google Doc from HTML ────────────────────────────────────────────

def create_doc(html: str, title: str, folder_id: str, creds) -> str:
    drive = build("drive", "v3", credentials=creds)
    file_metadata = {
        "name": title,
        "mimeType": "application/vnd.google-apps.document",
        "parents": [folder_id],
    }
    media = MediaIoBaseUpload(
        io.BytesIO(html.encode("utf-8")),
        mimetype="text/html",
        resumable=False,
    )
    file = drive.files().create(
        body=file_metadata, media_body=media, fields="id"
    ).execute()
    doc_id = file["id"]

    # Make readable by anyone with link
    drive.permissions().create(
        fileId=doc_id,
        body={"role": "reader", "type": "anyone"},
    ).execute()

    return doc_id


# ── 5. Apply black 0.5pt borders to every table in the doc ───────────────────

def apply_table_borders(doc_id: str, creds):
    docs = build("docs", "v1", credentials=creds)
    doc = docs.documents().get(documentId=doc_id).execute()
    content = doc.get("body", {}).get("content", [])

    border = {
        "color": {"color": {"rgbColor": {"red": 0, "green": 0, "blue": 0}}},
        "width": {"magnitude": 0.5, "unit": "PT"},
        "dashStyle": "SOLID",
    }

    requests = []
    for elem in content:
        if "table" not in elem:
            continue
        table_start = elem["startIndex"]
        for row_i, row in enumerate(elem["table"].get("tableRows", [])):
            for col_i in range(len(row.get("tableCells", []))):
                requests.append({
                    "updateTableCellStyle": {
                        "tableRange": {
                            "tableCellLocation": {
                                "tableStartLocation": {"index": table_start},
                                "rowIndex": row_i,
                                "columnIndex": col_i,
                            },
                            "rowSpan": 1,
                            "columnSpan": 1,
                        },
                        "tableCellStyle": {
                            "borderLeft":   border,
                            "borderRight":  border,
                            "borderTop":    border,
                            "borderBottom": border,
                        },
                        "fields": "borderLeft,borderRight,borderTop,borderBottom",
                    }
                })

    if requests:
        docs.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()
        print(f"  Applied borders to {len(requests)} table cells", file=sys.stderr)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 create_geo_doc.py <markdown_file> <doc_title> <folder_id>")
        sys.exit(1)

    md_file, title, folder_id = sys.argv[1], sys.argv[2], sys.argv[3]

    with open(md_file, encoding="utf-8") as f:
        md = f.read()

    # Clean up
    md = strip_comments(md)

    # Warn if FAQ missing (should not happen with updated prompt)
    if not has_faq(md):
        print("WARNING: No FAQ section found in optimized content.", file=sys.stderr)

    # Convert to HTML
    html = markdown_to_html(md)

    # Load OAuth credentials
    with open(TOKEN_FILE, "rb") as f:
        import pickle
        creds = pickle.load(f)

    # Create doc
    doc_id = create_doc(html, title, folder_id, creds)
    print(f"  Doc created: {doc_id}", file=sys.stderr)

    # Apply table borders
    apply_table_borders(doc_id, creds)

    # Output the final URL
    print(f"https://docs.google.com/document/d/{doc_id}/edit")


if __name__ == "__main__":
    main()
