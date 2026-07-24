"""Test clinical_calc.py — máy tính suy luận lâm sàng (Bayes/ngưỡng/NNT/GRADE).

Mỗi test khóa lại một ví dụ đã KIỂM TRA TAY (trường hợp biên giải tích cụ thể) trước
khi viết module (xem docstring module để biết cách dẫn xuất ngưỡng test/treat).

SỬA 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 23, phát hiện HIGH): dòng cũ ở đây
khẳng định "đã xác minh 64.659 lần thử ngẫu nhiên khớp 100% brute-force" — con số này
KHÔNG có script/seed/log nào trong repo (kể cả lịch sử git) để tái lập; gỡ bỏ khẳng
định không tái lập được. Các test dưới đây (perfect-free-test, useless-test-collapse,
useless-test-with-cost) là trường hợp biên giải tích thật, không phải Monte Carlo.
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


# ── Vá 2026-07-04 (red-team): _z_from_alpha() bản cũ ÂM THẦM trả z của alpha=0.05
# cho MỌI alpha khác khi thiếu scipy (venv dự án hiện KHÔNG có scipy) — CI 90%/80%
# dùng alpha=0.10/0.20 (rất phổ biến) bị dán nhãn sai thành CI 95%.
def test_nnt_from_counts_alpha_90pct_gives_narrower_ci_than_95pct():
    kwargs = dict(events_control=300, n_control=1000,
                  events_experimental=200, n_experimental=1000)
    r95 = CC.nnt_from_counts(alpha=0.05, **kwargs)
    r90 = CC.nnt_from_counts(alpha=0.10, **kwargs)
    lo95, hi95 = r95["arr_ci"]
    lo90, hi90 = r90["arr_ci"]
    assert (hi90 - lo90) < (hi95 - lo95)  # CI 90% phải HẸP hơn CI 95%
    assert r90["arr_ci"] != r95["arr_ci"]  # bug cũ: 2 khoảng này từng GIỐNG HỆT nhau


def test_z_from_alpha_matches_known_critical_values_without_scipy():
    assert CC._z_from_alpha(0.05) == pytest.approx(1.959963985, abs=1e-6)
    assert CC._z_from_alpha(0.10) == pytest.approx(1.644853627, abs=1e-6)
    assert CC._z_from_alpha(0.20) == pytest.approx(1.281551566, abs=1e-6)
    assert CC._z_from_alpha(0.01) == pytest.approx(2.575829304, abs=1e-6)


def test_z_from_alpha_rejects_out_of_range():
    with pytest.raises(CC.ClinicalCalcError):
        CC._z_from_alpha(0.0)
    with pytest.raises(CC.ClinicalCalcError):
        CC._z_from_alpha(1.5)


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


# ── GRADE-DTA (2026-07-12, task_5a25a9c7) — độ chính xác chẩn đoán ─────────
# Bắt đầu CAO (như RCT), xác minh qua PubMed TRƯỚC khi code (Schünemann et al.
# J Clin Epidemiol 2020;122:129-141, PMID:32060007) — KHÔNG suy đoán từ "observational".

def test_grade_dta_starts_high_like_rct_not_low_like_observational():
    r = CC.grade_rating(design="dta")
    assert r["start_level"] == 4
    assert r["start_label"].startswith("Cao")
    assert r["final_level"] == 4


def test_grade_dta_downgraded_by_quadas2_risk_of_bias():
    # risk_of_bias ở đây được chấm bằng QUADAS-2 (không phải RoB 2) — cùng thang 0/1/2.
    r = CC.grade_rating(design="dta", risk_of_bias=1)
    assert r["final_level"] == 3
    assert "QUADAS-2" in r["note"]


def test_grade_dta_downgraded_by_indirectness_and_imprecision():
    r = CC.grade_rating(design="dta", indirectness=1, imprecision=2)
    assert r["final_level"] == 1  # 4 - 1 - 2 = 1


def test_grade_dta_has_no_observational_upgrade_factors():
    # GRADE-DTA không định nghĩa large_effect/dose_response/confounding — truyền vào
    # không được cộng thêm điểm (khác observational, nơi các yếu tố này CÓ áp dụng).
    r = CC.grade_rating(design="dta", large_effect=2, dose_response=1,
                        plausible_confounding_reduces_effect=1)
    assert r["total_upgrade"] == 0
    assert r["final_level"] == 4  # vẫn kẹp ở trần 4, không vượt
    assert r["domains"]["large_effect"] != 2


def test_grade_dta_accepted_by_cli_design_choices():
    # Hồi quy: trước bản vá, "dta" không có trong _START_LEVEL -> ClinicalCalcError.
    r = CC.grade_rating(design="DTA")  # cũng kiểm chuẩn hóa hoa/thường
    assert r["design"] == "dta"


# ── CLI --pretest percent-vs-decimal guard (vòng lặp vòng 23, phát hiện MEDIUM) ──
class TestBayesCliPretestWarning:
    """Trước vá 2026-07-24: chan-doan-xac-suat.md nhắc bác sĩ tự xác nhận đã chia 100
    trước khi gọi --pretest, nhưng KHÔNG có backstop kỹ thuật nào trong công cụ — lỗi
    gõ nhầm "0.5" (nghĩ "0,5%") vẫn bị chấp nhận âm thầm. Nay CLI tự cảnh báo khi
    pretest > 0.3 (không chặn cứng, vì bác sĩ có thể có pretest thật sự cao)."""

    def _run(self, *args):
        import subprocess
        repo_root = Path(__file__).resolve().parent.parent
        return subprocess.run(
            [sys.executable, str(TOOLS / "clinical_calc.py"), *args],
            cwd=repo_root, capture_output=True, text=True, timeout=30,
        )

    def test_high_pretest_triggers_warning(self):
        res = self._run("bayes", "--pretest", "0.5", "--lr", "6", "--json")
        assert res.returncode == 0, res.stderr
        import json
        out = json.loads(res.stdout)
        assert "warning" in out
        assert "0.3" in out["warning"]

    def test_low_pretest_no_warning(self):
        res = self._run("bayes", "--pretest", "0.005", "--lr", "6", "--json")
        assert res.returncode == 0, res.stderr
        import json
        out = json.loads(res.stdout)
        assert "warning" not in out

    def test_pretest_at_boundary_no_warning(self):
        res = self._run("bayes", "--pretest", "0.3", "--lr", "6", "--json")
        import json
        out = json.loads(res.stdout)
        assert "warning" not in out
