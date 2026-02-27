# 🤖 Agent Builder

> Tự động tạo AI agent từ mô tả tự nhiên — chạy ngay, cải tiến qua feedback loop.

**Standalone tool** — hoạt động trên bất kỳ project nào, không cần CCPM hay framework khác.

## Quick Start

### 1. Cài đặt

```bash
# Copy workflow vào project của bạn
./install.sh

# Hoặc thủ công:
mkdir -p .agent/workflows/
cp agent-build.md .agent/workflows/
```

### 2. Sử dụng

Trong Antigravity (hoặc bất kỳ AI IDE hỗ trợ workflows):

```
@[/agent-build] "thu thập tiêu đề và URL bài viết từ một trang web"
@[/agent-build] "review code Python và đưa ra gợi ý cải thiện"
@[/agent-build] "tổng hợp các key points từ một tài liệu dài"
```

### 3. Kết quả

Tool sẽ:
1. 🔍 Phân tích mô tả → xác định loại agent
2. 🏗️ Generate agent definition (YAML + system prompt)
3. 🚀 Chạy agent ngay lập tức
4. 🔄 Hỏi feedback → cải tiến → chạy lại (refinement loop)

Agent file được lưu tại `./agents/<name>.md` — sẵn sàng dùng lại.

## Agent Types

| Type | Color | Use Case |
|------|-------|----------|
| 🔵 Strategic | blue | Research, planning, analysis |
| 🟢 Implementation | green | Code writing, data collection |
| 🔴 Quality | red | Testing, review, audit |
| 🟣 Coordination | purple | Orchestration, workflow management |

Type được auto-detect từ mô tả — hỗ trợ cả tiếng Anh và tiếng Việt.

## Tool Safety

Agent Builder áp dụng hệ thống 3-tier bảo vệ:

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
