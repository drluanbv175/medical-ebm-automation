"""Hồi quy: cảnh báo «ký tự không hiển thị được» của md2docx_vn phải mô tả file CUỐI.

Vì sao có (06/09/2026, đo trên đề tài thật C1a): mỗi lần lắp đề cương, md2docx_vn in
«CẢNH BÁO: … còn '🚧' (U+1F6A7) x1» trong khi .docx cuối KHÔNG còn ký tự đó — bộ làm
sạch `chuan_trinh_bay.lam_sach_tai_lieu` (chạy sau cùng, trước doc.save) đã đổi nó thành
«[Đang dừng]». `_font_safe` ghi nhận ký tự rủi ro trên bản THÔ, trước khi bộ làm sạch
chạy ⇒ báo động giả ở mọi lần xuất. Báo động giả dạy người ta bỏ qua cảnh báo thật (BH08).

Hai ca khoá hai chiều: (1) ký tự bộ làm sạch BIẾT ⇒ không cảnh báo, và .docx thật sạch;
(2) ký tự bộ làm sạch KHÔNG biết ⇒ vẫn phải cảnh báo — sửa (1) mà làm câm (2) là fail-open.
Ngoại tuyến; kiểm trên file .docx thật (mở zip đọc XML).
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

docx = pytest.importorskip("docx")  # noqa: F841 — python-docx bắt buộc cho bộ này
import chuan_trinh_bay as CTB  # noqa: E402
import md2docx_vn as M  # noqa: E402


def _body(path: Path) -> str:
    return zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")


class TestGlyphWarningDescribesFinalFile:
    def test_char_known_to_cleaner_is_a_note_not_a_warning(self, tmp_path, capsys):
        assert "🚧" in CTB._THAY_KY_HIEU, "tiền đề: bộ làm sạch phải biết ký tự này"
        out = tmp_path / "nhap.docx"
        M.markdown_to_docx("> 🚧 **BẢN NHÁP** — chưa nộp.\n\n# 1. Tóm tắt\n\nNội dung.\n", out)
        body = _body(out)
        assert "🚧" not in body and CTB._THAY_KY_HIEU["🚧"] in body
        # Không được CẢNH BÁO về ký tự KHÔNG còn trong file cuối…
        assert "🚧" not in M._glyph_canh_bao
        err = capsys.readouterr().err
        assert "CẢNH BÁO" not in err
        # …nhưng cũng không được IM: người soạn vẫn cần biết nguồn có ký tự đó (chốt 03/08).
        assert M._glyph_da_lam_sach.get("🚧", 0) >= 1
        assert "GHI CHÚ" in err and "🚧" in err

    def test_char_unknown_to_cleaner_is_still_reported(self, tmp_path, capsys):
        ky_tu = "🦠"  # emoji Times New Roman không có, bộ làm sạch không biết
        assert ky_tu not in CTB._THAY_KY_HIEU and ky_tu not in CTB._BO_HAN
        out = tmp_path / "vi_khuan.docx"
        M.markdown_to_docx(f"# 1. Tóm tắt\n\nVi khuẩn {ky_tu} thử.\n", out)
        assert ky_tu in _body(out), "ký tự còn nguyên trong file ⇒ cảnh báo phải nói ra"
        assert M._glyph_canh_bao.get(ky_tu, 0) >= 1
        assert "CẢNH BÁO" in capsys.readouterr().err

    def test_both_counters_reset_between_exports(self, tmp_path, capsys):
        """Tài liệu bẩn không được làm tài liệu sạch xuất sau đó kêu oan — áp cho CẢ
        bộ đếm ghi chú mới (chốt 03/08 chỉ khoá bộ đếm cảnh báo)."""
        M.markdown_to_docx("Ký tự 🚧 và 🦠.", tmp_path / "ban.docx")
        capsys.readouterr()
        M.markdown_to_docx("Chỉ chữ thường.", tmp_path / "sach.docx")
        assert not M._glyph_canh_bao and not M._glyph_da_lam_sach
        assert capsys.readouterr().err.strip() == ""
