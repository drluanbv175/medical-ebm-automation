# -*- coding: utf-8 -*-
"""Test tools/normal_dist.py — inv_phi() phải khớp giá trị Z-table kinh điển TRƯỚC khi
được clinical_calc.py/interim_analysis_calc.py tin dùng thay bảng tra cứu cứng cũ."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import normal_dist as ND  # noqa: E402

# Giá trị tham chiếu kinh điển (Z-table / scipy.stats.norm.ppf) — sai số cho phép 1e-4
# (Acklam xấp xỉ có sai số tương đối tối đa ~1.15e-9, dư sức đạt ngưỡng này). Quy ước
# dấu: Phi^-1(p) ÂM khi p<0.5 (đuôi trái), DƯƠNG khi p>0.5 (đuôi phải) — vd Phi^-1(0.975)
# = +1.96 (bách phân vị 97.5%, TRÊN trung vị), KHÔNG phải -1.96.
REFERENCE = [
    (0.5, 0.0),
    (0.025, -1.95996398),
    (0.05, -1.64485363),
    (0.01, -2.32634787),
    (0.005, -2.57582930),
    (0.20, -0.84162123),
    (0.10, -1.28155157),
    (0.001, -3.09023231),
    (0.975, 1.95996398),
    (0.99, 2.32634787),
]


@pytest.mark.parametrize("p,expected_z", REFERENCE)
def test_inv_phi_matches_z_table(p, expected_z):
    assert ND.inv_phi(p) == pytest.approx(expected_z, abs=1e-4)


def test_inv_phi_rejects_p_equal_zero():
    with pytest.raises(ND.NormalDistError):
        ND.inv_phi(0.0)


def test_inv_phi_rejects_p_equal_one():
    with pytest.raises(ND.NormalDistError):
        ND.inv_phi(1.0)


def test_inv_phi_rejects_p_out_of_range():
    with pytest.raises(ND.NormalDistError):
        ND.inv_phi(1.5)
    with pytest.raises(ND.NormalDistError):
        ND.inv_phi(-0.1)


def test_inv_phi_is_odd_symmetric_around_half():
    # Phi^-1(p) = -Phi^-1(1-p) — bất biến toán học cơ bản, kiểm cả 2 nhánh (low/high)
    # của xấp xỉ Acklam (p<0.02425 dùng nhánh đuôi khác với 0.02425<=p<=0.97575).
    for p in (0.001, 0.01, 0.024, 0.05, 0.3, 0.4999):
        assert ND.inv_phi(p) == pytest.approx(-ND.inv_phi(1 - p), abs=1e-6)


def test_phi_roundtrips_with_inv_phi():
    for p in (0.001, 0.025, 0.05, 0.20, 0.5, 0.80, 0.975, 0.999):
        z = ND.inv_phi(p)
        assert ND.phi(z) == pytest.approx(p, abs=1e-6)


def test_inv_phi_matches_scipy_when_available():
    pytest.importorskip("scipy")
    from scipy.stats import norm
    for p in (0.001, 0.01, 0.025, 0.05, 0.10, 0.20, 0.5, 0.90, 0.99):
        assert ND.inv_phi(p) == pytest.approx(float(norm.ppf(p)), abs=1e-6)


def test_phi_matches_math_erf_fallback_directly():
    # Xác nhận công thức phi() không phụ thuộc scipy cho một vài giá trị đã biết.
    assert ND.phi(0.0) == pytest.approx(0.5, abs=1e-9)
    assert ND.phi(1.96) == pytest.approx(0.9750021, abs=1e-6)
