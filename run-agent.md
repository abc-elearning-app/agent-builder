---
description: Chọn agent trên máy và chạy ngay với task cụ thể — không cần nhớ tên chính xác
---

# Run Agent

Xem danh sách agents đã cài, tìm kiếm theo từ khoá, chọn và chạy ngay — không cần nhớ tên.

> **Quick launcher** — gõ số để chọn, nhập task, AI tự spawn agent.

## Usage
```
/run-agent
```

## Preflight (silent)

**Detect local agent dir:** Tìm theo thứ tự:
- `./agents/` → `.claude/agents/` → `.agent/agents/`
- Nếu không tìm thấy hoặc rỗng → báo và gợi ý tạo mới

## Instructions

### Step 1: Hiển thị danh sách

Scan `<LOCAL_AGENT_DIR>` — đọc frontmatter mỗi `.md` file (name, description, color/type, tags).

Map color → type emoji:
- `blue` → 🔵 Strategic
- `green` → 🟢 Implementation
- `red` → 🔴 Quality
- `purple` → 🟣 Coordination
- Không có → ⚪

Hiển thị:

```
🤖 Agents trên máy — <LOCAL_AGENT_DIR> (<N> agents)

#   Type  Name                              Description
1.  🟢    ai-cli-launcher                   Tạo shell script macOS mở Terminal
2.  ⚪    code-analyzer                     Phân tích code changes tìm bugs
3.  ⚪    file-analyzer                     Analyze và tóm tắt nội dung file
4.  🔴    flutter-maestro-test-generator    Generate Maestro YAML test flows
5.  🟢    gcloud-datastore-reader           Query Google Cloud Datastore
6.  🔵    gold-price-forecaster             Dự báo giá vàng từ dữ liệu SJC
7.  🔵    hanoi-weather-forecast            Thu thập dự báo thời tiết Hà Nội
8.  🟢    mac-node-installer                Kiểm tra và cài Node.js trên macOS
9.  🟢    mb-lottery-special-prize-collector Thu thập kết quả xổ số Miền Bắc
10. 🟣    parallel-worker                   Thực thi parallel work streams
11. 🔴    test-runner                       Chạy tests và phân tích kết quả

Gõ số để chọn, hoặc tìm kiếm: ___
```

**Nếu 0 agents:**
```
📭 Chưa có agent nào trên máy.
   Tạo agent mới: /agent-factory "<mô tả>"
   Cài từ kho chung: /agent-shared
```

### Step 2: Xử lý input

**Nếu user gõ số** (ví dụ: `7`) → load agent đó, chuyển sang Step 3.

**Nếu user gõ từ khoá** (không phải số) → filter danh sách:
- Tìm case-insensitive trong name, description, tags của mỗi agent
- Hiển thị lại danh sách đã lọc với số mới:
  ```
  🔍 Kết quả cho "weather" — 1 agent:

  #   Type  Name                    Description
  1.  🔵    hanoi-weather-forecast  Thu thập dự báo thời tiết Hà Nội

  Gõ số để chọn, hoặc tìm lại: ___
  ```
- Nếu 0 kết quả:
  ```
  🔍 Không tìm thấy agent nào cho "<keyword>".
     Thử từ khoá khác, hoặc xem toàn bộ danh sách: gõ "all"
  ```

**Nếu user gõ `"all"`** → hiện lại danh sách đầy đủ (Step 1).

**Nếu user gõ `"0"` hoặc `"q"`** → thoát.

### Step 3: Xem chi tiết + nhận task

Đọc file agent, hiển thị thông tin ngắn:

```
🤖 hanoi-weather-forecast

Mô tả:  Thu thập dự báo thời tiết Hà Nội cho ngày mai từ Google Search
Loại:   🔵 Strategic
Tools:  Read, Glob, Grep, WebSearch, WebFetch
Tags:   weather, hanoi, forecast

Bạn muốn làm gì? (Enter để dùng mặc định, hoặc mô tả task cụ thể): ___
```

**Nếu user nhấn Enter (không nhập gì)** → dùng description của agent làm task prompt.

**Nếu user nhập task cụ thể** → dùng task đó làm prompt.

### Step 4: Spawn agent

Spawn agent vừa chọn bằng Task tool với prompt đã xác định ở Step 3.

```
⚡ Đang khởi chạy hanoi-weather-forecast...
```

Sau khi agent hoàn thành, hỏi:

```
✅ Xong.

Chạy agent khác?
1. Chọn agent khác — quay lại danh sách
2. Chạy lại agent này — với task khác
0. Thoát

Chọn (0-2): ___
```

- Chọn **1** → quay lại Step 1
- Chọn **2** → quay lại Step 3 (giữ nguyên agent đang chọn)
- Chọn **0** → thoát

## IMPORTANT

- **Không cần nhớ tên chính xác** — gõ keyword để filter, gõ số để chọn
- **Enter để dùng mặc định** — không cần nhập task nếu description đã đủ rõ
- **Spawn ngay** — không có bước confirm thêm sau khi chọn task
- **IDE-agnostic** — hoạt động với Claude Code, Gemini CLI, Antigravity
