"""Bộ tách bản đọc ảnh theo định dạng THẬT của Claude + hiển thị cờ đỏ an toàn — 17/11/2026.

Chạy thật Opus 5.5 trên dải ECG tổng hợp trả nhãn in đậm «**MÔ TẢ:**». Bộ tách cũ chỉ nhận nhãn trơn ⇒ mọi mục rỗng và
bản nháp hiện «Cờ đỏ: Không thấy trên ảnh» — một bản đọc HỎNG được trình như bản đọc «bình thường». Mẫu dưới đây giữ
đúng KHUÔN câu trả lời thật (nội dung rút gọn, dữ liệu tổng hợp, không PII).
"""
from __future__ import annotations

import pytest

from app.integrations.image_reading import ImageReading, parse_reading

MAU_THAT = """# Đọc sơ bộ ECG (NHÁP hỗ trợ, không phải kết luận chẩn đoán)

**Định danh:** Không thấy tên, mã BN hay ngày sinh trên ảnh.

**Giới hạn của ảnh:**
- Chỉ có **1 chuyển đạo (DII)**, không phải ECG 12 chuyển đạo.

---

**MÔ TẢ:**
- **Tần số:** RR đều khoảng 0,8 s, tương ứng **khoảng 75 l/ph**.
- **Đoạn ST:** Đẳng điện.

**GỢI Ý:**
- Phù hợp **nhịp xoang đều** **[cần đối chiếu lâm sàng]**.

**CỜ ĐỎ:** Không thấy trên ảnh. Trong giới hạn 1 chuyển đạo DII.
"""


def test_tach_dung_khuon_that_cua_claude():
    r = parse_reading("ecg", MAU_THAT)
    assert "Tần số" in r.description and "Đoạn ST" in r.description
    assert "nhịp xoang" in r.impression
    assert r.red_flags.startswith("Không thấy trên ảnh")
    # Nhãn con trong mục («- **Tần số:**») KHÔNG được coi là nhãn mục mới.
    assert "Tần số" not in r.impression
    # Đoạn trước nhãn đầu tiên (giới hạn của ảnh) không bị bỏ âm thầm.
    assert "1 chuyển đạo" in r.ghi_chu and "# Đọc sơ bộ" not in r.ghi_chu
    md = r.to_markdown()
    assert "Giới hạn / ghi chú" in md and "KHÔNG TÁCH" not in md


@pytest.mark.parametrize("dong", ["**MÔ TẢ**: x", "1. MÔ TẢ: x", "MÔ TẢ: x", "## Mô tả x", "__Mô tả:__ x",
                                  "> **Description:** x"])
def test_cac_bien_the_nhan(dong):
    r = parse_reading("ecg", f"{dong}\n**CỜ ĐỎ:** không thấy trên ảnh")
    assert r.description == "x"


def test_khong_tach_duoc_thi_khong_bao_gio_noi_khong_co_co_do():
    raw = "Bản đọc tự do không theo khung: nhịp nhanh, nghi ST chênh lên ở DII."
    r = parse_reading("ecg", raw)
    assert r.tach_duoc is False
    md = r.to_markdown()
    assert "KHÔNG TÁCH ĐƯỢC" in md and "ST chênh lên" in md     # bác sĩ thấy nguyên văn
    assert "Không thấy trên ảnh" not in md


def test_vang_muc_co_do_la_chua_biet():
    r = parse_reading("ecg", "**MÔ TẢ:** nhịp xoang\n**GỢI Ý:** bình thường")
    md = r.to_markdown()
    assert "KHÔNG ghi mục cờ đỏ" in md and "Không thấy trên ảnh" not in md


def test_khong_co_cau_tra_loi_van_coi_la_tach_duoc_rong():
    assert ImageReading(modality="ecg").tach_duoc is True   # chưa gọi gì: không có gì để cảnh báo «tách hỏng»


def test_bang_tich_hop_nhan_khoa_trong_kho_bi_mat(monkeypatch):
    import app.dashboard.integrations_panel as panel
    from app.integrations._api_claude import cau_noi

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(cau_noi(), "khoa_api", lambda *a, **k: "khoa-trong-kho")   # bimat-mien: giá trị giả
    assert panel.has_anthropic_key() is True
    monkeypatch.setattr(cau_noi(), "khoa_api", lambda *a, **k: "")
    assert panel.has_anthropic_key() is False
