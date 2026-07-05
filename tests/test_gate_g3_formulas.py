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
    n_continuous_md,
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


class TestNContinuousMD:
    """Cỡ mẫu 2 nhóm độc lập, kết cục LIÊN TỤC (Mean Difference) — thêm
    2026-07-06 sau khi chạy thật G0→G10 trên 1 đề tài RCT mới (đau khớp gối)
    phát hiện design=rct/cohort + effect_type=MD KHÔNG có công thức tự động,
    dù đây là loại kết cục PHỔ BIẾN NHẤT cho thử nghiệm về triệu chứng."""

    def test_large_effect_d_1_0(self):
        """SD=MD=1 (Cohen's d=1.0, effect lớn) → n=16/nhóm, khớp bảng chuẩn Cohen/Machin."""
        assert n_continuous_md(md=1.0, sd=1.0, alpha=0.05, power=0.80) == 16

    def test_medium_effect_d_0_5(self):
        """SD=1, MD=0.5 (d=0.5, effect vừa) → n≈63/nhóm, khớp bảng chuẩn Cohen (n=64)."""
        n = n_continuous_md(md=0.5, sd=1.0, alpha=0.05, power=0.80)
        assert 60 <= n <= 66

    def test_symmetric_direction(self):
        """MD âm (giảm) và MD dương (tăng) cùng độ lớn phải cho CÙNG N."""
        n_pos = n_continuous_md(md=1.5, sd=1.8, alpha=0.05, power=0.80)
        n_neg = n_continuous_md(md=-1.5, sd=1.8, alpha=0.05, power=0.80)
        assert n_pos == n_neg

    def test_rejects_zero_or_negative_sd(self):
        with pytest.raises(InvalidEffectSizeError):
            n_continuous_md(md=1.0, sd=0)
        with pytest.raises(InvalidEffectSizeError):
            n_continuous_md(md=1.0, sd=-2.0)

    def test_rejects_zero_md(self):
        """MD=0 nghĩa là không có hiệu quả để phát hiện — không có N hữu hạn hợp lý."""
        with pytest.raises(InvalidEffectSizeError):
            n_continuous_md(md=0.0, sd=1.8)

    def test_matches_real_rct_scenario_knee_oa(self):
        """
        Kịch bản thật dùng để chạy G0→G10 (2026-07-06): MD=1.5 (thang đau
        NRS 0-10), SD≈1.82 suy từ 95%CI của Gohir 2021 JAMA Netw Open
        (PMID 33620447, DOI 10.1001/jamanetworkopen.2021.0012): SE_diff =
        (2.2-0.8)/(2×1.96) ≈0.357; SD = SE_diff/sqrt(1/48+1/57) ≈1.82
        (giả định phương sai bằng nhau 2 nhóm, n=48/57 theo bài báo).
        Xác nhận N ra số hữu hạn hợp lý cho một RCT triệu chứng cỡ vừa.
        """
        n = n_continuous_md(md=1.5, sd=1.82, alpha=0.05, power=0.80)
        assert 10 <= n <= 40
