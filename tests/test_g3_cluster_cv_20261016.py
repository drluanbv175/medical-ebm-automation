"""F1 (16/10/2026, diễn tập C1a): hiệu ứng thiết kế cụm KHÔNG đều — DE = 1+((CV²+1)m−1)·ICC (Eldridge, Ashby & Kerry
2006, Int J Epidemiol 35:1292–1300). C1a: ICC 0,02, m 20 ⇒ DE 1,38 (cụm đều) / 1,78 (CV 1,0)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import g3_quality_gate as G3Q  # noqa: E402
import run_g3_auto as G3  # noqa: E402


def test_f1_khong_cv_giu_cong_thuc_cu():
    assert G3.he_so_thiet_ke(0.02, 20) == pytest.approx(1.38)


def test_f1_cv_1_ra_de_1_78_nhu_de_cuong_nop():
    assert G3.he_so_thiet_ke(0.02, 20, 1.0) == pytest.approx(1.78)
    assert G3.he_so_thiet_ke(0.02, 20, 0.0) == pytest.approx(1.38)
    with pytest.raises(ValueError):
        G3.he_so_thiet_ke(0.02, 20, -0.5)


def test_f1_ap_fpc_cum_dung_cv():
    n2, _nhom, ghi, de, _cum, _truoc = G3.ap_fpc_cum(454, "cross_sectional", None, 0.02, 20, 1.0)
    assert de == pytest.approx(1.78) and n2 == 809 and "Eldridge" in ghi


def test_f1_dau_van_tay_khong_doi_khi_khong_khai_cv():
    cp = {"design_code": "cross_sectional", "icc": 0.02, "cluster_size": 20, "n_adjusted": 626}
    assert G3Q.dau_van_tay_g3(cp) == G3Q.dau_van_tay_g3(dict(cp, cluster_cv=None))
    assert G3Q.dau_van_tay_g3(cp) != G3Q.dau_van_tay_g3(dict(cp, cluster_cv=1.0))
