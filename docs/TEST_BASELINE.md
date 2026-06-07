# Test Baseline & Change Log

Bản ghi mốc kiểm thử để theo dõi độ trôi (regression) của bộ test.

| Ngày | Sự kiện | Kết quả pytest | Ghi chú |
|------|---------|----------------|---------|
| 2026-06-07 | Khởi tạo harness + baseline đầu tiên (task 0.1) | **95 passed, 0 failed** | venv `~/.ebm-venv` (Python 3.9.6, ngoài OneDrive); `USE_MOCK_SOURCES=true`; 2.8s |

## Cách tái lập baseline

```bash
source ~/.ebm-venv/bin/activate
cd "<đường-dẫn>/medical-ebm-automation"
USE_MOCK_SOURCES=true python -m pytest -q
```

## Lưu ý môi trường

- **venv phải nằm ngoài thư mục OneDrive** (xem README §2) — đã đặt tại `~/.ebm-venv`.
- Python hệ thống hiện là **3.9.6** (dưới mức khuyến nghị 3.10+; chạy được nhờ `from __future__ import annotations`). Cân nhắc nâng lên 3.12 cho production.
