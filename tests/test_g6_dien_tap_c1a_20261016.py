"""Lỗi G6 lộ ra khi DIỄN TẬP C1a (16/10/2026) — mỗi lỗi một chốt.

F13: tên kết cục chính trong backtick dài 2 ký tự (`g1` — tên trường REDCap của C1a) bị bỏ qua ⇒ rút nhầm tên khái
     niệm trong ngoặc đơn của đề cương gốc ⇒ G6-AUTO-04 báo «lệch kết cục chính» oan.
(F15 — họ mô hình đọc cả dòng chú thích — là vấn đề THIẾT KẾ quy trình: bộ sinh để mô hình chính ở dạng chú thích cho
cả 8 thiết kế; ghi trong biên bản diễn tập, chờ bác sĩ/thống kê viên chọn hướng, chưa sửa ở đây.)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import g6_quality_gate as G6  # noqa: E402

DONG_C1A = ("- **Kết cục chính:** G1 — mức hài lòng chung, hỏi trực tiếp (biến SHLNBChung_TrucTiep), Phần 3 phiếu — "
            "trường dữ liệu `g1`, thang thứ hạng Likert 1–5")


def test_f13_ten_truong_hai_ky_tu_trong_backtick_duoc_uu_tien():
    assert G6.ket_cuc_chinh_sap(DONG_C1A) == "g1"


def test_f13_khong_backtick_van_lay_ten_trong_ngoac_nhu_cu():
    assert G6.ket_cuc_chinh_sap("- **Kết cục chính:** G1 (biến SHLNBChung_TrucTiep), Phần 3") == "shlnbchung_tructiep"
