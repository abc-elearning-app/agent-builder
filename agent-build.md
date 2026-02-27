---
description: Auto-generate AI agents from natural language descriptions, run immediately, and refine through feedback loop
---

# Agent Build

Tự động tạo AI agent từ mô tả tự nhiên, chạy ngay, và cải tiến qua vòng lặp phản hồi.

> **Standalone tool** — hoạt động trên bất kỳ project nào, không cần CCPM.

## Usage
```
/agent-build <description>
```

**Ví dụ:**
```
/agent-build "thu thập tiêu đề và URL bài viết từ một trang web"
/agent-build "review code Python và đưa ra gợi ý cải thiện"
/agent-build "tổng hợp các key points từ một tài liệu dài"
```

## Preflight (silent)

1. **Kiểm tra description:** Nếu `<description>` rỗng → in usage + ví dụ và dừng.
2. **Detect agent directory:**
   - Nếu `./agents/` tồn tại → dùng `./agents/`
   - Nếu `.claude/agents/` tồn tại → dùng `.claude/agents/`
   - Nếu `.agent/agents/` tồn tại → dùng `.agent/agents/`
   - Không tìm thấy → tạo `./agents/` (default)
3. **Chuẩn bị thư mục:** `mkdir -p <agent_dir> 2>/dev/null`

## Instructions

### Step 1: Clarification Round

Đánh giá description có đủ thông tin không:

**Trigger clarification nếu:**
- Description < 20 words VÀ thiếu ít nhất 1 trong 3: input source, output format, task scope
- Ví dụ mơ hồ: "tạo agent scraping" (thiếu: scrape cái gì? lấy field nào?)
- Ví dụ đủ: "thu thập tiêu đề, ngày đăng và tác giả bài viết từ trang VnExpress" (rõ ràng)

**Nếu cần clarification**, hỏi tối đa 3 câu (nhóm vào 1 message):
```
🔍 Tôi cần thêm thông tin để tạo agent tốt hơn:

1. [Input]: Nguồn dữ liệu là gì? (URL cụ thể, loại file, hay text?)
2. [Output]: Kết quả mong muốn có format gì? (list, JSON, markdown table?)
3. [Scope]: Có constraint nào không? (chỉ read, giới hạn số lượng?)

Hoặc nếu bạn muốn tôi tự quyết → gõ "proceed"
```

**Nếu đủ thông tin** → skip clarification, proceed ngay.

### Step 1.5: Type Classification

Auto-detect agent type từ description bằng keyword matching (xem **Agent Type Reference** bên dưới).

1. Scan description (lowercase) → đếm keyword matches cho mỗi type
2. Nếu 1 type dẫn đầu rõ ràng → assign type + color tự động:
   ```
   🏷️ Agent type: Implementation 🟢
      Color: green (auto-assigned)
   ```
3. Nếu tie hoặc 0 matches hoặc description < 5 words → hỏi fallback question (xem Agent Type Reference)
4. Set `detected_type` và `detected_color` cho các step sau

**Lưu ý:** Step này tối đa hỏi 1 câu (fallback question). Nếu Step 1 đã hỏi clarification → tổng cộng ≤ 4 câu hỏi.

### Step 2: Learn Agent Format

1. **Check existing agents:** Glob `<agent_dir>/*.md` — nếu tìm được → đọc file đầu tiên làm format reference
2. **Check examples:** Nếu không có agents → tìm `examples/*.md` ở project root, đọc 1 file mẫu
3. **Minimal fallback:** Nếu không có gì → dùng built-in format:
   ```yaml
   ---
   name: {name}
   description: {description}
   tools: {tools}
   model: inherit
   color: {detected_color}
   field: {detected_field}
   expertise: expert
   ---
   ```

### Step 3: Generate Agent

#### 3a. Đặt tên agent
- Tạo kebab-case name ngắn gọn (2-4 words) từ description
- Chỉ dùng `[a-z0-9-]`, không có số đầu, không kết thúc bằng `-`
- Ví dụ: "thu thập bài viết VnExpress" → `vnexpress-article-collector`
- Ví dụ: "review code Python" → `python-code-reviewer`

**Kiểm tra trùng tên:** Nếu `<agent_dir>/<name>.md` đã tồn tại:
```
⚠️ Agent '<name>' đã tồn tại. Overwrite? (yes / rename to <name>-2)
```
Chờ user xác nhận trước khi tiếp tục.

#### 3b. Chọn tools (type-aware + 3-tier safety)

**Base 3-tier model:**

| Tier | Tools | Rule |
|------|-------|------|
| **Safe** (auto) | `Read, Glob, Grep, LS, WebFetch, WebSearch` | Mặc định |
| **Cautious** (auto + warn) | `Write, Edit, NotebookEdit` | Khi cần write |
| **Restricted** (hỏi user) | `Bash, Task, Agent` | Luôn hỏi |

**Type-based recommendation** (từ Step 1.5):

```
ℹ️ Agent type: {detected_type} {emoji}
   Recommended tools: {tools_from_type_matrix}
   {warning nếu có, ví dụ: "⚠️ Quality agents chạy sequential only"}

   Dùng recommended tools? (yes / custom)
```

**Type → Tools override:**
- **Strategic 🔵:** Safe only → `Read, Glob, Grep, WebFetch, WebSearch` (no Write/Bash)
- **Implementation 🟢:** Safe + Cautious auto → `Read, Write, Edit, Glob, Grep` + ask Bash
- **Quality 🔴:** Safe + Cautious + Bash auto → `Read, Write, Edit, Bash, Glob, Grep` ⚠️ sequential only
- **Coordination 🟣:** Lightweight → `Read, Glob, Grep` + ask Task/Agent

**Nếu user chọn "custom":** Hiện 3-tier table, cho user chọn manual. Nếu user thêm Bash vào Strategic → warn nhưng cho phép.

#### 3c. Viết system prompt

Viết một system prompt chất lượng cao cho agent:
- **Role:** Mô tả rõ vai trò chuyên biệt (không generic)
  - ✅ "Bạn là chuyên gia phân tích bảo mật code Python"
  - ❌ "Bạn là một AI assistant hữu ích"
- **Quy trình:** Steps rõ ràng, đánh số, mỗi bước 2-3 câu, nêu tool nào dùng
- **Input/Output:** Format cụ thể (JSON, table, list)
- **Edge cases:** Xử lý khi không tìm thấy data, lỗi kết nối, etc.
- **Output format:** Cấu trúc rõ ràng

**YAML frontmatter phải có:**
```yaml
---
name: {kebab-case-name}
description: {action-oriented, ≥10 words}
tools: {comma-separated}
model: inherit
color: {detected_color}
field: {detected_field}       # optional: frontend|backend|testing|security|data|ai|...
expertise: expert             # optional: beginner|intermediate|expert
---
```

**Auto-detect `field`:**
- Code-related keywords → `backend` / `frontend` / `fullstack`
- Test/review keywords → `testing`
- Security keywords → `security`
- Data/scrape keywords → `data`
- AI/ML keywords → `ai`
- Không match → bỏ qua field (optional)

#### 3d. Tạo file agent

Tạo `<agent_dir>/<name>.md` theo format đã học.

**Sau khi tạo, hiển thị:**
```
📝 Agent created: <agent_dir>/<name>.md
   Name: <name>
   Type: <detected_type> <emoji>
   Tools: <comma-separated list>
   Field: <field> | Expertise: <expertise>
   Description: <1-line summary>

Đang khởi chạy agent...
```

#### 3e. Validate (3-step)

Sau khi tạo file, chạy validation trước khi execute:

**Step V1: Name validation**
- Regex: `^[a-z0-9][a-z0-9-]*[a-z0-9]$`
- Length: 3-40 chars, no double hyphens (`--`)
- **Auto-fix:** uppercase → lowercase, spaces → hyphens

**Step V2: YAML validation**
- Required fields: `name`, `description`, `tools`, `model`, `color`
- `tools` phải là comma-separated string (không phải array)
- `model` hợp lệ: `sonnet` | `opus` | `haiku` | `inherit`
- `color` hợp lệ: `blue` | `green` | `red` | `purple` | `orange`
- **Auto-fix:** missing `color` → assign từ type; missing `model` → `inherit`

**Step V3: Description quality** (warn only, không block)
- ≥ 10 words
- Không generic: reject "An agent that..." / "A tool for..."
- Nên mô tả WHEN to invoke, không chỉ WHAT it does
- **Nếu fail:** warn + suggest improvement, nhưng vẫn tiếp tục

**Output validation:**
```
✅ Validation passed (3/3)
   V1 Name: code-security-scanner ✅
   V2 YAML: 5/5 required fields ✅
   V3 Description: 12 words ✅
```

### Step 4: Immediate Execution

Spawn agent vừa tạo bằng Task tool hoặc browser subagent (tuỳ IDE).

**Prompt cho agent:** Dựa trên description gốc + context rõ ràng từ user.

**Nếu agent fail:**
```
❌ Agent gặp lỗi: <error message>

Nguyên nhân có thể:
- Thiếu quyền truy cập URL/file
- Tool không phù hợp cho task
- System prompt cần điều chỉnh

→ Mô tả lỗi để tôi sửa agent
```
Không tiếp tục loop nếu agent crash — fix trước.

### Step 5: Refinement Loop

Sau khi agent hoàn thành và hiển thị kết quả:

```
✅ Agent hoàn thành. (Iteration {N}/10)

Kết quả có đúng ý bạn không?
- Nếu OK → gõ "done" — agent đã lưu tại <agent_dir>/<name>.md
- Nếu cần cải tiến → mô tả cụ thể cần sửa gì
  (ví dụ: "thêm trường tác giả", "lọc bài trong 7 ngày", "output dạng JSON")
```

**Khi nhận feedback:**
1. Cập nhật agent definition (overwrite `<agent_dir>/<name>.md`) theo feedback
2. Hiển thị tóm tắt thay đổi: "Đã cập nhật: [list changes]"
3. Re-spawn agent với cùng task
4. Loop

**Giới hạn iterations:**
- Sau iteration **5**: thêm gợi ý:
  ```
  💡 Đã qua 5 lần cải tiến. Nếu agent vẫn chưa đúng ý,
     thử mô tả lại từ đầu: /agent-build "<mô tả mới rõ hơn>"
  ```
- Sau iteration **10**: dừng tự động:
  ```
  ⚠️ Đã đạt giới hạn 10 iterations. Agent hiện tại lưu tại <agent_dir>/<name>.md
     Để tiếp tục, chạy: /agent-build "<mô tả mới>"
  ```

**Khi user gõ "done":**
```
✅ Agent '<name>' đã sẵn sàng.
   Saved: <agent_dir>/<name>.md
   Tools: <tools>

Để chạy lại agent sau: /agent-build "<description gốc>"
Để chỉnh sửa thủ công: Edit <agent_dir>/<name>.md
```

## IMPORTANT

- **Auto-detect agent dir** — tìm `./agents/`, `.claude/agents/`, `.agent/agents/` trước khi tạo mới
- **Type-aware** — auto-detect type → color + tools recommendation
- **Tool safety first** — không tự động thêm Bash/Task/Agent
- **Overwrite on refinement** — mỗi iteration ghi đè file, không tạo versions
- **Fail fast** — nếu agent crash, fix trước khi loop
- **IDE-agnostic** — hoạt động với Antigravity, Claude Code, hoặc bất kỳ AI IDE nào hỗ trợ workflow

## Agent Type Reference

### 4 Agent Types

| Type | Color | Default Tools | Parallel | Use Case |
|------|-------|---------------|----------|----------|
| **Strategic** | 🔵 blue | `Read, Glob, Grep, WebFetch, WebSearch` | ✅ 4-5 agents | Planning, research, analysis |
| **Implementation** | 🟢 green | `Read, Write, Edit, Glob, Grep` + ask Bash | ⚠️ 2-3 agents | Code writing, building |
| **Quality** | 🔴 red | `Read, Write, Edit, Bash, Glob, Grep` | ❌ Sequential only | Testing, review, audit |
| **Coordination** | 🟣 purple | `Read, Glob, Grep` | ✅ Lightweight | Orchestration, delegation |

### Keyword → Type Mapping

**Strategic** 🔵 (planning, research, analysis — no code execution):
`plan`, `research`, `analyze`, `design`, `architect`, `strategy`, `brainstorm`, `evaluate`, `assess`, `compare`
Vietnamese: `lập kế hoạch`, `nghiên cứu`, `phân tích`, `thiết kế`, `đánh giá`, `so sánh`, `tổng hợp`, `chiến lược`

**Implementation** 🟢 (build, create, write — code execution):
`build`, `create`, `implement`, `develop`, `write code`, `generate`, `scrape`, `collect`, `fetch`, `extract`
Vietnamese: `tạo`, `xây dựng`, `phát triển`, `thu thập`, `viết`, `lấy dữ liệu`, `crawl`, `gom`

**Quality** 🔴 (test, validate, review — heavy execution):
`test`, `review`, `audit`, `check`, `validate`, `lint`, `scan`, `verify`, `inspect`, `benchmark`
Vietnamese: `kiểm tra`, `đánh giá`, `rà soát`, `audit`, `review`, `test`, `xác minh`, `quét`

**Coordination** 🟣 (orchestrate, manage — lightweight):
`orchestrate`, `coordinate`, `manage`, `delegate`, `pipeline`, `workflow`, `dispatch`, `route`, `schedule`, `batch`
Vietnamese: `điều phối`, `quản lý`, `phân công`, `lập lịch`, `điều hướng`

### Auto-detect Logic

```
1. Scan description (lowercase) for keywords in each type
2. Count matches per type
3. If 1 type has most matches → assign that type (confidence = matches/total_keywords)
4. If tie between 2+ types → prefer Implementation (safest default)
5. If 0 matches OR confidence < 50% → fallback question
6. If description < 5 words → always fallback question
```

**Fallback question:**
```
🔍 Tôi chưa xác định được loại agent. Agent này thuộc loại nào?

1. 🔵 Strategic — Lập kế hoạch, nghiên cứu, phân tích (không viết code)
2. 🟢 Implementation — Tạo, xây dựng, thu thập dữ liệu (viết code/files)
3. 🔴 Quality — Kiểm tra, review, audit (chạy tests, validate)
4. 🟣 Coordination — Điều phối, quản lý workflow (nhẹ, không code)

Chọn (1-4): ___
```

### Tool Access Decision Matrix

| Tool | Strategic 🔵 | Implementation 🟢 | Quality 🔴 | Coordination 🟣 |
|------|:-----------:|:-----------------:|:---------:|:---------------:|
| Read | ✅ auto | ✅ auto | ✅ auto | ✅ auto |
| Glob | ✅ auto | ✅ auto | ✅ auto | ✅ auto |
| Grep | ✅ auto | ✅ auto | ✅ auto | ✅ auto |
| WebFetch | ✅ auto | ✅ auto | ❌ | ❌ |
| WebSearch | ✅ auto | ✅ auto | ❌ | ❌ |
| Write | ❌ | ✅ auto | ✅ auto | ❌ |
| Edit | ❌ | ✅ auto | ✅ auto | ❌ |
| Bash | ❌ | ⚠️ ask | ✅ auto | ❌ |
| Task | ❌ | ❌ | ❌ | ⚠️ ask |
| Agent | ❌ | ❌ | ❌ | ⚠️ ask |
