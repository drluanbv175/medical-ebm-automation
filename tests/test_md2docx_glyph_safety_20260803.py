# -*- coding: utf-8 -*-
"""Kiểm hồi quy cho lớp an toàn glyph của md2docx_vn (vá 2026-08-03).

Bối cảnh: bản .docx của đề tài C1a hiển thị sai ở 6 ký tự mà Times New Roman
KHÔNG có glyph (₀ ₁ ₂ ₋ ⁴ ☐). Word rơi sang font thay thế nên chữ lệch cỡ hoặc
thành ô vuông. Bẫy khiến lỗi khó thấy: ² và ³ (khối Latin-1) LẠI có glyph, nên
cùng một công thức hiển thị nửa đúng nửa sai.

Ba hành vi được khoá ở đây:
  1. Ký tự chỉ số Unicode -> run mang w:vertAlign, in bằng chữ số ASCII.
  2. Cú pháp `_{...}` / `^{...}` cho chỉ số NHIỀU ký tự (Z_{1−α/2}), vì α và "/"
     không tồn tại ở khối chỉ số dưới.
  3. Chốt cảnh báo: kêu khi còn ký tự thiếu glyph, IM khi sạch — đối chiếu bảng
     glyph thật của font, không đoán theo khối Unicode.
"""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

docx = pytest.importorskip("docx", reason="cần python-docx")
import md2docx_vn as M  # noqa: E402
from docx import Document  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402


def _xuat(md: str, tmp_path: Path, ten: str = "thu"):
    """Chuyển md -> docx, trả (Document, chuỗi cảnh báo trên stderr)."""
    err = io.StringIO()
    out = tmp_path / f"{ten}.docx"
    with contextlib.redirect_stderr(err):
        M.markdown_to_docx(md, out)
    return Document(str(out)), err.getvalue()


def _cac_run(doc):
    for p in doc.paragraphs:
        for r in p.runs:
            yield r
    for tb in doc.tables:
        for row in tb.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    for r in p.runs:
                        yield r


def _vert_align(run):
    rpr = run._element.find(qn("w:rPr"))
    if rpr is None:
        return None
    el = rpr.find(qn("w:vertAlign"))
    return None if el is None else el.get(qn("w:val"))


def test_chi_so_unicode_thanh_run_vertalign(tmp_path):
    """₀ ₂ ⁴ -> run vertAlign in bằng chữ số ASCII, không còn ký tự dựng sẵn."""
    doc, _ = _xuat("n₀ và d² và 1,098⁴", tmp_path)
    ban_do = [(r.text, _vert_align(r)) for r in _cac_run(doc)]
    assert ("0", "subscript") in ban_do
    assert ("2", "superscript") in ban_do
    assert ("4", "superscript") in ban_do
    toan_van = "".join(r.text for r in _cac_run(doc))
    for ky_tu in "₀²⁴":
        assert ky_tu not in toan_van, f"{ky_tu!r} còn sót ở dạng dựng sẵn"


def test_cu_phap_chi_so_nhieu_ky_tu(tmp_path):
    """Z_{1−α/2} -> MỘT run subscript chứa trọn '1−α/2', không tách vụn."""
    doc, _ = _xuat("Z_{1−α/2} và z_{1−β}", tmp_path)
    sub = [r.text for r in _cac_run(doc) if _vert_align(r) == "subscript"]
    assert "1−α/2" in sub
    assert "1−β" in sub
    assert "_{" not in "".join(r.text for r in _cac_run(doc))


def test_ky_tu_thieu_glyph_duoc_thay_the(tmp_path):
    """☐ ☑ ⚠ ✅ -> ký tự có glyph; bộ chọn hiển thị emoji bị gỡ."""
    doc, _ = _xuat("Ô ☐, đã ☑, cảnh báo ⚠️, đạt ✅", tmp_path)
    toan_van = "".join(r.text for r in _cac_run(doc))
    for ky_tu in "☐☑⚠✅️":
        assert ky_tu not in toan_van, f"{ky_tu!r} chưa được thay thế"
    assert "□" in toan_van and "■" in toan_van


@pytest.mark.parametrize(
    "md, phai_keu",
    [
        ("Z_{1−α/2}, d², Σpᵢ³, 1,098⁴, ☐, ⚠️, ✅", False),
        ("Chỉ chữ tiếng Việt có dấu, không ký tự lạ.", False),
        ("Mũi tên → ↔ và chữ Hy Lạp α β Σ χ", False),   # Times CÓ glyph, không được kêu oan
        ("Ký tự lạ 🧪", True),
        ("Đồng hồ ⏱ ở khối Miscellaneous Technical", True),
        ("Dấu tick ✓ mà Times không có", True),
    ],
)
def test_chot_canh_bao(md, phai_keu, tmp_path):
    """Chốt phải kêu khi còn ký tự thiếu glyph và IM khi sạch.

    Ca '⏱' khoá đúng lý do đã chuyển từ đoán khối Unicode sang đối chiếu bảng
    glyph thật: U+23F1 nằm ở khối mà một danh sách viết tay dễ bỏ sót.
    """
    _, canh_bao = _xuat(md, tmp_path)
    assert bool(canh_bao.strip()) is phai_keu, canh_bao


def test_bo_dem_canh_bao_duoc_reset_giua_cac_lan_xuat(tmp_path):
    """Tài liệu bẩn không được làm tài liệu sạch xuất sau đó kêu oan."""
    _, ban = _xuat("Ký tự lạ 🧪", tmp_path, "ban")
    assert ban.strip()
    _, sach = _xuat("Chỉ chữ thường.", tmp_path, "sach")
    assert not sach.strip(), f"kêu oan sau một lần xuất bẩn: {sach}"
