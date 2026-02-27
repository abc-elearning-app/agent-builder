# Hướng Dẫn Cài Đặt — Email Support Automation

> Dành cho người chưa biết gì về code. Đọc từng bước, không bỏ qua bước nào.

---

## Tổng quan

Script này tự động đọc email hỗ trợ trong Gmail, dùng AI để trả lời tự động hoặc báo về Discord để bạn tự phản hồi.

**Bạn cần chuẩn bị 3 thứ:**
1. **Anthropic API Key** — để AI đọc và xử lý email
2. **Gmail API Credentials** — để script truy cập Gmail của bạn
3. **Discord Webhook URL** — để nhận thông báo khi có email cần xử lý thủ công

---

## Bước 1 — Cài Python

Python là ngôn ngữ lập trình mà script sử dụng.

### Kiểm tra xem máy đã có Python chưa

Mở **Terminal** (Mac) hoặc **Command Prompt** (Windows):
- **Mac:** nhấn `Cmd + Space`, gõ `Terminal`, Enter
- **Windows:** nhấn `Win + R`, gõ `cmd`, Enter

Gõ lệnh sau rồi Enter:
```
python3 --version
```

- Nếu thấy `Python 3.10.x` trở lên → **đã có, bỏ qua bước này**
- Nếu thấy lỗi → **cần cài**

### Cài Python (nếu chưa có)

1. Truy cập: **https://www.python.org/downloads/**
2. Nhấn nút **Download Python 3.x.x** (chọn bản mới nhất)
3. Chạy file vừa tải
4. **QUAN TRỌNG (Windows):** Tick chọn ô **"Add Python to PATH"** trước khi nhấn Install
5. Nhấn **Install Now**
6. Sau khi xong, mở lại Terminal/Command Prompt và kiểm tra lại: `python3 --version`

---

## Bước 2 — Lấy Anthropic API Key

API Key là "chìa khóa" để script gọi AI của Anthropic.

1. Truy cập: **https://console.anthropic.com/**
2. Đăng ký tài khoản (hoặc đăng nhập nếu đã có)
3. Sau khi đăng nhập, nhấn vào **"API Keys"** ở menu bên trái
4. Nhấn **"Create Key"**
5. Đặt tên bất kỳ (ví dụ: `email-support`)
6. **Copy key vừa tạo** — key có dạng `sk-ant-api03-...`
7. Lưu key này lại, sẽ dùng ở Bước 5

> ⚠️ Key này như mật khẩu, đừng chia sẻ cho ai.

---

## Bước 3 — Tạo Gmail API Credentials

Đây là phần phức tạp nhất. Làm theo từng bước, không bỏ qua.

### 3.1 — Tạo project trên Google Cloud

1. Truy cập: **https://console.cloud.google.com/**
2. Đăng nhập bằng tài khoản Google (tài khoản chứa Gmail hỗ trợ)
3. Ở thanh trên cùng, nhấn vào ô dropdown **"Select a project"** → nhấn **"New Project"**
4. Đặt tên project, ví dụ: `email-support-bot`
5. Nhấn **"Create"**
6. Đợi vài giây, sau đó chọn project vừa tạo trong dropdown

### 3.2 — Bật Gmail API

1. Ở menu bên trái, nhấn **"APIs & Services"** → **"Library"**
2. Trong ô tìm kiếm, gõ `Gmail API`
3. Nhấn vào kết quả **"Gmail API"**
4. Nhấn nút **"Enable"** (Bật)
5. Đợi vài giây cho đến khi trang chuyển sang

### 3.3 — Cấu hình màn hình đồng ý (OAuth Consent Screen)

1. Ở menu bên trái, nhấn **"APIs & Services"** → **"OAuth consent screen"**
2. Chọn **"External"** → nhấn **"Create"**
3. Điền thông tin:
   - **App name:** `Email Support Bot` (gõ tùy ý)
   - **User support email:** chọn email của bạn
   - **Developer contact information:** nhập email của bạn
4. Nhấn **"Save and Continue"**
5. Trang **Scopes:** nhấn **"Save and Continue"** (không cần thêm gì)
6. Trang **Test users:**
   - Nhấn **"+ Add Users"**
   - Nhập địa chỉ Gmail hỗ trợ (email mà script sẽ đọc)
   - Nhấn **"Add"**
7. Nhấn **"Save and Continue"** → **"Back to Dashboard"**

### 3.4 — Tạo OAuth Credentials

1. Ở menu bên trái, nhấn **"APIs & Services"** → **"Credentials"**
2. Nhấn **"+ Create Credentials"** → chọn **"OAuth client ID"**
3. Ở **"Application type"**, chọn **"Desktop app"**
4. Đặt tên bất kỳ, ví dụ: `Email Bot Desktop`
5. Nhấn **"Create"**
6. Popup hiện ra → nhấn **"Download JSON"**
7. File tải về có tên dạng `client_secret_xxx.json`
8. **Đổi tên file thành `gmail_credentials.json`**
9. **Copy file này vào thư mục `email-automation/`** (cùng chỗ với `email_automation.py`)

---

## Bước 4 — Tạo Discord Webhook

Webhook là địa chỉ để script gửi thông báo vào kênh Discord của bạn.

1. Mở Discord, vào **Server** của bạn (tạo server mới nếu chưa có)
2. Nhấn chuột phải vào **kênh text** muốn nhận thông báo → **"Edit Channel"**
3. Chọn tab **"Integrations"**
4. Nhấn **"Webhooks"** → **"New Webhook"**
5. Đặt tên, ví dụ: `Email Support Bot`
6. Nhấn **"Copy Webhook URL"** — URL có dạng `https://discord.com/api/webhooks/...`
7. Lưu URL này lại, sẽ dùng ở Bước 5

---

## Bước 5 — Cấu hình file .env

File `.env` chứa tất cả thông tin cấu hình, **không được chia sẻ file này cho ai**.

### Tạo file .env

1. Vào thư mục `email-automation/`
2. Tìm file `.env.example`

   > **Mac:** File bắt đầu bằng dấu `.` nên bị ẩn. Trong Finder, nhấn `Cmd + Shift + .` để hiện file ẩn.
   > **Windows:** Trong File Explorer, vào View → tick **"Hidden items"**.

3. **Copy** file `.env.example` và **đổi tên bản copy thành `.env`** (bỏ phần `example`)

### Điền thông tin vào .env

Mở file `.env` bằng Notepad (Windows) hoặc TextEdit (Mac), bạn thấy nội dung như sau:

```
ANTHROPIC_API_KEY=sk-ant-...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/XXXX/YYYY
SUPPORT_EMAIL_ADDRESS=support@your-domain.com
```

Thay thế:
- `sk-ant-...` → API Key lấy ở Bước 2
- `https://discord.com/api/webhooks/XXXX/YYYY` → Webhook URL lấy ở Bước 4
- `support@your-domain.com` → địa chỉ Gmail hỗ trợ của bạn

Lưu file lại.

---

## Bước 6 — Cài đặt thư viện Python

Mở Terminal/Command Prompt, điều hướng vào thư mục `email-automation`:

**Mac:**
```bash
cd đường-dẫn-đến-thư-mục/email-automation
```

> Mẹo: Kéo thư mục `email-automation` từ Finder vào cửa sổ Terminal thay vì gõ đường dẫn.

**Windows:**
```
cd C:\đường-dẫn-đến-thư-mục\email-automation
```

Sau đó chạy lệnh cài thư viện:
```bash
pip install -r requirements.txt
```

Đợi đến khi thấy dòng `Successfully installed ...` là xong.

> ⚠️ Nếu báo lỗi `pip not found`, thử dùng `pip3` thay cho `pip`.

---

## Bước 7 — Chạy script lần đầu

Đảm bảo bạn đang ở trong thư mục `email-automation`, sau đó chạy:

```bash
python3 email_automation.py
```

### Lần đầu: Xác thực Gmail

1. **Trình duyệt tự động mở** một trang Google đăng nhập
2. Chọn tài khoản Gmail hỗ trợ của bạn
3. Nếu thấy cảnh báo **"Google hasn't verified this app"** → nhấn **"Advanced"** → **"Go to Email Support Bot (unsafe)"**

   > Cảnh báo này xuất hiện vì app chưa được Google xác minh. Hoàn toàn an toàn vì bạn tự tạo app này.

4. Nhấn **"Continue"** / **"Allow"** để cấp quyền
5. Trình duyệt hiện **"The authentication flow has completed"** → quay lại Terminal

Từ lần sau, bước này **không còn xuất hiện** nữa (token đã được lưu).

### Script đang chạy bình thường

Terminal sẽ hiển thị:

```
🚀 Email automation started — polling every 60s  (Ctrl+C to stop)
```

Script sẽ tự động kiểm tra Gmail mỗi 60 giây.

---

## Bước 8 — Cập nhật Support Guideline

File `agents/support_guideline.md` chứa các quy trình hỗ trợ mà AI dùng để trả lời.

Mở file bằng bất kỳ trình soạn thảo văn bản nào và chỉnh sửa theo nhu cầu. **Không cần khởi động lại script** — file được đọc mỗi khi script khởi động.

---

## Cách sử dụng hàng ngày

### Chạy script

```bash
cd email-automation
python3 email_automation.py
```

Giữ cửa sổ Terminal mở. Script chạy liên tục cho đến khi bạn dừng.

### Dừng script

Nhấn `Ctrl + C` trong Terminal.

### Khi có email tự động trả lời

Script tự gửi reply và hiện trong Terminal:
```
✅ AUTO_REPLY sent to customer@example.com
```

Gmail sẽ tự động gắn nhãn **AUTO_REPLIED** vào email đó.

### Khi có email cần xử lý thủ công

1. Discord nhận được thông báo với thông tin email
2. Terminal hiện prompt để bạn nhập nội dung trả lời:

```
────────────────────────────────────────────────────────────────────
  🚨 MANUAL REVIEW REQUIRED
────────────────────────────────────────────────────────────────────
  From    : customer@example.com
  Subject : [nội dung tiêu đề]
  Reason  : [lý do cần xử lý thủ công]
────────────────────────────────────────────────────────────────────
  ✏️  Type your reply then press Enter twice to send.
  ⏭️  Type 'skip' to handle manually in Gmail.
  ⛔  Type 'quit' to stop the automation.
────────────────────────────────────────────────────────────────────
```

**Các lựa chọn:**
- **Nhập nội dung** → nhấn Enter → nhập tiếp → nhấn Enter hai lần để gửi
- Gõ `skip` → để email trong Gmail, bạn tự vào Gmail trả lời
- Gõ `quit` → dừng script

---

## Xử lý sự cố thường gặp

### ❌ `ModuleNotFoundError: No module named 'anthropic'`
```bash
pip install -r requirements.txt
```

### ❌ `FileNotFoundError: gmail_credentials.json`
File `gmail_credentials.json` chưa được copy vào đúng thư mục. Kiểm tra lại Bước 3.4.

### ❌ `Missing required environment variables`
File `.env` chưa được tạo hoặc thiếu thông tin. Kiểm tra lại Bước 5.

### ❌ Trình duyệt không tự mở khi xác thực Gmail
Chạy script, copy URL xuất hiện trong Terminal, dán vào trình duyệt và mở thủ công.

### ❌ Script không nhận email mới
- Kiểm tra email có nằm trong **Inbox** và chưa đọc không
- Kiểm tra Gmail không filter email vào Spam

---

## Cấu trúc thư mục

```
email-automation/
├── email_automation.py      ← Script chính (không sửa nếu không cần)
├── requirements.txt         ← Danh sách thư viện
├── .env.example             ← Mẫu cấu hình
├── .env                     ← Cấu hình thực (tự tạo, không chia sẻ)
├── gmail_credentials.json   ← Tải từ Google Cloud (không chia sẻ)
├── gmail_token.json         ← Tự tạo sau lần đầu xác thực (không chia sẻ)
├── processed_email_ids.json ← Tự tạo khi chạy (không xóa)
└── agents/
    ├── email-support-agent.md   ← Cấu hình AI agent
    └── support_guideline.md     ← Quy trình hỗ trợ (chỉnh sửa theo nhu cầu)
```

> **3 file không được chia sẻ hoặc commit lên Git:**
> `.env` · `gmail_credentials.json` · `gmail_token.json`
