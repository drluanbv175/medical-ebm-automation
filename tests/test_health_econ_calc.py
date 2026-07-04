"""Test health_econ_calc.py — máy tính kinh tế y tế (ICER/Markov/tornado/PSA).

Markov cohort đối chiếu khớp TAY TÍNH (2 trạng thái, không chiết khấu). Phân phối
Gamma/Beta trong PSA đối chiếu bằng mô phỏng 1 triệu mẫu (mean/se khớp target).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))
import health_econ_calc as HE  # noqa: E402


# ── ICER ─────────────────────────────────────────────────────────────────────
def test_icer_northeast_quadrant():
    r = HE.icer(cost1=100, effect1=0.8, cost2=150, effect2=0.9, wtp=50000)
    assert r["delta_cost"] == pytest.approx(50)
    assert r["delta_effect"] == pytest.approx(0.1)
    assert r["icer"] == pytest.approx(500, abs=1e-6)
    assert "Đông Bắc" in r["quadrant"]
    assert r["nmb_incremental_at_wtp"] == pytest.approx(0.1 * 50000 - 50)
    assert r["cost_effective_at_wtp"] is True


def test_icer_dominant_southeast():
    r = HE.icer(cost1=150, effect1=0.8, cost2=100, effect2=0.9)
    assert "THỐNG TRỊ" in r["quadrant"]
    assert r["icer"] < 0


def test_icer_dominated_northwest():
    r = HE.icer(cost1=100, effect1=0.9, cost2=150, effect2=0.8)
    assert "BỊ THỐNG TRỊ" in r["quadrant"]


def test_icer_undefined_when_equal_effect():
    r = HE.icer(cost1=100, effect1=0.8, cost2=150, effect2=0.8)
    assert r["icer"] is None


def test_icer_rejects_negative_wtp():
    with pytest.raises(HE.HealthEconError):
        HE.icer(cost1=100, effect1=0.8, cost2=150, effect2=0.9, wtp=-1)


# ── Vá 2026-07-04 (red-team): delta_effect ~1e-15 (sai số làm tròn dấu phẩy động
# tích lũy qua markov_cohort, KHÔNG phải 0 tuyệt đối) từng khiến ICER "nổ" thành số
# vô nghĩa (~1e18) thay vì được coi là "hiệu quả bằng nhau".
def test_icer_treats_floating_point_roundoff_as_equal_effect():
    r = HE.icer(cost1=12000.0, effect1=8.4, cost2=15000.0, effect2=8.4 + 1.776e-15)
    assert r["icer"] is None
    assert "BẰNG NHAU" in r["quadrant"]


def test_icer_still_computes_for_genuinely_different_small_effect():
    # Chênh lệch effect NHỎ nhưng THẬT (không phải nhiễu số học) vẫn phải tính ICER.
    r = HE.icer(cost1=12000.0, effect1=8.4, cost2=15000.0, effect2=8.401)
    assert r["icer"] is not None
    assert r["icer"] == pytest.approx(3000 / 0.001, rel=1e-6)


# ── Markov cohort ────────────────────────────────────────────────────────────
def test_markov_two_state_matches_hand_calculation():
    # Healthy/Dead, p(die)=0.1/cycle, cost=100/cycle alive, utility=1/năm alive,
    # KHÔNG chiết khấu, 2 chu kỳ -> tay tính: cost=171, qaly=1.71.
    r = HE.markov_cohort(
        state_names=["Healthy", "Dead"],
        transition_matrix=[[0.9, 0.1], [0.0, 1.0]],
        costs_per_cycle=[100, 0], utilities_per_cycle=[1, 0],
        initial_distribution=[1, 0], n_cycles=2,
        cycle_length_years=1.0, discount_rate=0.0)
    assert r["total_discounted_cost"] == pytest.approx(171.0, abs=1e-9)
    assert r["total_discounted_qaly"] == pytest.approx(1.71, abs=1e-9)
    assert r["final_state_distribution"]["Healthy"] == pytest.approx(0.81, abs=1e-9)
    assert r["final_state_distribution"]["Dead"] == pytest.approx(0.19, abs=1e-9)


def test_markov_discounting_reduces_later_cycle_contribution():
    r0 = HE.markov_cohort(["A", "B"], [[1.0, 0.0], [0.0, 1.0]], [100, 0], [1, 0],
                          [1, 0], 5, 1.0, 0.0)
    r_disc = HE.markov_cohort(["A", "B"], [[1.0, 0.0], [0.0, 1.0]], [100, 0], [1, 0],
                              [1, 0], 5, 1.0, 0.03)
    assert r_disc["total_discounted_cost"] < r0["total_discounted_cost"]


def test_markov_rejects_transition_row_not_summing_to_1():
    with pytest.raises(HE.HealthEconError):
        HE.markov_cohort(["A", "B"], [[0.9, 0.05], [0.0, 1.0]], [100, 0], [1, 0],
                         [1, 0], 2, 1.0, 0.0)


def test_markov_rejects_initial_distribution_not_summing_to_1():
    with pytest.raises(HE.HealthEconError):
        HE.markov_cohort(["A", "B"], [[1.0, 0.0], [0.0, 1.0]], [100, 0], [1, 0],
                         [0.5, 0.3], 2, 1.0, 0.0)


def test_markov_rejects_mismatched_dimensions():
    with pytest.raises(HE.HealthEconError):
        HE.markov_cohort(["A", "B"], [[1.0, 0.0], [0.0, 1.0]], [100], [1, 0],
                         [1, 0], 2, 1.0, 0.0)


# ── Vá 2026-07-04 (red-team): [-0.1, 1.0, 0.1] có TỔNG=1.0 (qua được validate cũ) dù
# chứa xác suất ÂM -0.1 — trước đây lọt qua, khiến occupancy trạng thái ÂM (vô nghĩa
# vật lý) lan truyền âm thầm vào total_discounted_cost/qaly.
def test_markov_rejects_negative_element_even_when_row_sums_to_one():
    with pytest.raises(HE.HealthEconError):
        HE.markov_cohort(
            ["A", "B", "C"],
            [[-0.1, 1.0, 0.1], [0.0, 0.85, 0.15], [0.0, 0.0, 1.0]],
            [100, 50, 0], [1, 0.5, 0], [1, 0, 0], 5, 1.0, 0.0)


def test_markov_rejects_element_greater_than_one():
    with pytest.raises(HE.HealthEconError):
        HE.markov_cohort(
            ["A", "B"], [[1.5, -0.5], [0.0, 1.0]],
            [100, 0], [1, 0], [1, 0], 2, 1.0, 0.0)


# ── Tornado ──────────────────────────────────────────────────────────────────
def test_tornado_ranks_by_range_width_descending():
    r = HE.tornado_two_arm(100, 0.8, 150, 0.9,
                           {"cost2": (100, 200), "effect2": (0.85, 0.95)})
    widths = [row["range_width"] for row in r["tornado_ranked"]]
    assert widths == sorted(widths, reverse=True)
    assert r["tornado_ranked"][0]["parameter"] == "cost2"  # rộng hơn trong ví dụ này


def test_tornado_rejects_invalid_parameter_name():
    with pytest.raises(HE.HealthEconError):
        HE.tornado_two_arm(100, 0.8, 150, 0.9, {"not_a_param": (1, 2)})


def test_tornado_rejects_zero_effect_base_case():
    with pytest.raises(HE.HealthEconError):
        HE.tornado_two_arm(100, 0.8, 150, 0.8, {"cost2": (100, 200)})


# ── Vá 2026-07-04 (red-team): param_range bắc ngang điểm hòa effect1 (0.8) đổi góc
# phần tư (Đông Bắc "tốn hơn+hiệu quả hơn" <-> Tây Bắc "tốn hơn+bị thống trị") —
# trước đây range_width vẫn tính mù |ICER_cao − ICER_thấp| dù 2 số không cùng ý nghĩa.
def test_tornado_flags_quadrant_crossing_instead_of_blind_range_width():
    r = HE.tornado_two_arm(100, 0.8, 150, 0.9, {"effect2": (0.75, 0.95)})
    row = r["tornado_ranked"][0]
    assert row["parameter"] == "effect2"
    assert row["quadrant_crossed"] is True
    assert row["range_width"] is None
    assert row["quadrant_at_low"] != row["quadrant_at_high"]


def test_tornado_quadrant_crossed_param_ranked_first():
    # Tham số đổi góc phần tư phải xếp ĐẦU (phát hiện quan trọng nhất), không phải cuối
    # chỉ vì range_width=None.
    r = HE.tornado_two_arm(100, 0.8, 150, 0.9,
                           {"cost2": (100, 200), "effect2": (0.75, 0.95)})
    assert r["tornado_ranked"][0]["parameter"] == "effect2"
    assert r["tornado_ranked"][0]["quadrant_crossed"] is True


def test_tornado_no_quadrant_crossing_keeps_normal_range_width():
    r = HE.tornado_two_arm(100, 0.8, 150, 0.9, {"cost2": (100, 200)})
    row = r["tornado_ranked"][0]
    assert row["quadrant_crossed"] is False
    assert row["range_width"] is not None


# ── PSA Monte Carlo ──────────────────────────────────────────────────────────
def test_psa_reproducible_with_same_seed():
    kwargs = dict(cost1_mean=100, cost1_se=20, cost1_dist="gamma",
                 effect1_mean=0.8, effect1_se=0.05, effect1_dist="beta",
                 cost2_mean=150, cost2_se=25, cost2_dist="gamma",
                 effect2_mean=0.9, effect2_se=0.04, effect2_dist="beta",
                 n_iterations=2000, wtp_values=[10000, 50000], seed=2026)
    r1 = HE.psa_monte_carlo(**kwargs)
    r2 = HE.psa_monte_carlo(**kwargs)
    assert r1 == r2


def test_psa_ceac_probabilities_in_valid_range():
    r = HE.psa_monte_carlo(100, 20, "gamma", 0.8, 0.05, "beta", 150, 25, "gamma",
                           0.9, 0.04, "beta", 2000, [0, 25000, 50000, 100000], seed=2026)
    for point in r["ceac"]:
        assert 0.0 <= point["probability_cost_effective"] <= 1.0


def test_psa_rejects_too_few_iterations():
    with pytest.raises(HE.HealthEconError):
        HE.psa_monte_carlo(100, 20, "gamma", 0.8, 0.05, "beta", 150, 25, "gamma",
                          0.9, 0.04, "beta", 10, [10000], seed=2026)


def test_psa_gamma_distribution_matches_target_moments():
    import numpy as np
    rng = np.random.default_rng(2026)
    samples = HE._sample("gamma", 100, 20, 500_000, rng)
    assert samples.mean() == pytest.approx(100, rel=0.02)
    assert samples.std() == pytest.approx(20, rel=0.05)


def test_psa_beta_distribution_matches_target_moments():
    import numpy as np
    rng = np.random.default_rng(2026)
    samples = HE._sample("beta", 0.8, 0.05, 500_000, rng)
    assert samples.mean() == pytest.approx(0.8, rel=0.02)
    assert samples.std() == pytest.approx(0.05, rel=0.05)


def test_psa_rejects_invalid_beta_mean_out_of_range():
    with pytest.raises(HE.HealthEconError):
        HE.psa_monte_carlo(100, 20, "gamma", 1.5, 0.05, "beta", 150, 25, "gamma",
                          0.9, 0.04, "beta", 1000, [10000], seed=2026)
