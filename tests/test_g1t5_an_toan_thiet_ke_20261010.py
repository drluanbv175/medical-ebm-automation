# -*- coding: utf-8 -*-
"""Kiểm máy cấp nhiệm vụ G1-T5 — an toàn người tham gia trong đề cương lõi RCT (10/10/2026).

Bác sĩ giao «Gộp và tiếp tục hoàn thiện». Đo 10/10: G1-T5 (`an-toan-nghien-cuu`, RCT) không gắn tiêu chí máy nào —
G1-AUTO-07 đếm ô trống đề cương lõi nhưng giao hết cho G1-T1 (`thiet-ke-nghien-cuu`), kể cả hai dòng an toàn (cân
bằng lợi ích–nguy cơ; tiêu chí dừng/chuyển/điều trị cứu hộ). Kiểm này dùng ĐÚNG `g1_quality_gate.o_trong_pham_vi_g1`
và chỉ lọc hai dòng đó. Ngoại tuyến, dữ liệu giả.
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
import g1_quality_gate as G1Q  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import skill_standards as SK  # noqa: E402

STUDY = "G1T5-THU"
DU = {"benefit_risk_rationale": "Can thiệp nguy cơ thấp, lợi ích kỳ vọng trên kết cục chính có nguồn.",
      "stopping_rescue_rules": "Ngừng can thiệp khi có biến cố nặng; điều trị cứu hộ theo phác đồ khoa."}


def _a2(g1: dict, internal: str = "rct") -> str:
    meta = {"gate_params": {"G1": g1}}
    return G1Q.build_protocol_core(study=STUDY, topic="thử nghiệm X", design={"internal_code": internal},
                                   meta=meta, generated_at="2026-10-10")


def _de_tai(tmp_path: Path, van: str) -> Path:
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    (out / f"G1_A2_PROTOCOL_DESIGN_{STUDY}.md").write_text(van, encoding="utf-8", newline="\n")
    return out


def test_nhan_dong_chep_dung_khuon_sinh_that():
    van = _a2({})
    for nhan in HD._DONG_AN_TOAN_G1:
        assert van.count(nhan) == 1, nhan


def test_hai_dong_an_toan_da_dien_thi_qua(tmp_path):
    assert HD._kiem_an_toan_thiet_ke(_de_tai(tmp_path, _a2(DU)), STUDY) == []


@pytest.mark.parametrize("bo, can", [
    ("stopping_rescue_rules", "- Tiêu chí dừng/chuyển/điều trị cứu hộ"),
    ("benefit_risk_rationale", "- Cân bằng lợi ích, nguy cơ"),
])
def test_dong_an_toan_con_trong_bi_bat(tmp_path, bo, can):
    g1 = {k: v for k, v in DU.items() if k != bo}
    loi = HD._kiem_an_toan_thiet_ke(_de_tai(tmp_path, _a2(g1)), STUDY)
    assert len(loi) == 1 and loi[0].startswith("đề cương lõi còn trống: " + can), loi


def test_na_co_ly_do_hop_le_nhu_bo_cham(tmp_path):
    g1 = dict(DU, stopping_rescue_rules="N/A — can thiệp giáo dục sức khoẻ, không có tiêu chí dừng riêng")
    assert HD._kiem_an_toan_thiet_ke(_de_tai(tmp_path, _a2(g1)), STUDY) == []


def test_o_trong_khac_cua_g1_khong_quy_cho_g1t5(tmp_path):
    """Dòng trống không thuộc an toàn (vd team_roles, randomisation) vẫn là việc của G1-T1 qua G1-AUTO-07."""
    van = _a2(DU)
    assert G1Q.o_trong_pham_vi_g1(van), "đồ gá phải còn ô trống khác để phép thử có nghĩa"
    assert HD._kiem_an_toan_thiet_ke(_de_tai(tmp_path, van), STUDY) == []


def test_de_cuong_khuon_cu_thieu_dong_bi_bat(tmp_path):
    loi = HD._kiem_an_toan_thiet_ke(_de_tai(tmp_path, "# A2\n\n## PHẦN 0 — ĐỀ CƯƠNG LÕI\n- Mục tiêu: x\n\n---\n"),
                                    STUDY)
    assert len(loi) == 2 and all(x.startswith("đề cương lõi thiếu dòng «") for x in loi), loi


def test_dong_nam_ngoai_phan_0_khong_tinh(tmp_path):
    """Nhãn chỉ xuất hiện SAU PHẦN 0 (vd phụ lục) không thay được dòng của đề cương lõi."""
    van = ("## PHẦN 0 — ĐỀ CƯƠNG LÕI\n- Mục tiêu: x\n\n---\n## PHỤ LỤC\n"
           + "\n".join(f"{n} có nội dung" for n in HD._DONG_AN_TOAN_G1) + "\n")
    assert len(HD._kiem_an_toan_thiet_ke(_de_tai(tmp_path, van), STUDY)) == 2


def test_thieu_tep_khong_ghi_kiem(tmp_path):
    out = tmp_path / "exports" / STUDY
    out.mkdir(parents=True)
    assert HD._kiem_an_toan_thiet_ke(out, STUDY) == []


@pytest.mark.parametrize("thiet_ke, chay", [("rct", True), ("cohort", False), (None, False)])
def test_bang_trach_nhiem_chi_kiem_khi_chac_la_rct(monkeypatch, tmp_path, thiet_ke, chay):
    out = _de_tai(tmp_path, _a2({k: v for k, v in DU.items() if k != "stopping_rescue_rules"}))
    hang = [{"id": ma, "status": "PASS"} for ma in HD.PHAN_CONG["G1"]]
    monkeypatch.setattr(CS, "trang_thai_song", lambda *a, **k: {"status": "PASS_G1_CONFIRMED", "nguon": "song",
                                                                 "bao_cao": {"automatic_criteria": hang}})
    monkeypatch.setattr(SK, "dac_ta_thiet_ke", lambda out_dir: {"design_code": thiet_ke})
    kq = HD.trach_nhiem(STUDY, "G1", out)
    viec = [m for m in kq["agent_con_viec"] if m["id"] == "G1-T5:kiem-may"]
    assert bool(viec) is chay
    if chay:
        assert viec[0]["agent"] == "an-toan-nghien-cuu" and "Tiêu chí dừng" in viec[0]["viec"]
        assert kq["ket_luan"] == "AGENT_CON_VIEC"
