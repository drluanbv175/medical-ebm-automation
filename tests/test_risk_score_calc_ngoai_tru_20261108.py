"""Test 7 máy tính bổ sung 08/11/2026 cho lý do khám ngoại trú thường gặp.

Mỗi test khoá một ĐIỂM CẮT đã kiểm tay theo nguồn trong docstring hàm (Wells 2003,
McIsaac 1998 + NICE NG84, Bösner 2010, Little 2013 + NICE NG84, Bauer 2006 + NICE NG250,
Stiell 1993/1996). Test biên (tuổi 54/55, 64/65; điểm 1/2, 2/3, 3/4) để đột biến lệch
một bậc ở ngưỡng làm test đỏ ngay. Không gọi mạng.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
import risk_score_calc as RS  # noqa: E402

from app.clinical_scores.verified import VERIFIED_SCORES  # noqa: E402


def _wells(**kw):
    base = dict(active_cancer=0, paralysis_or_cast=0, bedridden_or_surgery=0,
                deep_vein_tenderness=0, entire_leg_swollen=0, calf_swelling_3cm=0,
                pitting_edema=0, collateral_veins=0, previous_dvt=0,
                alternative_dx_as_likely=0)
    base.update(kw)
    return RS.wells_dvt(**base)


# ── Wells DVT ────────────────────────────────────────────────────────────────
def test_wells_dvt_bien_1_la_it_kha_nang():
    r = _wells(pitting_edema=1)
    assert r["score"] == 1
    assert "ít khả năng" in r["category"]


def test_wells_dvt_bien_2_la_nhieu_kha_nang():
    r = _wells(pitting_edema=1, calf_swelling_3cm=1)
    assert r["score"] == 2
    assert "nhiều khả năng" in r["category"]


def test_wells_dvt_chan_doan_khac_tru_2():
    r = _wells(pitting_edema=1, calf_swelling_3cm=1, alternative_dx_as_likely=1)
    assert r["score"] == 0
    assert r["components"]["alternative_dx_as_likely"] == -2


def test_wells_dvt_ung_thu_co_canh_bao_khong_an_toan():
    r = _wells(active_cancer=1)
    assert "UNG THƯ" in r["note"]


def test_wells_dvt_tu_choi_gia_tri_khong_phai_0_1():
    with pytest.raises(RS.RiskScoreError):
        _wells(pitting_edema=2)


# ── Centor / McIsaac ─────────────────────────────────────────────────────────
@pytest.mark.parametrize("age,adj", [(3, 1), (14, 1), (15, 0), (44, 0), (45, -1), (80, -1)])
def test_mcisaac_hieu_chinh_tuoi_dung_bien(age, adj):
    r = RS.centor_mcisaac(0, 0, 0, 0, age)
    assert r["components"]["age_adjustment"] == adj
    assert r["score"] == adj


def test_mcisaac_bien_1_va_2():
    assert "thấp" in RS.centor_mcisaac(1, 0, 0, 0, 30)["category"]
    assert "trung gian" in RS.centor_mcisaac(1, 1, 0, 0, 30)["category"]


def test_mcisaac_bien_3_va_4():
    assert "trung gian" in RS.centor_mcisaac(1, 1, 1, 0, 30)["category"]
    assert "cao" in RS.centor_mcisaac(1, 1, 1, 1, 30)["category"]


def test_centor_goc_nice_ng84_bien_2_va_3():
    assert RS.centor_mcisaac(1, 1, 0, 0, 50)["centor_score"] == 2
    assert "không kê kháng sinh" in RS.centor_mcisaac(1, 1, 0, 0, 50)["centor_nice_ng84"]
    assert "cân nhắc kháng sinh" in RS.centor_mcisaac(1, 1, 1, 0, 50)["centor_nice_ng84"]


def test_mcisaac_tu_choi_duoi_3_tuoi():
    with pytest.raises(RS.RiskScoreError):
        RS.centor_mcisaac(1, 1, 1, 1, 2)


# ── Marburg Heart Score ──────────────────────────────────────────────────────
@pytest.mark.parametrize("age,sex,diem", [(64, "female", 0), (65, "female", 1),
                                          (54, "male", 0), (55, "male", 1)])
def test_marburg_tieu_chi_tuoi_gioi_dung_bien(age, sex, diem):
    r = RS.marburg_heart(age, sex, 0, 0, 0, 0)
    assert r["components"]["age_sex"] == diem


def test_marburg_bien_2_am_tinh_3_duong_tinh():
    assert RS.marburg_heart(40, "male", 1, 1, 0, 0)["score"] == 2
    assert "âm tính" in RS.marburg_heart(40, "male", 1, 1, 0, 0)["category"]
    r = RS.marburg_heart(40, "male", 1, 1, 1, 0)
    assert r["score"] == 3 and "dương tính" in r["category"]


def test_marburg_toi_da_5():
    assert RS.marburg_heart(70, "female", 1, 1, 1, 1)["score"] == 5


def test_marburg_ghi_ro_khong_loai_tru_hcvc():
    assert "KHÔNG dùng để loại trừ hội chứng vành cấp" in RS.marburg_heart(40, "male", 0, 0, 0, 0)["note"]


def test_marburg_tu_choi_gioi_la_va_tuoi_tre():
    with pytest.raises(RS.RiskScoreError):
        RS.marburg_heart(40, "other", 0, 0, 0, 0)
    with pytest.raises(RS.RiskScoreError):
        RS.marburg_heart(16, "male", 0, 0, 0, 0)


# ── FeverPAIN ────────────────────────────────────────────────────────────────
def test_feverpain_bien_1_va_2():
    assert "thấp" in RS.feverpain(1, 0, 0, 0, 0)["category"]
    assert "trung gian" in RS.feverpain(1, 1, 0, 0, 0)["category"]


def test_feverpain_bien_3_va_4():
    assert "trung gian" in RS.feverpain(1, 1, 1, 0, 0)["category"]
    r = RS.feverpain(1, 1, 1, 1, 0)
    assert r["score"] == 4 and "cao" in r["category"]


def test_feverpain_toi_da_5_va_tu_choi_sai():
    assert RS.feverpain(1, 1, 1, 1, 1)["score"] == 5
    with pytest.raises(RS.RiskScoreError):
        RS.feverpain(1, 1, 1, 1, -1)


# ── CRB-65 ───────────────────────────────────────────────────────────────────
def test_crb65_tuoi_64_va_65():
    assert RS.crb65(0, 0, 0, 64)["score"] == 0
    assert RS.crb65(0, 0, 0, 65)["score"] == 1


@pytest.mark.parametrize("args,diem,nhan", [((0, 0, 0, 40), 0, "thấp"),
                                            ((1, 0, 0, 40), 1, "trung gian"),
                                            ((1, 1, 0, 40), 2, "trung gian"),
                                            ((1, 1, 1, 40), 3, "cao"),
                                            ((1, 1, 1, 70), 4, "cao")])
def test_crb65_phan_tang_nice_ng250(args, diem, nhan):
    r = RS.crb65(*args)
    assert r["score"] == diem and nhan in r["category"]


# ── Ottawa cổ chân / bàn chân ────────────────────────────────────────────────
def _ankle(**kw):
    base = dict(malleolar_pain=0, lateral_malleolus_tenderness=0, medial_malleolus_tenderness=0,
                midfoot_pain=0, fifth_metatarsal_tenderness=0, navicular_tenderness=0,
                unable_bear_weight=0)
    base.update(kw)
    return RS.ottawa_ankle(**base)


@pytest.mark.parametrize("tieu_chi", ["lateral_malleolus_tenderness",
                                      "medial_malleolus_tenderness", "unable_bear_weight"])
def test_ottawa_co_chan_moi_tieu_chi_mat_ca_deu_chi_dinh(tieu_chi):
    assert _ankle(malleolar_pain=1, **{tieu_chi: 1})["ankle_xray_indicated"] is True


def test_ottawa_co_chan_dau_mat_ca_khong_tieu_chi_la_am_tinh():
    r = _ankle(malleolar_pain=1)
    assert r["ankle_xray_indicated"] is False and r["foot_xray_indicated"] is False


def test_ottawa_an_dau_mat_ca_khi_khong_dau_vung_mat_ca_khong_chi_dinh():
    assert _ankle(lateral_malleolus_tenderness=1)["ankle_xray_indicated"] is False


@pytest.mark.parametrize("tieu_chi", ["fifth_metatarsal_tenderness", "navicular_tenderness",
                                      "unable_bear_weight"])
def test_ottawa_ban_chan_moi_tieu_chi_deu_chi_dinh(tieu_chi):
    assert _ankle(midfoot_pain=1, **{tieu_chi: 1})["foot_xray_indicated"] is True


# ── Ottawa gối ───────────────────────────────────────────────────────────────
def test_ottawa_goi_tuoi_54_va_55():
    assert RS.ottawa_knee(54, 0, 0, 0, 0)["knee_xray_indicated"] is False
    assert RS.ottawa_knee(55, 0, 0, 0, 0)["knee_xray_indicated"] is True


@pytest.mark.parametrize("idx", range(4))
def test_ottawa_goi_moi_tieu_chi_deu_chi_dinh(idx):
    bits = [0, 0, 0, 0]
    bits[idx] = 1
    assert RS.ottawa_knee(30, *bits)["knee_xray_indicated"] is True


def test_ottawa_goi_tu_choi_tre_em():
    with pytest.raises(RS.RiskScoreError):
        RS.ottawa_knee(16, 0, 0, 0, 0)


# ── Đối chiếu chéo với sổ verified.py (một nguồn sự thật) ────────────────────
@pytest.mark.parametrize("sid,n_comp", [("marburg_heart", 5), ("feverpain", 5), ("crb65", 4),
                                        ("ottawa_knee", 5), ("ottawa_ankle", 2)])
def test_thang_moi_co_trong_so_verified_kem_pmid(sid, n_comp):
    s = next(x for x in VERIFIED_SCORES if x["score_id"] == sid)
    assert s.get("pmid"), f"{sid} thiếu PMID"
    assert len(s["components"]) == n_comp
    assert s["source"] and s["guideline_reference"]


def test_nguon_may_tinh_khop_nguon_so_verified():
    """Tên tác giả + năm trong `source` của máy tính phải trùng mục verified tương ứng."""
    cap = {"marburg_heart": RS.marburg_heart(40, "male", 0, 0, 0, 0),
           "feverpain": RS.feverpain(0, 0, 0, 0, 0),
           "crb65": RS.crb65(0, 0, 0, 40),
           "ottawa_knee": RS.ottawa_knee(30, 0, 0, 0, 0),
           "ottawa_ankle": _ankle()}
    for sid, res in cap.items():
        so = next(x for x in VERIFIED_SCORES if x["score_id"] == sid)["source"]
        tac_gia = res["source"].split(" et al")[0]
        assert tac_gia in so, f"{sid}: máy tính dẫn {tac_gia!r} nhưng sổ ghi {so[:60]!r}"


# ── CLI ──────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("argv,khoa", [
    (["wells-dvt", "--active-cancer", "0", "--paralysis-or-cast", "0", "--bedridden-or-surgery", "0",
      "--deep-vein-tenderness", "1", "--entire-leg-swollen", "0", "--calf-swelling-3cm", "1",
      "--pitting-edema", "0", "--collateral-veins", "0", "--previous-dvt", "0",
      "--alternative-dx-as-likely", "0"], "score"),
    (["centor-mcisaac", "--fever-over-38", "1", "--absence-of-cough", "1",
      "--tender-anterior-nodes", "0", "--tonsillar-swelling-exudate", "0", "--age", "30"], "score"),
    (["marburg", "--age", "60", "--sex", "female", "--known-vascular-disease", "0",
      "--pain-worse-on-exercise", "1", "--pain-not-reproducible-by-palpation", "1",
      "--patient-assumes-cardiac", "0"], "score"),
    (["feverpain", "--fever-24h", "1", "--purulence", "0", "--attend-within-3-days", "1",
      "--severely-inflamed-tonsils", "0", "--no-cough-or-coryza", "1"], "score"),
    (["crb65", "--confusion", "0", "--rr-high", "0", "--bp-low", "0", "--age", "70"], "score"),
    (["ottawa-ankle", "--malleolar-pain", "1", "--lateral-malleolus-tenderness", "1",
      "--medial-malleolus-tenderness", "0", "--midfoot-pain", "0",
      "--fifth-metatarsal-tenderness", "0", "--navicular-tenderness", "0",
      "--unable-bear-weight", "0"], "ankle_xray_indicated"),
    (["ottawa-knee", "--age", "60", "--fibular-head-tenderness", "0",
      "--isolated-patellar-tenderness", "0", "--unable-flex-90", "0",
      "--unable-bear-weight", "0"], "knee_xray_indicated"),
])
def test_cli_chay_duoc_va_tra_json(argv, khoa):
    p = subprocess.run([sys.executable, str(TOOLS / "risk_score_calc.py"), *argv, "--json"],
                       capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
    assert p.returncode == 0, p.stderr
    assert khoa in json.loads(p.stdout)


def test_cli_gia_tri_sai_tra_ma_1():
    p = subprocess.run([sys.executable, str(TOOLS / "risk_score_calc.py"), "crb65",
                        "--confusion", "2", "--rr-high", "0", "--bp-low", "0", "--age", "70"],
                       capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
    assert p.returncode == 1 and "LỖI" in p.stdout
