# -*- coding: utf-8 -*-
"""Trình bày .docx (giả lập lần 3, 15/11/2026): ghi chú (blockquote) theo cỡ THÂN BÀI, 🟠 thành chữ.

Đo được: G1_A13b_RISK_REGISTER đo «cỡ thân bài 11pt» (chuẩn 13pt) vì md2docx_vn dựng ghi chú «> …» ở cỡ BẢNG; ký tự 🟠
của nháp Kết quả G7 không có glyph trong Times New Roman (bộ làm sạch chưa có ánh xạ). Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import chuan_trinh_bay as CTB  # noqa: E402
import kiem_chi_tiet_he_nghien_cuu as KC  # noqa: E402
import xuat_docx_chuan as XDC  # noqa: E402


def test_lam_sach_doi_cham_cam_thanh_chu():
    assert CTB.lam_sach_van_ban("🟠 NHÁP") == "[Cảnh báo] NHÁP"


def test_ghi_chu_blockquote_theo_co_than_bai(tmp_path):
    md = tmp_path / "G1_A13b_RISK_REGISTER_THU.md"
    md.write_text("# Sổ rủi ro\n\n> Ghi chú dài: mức xác suất/tác động phải được nhóm nghiên cứu hiệu chỉnh theo thang "
                  "Thấp · Trung bình · Cao trước khi trình Hội đồng.\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n- mục\n",
                  encoding="utf-8", newline="\n")
    XDC.render_mot_file(md)
    d = KC.kiem_docx(md.with_suffix(".docx"))
    assert d["co_than_uu_the"] == 13.0 and d["co_bang_uu_the"] == 11.0, d
