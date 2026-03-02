---
description: Browse, search, and install shared agents from the team repository
---

# Agent Shared

Duyệt, tìm kiếm, và cài đặt agents từ kho chung của team — không cần biết git.

> **Menu-driven** — chỉ cần chọn số, AI xử lý mọi thao tác file/git.

## Usage
```
/agent-shared
```

## Preflight (silent)

1. **Detect shared repo:**
   - Kiểm tra `../agents-shared/` tồn tại VÀ có thư mục `agents/` bên trong
   - Nếu tìm thấy → set `SHARED_REPO` path, tiếp tục bước 2
   - Nếu KHÔNG tìm thấy → hiển thị:
     ```
     📁 Chưa tìm thấy kho agent chung (agents-shared).

     1. 📥 Clone từ GitHub (cần có URL repo)
     2. 📂 Nhập đường dẫn thủ công
     3. ❌ Huỷ

     Chọn (1-3): ___
     ```
     - **Chọn 1:** Hỏi URL → chạy `git clone <url> ../agents-shared/` → verify `agents/` dir
     - **Chọn 2:** Hỏi path → verify path có `agents/` dir
     - **Chọn 3:** Dừng workflow

2. **Silent git pull:** Cập nhật kho chung (không cần user biết):
   ```bash
   cd <SHARED_REPO> && git pull origin main --quiet 2>/dev/null || true
   ```
   - Nếu pull fail (offline, no remote) → tiếp tục với bản local
   - Ghi nhớ flag `PULL_OK` (true/false) để hiển thị ghi chú nếu cần

3. **Detect local agent dir:** Tìm thư mục cài agent trong project hiện tại:
   - `./agents/` → `.claude/agents/` → `.agent/agents/`
   - Nếu không có → tạo `./agents/`

## Instructions

### Step 1: Main Menu

Hiển thị menu chính:

```
🏪 Agent Shared — Kho agent dùng chung
```
Nếu `PULL_OK = false`:
```
   ⚠️ Không cập nhật được — đang dùng bản local
```
```

1. 📂 Browse  — Xem agents theo nhóm
2. 📥 Install — Cài agent vào project
3. 🔍 Search  — Tìm agent theo từ khoá

Chọn (1-3): ___
```

Chờ user chọn → chuyển sang Step tương ứng.

### Step 2: Browse Agents

#### 2a. Hiển thị danh sách categories

Scan `<SHARED_REPO>/agents/` — mỗi subdirectory là một category.

**7 categories chuẩn:**

| # | Category | Mô tả |
|---|----------|-------|
| 1 | dev | Development (FE, BE, Mobile) |
| 2 | qa | Testing, Review, Audit |
| 3 | ops | Deploy, Infra, Monitoring |
| 4 | data | Analytics, Scraping, Reporting |
| 5 | content | Writing, Editing, Translation |
| 6 | marketing | Campaigns, SEO, Social |
| 7 | general | Cross-team, Utilities |

Đếm số agents (`.md` files) trong mỗi category. Hiển thị:

```
📂 Nhóm agents:

1. dev        — Development           (5 agents)
2. qa         — Testing & Review      (3 agents)
3. ops        — Ops & Infra           (2 agents)
4. data       — Data & Analytics      (4 agents)
5. content    — Content & Writing     (1 agent)
6. marketing  — Marketing             (0 agents)
7. general    — General               (3 agents)
0. ← Quay lại menu

Chọn (0-7): ___
```

- Chọn **0** → quay lại Step 1
- Category có 0 agents → hiển thị "(trống)" và thông báo nếu chọn

#### 2b. Hiển thị agents trong category

Đọc frontmatter của mỗi `.md` file trong `<SHARED_REPO>/agents/<category>/`.

```
📂 dev — Development (5 agents)

#  Name                    Description                          Author    Tags
1. api-endpoint-builder    Build REST API endpoints from spec   hiep      api, rest, backend
2. react-component-gen     Generate React components            minh      react, frontend
3. db-migration-writer     Write database migration scripts     hiep      db, migration
4. unit-test-generator     Auto-generate unit tests             lan       testing, jest
5. docker-setup            Setup Dockerfile and compose         tuan      docker, devops
0. ← Quay lại danh sách nhóm

Chọn agent để xem chi tiết (0-5): ___
```

- Chọn **0** → quay lại Step 2a

#### 2c. Xem chi tiết agent

Đọc file agent, hiển thị frontmatter + preview system prompt (50 dòng đầu):

```
📋 api-endpoint-builder

Name:        api-endpoint-builder
Description: Build REST API endpoints from OpenAPI spec automatically
Author:      hiep
Type:        Implementation 🟢
Tools:       Read, Write, Edit, Glob, Grep
Tags:        api, rest, backend
Field:       backend
Expertise:   expert

--- Preview ---
(Hiển thị 50 dòng đầu của system prompt)
...

1. 📥 Install agent này
2. ← Quay lại danh sách
0. ← Quay lại menu chính

Chọn (0-2): ___
```

- Chọn **1** → chuyển sang Step 3 (Install) với agent đã chọn
- Chọn **2** → quay lại Step 2b
- Chọn **0** → quay lại Step 1

### Step 3: Install Agent

#### 3a. Xác định agent cần cài

- Nếu đến từ Browse (Step 2c) hoặc Search (Step 4) → đã biết agent, tiến hành cài
- Nếu đến từ menu chính → hỏi:
  ```
  📥 Nhập tên agent cần cài (hoặc "browse" để xem danh sách): ___
  ```
  - Nếu gõ "browse" → chuyển sang Step 2
  - Nếu gõ tên → tìm trong `<SHARED_REPO>/agents/**/<name>.md`
  - Không tìm thấy → gợi ý search: "Không tìm thấy '<name>'. Thử tìm kiếm?"

#### 3b. Kiểm tra trùng tên

Kiểm tra `<LOCAL_AGENT_DIR>/<name>.md` đã tồn tại chưa:

- Nếu CHƯA có → copy luôn (bước 3c)
- Nếu ĐÃ có → hỏi:
  ```
  ⚠️ Agent '<name>' đã có trong project.

  1. Ghi đè (overwrite)
  2. Bỏ qua (skip)

  Chọn (1-2): ___
  ```

#### 3c. Copy file

```bash
cp <SHARED_REPO>/agents/<category>/<name>.md <LOCAL_AGENT_DIR>/<name>.md
```

Hiển thị kết quả:

```
✅ Đã cài agent '<name>'
   Từ: agents-shared/<category>/<name>.md
   Vào: <LOCAL_AGENT_DIR>/<name>.md

📥 Cài thêm agent khác?
1. Có — quay lại Browse
2. Không — xong

Chọn (1-2): ___
```

- Chọn **1** → quay lại Step 2a (Browse)
- Chọn **2** → hiển thị tóm tắt và kết thúc

### Step 4: Search Agents

#### 4a. Nhận từ khoá

```
🔍 Nhập từ khoá tìm kiếm: ___
```

#### 4b. Tìm kiếm

Grep case-insensitive qua tất cả `<SHARED_REPO>/agents/**/*.md` — tìm trong cả frontmatter (name, description, tags, author) và body (system prompt).

#### 4c. Hiển thị kết quả

```
🔍 Kết quả cho "<keyword>" — 3 agents tìm thấy:

#  Category   Name                  Description                     Author
1. dev        api-endpoint-builder  Build REST API endpoints...     hiep
2. data       web-scraper           Collect data from websites...   minh
3. general    json-formatter        Format and validate JSON...     lan

Chọn agent để xem chi tiết hoặc cài đặt (0 = quay lại):  ___
```

- Nếu 0 kết quả:
  ```
  🔍 Không tìm thấy agent nào cho "<keyword>".
     Thử từ khoá khác hoặc browse danh sách.

  1. 🔍 Tìm lại
  2. 📂 Browse
  0. ← Quay lại menu

  Chọn (0-2): ___
  ```

- Chọn agent → hiển thị chi tiết (như Step 2c) → option Install hoặc quay lại

## IMPORTANT

- **Không cần git knowledge** — AI xử lý clone, pull, đọc file, copy hoàn toàn tự động
- **Silent pull** — cập nhật kho chung trước khi hiện nội dung, user không cần biết
- **Menu-driven** — user chỉ chọn số (0-7), không gõ lệnh terminal
- **Graceful offline** — pull fail thì dùng bản local, ghi chú "(bản local, có thể chưa cập nhật)"
- **Quay lại dễ dàng** — mọi menu đều có option "0. Quay lại"
- **IDE-agnostic** — hoạt động với Claude Code, Gemini CLI, Antigravity
