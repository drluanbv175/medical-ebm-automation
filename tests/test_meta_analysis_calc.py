"""Test meta_analysis_calc.py — máy tính phân tích gộp (meta-analysis).

pool_effects/egger_test đối chiếu khớp CHÍNH XÁC (float precision) với
statsmodels.stats.meta_analysis.combine_effects / statsmodels.api.OLS — thư viện
thống kê đã bình duyệt, độc lập (xem docstring module). Test này khóa các con số đã
đối chiếu đó làm hồi quy chuẩn.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))
import meta_analysis_calc as MC  # noqa: E402


# ── pool_effects — đối chiếu khớp statsmodels.combine_effects ──────────────
def test_pool_effects_matches_statsmodels_heterogeneous_case():
    r = MC.pool_effects([0.10, 0.55, -0.20, 0.60, 0.05], [0.02, 0.03, 0.025, 0.04, 0.015])
    assert r["fixed_effect"]["pooled"] == pytest.approx(0.15658914728682172, abs=1e-9)
    assert r["random_effect"]["pooled"] == pytest.approx(0.20136703393083213, abs=1e-9)
    assert r["heterogeneity"]["Q"] == pytest.approx(16.078165374677006, abs=1e-9)
    assert r["heterogeneity"]["tau2"] == pytest.approx(0.07224497681607421, abs=1e-9)
    assert r["heterogeneity"]["I2_percent"] == pytest.approx(75.12153963598377, abs=1e-6)


def test_pool_effects_clamps_negative_tau2_to_zero():
    # Ví dụ có Q < df (statsmodels combine_effects cho tau2 THÔ âm ~-0.0194,
    # KHÔNG tự kẹp) — module này PHẢI kẹp về 0, random == fixed.
    r = MC.pool_effects([0.1, 0.3, -0.05, 0.25, 0.15], [0.04, 0.09, 0.02, 0.06, 0.03])
    assert r["heterogeneity"]["tau2_raw_before_clamp"] < 0
    assert r["heterogeneity"]["tau2"] == 0.0
    assert r["heterogeneity"]["I2_percent"] == 0.0
    assert r["random_effect"]["pooled"] == pytest.approx(r["fixed_effect"]["pooled"], abs=1e-9)


def test_pool_effects_homogeneous_studies_zero_heterogeneity():
    # Nghiên cứu GIỐNG HỆT nhau -> Q~0, tau2=0, I2=0, random==fixed.
    r = MC.pool_effects([0.2, 0.2, 0.2], [0.01, 0.01, 0.01])
    assert r["heterogeneity"]["Q"] == pytest.approx(0.0, abs=1e-9)
    assert r["heterogeneity"]["tau2"] == 0.0
    assert r["fixed_effect"]["pooled"] == pytest.approx(0.2, abs=1e-9)
    assert r["random_effect"]["pooled"] == pytest.approx(0.2, abs=1e-9)


def test_pool_effects_prediction_interval_only_when_k_geq_3():
    r2 = MC.pool_effects([0.1, 0.3], [0.02, 0.03])
    assert r2["prediction_interval"]["pi"] is None
    r3 = MC.pool_effects([0.1, 0.3, 0.2], [0.02, 0.03, 0.025])
    assert r3["prediction_interval"]["pi"] is not None
    lo, hi = r3["prediction_interval"]["pi"]
    assert lo < r3["random_effect"]["pooled"] < hi


def test_pool_effects_rejects_too_few_studies():
    with pytest.raises(MC.MetaCalcError):
        MC.pool_effects([0.1], [0.02])


def test_pool_effects_rejects_nonpositive_variance():
    with pytest.raises(MC.MetaCalcError):
        MC.pool_effects([0.1, 0.2], [0.02, 0.0])


def test_pool_effects_rejects_mismatched_lengths():
    with pytest.raises(MC.MetaCalcError):
        MC.pool_effects([0.1, 0.2, 0.3], [0.02, 0.03])


# ── egger_test — đối chiếu khớp statsmodels.api.OLS ─────────────────────────
def test_egger_matches_statsmodels_ols():
    r = MC.egger_test([0.10, 0.55, -0.20, 0.60, 0.05], [0.02, 0.03, 0.025, 0.04, 0.015])
    assert r["intercept"] == pytest.approx(7.014757493308562, abs=1e-6)
    assert r["t"] == pytest.approx(1.47396678278401, abs=1e-6)
    assert r["p_value"] == pytest.approx(0.23692653810027164, abs=1e-4)


def test_egger_rejects_too_few_studies():
    with pytest.raises(MC.MetaCalcError):
        MC.egger_test([0.1, 0.2], [0.02, 0.03])


# ── Chuyển đổi cỡ hiệu ứng ───────────────────────────────────────────────────
def test_log_or_from_2x2_matches_hand_calculation():
    r = MC.log_or_from_2x2(15, 85, 5, 95)
    assert r["or"] == pytest.approx((15 * 95) / (85 * 5), abs=1e-9)


def test_log_rr_from_2x2_matches_hand_calculation():
    r = MC.log_rr_from_2x2(15, 85, 5, 95)
    assert r["rr"] == pytest.approx((15 / 100) / (5 / 100), abs=1e-9)


def test_2x2_applies_haldane_correction_on_zero_cell():
    r = MC.log_or_from_2x2(0, 85, 5, 95)
    assert "note" in r  # đã cảnh báo hiệu chỉnh liên tục
    assert math.isfinite(r["log_or"])


def test_2x2_rejects_negative_counts():
    with pytest.raises(MC.MetaCalcError):
        MC.log_or_from_2x2(-1, 85, 5, 95)


def test_log_hr_from_ci_matches_parmar_tierney_formula():
    r = MC.log_hr_from_ci(0.72, 0.58, 0.89)
    assert r["log_hr"] == pytest.approx(math.log(0.72), abs=1e-12)
    expected_se = (math.log(0.89) - math.log(0.58)) / (2 * 1.96)
    assert r["se"] == pytest.approx(expected_se, abs=1e-12)


def test_log_hr_from_ci_rejects_nonpositive_values():
    with pytest.raises(MC.MetaCalcError):
        MC.log_hr_from_ci(0, 0.58, 0.89)
    with pytest.raises(MC.MetaCalcError):
        MC.log_hr_from_ci(0.72, -0.1, 0.89)


def test_log_hr_from_ci_rejects_hr_outside_confidence_interval():
    with pytest.raises(MC.MetaCalcError):
        MC.log_hr_from_ci(0.95, 0.58, 0.89)  # hr not strictly between ci bounds


def test_smd_hedges_g_bias_correction_shrinks_toward_zero():
    # J luôn < 1 (hiệu chỉnh sai lệch mẫu nhỏ) -> |g| < |d| luôn đúng khi d>0.
    r = MC.smd_from_groups(5, 2, 10, 4, 2.2, 8)
    assert r["j_correction"] < 1.0
    assert abs(r["hedges_g"]) < abs(r["cohens_d"])


def test_smd_j_correction_approaches_1_for_large_n():
    r = MC.smd_from_groups(5, 2, 300, 4, 2.2, 280)
    assert r["j_correction"] > 0.99


def test_smd_rejects_small_n():
    with pytest.raises(MC.MetaCalcError):
        MC.smd_from_groups(5, 2, 1, 4, 2.2, 8)


# ── Vá 2026-07-04 (red-team): sd1=sd2=0 (SD chưa tính được bị điền tạm 0, hoặc thang
# đo hằng số) khiến pooled_sd=0 -> trước đây crash ZeroDivisionError thô (traceback
# Python không rõ nguyên nhân với người dùng lâm sàng) thay vì MetaCalcError rõ ràng.
def test_smd_rejects_both_sd_zero_with_clear_error_not_raw_crash():
    with pytest.raises(MC.MetaCalcError):
        MC.smd_from_groups(5, 0, 10, 4, 0, 8)


def test_smd_accepts_one_sd_zero_other_nonzero():
    # Chỉ 1 nhóm SD=0 vẫn tính được (pooled_sd>0 nhờ nhóm còn lại).
    r = MC.smd_from_groups(5, 0, 10, 4, 2.0, 8)
    assert r["hedges_g"] is not None


# ── Vá 2026-07-04 (red-team, cùng lỗi đã tìm ở clinical_calc.py/interim_analysis_calc.py):
# _z_from_alpha() bản cũ ÂM THẦM trả z của alpha=0.05 cho MỌI alpha khác khi thiếu scipy.
def test_z_from_alpha_matches_known_critical_values_without_scipy():
    assert MC._z_from_alpha(0.05) == pytest.approx(1.959963985, abs=1e-6)
    assert MC._z_from_alpha(0.10) == pytest.approx(1.644853627, abs=1e-6)
    assert MC._z_from_alpha(0.20) == pytest.approx(1.281551566, abs=1e-6)


def test_pool_effects_ci_width_differs_for_alpha_90_vs_95():
    effects = [0.1, 0.2, 0.15]
    variances = [0.01, 0.015, 0.012]
    r95 = MC.pool_effects(effects, variances, alpha=0.05)
    r90 = MC.pool_effects(effects, variances, alpha=0.10)
    w95 = r95["fixed_effect"]["ci"][1] - r95["fixed_effect"]["ci"][0]
    w90 = r90["fixed_effect"]["ci"][1] - r90["fixed_effect"]["ci"][0]
    assert w90 < w95  # bug cũ: 2 khoảng này từng GIỐNG HỆT nhau


def test_md_from_groups_simple_difference():
    r = MC.md_from_groups(5, 2, 30, 4, 2.2, 28)
    assert r["md"] == pytest.approx(1.0, abs=1e-9)
    assert r["se"] == pytest.approx(math.sqrt(4 / 30 + 4.84 / 28), abs=1e-9)


# ── CLI smoke test ───────────────────────────────────────────────────────────
# Vá 2026-07-26 (vòng lặp kiểm tra-hoàn thiện vòng 28): argparse's add_parser(help=...)
# treats a literal "%" in the help string as an old-style format directive and crashes
# at parser-build time (ValueError: unsupported format character) UNLESS escaped as
# "%%" — a bug the pure-function unit tests above never exercise, since they call
# MC.<fn>() directly and never build the argparse parser. This test runs the actual
# CLI entry point so a future subcommand with an unescaped "%" in its help text fails
# the test suite instead of only failing at first real invocation.
def test_cli_hr_subcommand_runs_without_argparse_error():
    import subprocess

    script = TOOLS / "meta_analysis_calc.py"
    result = subprocess.run(
        [sys.executable, str(script), "hr", "--hr", "0.72",
         "--ci_lower", "0.58", "--ci_upper", "0.89", "--json"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "log_hr" in result.stdout
