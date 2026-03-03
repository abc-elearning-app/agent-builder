# 🤖 Agent Factory

> Tự động tạo AI agent từ mô tả tự nhiên — chạy ngay, cải tiến qua feedback loop.

**Standalone tool** — hoạt động trên bất kỳ project nào, không cần CCPM hay framework khác.

## Quick Start

### 1. Cài đặt

```bash
# Copy workflow vào project của bạn
./install.sh

# Hoặc thủ công:
mkdir -p .agent/workflows/
cp agent-factory.md .agent/workflows/
```

### 2. Sử dụng

3 lệnh chính — dùng trên Claude Code, Gemini CLI, hoặc Antigravity:

| Lệnh | Mục đích |
|------|----------|
| `/agent-factory "..."` | Tạo agent mới từ mô tả |
| `/agent-shared` | Duyệt, cài và đẩy agent lên kho chung |
| `/run-agent` | Chạy nhanh agent đã có trên máy |

#### `/agent-factory` — Tạo agent mới

```
/agent-factory "thu thập tiêu đề và URL bài viết từ một trang web"
/agent-factory "review code Python và đưa ra gợi ý cải thiện"
/agent-factory "tổng hợp các key points từ một tài liệu dài"
```

Tool sẽ:
1. 🔍 Phân tích mô tả → xác định loại agent
2. 🏗️ Generate agent definition (YAML + system prompt)
3. 🚀 Chạy agent ngay lập tức
4. 🔄 Hỏi feedback → cải tiến → chạy lại (refinement loop)
5. 📤 Hỏi có muốn share lên kho chung không

Agent file được lưu tại `./agents/<name>.md` — sẵn sàng dùng lại.

#### `/agent-shared` — Kho agent dùng chung

Menu-driven, chọn số để thao tác:

```
1. 📂 Browse  — Xem agents theo nhóm (dev, qa, ops, data, content, marketing, general)
2. 📥 Install — Cài agent vào project hiện tại
3. 🔍 Search  — Tìm agent theo từ khoá
4. 📤 Push    — Đẩy agent của bạn lên kho chung (tạo PR tự động)
```

Kho chung: [`abc-elearning-app/agents-shared`](https://github.com/abc-elearning-app/agents-shared). Auto-clone lần đầu, silent pull mỗi lần mở.

> **Lưu ý:** Agent push lên qua PR — phải được admin review và merge vào `main` thì mới available cho team.

#### `/run-agent` — Chạy agent nhanh

Liệt kê agents trên máy, filter theo từ khoá, chọn số, nhập task và spawn ngay:

```
🤖 Agents trên máy — .claude/agents/ (12 agents)

#    Type  Name                    Description
1.   🟢    hanoi-weather-forecast  Thu thập dự báo thời tiết Hà Nội
2.   🔴    code-analyzer           Phân tích code changes tìm bugs
...

Gõ số để chọn, hoặc tìm kiếm: ___
```

## Agent Types

| Type | Color | Use Case |
|------|-------|----------|
| 🔵 Strategic | blue | Research, planning, analysis |
| 🟢 Implementation | green | Code writing, data collection |
| 🔴 Quality | red | Testing, review, audit |
| 🟣 Coordination | purple | Orchestration, workflow management |

Type được auto-detect từ mô tả — hỗ trợ cả tiếng Anh và tiếng Việt.

## Tool Safety

Agent Factory áp dụng hệ thống 3-tier bảo vệ:

| Tier | Tools | Hành vi |
|------|-------|---------|
| ✅ Safe | Read, Glob, Grep, WebFetch, WebSearch | Auto-enable |
| ⚠️ Cautious | Write, Edit | Enable + cảnh báo |
| 🔒 Restricted | Bash, Task, Agent | Phải hỏi user |

## Agent Directory

Tool tự động detect agent directory theo thứ tự:
1. `./agents/` (default)
2. `.claude/agents/` (CCPM projects)
3. `.agent/agents/` (Antigravity projects)

## Examples

Xem thư mục [`examples/`](examples/) để tham khảo 3 agent mẫu:
- `web-scraper.md` — Thu thập dữ liệu từ web
- `code-reviewer.md` — Review code tìm bugs & anti-patterns
- `data-analyzer.md` — Phân tích dữ liệu có cấu trúc

## License

MIT
