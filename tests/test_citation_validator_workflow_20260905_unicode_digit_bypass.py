"""Hồi quy phát hiện #4 (Medium) của Workflow đối kháng đa-agent 2026-09-05
(vòng 13) trong `app/evidence/citation_validator.py::validate_identifier()`.

CƠ CHẾ LỖI: mặc định `\\d` của Python (`re` không có cờ `re.ASCII`) khớp
MỌI ký tự thuộc phạm trù Unicode "chữ số thập phân" (category Nd), không
chỉ 0-9 ASCII — ví dụ chữ số full-width "１２３４５６７８" (U+FF11...) hay
chữ số Ả Rập-Ấn Độ "١٢٣٤٥٦٧٨" (U+0661...) đều khớp `^\\d{4,9}$`. Một chuỗi
như vậy KHÔNG PHẢI định danh PMID/DOI thật — PubMed E-utilities và DOI
registry chỉ nhận chữ số ASCII — nhưng trước bản vá, `validate_identifier()`
vẫn báo `valid=True` cho nó. Đây là "một định danh trông hợp lệ nhưng sai
dạng" lọt qua, cùng họ lỗi với sha256 hoa/thường đã sửa ở
`manual_source_import.py` (task #91, vòng 6).

BẢN VÁ: thêm cờ `re.ASCII` vào cả `_PMID` và `_DOI` để `\\d`/`\\S` chỉ khớp
ký tự ASCII.

Nguyên tắc viết test: gọi THẲNG `validate_identifier()` thật, dùng chuỗi
Unicode chữ số THẬT (không phải placeholder), đối chiếu bằng `match()` sống
trước khi tin vào assert.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.evidence.citation_validator import validate_identifier  # noqa: E402

_FULLWIDTH_DIGITS = "１２３４５６７８"  # "12345678" full-width
_ARABIC_INDIC_DIGITS = "١٢٣٤٥٦٧٨"  # "12345678" Ả Rập-Ấn Độ


class TestPmidChuSoUnicodeKhongPhaiAsciiBiTuChoi:
    """★★★ Ca chính — chuỗi trông "đủ 8 chữ số" theo `\\d` mặc định nhưng
    KHÔNG PHẢI chữ số ASCII phải bị từ chối, không được báo valid=True."""

    def test_pmid_full_width_digit_bi_tu_choi(self):
        result = validate_identifier({"pmid": _FULLWIDTH_DIGITS})
        assert result.valid is False, (
            "TRƯỚC bản vá: `\\d` mặc định khớp cả chữ số full-width Unicode, "
            "khiến một PMID giả dạng bị báo hợp lệ"
        )
        assert result.identifier_type == "pmid"

    def test_pmid_arabic_indic_digit_bi_tu_choi(self):
        result = validate_identifier({"pmid": _ARABIC_INDIC_DIGITS})
        assert result.valid is False
        assert result.identifier_type == "pmid"

    def test_doi_chua_chu_so_full_width_van_khop_phan_prefix_nhung_khong_dung_dinh_dang(self):
        """DOI dùng `\\d{4,9}` cho phần registrant code trước dấu `/` — chữ số
        full-width ở đó cũng phải bị từ chối."""
        doi_gia = f"10.{_FULLWIDTH_DIGITS}/suffix"
        result = validate_identifier({"doi": doi_gia})
        assert result.valid is False
        assert result.identifier_type == "doi"


class TestPmidAsciiThatVanDuocChapNhanNhuCu:
    """Đối chứng bắt buộc — PMID/DOI ASCII bình thường vẫn hợp lệ như cũ,
    bản vá không nới/siết quá tay."""

    def test_pmid_ascii_8_chu_so_hop_le(self):
        result = validate_identifier({"pmid": "12345678"})
        assert result.valid is True
        assert result.identifier_type == "pmid"

    def test_doi_ascii_hop_le(self):
        result = validate_identifier({"doi": "10.1001/jamaoncol.2018.4070"})
        assert result.valid is True
        assert result.identifier_type == "doi"

    def test_url_van_khong_bi_anh_huong(self):
        result = validate_identifier({"url": "https://example.org/guideline"})
        assert result.valid is True
        assert result.identifier_type == "url"


class TestGiaThietSongVeUnicodeDigitTruocKhiTin:
    """Kiểm chứng độc lập bằng chính module `re` — xác nhận tiền đề của
    bản vá là đúng (chữ số Unicode THỰC SỰ khớp `\\d` khi không có
    `re.ASCII`), tránh test dựa trên một giả định sai về hành vi Python."""

    def test_fullwidth_khop_d_mac_dinh_khong_co_ascii_flag(self):
        import re

        assert re.match(r"^\d{4,9}$", _FULLWIDTH_DIGITS) is not None
        assert re.match(r"^\d{4,9}$", _FULLWIDTH_DIGITS, re.ASCII) is None

    def test_arabic_indic_khop_d_mac_dinh_khong_co_ascii_flag(self):
        import re

        assert re.match(r"^\d{4,9}$", _ARABIC_INDIC_DIGITS) is not None
        assert re.match(r"^\d{4,9}$", _ARABIC_INDIC_DIGITS, re.ASCII) is None
