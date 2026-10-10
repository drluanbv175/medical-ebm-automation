# -*- coding: utf-8 -*-
"""G6-AUTO-09 có chủ theo thiết kế: tổng quan hệ thống có gộp ⇒ G6-T2 `meta-phan-tich` (10/10/2026).

Đo 10/10: G6-T2 (phân tích gộp, chỉ khi tổng quan hệ thống có gộp định lượng) không gắn tiêu chí máy nào, dù G6-AUTO-09
(mô hình phân tích chính ↔ SAP §4) có họ «meta» và khuôn script SR/MA của `run_g6_auto` sinh đúng metabin/metagen —
tiêu chí giao cố định cho G6-T1 `phan-tich-thong-ke`. Nay ô có điều kiện «G6-T2|G6-T1» (khuôn của G2-AUTO-07).
Ngoại tuyến, dữ liệu giả.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import g6_quality_gate as G6Q  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import run_g6_auto as R6  # noqa: E402
import skill_standards as SK  # noqa: E402

STUDY = "G6T2-THU"


@pytest.mark.parametrize("thiet_ke, nhiem_vu, agent", [
    ("sr_ma", "G6-T2", "meta-phan-tich"),
    ("cohort", "G6-T1", "phan-tich-thong-ke"),
    ("rct", "G6-T1", "phan-tich-thong-ke"),
    (None, "G6-T1", "phan-tich-thong-ke"),
])
def test_chu_g6_auto_09_theo_thiet_ke(thiet_ke, nhiem_vu, agent):
    pc = HD.phan_cong("G6", "G6-AUTO-09", thiet_ke)
    assert (pc["nhiem_vu"], pc["agent"], pc["lua_chon"]) == (nhiem_vu, agent, ["G6-T2", "G6-T4", "G6-T5", "G6-T1"])


def test_g6t2_khong_con_la_nhiem_vu_khong_tieu_chi():
    assert "G6-T2" not in HD.nhiem_vu_khong_tieu_chi("G6")
    assert "G6-T3" in HD.nhiem_vu_khong_tieu_chi("G6"), "diễn giải vẫn chỉ bảo đảm bằng đánh giá chéo"


def test_g6_auto_09_that_su_phu_ho_meta_cua_khuon_sr_ma():
    """Neo: khuôn script SR/MA của bộ sinh G6 được bộ chấm nhận là họ «meta»; SAP «random-effects» rút ra họ «meta»."""
    assert G6Q._ho_mo_hinh_script(R6._r03_srma_template())[:1] == ["meta"]
    assert "meta" in G6Q._ho_mo_hinh_sap("phân tích gộp random-effects (REML), báo I² và τ²")


@pytest.mark.parametrize("thiet_ke, agent", [("sr_ma", "meta-phan-tich"), ("cohort", "phan-tich-thong-ke")])
def test_bang_trach_nhiem_giao_dung_agent(monkeypatch, tmp_path, thiet_ke, agent):
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    (out / f"G6_A7_ANALYSIS_SCRIPTS_{STUDY}.md").write_text("# A7\n", encoding="utf-8", newline="\n")
    hang = [{"id": ma, "status": "BLOCK" if ma == "G6-AUTO-09" else "PASS",
             "evidence": "phân tích chính khác SAP §4"} for ma in HD.PHAN_CONG["G6"]]
    monkeypatch.setattr(CS, "trang_thai_song", lambda *a, **k: {"status": "DRAFT_G6_SCRIPTS", "nguon": "song",
                                                                 "bao_cao": {"automatic_criteria": hang}})
    monkeypatch.setattr(SK, "dac_ta_thiet_ke", lambda out_dir: {"design_code": thiet_ke})
    kq = HD.trach_nhiem(STUDY, "G6", out)
    viec = [m for m in kq["agent_con_viec"] if m["id"] == "G6-AUTO-09"]
    assert len(viec) == 1 and viec[0]["agent"] == agent, viec


def test_tai_lieu_hai_agent_neu_dung_vai():
    meta = (ROOT / ".claude" / "agents" / "meta-phan-tich.md").read_text(encoding="utf-8")
    pttk = (ROOT / ".claude" / "agents" / "phan-tich-thong-ke.md").read_text(encoding="utf-8")
    assert "G6-AUTO-09 (nếu áp dụng)" in meta
    assert "G6-AUTO-09 (khi G6-T2 không áp dụng)" in pttk
