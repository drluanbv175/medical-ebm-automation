"""Test risk_score_calc.py — máy tính thang điểm nguy cơ lâm sàng.

Mỗi test khóa một điểm số đã KIỂM TRA TAY theo công thức/bảng điểm gốc trích trong
docstring module (Lip 2010, Pisters 2010, Lim 2003, Singer 2016, Wells 2000, Kline
2004, Pugh 1973, Kamath 2001/OPTN).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))
import risk_score_calc as RS  # noqa: E402


# ── CHA₂DS₂-VASc ─────────────────────────────────────────────────────────────
def test_cha2ds2vasc_hand_calculation():
    r = RS.cha2ds2vasc(chf=0, hypertension=1, age=78, diabetes=1,
                       stroke_tia_thromboembolism=0, vascular_disease=0, sex="male")
    assert r["score"] == 4  # age>=75(2) + htn(1) + dm(1)


def test_cha2ds2vasc_female_alone_no_sex_point():
    r = RS.cha2ds2vasc(chf=0, hypertension=0, age=40, diabetes=0,
                       stroke_tia_thromboembolism=0, vascular_disease=0, sex="female")
    assert r["score"] == 0
    assert r["components"]["sex_points"] == 0


def test_cha2ds2vasc_female_with_other_factor_gets_sex_point():
    r = RS.cha2ds2vasc(chf=0, hypertension=1, age=40, diabetes=0,
                       stroke_tia_thromboembolism=0, vascular_disease=0, sex="female")
    assert r["components"]["sex_points"] == 1
    assert r["score"] == 2  # htn(1) + sex(1)


def test_cha2ds2vasc_age_65_74_gives_1_point_not_2():
    r = RS.cha2ds2vasc(chf=0, hypertension=0, age=70, diabetes=0,
                       stroke_tia_thromboembolism=0, vascular_disease=0, sex="male")
    assert r["components"]["age_points"] == 1


def test_cha2ds2vasc_stroke_tia_worth_2_points():
    r = RS.cha2ds2vasc(chf=0, hypertension=0, age=40, diabetes=0,
                       stroke_tia_thromboembolism=1, vascular_disease=0, sex="male")
    assert r["score"] == 2


def test_cha2ds2vasc_rejects_invalid_sex():
    with pytest.raises(RS.RiskScoreError):
        RS.cha2ds2vasc(chf=0, hypertension=0, age=40, diabetes=0,
                       stroke_tia_thromboembolism=0, vascular_disease=0, sex="other")


def test_cha2ds2vasc_rejects_non_binary_input():
    with pytest.raises(RS.RiskScoreError):
        RS.cha2ds2vasc(chf=2, hypertension=0, age=40, diabetes=0,
                       stroke_tia_thromboembolism=0, vascular_disease=0, sex="male")


# ── HAS-BLED ─────────────────────────────────────────────────────────────────
def test_hasbled_simple_sum():
    r = RS.hasbled(hypertension=1, abnormal_renal=1, abnormal_liver=0, stroke=0,
                   bleeding_history=0, labile_inr=0, age=70, drugs=0, alcohol=0)
    assert r["score"] == 3  # htn(1)+renal(1)+elderly>65(1)
    assert "cao" in r["category"]


def test_hasbled_max_score_9():
    r = RS.hasbled(hypertension=1, abnormal_renal=1, abnormal_liver=1, stroke=1,
                   bleeding_history=1, labile_inr=1, age=80, drugs=1, alcohol=1)
    assert r["score"] == 9


# ── CURB-65 ──────────────────────────────────────────────────────────────────
def test_curb65_hand_calculation():
    r = RS.curb65(confusion=0, urea_high=1, rr_high=0, bp_low=0, age=78)
    assert r["score"] == 2
    assert "vừa" in r["category"]


def test_curb65_zero_low_risk():
    r = RS.curb65(confusion=0, urea_high=0, rr_high=0, bp_low=0, age=40)
    assert r["score"] == 0
    assert "nhẹ" in r["category"]


def test_curb65_high_score_severe():
    r = RS.curb65(confusion=1, urea_high=1, rr_high=1, bp_low=1, age=78)
    assert r["score"] == 5
    assert "nặng" in r["category"]


# ── qSOFA ────────────────────────────────────────────────────────────────────
def test_qsofa_threshold_at_2():
    r1 = RS.qsofa(rr_high=1, altered_mentation=0, sbp_low=0)
    assert r1["score"] == 1 and "thấp" in r1["category"]
    r2 = RS.qsofa(rr_high=1, altered_mentation=1, sbp_low=0)
    assert r2["score"] == 2 and "tăng" in r2["category"]


# ── Wells (PE) ───────────────────────────────────────────────────────────────
def test_wells_pe_float_arithmetic():
    r = RS.wells_pe(dvt_signs=0, pe_most_likely=1, hr_over_100=1,
                    immobilization_surgery=0, previous_dvt_pe=0,
                    hemoptysis=0, malignancy=0)
    assert r["score"] == pytest.approx(4.5)  # 3.0 + 1.5
    assert r["three_tier_category"] == "vừa (2-6)"
    assert "likely" in r["two_tier_category"] and "không" not in r["two_tier_category"]


def test_wells_pe_zero_score_low_tier():
    r = RS.wells_pe(dvt_signs=0, pe_most_likely=0, hr_over_100=0,
                    immobilization_surgery=0, previous_dvt_pe=0,
                    hemoptysis=0, malignancy=0)
    assert r["score"] == 0.0
    assert r["three_tier_category"] == "thấp (<2)"


def test_wells_pe_max_score():
    r = RS.wells_pe(dvt_signs=1, pe_most_likely=1, hr_over_100=1,
                    immobilization_surgery=1, previous_dvt_pe=1,
                    hemoptysis=1, malignancy=1)
    assert r["score"] == pytest.approx(12.5)


# ── PERC ─────────────────────────────────────────────────────────────────────
def test_perc_all_pass():
    r = RS.perc(age_under_50=1, hr_under_100=1, spo2_95_or_above=1, no_hemoptysis=1,
               no_estrogen=1, no_prior_dvt_pe=1, no_leg_swelling=1, no_recent_surgery_trauma=1)
    assert r["all_criteria_met"] is True
    assert r["n_criteria_met"] == 8


def test_perc_one_fail():
    r = RS.perc(age_under_50=0, hr_under_100=1, spo2_95_or_above=1, no_hemoptysis=1,
               no_estrogen=1, no_prior_dvt_pe=1, no_leg_swelling=1, no_recent_surgery_trauma=1)
    assert r["all_criteria_met"] is False
    assert r["n_criteria_met"] == 7


# ── Child-Pugh ───────────────────────────────────────────────────────────────
def test_child_pugh_hand_calculation_class_c():
    r = RS.child_pugh(bilirubin=2.5, albumin=3.0, inr=1.9,
                      ascites="moderate_severe", encephalopathy="none")
    assert r["score"] == 10  # 2+2+2+3+1
    assert r["class"] == "C"


def test_child_pugh_best_case_class_a():
    r = RS.child_pugh(bilirubin=1.0, albumin=4.0, inr=1.0,
                      ascites="none", encephalopathy="none")
    assert r["score"] == 5
    assert r["class"] == "A"


def test_child_pugh_worst_case_class_c():
    r = RS.child_pugh(bilirubin=5.0, albumin=2.0, inr=3.0,
                      ascites="moderate_severe", encephalopathy="grade_3_4")
    assert r["score"] == 15
    assert r["class"] == "C"


def test_child_pugh_rejects_invalid_category():
    with pytest.raises(RS.RiskScoreError):
        RS.child_pugh(bilirubin=2.0, albumin=3.0, inr=1.5, ascites="severe", encephalopathy="none")


# ── MELD ─────────────────────────────────────────────────────────────────────
def test_meld_hand_calculation():
    r = RS.meld(bilirubin=2.5, inr=1.9, creatinine=1.8)
    expected = 3.78 * math.log(2.5) + 11.2 * math.log(1.9) + 9.57 * math.log(1.8) + 6.43
    assert r["raw_before_rounding_and_clamp"] == pytest.approx(expected, abs=1e-9)
    assert r["score"] == round(expected)


def test_meld_values_under_1_clamped_to_1_before_log():
    # bilirubin=0.5 -> ép về 1.0 trước log(1.0)=0, không âm.
    r = RS.meld(bilirubin=0.5, inr=1.0, creatinine=0.8)
    assert r["inputs_used"]["bilirubin"] == 1.0
    assert r["inputs_used"]["creatinine"] == 1.0


def test_meld_dialysis_forces_creatinine_to_4():
    r = RS.meld(bilirubin=2.0, inr=1.5, creatinine=1.0, dialysis_2x_past_week=True)
    assert r["inputs_used"]["creatinine"] == 4.0


def test_meld_creatinine_capped_at_4_without_dialysis():
    r = RS.meld(bilirubin=2.0, inr=1.5, creatinine=8.0, dialysis_2x_past_week=False)
    assert r["inputs_used"]["creatinine"] == 4.0


def test_meld_score_bounded_6_to_40():
    r_low = RS.meld(bilirubin=1.0, inr=1.0, creatinine=1.0)
    assert r_low["score"] >= 6
    r_high = RS.meld(bilirubin=50.0, inr=10.0, creatinine=4.0)
    assert r_high["score"] <= 40


def test_meld_rejects_nonpositive_inputs():
    with pytest.raises(RS.RiskScoreError):
        RS.meld(bilirubin=0, inr=1.5, creatinine=1.0)
