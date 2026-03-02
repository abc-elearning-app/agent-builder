# Hướng dẫn sử dụng Agent Factory

## Agent Factory là gì?

Agent Factory giúp bạn **tạo AI agent chỉ bằng 1 câu mô tả** — không cần biết code, không cần config. AI sẽ tự tạo agent, chạy ngay, và bạn có thể góp ý để cải tiến.

Ngoài ra, bạn có thể **duyệt và cài agent** mà team đã tạo sẵn, thông qua lệnh `/agent-shared`.

---

## Cài đặt

Nhờ dev chạy 1 lần trong thư mục project:

```bash
./install.sh
```

Sau khi cài xong, bạn sẽ dùng được 2 lệnh:
- `/agent-factory` — Tạo agent mới
- `/agent-shared` — Duyệt và cài agent từ kho chung

---

## Lệnh 1: Tạo agent mới (`/agent-factory`)

### Cách dùng

Gõ trong AI IDE (Claude Code, Gemini CLI, hoặc Antigravity):

```
/agent-factory "mô tả việc bạn muốn agent làm"
```

### Ví dụ

```
/agent-factory "thu thập tiêu đề và URL bài viết từ VnExpress"
/agent-factory "review code Python và đưa ra gợi ý cải thiện"
/agent-factory "tổng hợp key points từ một tài liệu dài"
/agent-factory "phân tích dữ liệu campaign từ file CSV"
```

### Chuyện gì xảy ra?

1. AI hỏi thêm thông tin nếu mô tả chưa đủ rõ (tối đa 3 câu)
2. AI tự phân loại agent, chọn tools phù hợp
3. AI tạo file agent và chạy ngay
4. Bạn xem kết quả → góp ý → AI cải tiến → chạy lại
5. Khi hài lòng → gõ **"done"**
6. AI hỏi bạn có muốn share agent cho team không

### Mẹo viết mô tả tốt

| Mô tả mơ hồ | Mô tả rõ ràng |
|---|---|
| "tạo agent scraping" | "thu thập tiêu đề, ngày đăng và URL bài viết từ VnExpress" |
| "review code" | "review code Python, tìm lỗi bảo mật và gợi ý cải thiện" |
| "phân tích data" | "phân tích dữ liệu từ file CSV, tìm insight về conversion rate" |

Mô tả càng cụ thể, agent tạo ra càng chính xác.

### Cải tiến agent

Sau khi agent chạy xong, bạn có thể góp ý:

- "thêm trường tác giả" → AI cập nhật agent và chạy lại
- "lọc bài trong 7 ngày gần nhất" → AI cập nhật agent và chạy lại
- "output dạng JSON thay vì bảng" → AI cập nhật agent và chạy lại
- **"done"** → AI lưu agent, hỏi bạn muốn share không

Tối đa 10 lần cải tiến. Sau 5 lần, AI sẽ gợi ý bạn thử mô tả lại từ đầu nếu chưa đúng ý.

### Share agent cho team

Khi gõ "done", AI hỏi:

```
📤 Bạn muốn share agent này cho team không?
   1. Share → Tạo PR vào kho chung
   2. Skip → Giữ local, share sau
```

Chọn **1** → AI tự động: chọn nhóm → copy file → tạo PR trên GitHub.
Bạn không cần biết git — AI lo hết.

---

## Lệnh 2: Cài agent từ kho chung (`/agent-shared`)

### Cách dùng

```
/agent-shared
```

AI hiện menu, bạn chỉ cần chọn số.

### Menu chính

```
🏪 Agent Shared — Kho agent dùng chung

1. 📂 Browse  — Xem agents theo nhóm
2. 📥 Install — Cài agent vào project
3. 🔍 Search  — Tìm agent theo từ khoá

Chọn (1-3): ___
```

### Browse (xem theo nhóm)

Chọn **1** → AI hiện danh sách 7 nhóm:

| # | Nhóm | Dành cho |
|---|------|----------|
| 1 | dev | Development — FE, BE, Mobile |
| 2 | qa | Testing, Review, Audit |
| 3 | ops | Deploy, Infra, Monitoring |
| 4 | data | Data, Scraping, Reporting |
| 5 | content | Writing, Editing, Translation |
| 6 | marketing | Campaigns, SEO, Social |
| 7 | general | Cross-team, Utilities |

Chọn nhóm → xem danh sách agents → chọn agent → xem chi tiết → cài đặt.

Mọi bước đều có **"0. Quay lại"** để trở về menu trước.

### Install (cài đặt)

Chọn **2** → nhập tên agent hoặc browse danh sách.

Nếu agent đã có trong project, AI sẽ hỏi ghi đè hay bỏ qua. Sau khi cài xong, AI hỏi bạn muốn cài thêm không.

### Search (tìm kiếm)

Chọn **3** → nhập từ khoá → AI tìm trong tất cả agents (tên, mô tả, tags, nội dung).

Ví dụ: gõ "scraping" → AI tìm tất cả agents liên quan đến scraping.

---

## 4 loại agent

Agent Factory tự phân loại agent dựa trên mô tả của bạn:

| Loại | Màu | Dành cho | Ví dụ |
|------|-----|----------|-------|
| Strategic | 🔵 xanh dương | Phân tích, nghiên cứu | Phân tích data, so sánh đối thủ |
| Implementation | 🟢 xanh lá | Tạo, thu thập, xây dựng | Scraping, code gen, viết nội dung |
| Quality | 🔴 đỏ | Kiểm tra, review, audit | Code review, test, quét lỗi |
| Coordination | 🟣 tím | Điều phối, quản lý | Pipeline, workflow, phân công |

Bạn không cần nhớ — AI tự chọn loại phù hợp.

---

## Câu hỏi thường gặp

### Tôi không biết code, có dùng được không?

Có. Bạn chỉ cần gõ `/agent-factory "mô tả"` hoặc `/agent-shared` rồi chọn số trong menu. AI xử lý mọi thứ.

### Agent lưu ở đâu?

Trong thư mục `agents/` (hoặc `.claude/agents/`, `.agent/agents/`) của project. Mỗi agent là 1 file `.md`.

### Tôi muốn sửa agent đã tạo?

Mở file agent trong thư mục `agents/` và sửa trực tiếp, hoặc chạy lại `/agent-factory` với mô tả mới.

### Agent có an toàn không?

Agent Factory dùng hệ thống 3 tầng an toàn:
- **Tầng 1 (tự động):** Đọc file, tìm kiếm — không rủi ro
- **Tầng 2 (tự động + cảnh báo):** Ghi file — AI cảnh báo trước
- **Tầng 3 (luôn hỏi):** Chạy lệnh hệ thống — luôn hỏi bạn trước khi thực hiện

### Offline thì sao?

`/agent-factory` hoạt động bình thường (không cần mạng).
`/agent-shared` sẽ dùng bản local nếu không cập nhật được kho chung — AI sẽ ghi chú cho bạn biết.

### Dùng trên IDE nào?

Cả 3 IDE đều hỗ trợ:

| IDE | Lệnh tạo agent | Lệnh duyệt kho |
|-----|-----------------|-----------------|
| Claude Code | `/agent-factory "..."` | `/agent-shared` |
| Gemini CLI | `/agent-factory "..."` | `/agent-shared` |
| Antigravity | `@[/agent-factory] "..."` | `@[/agent-shared]` |
