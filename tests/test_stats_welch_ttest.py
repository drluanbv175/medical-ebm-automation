"""_compare_continuous() dùng Welch's t-test cho p-value, khớp công thức SE (không gộp
phương sai) đã dùng sẵn để dựng CI (audit 2026-07-11, vòng 8). Trước vá: ttest_ind() không
truyền equal_var → mặc định Student's (gộp phương sai), trong khi CI lại tính theo SE Welch —
2 giả định phương sai khác nhau trong CÙNG 1 kết quả, có thể mâu thuẫn suy luận khi n1≠n2 hoặc
phương sai 2 nhóm lệch nhau."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import run_stats_analysis as rsa  # noqa: E402

pytest.importorskip("scipy")
from scipy import stats as sp_stats  # noqa: E402


def _unequal_variance_groups(seed: int = 0):
    """n1≠n2 và phương sai lệch rõ — nơi Welch's và Student's p-value khác nhau đáng kể."""
    rng = np.random.default_rng(seed)
    a = pd.Series(rng.normal(100, 5, 60))
    b = pd.Series(rng.normal(103, 25, 15))
    return a, b


def test_uses_welch_not_student_pvalue():
    a, b = _unequal_variance_groups()
    res = rsa._compare_continuous(a, b)
    _, p_welch = sp_stats.ttest_ind(a, b, equal_var=False)
    _, p_student = sp_stats.ttest_ind(a, b, equal_var=True)
    assert res["p"] == round(float(p_welch), 4)
    assert res["p"] != round(float(p_student), 4), (
        "test cần chọn dữ liệu có phương sai đủ lệch để Welch/Student cho p khác nhau — "
        "nếu bằng nhau, sinh lại seed/tham số groups"
    )


def test_test_label_says_welch():
    a, b = _unequal_variance_groups()
    res = rsa._compare_continuous(a, b)
    assert res["test"] == "Welch's t-test"


def test_ci_se_formula_matches_welch_not_pooled():
    """SE dùng cho CI đã là Welch's từ trước — vá này chỉ đổi p-value để khớp,
    không đổi công thức CI. Xác nhận cả 2 vẫn nhất quán sau vá."""
    a, b = _unequal_variance_groups()
    res = rsa._compare_continuous(a, b)
    v1, v2 = a.std() ** 2 / len(a), b.std() ** 2 / len(b)
    se_welch = np.sqrt(v1 + v2)
    md = a.mean() - b.mean()
    df_ws = (v1 + v2) ** 2 / (v1**2 / (len(a) - 1) + v2**2 / (len(b) - 1))
    t_crit = sp_stats.t.ppf(0.975, df_ws)
    expected_ci = (round(md - t_crit * se_welch, 3), round(md + t_crit * se_welch, 3))
    assert f"{expected_ci[0]}" in res["effect"] and f"{expected_ci[1]}" in res["effect"]


class TestCiUsesWelchSatterthwaiteTNotFixedZ:
    """Hồi quy (vòng lặp kiểm tra-hoàn thiện vòng 22, 2026-07-24, phát hiện MEDIUM):
    trước đây CI dùng z=1.96 cố định trong khi p-value đã dùng bậc tự do Welch-
    Satterthwaite (nội bộ scipy) — 2 phương pháp khác nhau trong CÙNG 1 kết quả,
    lệch đáng kể ở mẫu nhỏ (t_crit > 1.96 khi df nhỏ)."""

    def test_small_sample_ci_wider_than_fixed_z_would_give(self):
        rng = np.random.default_rng(1)
        a = pd.Series(rng.normal(10, 2, 5))
        b = pd.Series(rng.normal(12, 3, 5))
        res = rsa._compare_continuous(a, b)
        v1, v2 = a.std() ** 2 / len(a), b.std() ** 2 / len(b)
        se = np.sqrt(v1 + v2)
        df_ws = (v1 + v2) ** 2 / (v1**2 / (len(a) - 1) + v2**2 / (len(b) - 1))
        t_crit = sp_stats.t.ppf(0.975, df_ws)
        assert t_crit > 1.96, "test cần df đủ nhỏ để t_crit khác 1.96 rõ rệt"
        md = a.mean() - b.mean()
        expected_ci = (round(md - t_crit * se, 3), round(md + t_crit * se, 3))
        assert f"{expected_ci[0]}" in res["effect"] and f"{expected_ci[1]}" in res["effect"]
        wrong_ci_with_fixed_z = (round(md - 1.96 * se, 3), round(md + 1.96 * se, 3))
        assert wrong_ci_with_fixed_z != expected_ci
