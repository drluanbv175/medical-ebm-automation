# Hướng dẫn chạy tự động trên máy Windows (chạy song song với Mac)

Mục tiêu: máy nào bật lúc ~18:00 cũng tự cập nhật và gửi email. Dữ liệu đồng bộ qua
OneDrive nên file `.env` (đã có cấu hình email) tự xuất hiện trên Windows.

> Lịch khuyến nghị: **Mac 18:00, Windows 18:05** (lệch 5 phút để hai máy không ghi đè
> dữ liệu cùng lúc; máy chạy sau sẽ thấy "không có gì mới" và không gửi email trùng).

---

## A. Cài đặt 1 lần

1. **Cài Python**: vào https://www.python.org/downloads/ → tải bản mới nhất → khi cài,
   **TÍCH ô "Add Python to PATH"** rồi bấm Install.

2. **Tìm thư mục dự án trên Windows**: mở **File Explorer** → vào **OneDrive** →
   `Claude AI` → `medical-ebm-automation` → mở thư mục `scripts`.

3. **Nháy đúp file `setup_ebm_windows.bat`**.
   - Một cửa sổ đen mở ra, tự tạo môi trường và cài thư viện (vài phút).
   - Khi thấy dòng **"CAI DAT XONG"** là thành công. Đóng cửa sổ.
   - Nếu báo "Chua cai Python" → cài lại Python (nhớ tích Add to PATH) rồi chạy lại.

## B. Hẹn giờ chạy 18:05 hằng ngày (Task Scheduler)

1. Bấm phím **Windows**, gõ **Task Scheduler** (Trình lập lịch tác vụ) → mở.
2. Bên phải bấm **Create Basic Task** (Tạo tác vụ cơ bản).
3. Đặt tên: `EBM Update` → **Next**.
4. Chọn **Daily** (Hằng ngày) → Next → đặt giờ **18:05** → Next.
5. Chọn **Start a program** (Khởi động chương trình) → Next.
6. Ô **Program/script**, bấm **Browse**, tìm tới:
   `OneDrive\Claude AI\medical-ebm-automation\scripts\run_ebm_windows.bat` → chọn.
7. **Next** → **Finish**.

(Tùy chọn nên bật: trong danh sách tác vụ, nháy đúp `EBM Update` → tab **Conditions**
→ BỎ tích "Start the task only if the computer is on AC power" nếu muốn chạy cả khi
dùng pin; tab **Settings** → tích "Run task as soon as possible after a scheduled
start is missed" để bù khi máy vừa bật trễ.)

## C. Kiểm tra

- Nháy đúp `run_ebm_windows.bat` một lần để chạy thử.
- Mở Gmail xem có email cập nhật không.
- Nhật ký nằm ở `medical-ebm-automation\data\archive\windows_daily.log`.

## Lưu ý
- Windows dùng môi trường Python RIÊNG ở `C:\ebm-venv` (ngoài OneDrive) — đúng cách,
  không bị lỗi do đồng bộ đám mây. (Máy Mac dùng `~/.ebm-venv`, cũng ngoài OneDrive.)
- Nếu gặp lỗi, mở file `windows_daily.log`, copy đoạn lỗi gửi cho trợ lý để được chỉ cách sửa.
