"""Hồi quy phát hiện #3 (MEDIUM-HIGH) của Workflow đối kháng đa-agent
2026-09-06 (vòng 29) trong tools/research_ccn_status.py — is_closed_status()
đọc "UNRESOLVED" thành ĐÃ ĐÓNG do khớp chuỗi con "resolved" mà không bắt được
tiền tố phủ định DÍNH LIỀN "un".

CƠ CHẾ LỖI (TRƯỚC bản vá):
    _NEGATIVE_STATUS_MARKERS = ["not ", "chưa ", ...]   # chỉ phủ định TÁCH RỜI
    _POSITIVE_STATUS_MARKERS = [..., "resolved", ...]

    def is_closed_status(status_text):
        s = status_text.strip().lower()
        if any(m in s for m in _NEGATIVE_STATUS_MARKERS):
            return False
        return any(m in s for m in _POSITIVE_STATUS_MARKERS)

"UNRESOLVED" hạ chữ thường thành "unresolved": không khớp bất kỳ negative
marker nào (chỉ có "not " với khoảng trắng, không phải tiền tố "un" dính
liền) — nhưng LẠI khớp "resolved" (positive marker) vì `in` là khớp chuỗi
con thuần túy. Hàm trả True (ĐÃ ĐÓNG) cho một trạng thái CÒN MỞ — ngược
hoàn toàn với ý nghĩa thật, và ngược với chính nguyên tắc "KHÔNG suy diễn
CLOSED từ chuỗi phủ định" mà docstring của khối này tự khai.

HẠI THẬT: is_closed_status() được 3 hàm parse (GAP-REG/OPEN-DEP/EXT-DEP,
tools/research_ccn_status.py dòng ~299/332/365) dùng để xếp một mục "Cần
Chờ Người/hạ tầng Ngoài" vào CÒN MỞ hay ĐÃ ĐÓNG trong báo cáo tổng hợp CCN.
Một dòng trong bất kỳ sổ nguồn nào ghi trạng thái "Unresolved" hoặc "Issue
unresolved, waiting on vendor" (giá trị hoàn toàn hợp lý — dữ liệu hiện tại
trong repo chỉ tình cờ chưa dùng đúng từ này) sẽ bị đếm nhầm vào "Đã đóng",
khiến PI/bác sĩ đọc báo cáo tưởng một CCN đã giải quyết trong khi thực tế
vẫn đang bị chặn.

Cùng họ rủi ro không chỉ riêng "resolved": mọi từ khẳng định tiếng Anh khác
trong _POSITIVE_STATUS_MARKERS (signed, done, written, obtained, provided,
issued, engaged) đều có thể bị phủ định bằng tiền tố "un" dính liền theo
đúng cách tương tự ("unsigned", "undone", "unwritten"...).

BẢN VÁ: _has_unnegated_positive_marker() dùng regex với chuỗi lookbehind
phủ định `(?<!un)(?<!non)(?<!ir)` ngay trước mỗi positive marker — một
occurrence của marker chỉ được tính là "khẳng định thật" nếu KHÔNG có tiền
tố phủ định dính liền ngay trước nó. Đóng cả lớp rủi ro (un-/non-/ir-),
không chỉ riêng trường hợp "unresolved" đã đo được.

Nguyên tắc viết test:
1. Ca chính — "UNRESOLVED" và biến thể có ngữ cảnh phải trả False (không
   phải True).
2. Đối xứng — mọi positive marker khác cũng bị phủ định đúng cách khi có
   tiền tố "un" dính liền (không chỉ riêng "resolved").
3. Đối chứng bắt buộc — mọi ca dương/âm ĐÃ CÓ trong
   tests/test_research_ccn_status.py (OPEN/NOT PROVIDED/NOT DONE/MỞ/rỗng/
   CLOSED) không được đổi kết quả.
4. Đối chứng — "resolved"/"signed" KHÔNG bị tiền tố phủ định vẫn trả True
   như trước (bản vá không được làm mất khả năng phát hiện thật)."""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import research_ccn_status as RCCN  # noqa: E402


class TestUnresolvedKhongBiHieuThanhDaDong:
    """★★★ Ca chính — MUTATION-PHÂN-BIỆT ĐƯỢC. 'unresolved' phải là OPEN,
    không phải CLOSED."""

    def test_unresolved_don_le(self):
        assert RCCN.is_closed_status("UNRESOLVED") is False, (
            "TRƯỚC bản vá: 'unresolved' khớp chuỗi con 'resolved' (positive marker) "
            "và không khớp negative marker nào (chỉ có 'not ' với khoảng trắng) — "
            "is_closed_status() trả True (ĐÃ ĐÓNG) cho một trạng thái CÒN MỞ."
        )

    def test_unresolved_trong_cau_day_du(self):
        assert RCCN.is_closed_status("Issue unresolved, waiting on vendor") is False


class TestDoiXungCacPositiveMarkerKhacCungBiPhuDinhDinhLien:
    """Cùng họ rủi ro: mọi positive marker tiếng Anh khác cũng bị phủ định
    đúng cách bằng tiền tố 'un' dính liền, không chỉ riêng 'resolved'."""

    def test_unsigned_la_open(self):
        assert RCCN.is_closed_status("UNSIGNED") is False

    def test_undone_la_open(self):
        assert RCCN.is_closed_status("UNDONE") is False

    def test_unwritten_la_open(self):
        assert RCCN.is_closed_status("UNWRITTEN") is False

    def test_unobtained_la_open(self):
        assert RCCN.is_closed_status("UNOBTAINED") is False

    def test_unprovided_la_open(self):
        assert RCCN.is_closed_status("UNPROVIDED") is False

    def test_unissued_la_open(self):
        assert RCCN.is_closed_status("UNISSUED") is False

    def test_unengaged_la_open(self):
        assert RCCN.is_closed_status("UNENGAGED") is False


class TestDoiChungHanhViCuKhongDoi:
    """Đối chứng bắt buộc — mọi ca đã có trong
    tests/test_research_ccn_status.py không được đổi kết quả sau bản vá."""

    def test_open_external_van_open(self):
        assert RCCN.is_closed_status("OPEN — EXTERNAL") is False

    def test_not_provided_van_open(self):
        assert RCCN.is_closed_status("EXTERNAL — NOT PROVIDED") is False

    def test_not_done_van_open(self):
        assert RCCN.is_closed_status("NOT DONE") is False

    def test_mo_tieng_viet_van_open(self):
        assert RCCN.is_closed_status("MỞ (P1 gốc)") is False

    def test_chuoi_rong_van_open(self):
        assert RCCN.is_closed_status("") is False

    def test_closed_van_closed(self):
        assert RCCN.is_closed_status("CLOSED") is True


class TestDoiChungPositiveMarkerKhongBiPhuDinhVanHoatDong:
    """Đối chứng bắt buộc — bản vá không được làm mất khả năng phát hiện
    THẬT: positive marker không có tiền tố phủ định vẫn phải trả True."""

    def test_resolved_khong_tien_to_van_closed(self):
        assert RCCN.is_closed_status("RESOLVED") is True

    def test_signed_khong_tien_to_van_closed(self):
        assert RCCN.is_closed_status("SIGNED") is True

    def test_da_dong_tieng_viet_van_closed(self):
        assert RCCN.is_closed_status("Đã đóng") is True
