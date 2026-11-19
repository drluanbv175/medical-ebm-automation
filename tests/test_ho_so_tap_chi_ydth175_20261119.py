# -*- coding: utf-8 -*-
"""Hồ sơ định dạng «Tạp chí Y Dược Thực hành 175» (thêm 19/11/2026).

Bác sĩ giao «Tạp chí Y Dược thực hành 175 hãy đọc hướng dẫn và hoàn thiện để đăng bài». Thể lệ viết bài của tạp chí
(https://jpmp175.vn/yduocthuchanh175/guideline-for-contributors, đọc 19/11/2026): A4, Times New Roman cỡ 13, giãn dòng
1,3, lề trái 3 cm, phải 2 cm, trên 2 cm, dưới 2 cm, đánh số trang tự động. Test khoá các con số đó trong .docx THẬT
(không chỉ trong dict), và khoá rằng hồ sơ đã xác minh đủ nên KHÔNG chèn cảnh báo «cần xác minh».
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

pytest.importorskip("docx", reason="python-docx chưa cài — bỏ qua test sinh .docx thật")

import md2docx_vn as M2D  # noqa: E402

_MD = "# Tiêu đề\n\nĐoạn thân bài kiểm tra định dạng.\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"
_TEN = "Tạp chí Y Dược Thực hành 175"


def _xml(p: Path) -> str:
    with zipfile.ZipFile(p) as zf:
        return zf.read("word/document.xml").decode("utf-8", errors="ignore")


def _dung(tmp_path: Path) -> str:
    out = tmp_path / "ydth175.docx"
    M2D.markdown_to_docx(_MD, out, journal_profile=M2D.resolve_journal_profile(_TEN))
    return _xml(out)


def test_khop_ten_co_va_khong_dau():
    for ten in (_TEN, "tap chi y duoc thuc hanh 175", "TẠP CHÍ Y DƯỢC THỰC HÀNH 175", "YDTH175"):
        p = M2D.resolve_journal_profile(ten)
        assert p is not None and p["key"] == "tap_chi_y_duoc_thuc_hanh_175", ten


def test_ten_gan_dung_khong_khop_nham():
    assert M2D.resolve_journal_profile("Tạp chí Y Dược Thực hành 108") is None
    assert M2D.resolve_journal_profile("Tạp chí Y Dược") is None


def test_le_trang_dung_the_le(tmp_path):
    """Lề trái 3 cm = 1701 twip; phải/trên/dưới 2 cm = 1134 twip."""
    m = re.search(r'<w:pgMar w:top="(\d+)" w:right="(\d+)" w:bottom="(\d+)" w:left="(\d+)"', _dung(tmp_path))
    assert m, "không thấy w:pgMar"
    assert m.groups() == ("1134", "1134", "1134", "1701")


def test_kho_A4(tmp_path):
    m = re.search(r'<w:pgSz w:w="(\d+)" w:h="(\d+)"', _dung(tmp_path))
    assert m and m.groups() == ("11906", "16838")


def test_co_chu_13_va_gian_dong_1_3(tmp_path):
    xml = _dung(tmp_path)
    i = xml.find("Đoạn thân bài")
    assert i > 0
    truoc = xml[max(0, i - 600):i]
    # Đề mục phía trên có giãn dòng riêng ⇒ chỉ xét w:line GẦN NHẤT trước đoạn thân bài (pPr của chính đoạn đó).
    dong = re.findall(r'w:line="(\d+)"', truoc)
    assert dong and dong[-1] == "312", f"giãn dòng 1,3 ⇒ line=312 (240 × 1,3); thấy {dong[-1:] or 'không có'}"
    assert '<w:sz w:val="26"/>' in xml[max(0, i - 300):i + 200], "cỡ 13 ⇒ sz=26 (nửa điểm)"
    assert "Times New Roman" in truoc


def test_xac_minh_du_nen_khong_canh_bao(tmp_path):
    p = M2D.resolve_journal_profile(_TEN)
    assert not M2D._needs_verification_warning(p)
    assert "CẦN XÁC MINH" not in _dung(tmp_path).upper()


def test_nguon_ghi_trang_the_le():
    p = M2D.JOURNAL_PROFILES["tap_chi_y_duoc_thuc_hanh_175"]
    assert "jpmp175.vn/yduocthuchanh175/guideline-for-contributors" in p["source_note"]
