"""Test clinical_calc.py — máy tính suy luận lâm sàng (Bayes/ngưỡng/NNT/GRADE).

Mỗi test khóa lại một ví dụ đã KIỂM TRA TAY hoặc bằng mô phỏng brute-force trước khi
viết module (xem docstring module để biết cách dẫn xuất ngưỡng test/treat — đã xác
minh 64,659 lần thử ngẫu nhiên khớp 100% với so sánh kỳ vọng lợi ích brute-force).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))
import clinical_calc as CC  # noqa: E402


# ── Bayes ────────────────────────────────────────────────────────────────────
def test_bayes_posttest_classic_fagan_example():
    # Ví dụ kinh điển Fagan nomogram: pretest 0.30, LR+ 6 -> posttest ~0.72
    assert CC.bayes_posttest(0.30, 6) == pytest.approx(0.72, abs=1e-9)


def test_bayes_rejects_invalid_pretest():
    with pytest.raises(CC.ClinicalCalcError):
        CC.bayes_posttest(1.5, 2)
    with pytest.raises(CC.ClinicalCalcError):
        CC.bayes_posttest(0.0, 2)


def test_bayes_rejects_nonpositive_lr():
    with pytest.raises(CC.ClinicalCalcError):
        CC.bayes_posttest(0.3, 0)
    with pytest.raises(CC.ClinicalCalcError):
        CC.bayes_posttest(0.3, -1)


def test_lr_from_sensitivity_specificity():
    lrs = CC.lr_from_sensitivity_specificity(0.90, 0.80)
    assert lrs["lr_positive"] == pytest.approx(0.90 / 0.20)
    assert lrs["lr_negative"] == pytest.approx(0.10 / 0.80)


def test_sequential_bayes_matches_direct_combined_lr():
    # Nhân LR tuần tự (độc lập có điều kiện) phải khớp áp LR gộp trực tiếp.
    r = CC.sequential_bayes(0.10, [5, 4], conditionally_independent=True)
    direct = CC.bayes_posttest(0.10, 20)
    assert r["posttest"] == pytest.approx(direct, abs=1e-9)


def test_sequential_bayes_rejects_non_independent():
    with pytest.raises(CC.ClinicalCalcError):
        CC.sequential_bayes(0.10, [5, 4], conditionally_independent=False)


# ── Ngưỡng test/treat (Pauker-Kassirer, dẫn xuất decision-tree) ─────────────
def test_treatment_threshold_formula():
    assert CC.treatment_threshold(harm=3, benefit=5) == pytest.approx(3 / 8)


def test_treatment_threshold_rejects_nonpositive():
    with pytest.raises(CC.ClinicalCalcError):
        CC.treatment_threshold(0, 5)
    with pytest.raises(CC.ClinicalCalcError):
        CC.treatment_threshold(3, -1)


def test_test_threshold_perfect_free_test_spans_full_range():
    # Test hoàn hảo (Se=Sp=1) miễn phí -> vùng test gần như [0,1].
    r = CC.test_threshold(se=0.999999, sp=0.999999, harm=3, benefit=5, test_cost=0)
    assert r["lower"] == pytest.approx(0, abs=1e-5)
    assert r["upper"] == pytest.approx(1, abs=1e-5)
    assert r["valid_testing_zone"] is True


def test_test_threshold_useless_test_collapses_to_treatment_threshold():
    # Test vô dụng (Se=Sp=0.5) miễn phí -> vùng test co về đúng 1 điểm = ngưỡng điều trị.
    r = CC.test_threshold(se=0.5, sp=0.5, harm=3, benefit=5, test_cost=0)
    pt = CC.treatment_threshold(3, 5)
    assert r["lower"] == pytest.approx(pt, abs=1e-9)
    assert r["upper"] == pytest.approx(pt, abs=1e-9)


def test_test_threshold_useless_test_with_cost_has_no_valid_zone():
    # Test vô dụng CÓ phí -> không có vùng test hợp lệ (lower > upper).
    r = CC.test_threshold(se=0.5, sp=0.5, harm=3, benefit=5, test_cost=0.1)
    assert r["valid_testing_zone"] is False
    assert r["lower"] > r["upper"]


def test_test_threshold_rejects_invalid_se_sp():
    with pytest.raises(CC.ClinicalCalcError):
        CC.test_threshold(se=1.5, sp=0.8, harm=3, benefit=5)


# ── NNT/ARR (Altman 1998 CI; Zhang-Yu 1998 OR->RR) ──────────────────────────
def test_nnt_from_counts_classic_example_large_n():
    r = CC.nnt_from_counts(events_control=300, n_control=1000,
                           events_experimental=200, n_experimental=1000)
    assert r["arr"] == pytest.approx(0.10, abs=1e-9)
    assert r["nnt"] == pytest.approx(10.0, abs=1e-6)
    assert r["straddles_zero"] is False
    lo, hi = r["nnt_ci"]
    assert lo < 10.0 < hi  # CI của NNT phải bao quanh điểm ước lượng


def test_nnt_from_counts_straddles_zero_with_small_n():
    r = CC.nnt_from_counts(events_control=5, n_control=40,
                           events_experimental=4, n_experimental=40)
    assert r["straddles_zero"] is True
    assert "report" in r


def test_nnt_from_counts_zero_point_estimate_reports_straddle_not_crash():
    # ARR=0 điểm ước lượng NHƯNG có CI (từ số liệu thô) -> luôn thẳng vào nhánh
    # "CI vắt qua 0" một cách graceful, KHÔNG crash chia-cho-0.
    r = CC.nnt_from_counts(events_control=100, n_control=1000,
                           events_experimental=100, n_experimental=1000)
    assert r["arr"] == pytest.approx(0.0, abs=1e-9)
    assert r["straddles_zero"] is True


def test_nnt_from_rr_rejects_zero_arr_without_ci():
    # RR=1 (không khác biệt) và KHÔNG có CI đi kèm -> không có SE để suy ra
    # straddle, phải raise rõ ràng thay vì chia cho 0 âm thầm.
    with pytest.raises(CC.ClinicalCalcError):
        CC.nnt_from_rr(cer=0.30, rr=1.0)


def test_nnt_from_rr_arithmetic():
    r = CC.nnt_from_rr(cer=0.30, rr=0.75)
    assert r["arr"] == pytest.approx(0.30 * 0.25, abs=1e-9)
    assert r["nnt"] == pytest.approx(1 / (0.30 * 0.25), abs=1e-9)


def test_or_to_rr_zhang_yu_known_value():
    # OR=2, CER=0.5 -> RR = 2/(0.5+0.5*2) = 1.3333...
    assert CC.or_to_rr(cer=0.5, orr=2) == pytest.approx(4 / 3, abs=1e-9)


def test_nnt_from_or_uses_zhang_yu_conversion():
    r = CC.nnt_from_or(cer=0.5, orr=2)
    assert r["rr_derived_from_or"] == pytest.approx(4 / 3, abs=1e-9)
    assert r["direction"] == "NNH (tác hại, ARR<0)"  # RR>1 -> tác hại ở đây


def test_nnt_rejects_invalid_inputs():
    with pytest.raises(CC.ClinicalCalcError):
        CC.nnt_from_counts(events_control=-1, n_control=100,
                           events_experimental=10, n_experimental=100)
    with pytest.raises(CC.ClinicalCalcError):
        CC.nnt_from_rr(cer=1.5, rr=0.5)
    with pytest.raises(CC.ClinicalCalcError):
        CC.nnt_from_rr(cer=0.3, rr=-1)


# ── GRADE (thuật toán chính thức, tổng hợp domain judgment) ─────────────────
def test_grade_rct_no_downgrade_stays_high():
    r = CC.grade_rating(design="rct")
    assert r["final_level"] == 4
    assert r["final_label"].startswith("Cao")


def test_grade_rct_downgraded_by_serious_rob():
    r = CC.grade_rating(design="rct", risk_of_bias=1)
    assert r["final_level"] == 3


def test_grade_observational_starts_low():
    r = CC.grade_rating(design="observational")
    assert r["start_level"] == 2
    assert r["final_level"] == 2


def test_grade_observational_upgraded_by_large_effect():
    r = CC.grade_rating(design="observational", large_effect=1)
    assert r["final_level"] == 3


def test_grade_clamps_to_valid_range_never_negative_or_over():
    # Hạ bậc dồn dập không được kéo xuống dưới 1 (Rất thấp).
    r = CC.grade_rating(design="rct", risk_of_bias=2, inconsistency=2,
                        indirectness=2, imprecision=2, publication_bias=2)
    assert r["final_level"] == 1
    # Nâng bậc dồn dập không được vượt trên 4 (Cao).
    r2 = CC.grade_rating(design="observational", large_effect=2, dose_response=1,
                         plausible_confounding_reduces_effect=1)
    assert r2["final_level"] == 4


def test_grade_rejects_invalid_design():
    with pytest.raises(CC.ClinicalCalcError):
        CC.grade_rating(design="case-control")


def test_grade_rejects_out_of_range_domain_severity():
    with pytest.raises(CC.ClinicalCalcError):
        CC.grade_rating(design="rct", risk_of_bias=3)
