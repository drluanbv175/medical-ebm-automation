"""normal_dist.py — CDF chuẩn tắc `phi(x)` và nghịch đảo `inv_phi(p)` DÙNG CHUNG cho mọi
module thống kê (clinical_calc.py, interim_analysis_calc.py) — dùng scipy nếu có, xấp xỉ
số học chính xác cao nếu không.

Vá lỗi thật (audit đối kháng 2026-07-04): `clinical_calc._z_from_alpha()` và
`interim_analysis_calc._z_from_alpha_one_sided()` MỖI module tự viết fallback riêng khi
thiếu scipy — cả hai đều dùng bảng tra cứu CỨNG chỉ 3-4 giá trị alpha, và ÂM THẦM trả về
giá trị của alpha=0.05/0.025 cho BẤT KỲ alpha nào KHÁC (vd alpha=0.10/0.20/0.01 rất phổ
biến trong thực hành — CI 90%/80%, ngưỡng DSMB nghiêm ngặt hơn) — không raise lỗi, không
cảnh báo. Đã xác nhận: venv dự án (~/.ebm-venv) HIỆN TẠI không có scipy cài đặt (dù có
trong requirements.txt) nên nhánh fallback lỗi này đang THẬT SỰ chạy trong production,
không phải giả định lý thuyết.

Sửa: MỘT cài đặt `inv_phi()` dùng xấp xỉ hữu tỷ Acklam (Peter J. Acklam, 2003) — sai số
tương đối tối đa ~1.15e-9 trên toàn miền (0,1), KHÔNG cần scipy, đã kiểm bằng cách đối
chiếu 6 giá trị tham chiếu kinh điển (Z-table) TRƯỚC khi coi là đáng tin (xem
test_normal_dist.py): z(0.5)=0, z(0.025)=1.95996398, z(0.05)=1.64485363,
z(0.01)=2.32634787, z(0.005)=2.57582930, z(0.20)=0.84162123.
"""

from __future__ import annotations

import math


class NormalDistError(ValueError):
    """Input ngoài miền (0,1) — công cụ TỪ CHỐI tính thay vì bịa."""


def phi(x: float) -> float:
    """CDF chuẩn tắc Φ(x) — dùng scipy nếu có, xấp xỉ math.erf (chính xác máy) nếu không."""
    try:
        from scipy.stats import norm
        return float(norm.cdf(x))
    except ImportError:
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))


# Hệ số xấp xỉ hữu tỷ Acklam cho Φ⁻¹(p) — nguồn: Peter J. Acklam, "An algorithm for
# computing the inverse normal cumulative distribution function" (2003), thuật toán
# rational approximation dùng rộng rãi (vd tham chiếu trong Moro 1995, Wichura AS241).
_ACKLAM_A = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
             1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
_ACKLAM_B = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
             6.680131188771972e+01, -1.328068155288572e+01)
_ACKLAM_C = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
             -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00)
_ACKLAM_D = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
             3.754408661907416e+00)
_ACKLAM_P_LOW = 0.02425


def _inv_phi_acklam(p: float) -> float:
    a, b, c, d = _ACKLAM_A, _ACKLAM_B, _ACKLAM_C, _ACKLAM_D
    p_low, p_high = _ACKLAM_P_LOW, 1 - _ACKLAM_P_LOW
    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p <= p_high:
        q = p - 0.5
        r = q * q
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
               (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
           ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)


def inv_phi(p: float) -> float:
    """Φ⁻¹(p) — nghịch đảo CDF chuẩn tắc (quantile function / z-score).

    Dùng scipy.stats.norm.ppf nếu có; nếu không, xấp xỉ Acklam (chính xác cho MỌI
    p ∈ (0,1), không giới hạn vài giá trị hard-code như bản cũ ở 2 module gọi hàm này).
    """
    if not (0 < p < 1):
        raise NormalDistError(f"p={p} phải trong (0,1) — không tính được z-score.")
    try:
        from scipy.stats import norm
        return float(norm.ppf(p))
    except ImportError:
        return _inv_phi_acklam(p)
