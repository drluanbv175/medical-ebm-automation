"""Test interim_analysis_calc.py — hàm chi tiêu alpha (Lan-DeMets) + công suất có
điều kiện (Brownian motion drift theory).

alpha_spending đối chiếu với giá trị y văn thường trích (O'Brien-Fleming K=2, α=0.05
hai phía → ~0.0054-0.0057 ở t=0.5). conditional_power đối chiếu mô phỏng Brownian
motion độc lập 20 triệu đường (xem quá trình xác minh trong lịch sử phiên) — test
này khóa các giá trị đã xác minh làm hồi quy chuẩn.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))
import interim_analysis_calc as IA  # noqa: E402


# ── Alpha spending ───────────────────────────────────────────────────────────
def test_obrien_fleming_equals_overall_alpha_at_t1():
    r = IA.alpha_spending(1.0, 0.05, "obrien-fleming")
    assert r["alpha_spent_cumulative"] == pytest.approx(0.05, abs=1e-9)


def test_pocock_equals_overall_alpha_at_t1():
    r = IA.alpha_spending(1.0, 0.05, "pocock")
    assert r["alpha_spent_cumulative"] == pytest.approx(0.05, abs=1e-9)


def test_obrien_fleming_matches_commonly_cited_textbook_value_at_half_information():
    # K=2 chia đều, alpha=0.05 hai phía -> y văn thường trích ~0.0054-0.0057.
    r = IA.alpha_spending(0.5, 0.05, "obrien-fleming")
    assert 0.0050 < r["alpha_spent_cumulative"] < 0.0060


def test_pocock_spends_more_alpha_early_than_obrien_fleming():
    of = IA.alpha_spending(0.5, 0.05, "obrien-fleming")
    poc = IA.alpha_spending(0.5, 0.05, "pocock")
    assert poc["alpha_spent_cumulative"] > of["alpha_spent_cumulative"]


def test_alpha_spending_monotonically_increasing_in_t():
    vals = [IA.alpha_spending(t, 0.05, "obrien-fleming")["alpha_spent_cumulative"]
           for t in (0.1, 0.3, 0.5, 0.7, 0.9, 1.0)]
    assert vals == sorted(vals)


def test_alpha_spending_rejects_t_out_of_range():
    with pytest.raises(IA.InterimAnalysisError):
        IA.alpha_spending(0.0, 0.05, "obrien-fleming")
    with pytest.raises(IA.InterimAnalysisError):
        IA.alpha_spending(1.5, 0.05, "obrien-fleming")


def test_alpha_spending_rejects_invalid_type():
    with pytest.raises(IA.InterimAnalysisError):
        IA.alpha_spending(0.5, 0.05, "haybert-fleming")


# ── Conditional power (đối chiếu mô phỏng Brownian motion, xem docstring module) ──
@pytest.mark.parametrize("z0,expected_cp", [
    (1.0, 0.2201), (1.5, 0.5903), (2.0, 0.8903), (0.5, 0.0382),
])
def test_conditional_power_matches_brownian_motion_simulation(z0, expected_cp):
    r = IA.conditional_power(z_observed=z0, t=0.5, alpha_one_sided=0.025)
    assert r["conditional_power"] == pytest.approx(expected_cp, abs=0.002)


def test_conditional_power_current_trend_theta_equals_z_over_sqrt_t():
    r = IA.conditional_power(z_observed=1.5, t=0.5, alpha_one_sided=0.025)
    assert r["theta_used"] == pytest.approx(1.5 / (0.5 ** 0.5), abs=1e-9)
    assert "hiện tại" in r["assumption"]


def test_conditional_power_accepts_explicit_theta_design():
    r = IA.conditional_power(z_observed=1.5, t=0.5, alpha_one_sided=0.025, theta_design=2.0)
    assert r["theta_used"] == 2.0
    assert "gốc" in r["assumption"]


def test_conditional_power_increases_with_stronger_observed_effect():
    cp_low = IA.conditional_power(z_observed=0.5, t=0.5, alpha_one_sided=0.025)["conditional_power"]
    cp_high = IA.conditional_power(z_observed=2.5, t=0.5, alpha_one_sided=0.025)["conditional_power"]
    assert cp_high > cp_low


def test_conditional_power_rejects_t_out_of_open_range():
    with pytest.raises(IA.InterimAnalysisError):
        IA.conditional_power(z_observed=1.5, t=1.0, alpha_one_sided=0.025)
    with pytest.raises(IA.InterimAnalysisError):
        IA.conditional_power(z_observed=1.5, t=0.0, alpha_one_sided=0.025)
