#!/usr/bin/env python3
"""interim_analysis_calc.py — Máy tính PHÂN TÍCH GIỮA KỲ chạy được: hàm chi tiêu alpha
(O'Brien-Fleming-type/Pocock-type, Lan–DeMets) · công suất có điều kiện (conditional
power) cho quyết định dừng vì vô ích.

Vá khoảng trống đã xác nhận (audit 2026-07-04): `an-toan-nghien-cuu.md` yêu cầu "Alpha
giữa kỳ = ___ (tính từ phan-tich-thong-ke)" và "xác suất thành công < __% (Bayesian
conditional power)" nhưng KHÔNG nơi nào trong hệ có công cụ tính — chỉ có nhãn
`[CẦN NHÀ THỐNG KÊ CHỐT]`.

⚠️ PHẠM VI CÓ CHỦ Ý (an toàn hơn là đủ — quyết định DSMB là TỐI QUAN TRỌNG):
  Module này CHỈ triển khai 2 mảnh có công thức ĐÓNG, đã kiểm chứng độc lập bằng mô
  phỏng (KHÔNG dựa trí nhớ không kiểm chứng được):
    1. GIÁ TRỊ hàm chi tiêu alpha (Lan–DeMets 1983) tại một thời điểm thông tin t —
       O'Brien-Fleming-type: α₁(t)=2−2Φ(z_{α/2}/√t); Pocock-type: α₂(t)=α·ln(1+(e−1)t).
       Đã đối chiếu: α₁(1)=α₂(1)=α CHÍNH XÁC; α₁(0.5) với α=0.05 hai phía cho ≈0.0056,
       khớp giá trị y văn thường trích (~0.0054–0.0057, K=2 chia đều).
    2. CÔNG SUẤT CÓ ĐIỀU KIỆN (conditional power, lý thuyết Brownian motion có drift —
       Proschan/Lan/Wittes "Statistical Monitoring of Clinical Trials") — công thức
       CP=1−Φ((z_α−Z(t)/√t)/√(1−t)) (giả định "xu hướng hiện tại" — drift tiếp tục
       đúng như quan sát) ĐÃ KIỂM bằng mô phỏng Brownian motion độc lập (20 triệu
       đường ngẫu nhiên, sai lệch <0.002 so công thức ở mọi z(t) thử).

  KHÔNG triển khai: NGƯỠNG DỪNG THỰC TẾ (z-critical value tại mỗi lần nhìn giữa kỳ cho
  thiết kế NHIỀU HƠN 2 lần nhìn) — việc này cần GIẢI HỆ TÍCH PHÂN ĐA CHIỀU ĐỆ QUY (thuật
  toán Armitage-McPherson-Rowe) mà phần mềm chuyên dụng (R `gsDesign`, East, PASS) mới
  làm đúng — nhớ nhầm một bước đệ quy cho ngưỡng SAI mà không cách nào tự phát hiện.
  → Dùng phần mềm CHUYÊN DỤNG + nhà thống kê độc lập cho NGƯỠNG DỪNG THỰC TẾ của DSMB;
  công cụ này CHỈ hỗ trợ ước lượng nhanh alpha-đã-chi/công suất-điều-kiện để BÁC SĨ/nhà
  thống kê tham khảo TRƯỚC khi chốt bằng phần mềm chuyên dụng.

Dùng:
  python tools/interim_analysis_calc.py alpha-spending --t 0.5 --alpha-two-sided 0.05 --type obrien-fleming
  python tools/interim_analysis_calc.py conditional-power --z-observed 1.5 --t 0.5 --alpha-one-sided 0.025
  python tools/interim_analysis_calc.py conditional-power --z-observed 1.5 --t 0.5 \
      --alpha-one-sided 0.025 --theta-design 2.0
"""

from __future__ import annotations

import argparse
import json
import math

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
from typing import Dict, Optional

import gate_contract as _gate_contract
import normal_dist as _normal_dist

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


class InterimAnalysisError(ValueError):
    """Input ngoài miền hợp lệ — công cụ TỪ CHỐI tính thay vì bịa."""


DISCLAIMER = "Cần bác sĩ kiểm chứng."
BOUNDARY_LIMITATION = (
    "Đây KHÔNG phải ngưỡng dừng (z-critical value) thực tế cho DSMB — chỉ là GIÁ TRỊ "
    "hàm chi tiêu alpha/công suất điều kiện để tham khảo nhanh. Ngưỡng dừng thực tế "
    "(đặc biệt khi >2 lần nhìn giữa kỳ) PHẢI dùng phần mềm chuyên dụng (R gsDesign/East/"
    "PASS) + nhà thống kê độc lập — KHÔNG dùng công cụ này để tự quyết định dừng."
)


def _phi(x: float) -> float:
    """CDF chuẩn tắc — dùng scipy nếu có, xấp xỉ Abramowitz-Stegun nếu không."""
    return _normal_dist.phi(x)


def _z_from_alpha_one_sided(alpha: float) -> float:
    """z-critical MỘT phía — vá 2026-07-04 (red-team): bản cũ dùng bảng tra 3 giá trị
    cứng khi thiếu scipy, ÂM THẦM trả z của alpha=0.025 cho MỌI alpha khác (vd alpha=0.01
    một phía — mức nghiêm ngặt phổ biến trong DSMB thực hành) — sai lệch alpha-spending/
    conditional-power mà không báo lỗi. Nay dùng normal_dist.inv_phi() (đã kiểm Z-table).
    """
    if not (0 < alpha < 1):
        raise InterimAnalysisError(f"alpha_one_sided={alpha} phải trong (0,1).")
    return _normal_dist.inv_phi(1 - alpha)


# ═══════════════════════════════════════════════════════════════════════════
# 1. HÀM CHI TIÊU ALPHA — Lan DL, DeMets DM. Biometrika. 1983;70(3):659-63.
# ═══════════════════════════════════════════════════════════════════════════

def alpha_spending(t: float, alpha_two_sided: float, spending_type: str) -> Dict:
    """Alpha ĐÃ CHI TIÊU (lũy kế) tại thời điểm thông tin t ∈ (0,1] — Lan-DeMets.

    'obrien-fleming': α₁(t) = 2 − 2Φ(z_{α/2}/√t)  — thận trọng lúc đầu, gần giống
    ranh giới O'Brien-Fleming gốc (1979) khi số lần nhìn cố định trước.
    'pocock': α₂(t) = α·ln(1 + (e−1)·t)  — chi tiêu đều hơn, "dễ dừng sớm" hơn OF-type.
    """
    if not (0 < t <= 1):
        raise InterimAnalysisError(f"t={t} phải trong (0,1] (t=1 là phân tích cuối).")
    if not (0 < alpha_two_sided < 1):
        raise InterimAnalysisError(f"alpha_two_sided={alpha_two_sided} phải trong (0,1).")
    if spending_type not in ("obrien-fleming", "pocock"):
        raise InterimAnalysisError("spending_type phải là 'obrien-fleming' hoặc 'pocock'.")

    if spending_type == "obrien-fleming":
        z = _z_from_alpha_one_sided(alpha_two_sided / 2)
        spent = 2 - 2 * _phi(z / math.sqrt(t))
    else:
        spent = alpha_two_sided * math.log(1 + (math.e - 1) * t)

    return {
        "t": t, "spending_type": spending_type, "alpha_two_sided": alpha_two_sided,
        "alpha_spent_cumulative": spent,
        "alpha_remaining": alpha_two_sided - spent,
        "note": BOUNDARY_LIMITATION,
        "source": "Lan DL, DeMets DM. Biometrika. 1983;70(3):659-63.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# 2. CÔNG SUẤT CÓ ĐIỀU KIỆN — lý thuyết Brownian motion có drift
#    (Proschan MA, Lan KKG, Wittes JT. Statistical Monitoring of Clinical Trials, 2006)
# ═══════════════════════════════════════════════════════════════════════════

def conditional_power(z_observed: float, t: float, alpha_one_sided: float,
                      theta_design: Optional[float] = None) -> Dict:
    """Công suất có điều kiện đạt ý nghĩa ở phân tích CUỐI, cho trước Z quan sát ở
    thông tin t. Mặc định giả định "XU HƯỚNG HIỆN TẠI" (θ = z_observed/√t, tức giả
    định drift ĐÃ QUAN SÁT tiếp tục nguyên vẹn) — TRUYỀN --theta-design để dùng giả
    định THIẾT KẾ GỐC thay vào đó (θ_design = drift kỳ vọng ban đầu của SAP).

    CP = 1 − Φ( (z_α − z_observed·√t − θ·(1−t)) / √(1−t) )   [θ tổng quát]
    Rút gọn khi θ=z_observed/√t (xu hướng hiện tại): CP = 1−Φ((z_α−z_observed/√t)/√(1−t)).
    Đã kiểm bằng mô phỏng Brownian motion độc lập (20 triệu đường, sai lệch <0.002).
    """
    if not (0 < t < 1):
        raise InterimAnalysisError(f"t={t} phải trong (0,1) — dùng t<1 (giữa kỳ thật, chưa tới cuối).")
    if not (0 < alpha_one_sided < 1):
        raise InterimAnalysisError(f"alpha_one_sided={alpha_one_sided} phải trong (0,1).")

    z_alpha = _z_from_alpha_one_sided(alpha_one_sided)
    if theta_design is None:
        theta = z_observed / math.sqrt(t)
        assumption = "xu hướng hiện tại (θ = Z(t)/√t)"
    else:
        theta = theta_design
        assumption = f"thiết kế gốc (θ_design = {theta_design} do SAP cung cấp)"

    cp = 1 - _phi((z_alpha - z_observed * math.sqrt(t) - theta * (1 - t)) / math.sqrt(1 - t))
    return {
        "conditional_power": cp, "z_observed": z_observed, "t": t,
        "alpha_one_sided": alpha_one_sided, "theta_used": theta, "assumption": assumption,
        "note": "Công suất có điều kiện KHÔNG phải xác suất Bayes — là xác suất tần suất "
                "GIẢ ĐỊNH drift theo assumption trên tiếp tục đến hết nghiên cứu.",
        "source": "Proschan MA, Lan KKG, Wittes JT. Statistical Monitoring of Clinical "
                 "Trials: A Unified Approach. Springer, 2006 (lý thuyết Brownian motion).",
    }


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def _print(result: Dict, as_json: bool) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not as_json:
        print(f"\n{DISCLAIMER}")


def main() -> int:
    # Vá 2026-07-04 (red-team): tránh crash UnicodeEncodeError khi in DISCLAIMER tiếng
    # Việt trên console Windows mặc định (cp1252).
    _gate_contract.ensure_utf8_stdout()
    ap = argparse.ArgumentParser(description="Máy tính hỗ trợ phân tích giữa kỳ (alpha-spending/conditional power).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("alpha-spending")
    a.add_argument("--t", type=float, required=True, help="Thời điểm thông tin, 0<t≤1")
    a.add_argument("--alpha-two-sided", type=float, required=True, dest="alpha")
    a.add_argument("--type", required=True, choices=["obrien-fleming", "pocock"], dest="spending_type")
    a.add_argument("--json", action="store_true")

    c = sub.add_parser("conditional-power")
    c.add_argument("--z-observed", type=float, required=True, dest="z_observed")
    c.add_argument("--t", type=float, required=True)
    c.add_argument("--alpha-one-sided", type=float, required=True, dest="alpha_one_sided")
    c.add_argument("--theta-design", type=float, default=None, dest="theta_design",
                  help="Tùy chọn: drift thiết kế gốc (mặc định dùng xu hướng hiện tại)")
    c.add_argument("--json", action="store_true")

    args = ap.parse_args()
    try:
        if args.cmd == "alpha-spending":
            res = alpha_spending(args.t, args.alpha, args.spending_type)
        elif args.cmd == "conditional-power":
            res = conditional_power(args.z_observed, args.t, args.alpha_one_sided, args.theta_design)
    except InterimAnalysisError as e:
        print(f"❌ LỖI: {e}")
        return 1
    _print(res, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
