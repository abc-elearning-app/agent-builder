---
marp: true
theme: default
paginate: true
backgroundColor: #1a1a2e
color: #eee
style: |
  section {
    font-family: 'Inter', 'Noto Sans', sans-serif;
  }
  h1, h2 { color: #00d2ff; }
  h3 { color: #7b61ff; }
  strong { color: #ffd700; }
  code { background: #16213e; color: #0ff; border-radius: 4px; padding: 2px 6px; }
  table { font-size: 0.85em; }
  th { background: #16213e; color: #00d2ff; }
  td { background: #0f3460; }
  blockquote { border-left: 4px solid #7b61ff; background: #16213e; padding: 10px 20px; }
  a { color: #00d2ff; }
---

# Agent Factory

**Tạo AI agent trong 30 giây — bằng 1 câu mô tả**

<br>

```
/agent-factory "thu thập tiêu đề bài viết từ VnExpress"
```

<br>

> Không cần code. Không cần config. Chạy ngay.

---

## Vấn đề

<br>

### Mỗi team đều cần AI agent, nhưng...

| Cách truyền thống | Thời gian | Ai làm được? |
|---|---|---|
| Viết prompt dài + chọn tools + config YAML | 15-30 phút | Dev |
| Tìm template phù hợp + customize | 10-20 phút | Dev |
| Copy agent cũ + sửa lại | 5-10 phút | Dev |

<br>

**Kết quả:** Chỉ dev mới tạo được agent. Content & Marketing phải chờ.

---

## Giải pháp: Agent Factory

<br>

```
/agent-factory "<mô tả bằng tiếng Việt hoặc English>"
```

<br>

### Workflow tự động:

```
Mô tả → Hỏi lại (nếu thiếu) → Phân loại → Chọn tools → Viết prompt
       → Tạo file → Validate → Chạy ngay → Nhận feedback → Cải tiến
```

<br>

**Ai cũng dùng được** — chỉ cần mô tả việc muốn làm.

---

## Demo: Team Content

```
/agent-factory "thu thập tiêu đề và URL bài viết từ một trang web"
```

### Agent Factory tự động:

1. Phân loại → **Implementation** 🟢
2. Đặt tên → `web-article-collector`
3. Chọn tools → `Read, Glob, Grep, WebFetch, WebSearch`
4. Viết system prompt chuyên biệt
5. **Chạy ngay** → trả kết quả:

| # | Tiêu đề | Ngày | URL |
|---|---------|------|-----|
| 1 | Thị trường bất động sản... | 02/03 | [Link](#) |
| 2 | AI thay đổi ngành giáo dục... | 01/03 | [Link](#) |

---

## Demo: Team Marketing

```
/agent-factory "phân tích dữ liệu campaign từ file CSV,
              tìm insight về conversion rate"
```

### Kết quả:

- Type: **Strategic** 🔵 (phân tích, không sửa data)
- Tools: `Read, Glob, Grep` (an toàn, chỉ đọc)
- Output: báo cáo với key statistics + top insights + anomalies

<br>

> Agent tự biết dùng tool nào, format output phù hợp, xử lý edge cases.

---

## Demo: Team Dev

```
/agent-factory "review code Python và đưa ra gợi ý cải thiện"
```

### Kết quả:

- Type: **Quality** 🔴 (kiểm tra, audit)
- Tools: `Read, Glob, Grep` (read-only review)
- Output: báo cáo theo severity 🔴🟡🟢

```markdown
## Issues Found: 8 (🔴 2 / 🟡 3 / 🟢 3)

🔴 Critical
| File         | Line | Issue              | Fix              |
|--------------|------|--------------------|------------------|
| auth.py      | 42   | SQL injection      | Use parameterized|
| api/users.py | 15   | Hardcoded secret   | Move to .env     |
```

---

## 4 loại agent — tự phân loại

| Type | Dành cho | Tools | Ví dụ |
|------|----------|-------|-------|
| 🔵 **Strategic** | Phân tích, research | Read-only + Web | Phân tích data, so sánh |
| 🟢 **Implementation** | Tạo, thu thập | Read + Write | Scraping, code gen |
| 🔴 **Quality** | Kiểm tra, review | Full access | Code review, audit |
| 🟣 **Coordination** | Điều phối | Lightweight | Pipeline, workflow |

**Tool Safety — 3 tầng:** Safe (auto) → Cautious (auto + warn) → Restricted (luôn hỏi user)

---

## Refinement Loop — cải tiến tức thì

```
✅ Agent hoàn thành. (Iteration 1/10)
Kết quả có đúng ý bạn không?
→ Nếu OK: gõ "done"  |  Nếu cần sửa: mô tả cụ thể
```

### Ví dụ feedback:

- "thêm trường tác giả, lọc bài trong 7 ngày" → cập nhật + chạy lại
- "output dạng JSON thay vì table" → cập nhật + chạy lại
- "done" → ✅ Agent lưu tại `agents/web-article-collector.md`

**Tối đa 10 iterations** — gợi ý restart sau 5, dừng tự động sau 10.

---

## Cài đặt — 1 lệnh

```bash
./install.sh
```

### Hỗ trợ 3 AI IDE cùng lúc:

| IDE | Đường dẫn | Cách gọi |
|-----|-----------|----------|
| **Claude Code** | `.claude/commands/` | `/agent-factory "..."` |
| **Gemini CLI** | `.gemini/commands/` | `/agent-factory "..."` |
| **Antigravity** | `.agent/workflows/` | `@[/agent-factory] "..."` |

<br>

> Cài 1 lần, dùng ở đâu cũng được. Agent tạo ra cũng dùng được trên mọi IDE.

---

## Vấn đề mới: Agent nằm rải rác

<br>

### Mỗi người tạo agent riêng, nhưng...

| Vấn đề | Hệ quả |
|---|---|
| Agent chỉ nằm local | Người khác không biết đã có |
| Nhiều người tạo agent giống nhau | Lãng phí thời gian |
| Không có nơi tập trung | Không tìm được agent cần dùng |
| Không review chất lượng | Agent kém chất lượng lan tràn |

<br>

**Cần:** Một kho agent chung cho toàn công ty.

---

## Giải pháp: `agents-shared` repo

<br>

```
agents-shared/
├── agents/
│   ├── dev/          ← FE, BE, Mobile
│   ├── qa/           ← Testing, Review, Audit
│   ├── ops/          ← Deploy, Infra, Monitoring
│   ├── data/         ← Analytics, Scraping, Reporting
│   ├── content/      ← Writing, Editing, Translation
│   ├── marketing/    ← Campaigns, SEO, Social
│   └── general/      ← Cross-team, Utilities
├── install.sh        ← Cài agent vào project
└── CONTRIBUTING.md   ← Quy trình đóng góp
```

<br>

> Mỗi team có thư mục riêng. Ai cũng có thể đóng góp qua PR.

---

## Publish Flow — tích hợp sẵn trong Agent Factory

<br>

### Sau khi tạo + test xong agent, gõ "done":

```
✅ Agent 'vnexpress-scraper' đã sẵn sàng.
   Saved: agents/vnexpress-scraper.md

📤 Bạn muốn share agent này cho team không?
   1. Share → Tạo PR vào agents-shared repo
   2. Skip → Giữ local, share sau
```

<br>

**Chọn "Share" → Agent Factory tự động:**

Chọn category → Copy file → Tạo branch → Commit → Push → Mở PR

---

## Publish Flow — kết quả

<br>

```
✅ PR created successfully!
   🔗 https://github.com/abc-elearning-app/agents-shared/pull/42
   📁 agents/data/vnexpress-scraper.md
   🏷️ Branch: add/vnexpress-scraper
```

<br>

### PR được review bởi team → merge → agent available cho toàn công ty

<br>

> Không cần biết git. Agent Factory lo hết.

---

## Cài agent từ kho chung: `/agent-shared`

<br>

### Không cần biết git. Chỉ cần chọn số:

```
/agent-shared

🏪 Agent Shared — Kho agent dùng chung

1. 📂 Browse  — Xem agents theo nhóm
2. 📥 Install — Cài agent vào project
3. 🔍 Search  — Tìm agent theo từ khoá
```

<br>

**Browse:** Chọn nhóm → xem agent → cài 1 click
**Search:** Gõ từ khoá → tìm trong toàn bộ kho → cài ngay
**Install:** Tự kiểm tra trùng tên, hỏi overwrite nếu cần

---

## Full workflow

<br>

```
/agent-factory "mô tả"
  → Tạo agent → Chạy ngay → Feedback loop → Done
                                               ↓
                                        Share? (Y/N)
                                               ↓
                              Chọn category → PR → Review → Merge
                                                              ↓
                                                    agents-shared repo
                                                              ↓
                                    Team khác: /agent-shared → Browse → Install
```

<br>

**Từ ý tưởng → agent chạy ngay → share cho cả công ty — trong 1 session.**

---

## Tổng kết

| | Trước | Sau (Agent Factory) |
|---|---|---|
| **Ai tạo được** | Dev only | Ai cũng được |
| **Thời gian** | 30 phút+ | 30 giây |
| **Cần biết gì** | YAML, tools, prompt eng. | Mô tả việc cần làm |
| **Cải tiến** | Sửa file thủ công | Nói "thêm X, bớt Y" |
| **Share** | Copy-paste, hỏi trên Slack | 1 click → PR → team dùng ngay |
| **Tìm agent** | Không biết ai có gì | `/agent-shared` → browse, search, install |

---

<!-- _backgroundColor: #0f3460 -->

# Thử ngay

```bash
./install.sh                                    # Cài vào project
/agent-factory "mô tả việc bạn muốn agent làm"   # Tạo agent mới
/agent-shared                                    # Duyệt kho agent chung
```

**Tạo agent → cải tiến → share → team dùng ngay qua `/agent-shared`**

> Repo: `agent-factory/` | Kho chung: `agents-shared/` | Hướng dẫn: `HUONG-DAN.md`
