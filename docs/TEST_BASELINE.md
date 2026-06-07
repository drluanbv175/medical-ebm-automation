# Test Baseline & Change Log

Bản ghi mốc kiểm thử để theo dõi độ trôi (regression) của bộ test.

| Ngày | Sự kiện | Kết quả pytest | Ghi chú |
|------|---------|----------------|---------|
| 2026-06-07 | Khởi tạo harness + baseline đầu tiên (task 0.1) | **95 passed, 0 failed** | venv `~/.ebm-venv` (Python 3.9.6, ngoài OneDrive); `USE_MOCK_SOURCES=true`; 2.8s |
| 2026-06-07 | Task 1.1: khóa 6 cập nhật guideline (CHA2DS2-VA, FIB-4, qSOFA, MELD 3.0, GOLD 2025, ASCVD/PREVENT) | **107 passed, 0 failed** | +12 test pinning (`tests/test_clinical_scores_updates.py`); reviewer APPROVE (0 critical/major); mutation-verified guard |
| 2026-06-07 | Task 1.2–1.4: khóa GAD-7 (USPSTF 2023) + liêm chính danh mục (change-log idempotent, 32 verified/16 needs_verification) | **114 passed, 0 failed** | +`tests/test_clinical_scores_integrity.py`; số liệu xác minh bằng DB sạch khớp doc; reviewer APPROVE (0 critical/major) |
| 2026-06-07 | Task 0.2: thiết lập lint baseline (ruff) | 114 passed (test không đổi) | `ruff.toml` (E,F,W,I; py39; line=100). **Baseline lint: 189 cảnh báo** (131 E501, 39 I001, 10 F401, 6 E702, 3 khác). Chưa sửa — sửa là task riêng để review an toàn. |
| 2026-06-07 | Task 3.1: dọn lint về 0 | **114 passed** (không đổi) | Lỗi thực đã sửa (import/biến thừa, semicolon, tên `l`→`line`, bẻ dòng chuỗi). E501: line=120 + per-file-ignore file dữ liệu/template (`verified.py`, `_fixtures.py`, `package.py`). `ruff check` = **0 lỗi**; reviewer APPROVE (6/6 điểm tương đương ngữ nghĩa). |

## Cách tái lập baseline

```bash
source ~/.ebm-venv/bin/activate
cd "<đường-dẫn>/medical-ebm-automation"
USE_MOCK_SOURCES=true python -m pytest -q
```

## Lưu ý môi trường

- **venv phải nằm ngoài thư mục OneDrive** (xem README §2) — đã đặt tại `~/.ebm-venv`.
- Python hệ thống hiện là **3.9.6** (dưới mức khuyến nghị 3.10+; chạy được nhờ `from __future__ import annotations`). Cân nhắc nâng lên 3.12 cho production.
