"""
Test đơn vị cho công thức thống kê cốt lõi của cổng G3 (tools/run_g3_auto.py).

Các giá trị kỳ vọng đã đối chiếu tay với ví dụ sách giáo khoa (Machin/Campbell)
và xác nhận lại bằng cách chạy trực tiếp hàm thật trong dự án (không suy đoán).
Mục tiêu: bắt lại các bug đã từng xảy ra thật trong dự án — ví dụ thiếu hệ số 4
trong công thức Schoenfeld (N sai lệch đúng 4 lần) và hệ số 2 sai trong n_auc().
"""
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from run_g3_auto import (  # noqa: E402
    InvalidEffectSizeError,
    n_auc,
    n_log_rank,
    n_prevalence,
    n_two_proportion,
)


class TestNLogRank:
    """Công thức Schoenfeld (1983) — cỡ mẫu sống còn/log-rank."""

    def test_textbook_case_hr_0_5(self):
        """HR=0.5, alpha=0.05, power=80%, p_event=30% → khớp ví dụ Machin/Campbell."""
        n_total, n_events = n_log_rank(0.5, alpha=0.05, power=0.80, p_event=0.30)
        assert n_events == 66
        assert n_total == 220

    def test_symmetric_for_harm_direction(self):
        """HR=2.0 (hại) phải cho CÙNG số biến cố như HR=0.5 (lợi) — ln(HR)² đối xứng."""
        n_total_protect, n_events_protect = n_log_rank(0.5, 0.05, 0.80, 0.30)
        n_total_harm, n_events_harm = n_log_rank(2.0, 0.05, 0.80, 0.30)
        assert n_events_harm == n_events_protect
        assert n_total_harm == n_total_protect

    def test_has_coefficient_4_not_1(self):
        """
        Bug lịch sử: thiếu hệ số 4 trong tử số khiến N bị đánh giá thấp 4 lần.
        Xác nhận trực tiếp: n_events phải xấp xỉ 4x giá trị nếu KHÔNG có hệ số 4.
        """
        n_total, n_events = n_log_rank(0.5, 0.05, 0.80, 0.30)
        # Không có hệ số 4: d ≈ (za+zb)²/ln(HR)² ≈ 16.3 (làm tròn lên 17)
        n_events_without_coef4 = 17
        assert n_events >= 3 * n_events_without_coef4, (
            "n_events quá gần giá trị THIẾU hệ số 4 — nghi ngờ bug đã quay lại"
        )

    def test_rejects_hr_equal_1(self):
        with pytest.raises(InvalidEffectSizeError):
            n_log_rank(1.0)

    def test_rejects_hr_near_1(self):
        with pytest.raises(InvalidEffectSizeError):
            n_log_rank(1.005)

    def test_rejects_negative_hr(self):
        with pytest.raises(InvalidEffectSizeError):
            n_log_rank(-0.5)

    def test_rejects_zero_or_negative_p_event(self):
        with pytest.raises(InvalidEffectSizeError):
            n_log_rank(0.5, p_event=0)
        with pytest.raises(InvalidEffectSizeError):
            n_log_rank(0.5, p_event=-0.1)

    def test_lower_hr_needs_smaller_n(self):
        """HR càng xa 1 (hiệu quả càng mạnh) → cỡ mẫu cần càng nhỏ."""
        _, events_strong = n_log_rank(0.3, 0.05, 0.80, 0.30)
        _, events_weak = n_log_rank(0.8, 0.05, 0.80, 0.30)
        assert events_strong < events_weak


class TestNTwoProportion:
    """Cỡ mẫu so sánh hai tỷ lệ — dùng cho case-control/RCT nhị phân."""

    def test_known_case(self):
        n = n_two_proportion(0.20, 0.10, alpha=0.05, power=0.80)
        assert n == 199

    def test_rejects_equal_proportions(self):
        with pytest.raises(InvalidEffectSizeError):
            n_two_proportion(0.2, 0.2)

    def test_rejects_out_of_range(self):
        with pytest.raises(InvalidEffectSizeError):
            n_two_proportion(0.0, 0.5)
        with pytest.raises(InvalidEffectSizeError):
            n_two_proportion(0.5, 1.0)

    def test_symmetric_p1_p2(self):
        n_ab = n_two_proportion(0.20, 0.10)
        n_ba = n_two_proportion(0.10, 0.20)
        assert n_ab == n_ba


class TestNAuc:
    """
    Cỡ mẫu kiểm định MỘT AUC so với 0.5 (một mẫu) — KHÔNG phải so sánh 2 AUC.
    Bug lịch sử: công thức cũ nhân thêm hệ số 2 (chỉ đúng cho so sánh 2 AUC độc lập).
    """

    def test_known_case(self):
        assert n_auc(0.75, alpha=0.05, power=0.80) == 27

    def test_no_factor_2_regression(self):
        """
        Nếu bug hệ số-2 quay lại, n_auc(0.75) sẽ ≈ 2x giá trị đúng (~54 thay vì 27).
        """
        n = n_auc(0.75, 0.05, 0.80)
        assert n < 40, f"n_auc(0.75)={n} — nghi ngờ hệ số 2 sai đã quay lại (kỳ vọng ~27)"

    def test_rejects_auc_near_half(self):
        with pytest.raises(InvalidEffectSizeError):
            n_auc(0.5)
        with pytest.raises(InvalidEffectSizeError):
            n_auc(0.505)

    def test_rejects_out_of_range(self):
        with pytest.raises(InvalidEffectSizeError):
            n_auc(0.0)
        with pytest.raises(InvalidEffectSizeError):
            n_auc(1.0)


class TestNPrevalence:
    def test_known_case(self):
        assert n_prevalence(0.30, e=0.05, alpha=0.05) == 323

    def test_rejects_out_of_range_p(self):
        with pytest.raises(InvalidEffectSizeError):
            n_prevalence(0.0)
        with pytest.raises(InvalidEffectSizeError):
            n_prevalence(1.0)
