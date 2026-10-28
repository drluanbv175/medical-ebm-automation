# -*- coding: utf-8 -*-
"""Hồi quy 28/10/2026 — kiểm toàn diện hệ nghiên cứu (đề tài C1a).

1. Bộ sinh G1 chỉ xuất Word cho A2 ⇒ sau mỗi lần dựng lại, Word của A1b/A2b/A13/A13b CŨ hơn .md (kiem_chi_tiet trục ④
   báo «bản in CŨ HƠN nội dung .md») — người ký mở Word đọc bản lỗi thời.
2. Khối «TIÊU CHÍ QUA CỔNG G3» của A4 in hai việc của MÁY thành ô «- [ ]» ⇒ study_readiness đếm là việc người còn nợ.
Ngoại tuyến, dữ liệu tổng hợp.
"""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import cong_song as CS  # noqa: E402
import run_g1_auto as G1A  # noqa: E402
import run_g3_auto as R3  # noqa: E402
from _chuoi_da_chot import dung_g0_g1_da_chot  # noqa: E402
from test_g1_so_bang_chung_tu_sang_loc_g0_20261017 import STUDY as S_SO  # noqa: E402
from test_g1_so_bang_chung_tu_sang_loc_g0_20261017 import _de_tai as _de_tai_so  # noqa: E402


def test_dung_lai_ho_tro_xuat_word_chuan_cho_bon_tai_lieu_ho_tro(tmp_path):
    d = _de_tai_so(tmp_path)
    with contextlib.redirect_stdout(io.StringIO()):
        G1A.dung_lai_ho_tro(S_SO, d)
    for ten in ("A1b_PROJECT_CHARTER", "A2b_EVIDENCE_LEDGER", "A13_IMPLEMENTATION_PLAN", "A13b_RISK_REGISTER"):
        md, docx = d / f"G1_{ten}_{S_SO}.md", d / f"G1_{ten}_{S_SO}.docx"
        assert md.is_file() and docx.is_file(), ten
        assert docx.stat().st_mtime >= md.stat().st_mtime, f"{ten}: Word phải mới bằng .md"
    from docx import Document

    co = {r.font.size.pt for p in Document(d / f"G1_A2b_EVIDENCE_LEDGER_{S_SO}.docx").paragraphs for r in p.runs
          if r.font.size is not None and r.text.strip()}
    assert 13.0 in co, f"đúng chuẩn trình bày 13pt (md2docx_vn): {co}"


def test_tieu_chi_g3_khong_in_viec_cua_may_thanh_o_viec_nguoi(tmp_path, monkeypatch):
    study = "G3-VIEC-MAY"
    monkeypatch.setattr(R3, "BASE", tmp_path)
    d = tmp_path / "exports" / study
    dung_g0_g1_da_chot(d, study, thiet_ke="cross_sectional", mau_hieu_qua=[], chot_g1=True)
    CS.xoa_dem()
    monkeypatch.setattr(sys, "argv", ["run_g3_auto.py", "--study", study, "--prevalence", "0.5", "--precision", "0.05",
                                      "--dropout", "0.15"])
    with contextlib.redirect_stdout(io.StringIO()):
        R3.main()
    a4 = (d / f"G3_A4_SAMPLE_SIZE_{study}.md").read_text(encoding="utf-8")
    p5 = a4.split("## PHẦN 5 — TIÊU CHÍ QUA CỔNG G3")[1]
    o_viec = [x for x in p5.splitlines() if x.startswith("- [ ]")]
    assert o_viec and all("[CẦN BÁC SĨ]" in x for x in o_viec), o_viec
    assert "Máy tự làm, không phải ô việc của người" in p5 and "confirmed_n" in p5


def test_g1_day_du_cung_xuat_word_tai_lieu_ho_tro(tmp_path, monkeypatch):
    from test_g1_hoan_thien_20261004 import _chay_main

    with contextlib.redirect_stdout(io.StringIO()):
        d, _cp = _chay_main(tmp_path, monkeypatch, meta_g0={"question_type": "descriptive"})
    for ten in ("A1b_PROJECT_CHARTER", "A2b_EVIDENCE_LEDGER", "A13_IMPLEMENTATION_PLAN", "A13b_RISK_REGISTER"):
        md, docx = d / f"G1_{ten}_TEST-G1-MAIN.md", d / f"G1_{ten}_TEST-G1-MAIN.docx"
        assert docx.is_file() and docx.stat().st_mtime >= md.stat().st_mtime, ten
