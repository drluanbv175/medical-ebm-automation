"""Kiểm `app/sources/guideline_fulltext_common.py` — thêm 23/09/2026.

Hạ tầng dùng chung cho connector toàn văn guideline (GOLD/GINA/BTS/PMC). Test PDF
thật được DỰNG BẰNG CHÍNH pypdf (không tải/nhúng bất kỳ tài liệu có bản quyền nào),
nội dung chỉ là một câu tiếng Việt vô hại tự chọn cho mục đích kiểm thử.
"""
from __future__ import annotations

import io

from app.sources.guideline_fulltext_common import (
    GHI_CHU_BAN_QUYEN_CHUAN,
    KetQuaToanVanGuideline,
    trich_van_ban_tu_pdf,
)


def _dung_pdf_that(cau_van_ban: str = "Vi du kiem thu, khong phai chung cu that") -> bytes:
    """Dựng một PDF hợp lệ, một trang, có lớp văn bản trích được — bằng chính pypdf,
    không tải/sao chép nội dung có bản quyền từ đâu cả."""
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    w = PdfWriter()
    page = w.add_blank_page(width=200, height=200)

    content = f"BT /F1 24 Tf 10 100 Td ({cau_van_ban}) Tj ET".encode("latin-1")
    stream_obj = DecodedStreamObject()
    stream_obj.set_data(content)
    stream_ref = w._add_object(stream_obj)
    page[NameObject("/Contents")] = stream_ref

    font = DictionaryObject()
    font[NameObject("/Type")] = NameObject("/Font")
    font[NameObject("/Subtype")] = NameObject("/Type1")
    font[NameObject("/BaseFont")] = NameObject("/Helvetica")
    font_ref = w._add_object(font)
    resources = DictionaryObject()
    font_dict = DictionaryObject()
    font_dict[NameObject("/F1")] = font_ref
    resources[NameObject("/Font")] = font_dict
    page[NameObject("/Resources")] = resources

    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def test_trich_van_ban_tu_pdf_extracts_real_text():
    pdf_bytes = _dung_pdf_that("Vi du kiem thu")
    van_ban = trich_van_ban_tu_pdf(pdf_bytes)
    assert "Vi du kiem thu" in van_ban


def test_trich_van_ban_tu_pdf_returns_empty_string_on_garbage_not_raise():
    van_ban = trich_van_ban_tu_pdf(b"day khong phai la mot file PDF hop le")
    assert van_ban == ""


def test_trich_van_ban_tu_pdf_returns_empty_string_on_empty_bytes():
    assert trich_van_ban_tu_pdf(b"") == ""


def test_trich_van_ban_tu_pdf_respects_character_limit():
    # Một trang PDF thật nhưng gọi với giới hạn ký tự rất nhỏ -> chuỗi trả về bị cắt.
    pdf_bytes = _dung_pdf_that("Mot cau kha dai de kiem tra viec cat bot ky tu")
    van_ban = trich_van_ban_tu_pdf(pdf_bytes, gioi_han_ky_tu=5)
    assert len(van_ban) <= 5


def test_ket_qua_dataclass_default_copyright_note_is_the_standard_one():
    kq = KetQuaToanVanGuideline(to_chuc="GOLD", url_nguon="https://example.org/x.pdf", thanh_cong=True)
    assert kq.ghi_chu_ban_quyen == GHI_CHU_BAN_QUYEN_CHUAN
    assert "KHÔNG đăng lại toàn văn công khai" in kq.ghi_chu_ban_quyen
