#!/usr/bin/env python3
"""meta_analysis_calc.py — Máy tính PHÂN TÍCH GỘP (meta-analysis) chạy được: pooled
effect (fixed + random) · heterogeneity (Q/I²/τ²) · khoảng dự báo (PI) · Egger's test ·
chuyển đổi cỡ hiệu ứng (2x2→log-OR/RR, nhóm→MD/SMD, HR+CI95%→log-HR).

Vá khoảng trống đã xác nhận (kiểm tra trực tiếp mã nguồn 2026-07-04): `meta-phan-tich.md`
và `phan-tich-thong-ke.md` đều nói "chạy mô hình thật" nhưng KHÔNG có bất kỳ engine
Python nào — chỉ một đoạn R (`library(metafor); rma(...)`) trong văn xuôi agent, chưa
từng được xác minh chạy được trong hệ này. Module này lấp đúng khoảng trống: engine
Python THẬT cho gộp định lượng.

ĐỘ TIN CẬY CÔNG THỨC: pooled effect (fixed/random inverse-variance) + Q + τ²
(DerSimonian–Laird 1986) + I² (Higgins & Thompson 2002) đã **đối chiếu từng con số
khớp CHÍNH XÁC** với `statsmodels.stats.meta_analysis.combine_effects` (thư viện thống
kê đã bình duyệt, độc lập) trên ví dụ có τ² dương thật — khớp tới đầy đủ độ chính xác
float. Egger's test (hồi quy OLS) đối chiếu khớp `statsmodels.api.OLS`. Đây là mức xác
minh MẠNH HƠN so với chỉ tự kiểm nội bộ (không có thư viện tham chiếu nào cho ngưỡng
test/treat ở `clinical_calc.py` nên phải tự dẫn xuất+brute-force; ở đây CÓ thư viện
tham chiếu nên dùng nó để đối chiếu).

BẤT BIẾN LIÊM CHÍNH:
  - τ² (DerSimonian-Laird) được KẸP TẠI 0 khi công thức thô cho ra âm (quy ước chuẩn
    Cochrane Handbook/Higgins 2002 — τ² âm không có ý nghĩa, ép về 0 để random-effects
    KHÔNG suy biến thành số vô nghĩa). `statsmodels.combine_effects` KHÔNG tự kẹp —
    do đó module này KHÔNG dùng statsmodels làm engine runtime (chỉ dùng để KIỂM khi
    viết module), tự triển khai công thức có kẹp đúng quy ước.
  - Công cụ CHỈ gộp số bác sĩ/agent đã trích xuất — KHÔNG bịa hiệu ứng/SE của nghiên
    cứu gốc thiếu dữ liệu (từ chối tính khi thiếu, không suy diễn).
  - Đồng nhất lâm sàng/phương pháp là quyết định CỦA AGENT (`meta-phan-tich`), KHÔNG
    của công cụ này — công cụ chỉ làm phép tính SAU KHI agent xác nhận đủ điều kiện gộp.

Dùng:
  python tools/meta_analysis_calc.py pool --effects 0.1,0.55,-0.2 --variances 0.02,0.03,0.025 [--json]
  python tools/meta_analysis_calc.py or2x2 --a 15 --b 85 --c 5 --d 95     # log-OR + SE từ bảng 2x2
  python tools/meta_analysis_calc.py rr2x2 --a 15 --b 100 --c 5 --d 100   # log-RR + SE từ bảng 2x2
  python tools/meta_analysis_calc.py hr --hr 0.72 --ci_lower 0.58 --ci_upper 0.89  # log-HR + SE từ HR+CI95%
  python tools/meta_analysis_calc.py smd --mean1 5 --sd1 2 --n1 30 --mean2 4 --sd2 2.2 --n2 28
  python tools/meta_analysis_calc.py egger --effects ... --variances ...
"""

from __future__ import annotations

import argparse
import json
import math
from typing import Dict, List

import gate_contract as _gate_contract
import normal_dist as _normal_dist


class MetaCalcError(ValueError):
    """Input thiếu/ngoài miền hợp lệ — KHÔNG tự bịa để "gộp cho được"."""


DISCLAIMER = "Cần bác sĩ kiểm chứng."


# ═══════════════════════════════════════════════════════════════════════════
# 1. CHUYỂN ĐỔI CỠ HIỆU ỨNG — 2x2 → log-OR/log-RR ; nhóm → MD/SMD (Hedges' g)
# ═══════════════════════════════════════════════════════════════════════════

def _apply_haldane_correction(a: float, b: float, c: float, d: float) -> tuple:
    """Hiệu chỉnh liên tục Haldane–Anscombe (+0.5 mỗi ô) khi CÓ Ô BẰNG 0 — chuẩn
    Cochrane Handbook để log-OR/RR không vô định (chia 0/log 0)."""
    if 0 in (a, b, c, d):
        return a + 0.5, b + 0.5, c + 0.5, d + 0.5
    return a, b, c, d


def log_or_from_2x2(a: int, b: int, c: int, d: int) -> Dict:
    """log(OR) + SE từ bảng 2x2 (a=phơi nhiễm+biến cố, b=phơi nhiễm+không,
    c=không phơi nhiễm+biến cố, d=không phơi nhiễm+không). SE = sqrt(1/a+1/b+1/c+1/d)."""
    for name, v in (("a", a), ("b", b), ("c", c), ("d", d)):
        if v < 0:
            raise MetaCalcError(f"{name}={v} không được âm.")
    a2, b2, c2, d2 = _apply_haldane_correction(a, b, c, d)
    log_or = math.log((a2 * d2) / (b2 * c2))
    se = math.sqrt(1 / a2 + 1 / b2 + 1 / c2 + 1 / d2)
    out = {"log_or": log_or, "se": se, "or": math.exp(log_or)}
    if 0 in (a, b, c, d):
        out["note"] = "Đã áp hiệu chỉnh liên tục Haldane–Anscombe (+0.5 mỗi ô) do có ô = 0."
    return out


def log_rr_from_2x2(a: int, b: int, c: int, d: int) -> Dict:
    """log(RR) + SE từ bảng 2x2 (a=phơi nhiễm+biến cố, b=phơi nhiễm+không,
    c=không phơi nhiễm+biến cố, d=không phơi nhiễm+không).
    SE = sqrt(1/a - 1/(a+b) + 1/c - 1/(c+d))."""
    for name, v in (("a", a), ("b", b), ("c", c), ("d", d)):
        if v < 0:
            raise MetaCalcError(f"{name}={v} không được âm.")
    a2, b2, c2, d2 = _apply_haldane_correction(a, b, c, d)
    n1, n2 = a2 + b2, c2 + d2
    rr = (a2 / n1) / (c2 / n2)
    log_rr = math.log(rr)
    se = math.sqrt(1 / a2 - 1 / n1 + 1 / c2 - 1 / n2)
    out = {"log_rr": log_rr, "se": se, "rr": rr}
    if 0 in (a, b, c, d):
        out["note"] = "Đã áp hiệu chỉnh liên tục Haldane–Anscombe (+0.5 mỗi ô) do có ô = 0."
    return out


def log_hr_from_ci(hr: float, ci_lower: float, ci_upper: float) -> Dict:
    """log(HR) + SE từ HR đã công bố + khoảng tin cậy 95% — công thức chuẩn cho kết
    cục thời gian-đến-biến-cố (Parmar MK et al., Stat Med 1998;17(24):2815-34;
    Tierney JF et al., Trials 2007;8:16): log_hr = ln(HR); SE = (ln(CI_trên) −
    ln(CI_dưới)) / (2×1.96). CHỈ dùng khi trích trực tiếp HR + CI95% đã công bố từ
    một nghiên cứu (khi có dữ liệu thô hơn — số biến cố/người-năm mỗi nhánh, đường
    cong Kaplan-Meier — nên tái tạo log-HR/SE bằng phương pháp Parmar/Tierney đầy đủ
    thay vì công thức xấp xỉ này, vốn giả định CI đối xứng trên thang log)."""
    for name, v in (("hr", hr), ("ci_lower", ci_lower), ("ci_upper", ci_upper)):
        if v <= 0:
            raise MetaCalcError(f"{name}={v} phải dương (HR/CI luôn > 0).")
    if not (ci_lower < hr < ci_upper):
        raise MetaCalcError(
            f"CI không hợp lệ: cần ci_lower({ci_lower}) < hr({hr}) < ci_upper({ci_upper}).")
    log_hr = math.log(hr)
    se = (math.log(ci_upper) - math.log(ci_lower)) / (2 * 1.96)
    return {"log_hr": log_hr, "se": se, "hr": hr}


def md_from_groups(mean1: float, sd1: float, n1: int, mean2: float, sd2: float, n2: int) -> Dict:
    """Hiệu số trung bình (MD) thô + SE — dùng khi 2 nhóm đo CÙNG thang đo."""
    for name, v in (("n1", n1), ("n2", n2)):
        if v < 2:
            raise MetaCalcError(f"{name}={v} phải ≥2.")
    for name, v in (("sd1", sd1), ("sd2", sd2)):
        if v < 0:
            raise MetaCalcError(f"{name}={v} không được âm.")
    md = mean1 - mean2
    se = math.sqrt(sd1 ** 2 / n1 + sd2 ** 2 / n2)
    return {"md": md, "se": se}


def smd_from_groups(mean1: float, sd1: float, n1: int, mean2: float, sd2: float, n2: int) -> Dict:
    """Hedges' g (SMD hiệu chỉnh sai lệch mẫu nhỏ) + SE — dùng khi các nghiên cứu đo
    CÙNG khái niệm bằng THANG ĐO KHÁC NHAU. Nguồn: Hedges & Olkin 1985; Borenstein
    et al. Introduction to Meta-Analysis (2009) — J = 1 − 3/(4·df−1)."""
    for name, v in (("n1", n1), ("n2", n2)):
        if v < 2:
            raise MetaCalcError(f"{name}={v} phải ≥2.")
    for name, v in (("sd1", sd1), ("sd2", sd2)):
        if v < 0:
            raise MetaCalcError(f"{name}={v} không được âm.")
    if sd1 == 0 and sd2 == 0:
        # Vá 2026-07-04 (red-team): trước đây rơi thẳng vào ZeroDivisionError thô ở
        # phép chia dưới (pooled_sd=0) — traceback Python không rõ nguyên nhân với
        # người dùng lâm sàng, trong khi validate sd<0 ngay phía trên đã raise
        # MetaCalcError rõ ràng cho input âm. sd1=sd2=0 (thực tế: SD chưa tính được
        # bị điền tạm 0, hoặc thang đo hằng số) khiến Hedges' g VÔ ĐỊNH — từ chối rõ.
        raise MetaCalcError(
            "sd1 và sd2 đều bằng 0 — pooled SD=0, Hedges' g vô định (chia cho 0).")
    df = n1 + n2 - 2
    pooled_sd = math.sqrt(((n1 - 1) * sd1 ** 2 + (n2 - 1) * sd2 ** 2) / df)
    d = (mean1 - mean2) / pooled_sd
    j = 1 - 3 / (4 * df - 1)
    g = j * d
    se_d = math.sqrt((n1 + n2) / (n1 * n2) + d ** 2 / (2 * (n1 + n2)))
    se_g = j * se_d
    return {"cohens_d": d, "hedges_g": g, "se": se_g, "j_correction": j}


# ═══════════════════════════════════════════════════════════════════════════
# 2. GỘP ĐỊNH LƯỢNG — fixed (inverse-variance) + random (DerSimonian–Laird)
# ═══════════════════════════════════════════════════════════════════════════

def _z_from_alpha(alpha: float) -> float:
    """Vá 2026-07-04 (red-team, cùng lỗi đã tìm ở clinical_calc.py/interim_analysis_calc.py):
    bảng tra cứu cứng khi thiếu scipy ÂM THẦM trả z của alpha=0.05 cho MỌI alpha khác
    (vd 0.10/0.20). Nay dùng normal_dist.inv_phi() (đã kiểm Z-table) — đúng cho MỌI alpha."""
    if not (0 < alpha < 1):
        raise MetaCalcError(f"alpha={alpha} phải trong (0,1).")
    return _normal_dist.inv_phi(1 - alpha / 2)


def _t_from_alpha_df(alpha: float, df: int) -> float:
    try:
        from scipy.stats import t as t_dist
        return t_dist.ppf(1 - alpha / 2, df)
    except ImportError:
        return _z_from_alpha(alpha)  # xấp xỉ khi thiếu scipy (df lớn, sai số nhỏ)


def pool_effects(effects: List[float], variances: List[float], alpha: float = 0.05) -> Dict:
    """Gộp fixed-effect (inverse-variance) + random-effect (DerSimonian–Laird 1986).

    Yêu cầu effects/variances CÙNG THANG ĐO (log-OR/log-RR/log-HR/MD/SMD — không trộn
    lẫn). τ² kẹp tại 0 nếu công thức thô âm (Cochrane Handbook/Higgins 2002). PI
    (prediction interval, chỉ khi random + k≥3) theo Higgins/Thompson/Spiegelhalter,
    IntHout 2016 — độ phân tán hiệu ứng THẬT giữa nghiên cứu, KHÁC CI của trung bình.
    """
    k = len(effects)
    if k < 2:
        raise MetaCalcError(f"Cần ≥2 nghiên cứu để gộp, nhận {k}.")
    if len(variances) != k:
        raise MetaCalcError("effects và variances phải cùng độ dài.")
    for v in variances:
        if v <= 0:
            raise MetaCalcError(f"variance={v} phải dương (SE>0).")

    w = [1 / v for v in variances]
    sum_w = sum(w)
    pooled_fe = sum(wi * yi for wi, yi in zip(w, effects)) / sum_w
    var_fe = 1 / sum_w

    q = sum(wi * (yi - pooled_fe) ** 2 for wi, yi in zip(w, effects))
    df = k - 1
    c = sum_w - sum(wi ** 2 for wi in w) / sum_w
    tau2_raw = (q - df) / c if c > 0 else 0.0
    tau2 = max(0.0, tau2_raw)
    i2 = max(0.0, (q - df) / q) * 100 if q > 0 else 0.0

    w_re = [1 / (v + tau2) for v in variances]
    sum_w_re = sum(w_re)
    pooled_re = sum(wi * yi for wi, yi in zip(w_re, effects)) / sum_w_re
    var_re = 1 / sum_w_re

    z = _z_from_alpha(alpha)
    ci_fe = [pooled_fe - z * math.sqrt(var_fe), pooled_fe + z * math.sqrt(var_fe)]
    ci_re = [pooled_re - z * math.sqrt(var_re), pooled_re + z * math.sqrt(var_re)]

    out = {
        "k_studies": k,
        "fixed_effect": {"pooled": pooled_fe, "se": math.sqrt(var_fe), "ci": ci_fe},
        "random_effect": {"pooled": pooled_re, "se": math.sqrt(var_re), "ci": ci_re},
        "heterogeneity": {
            "Q": q, "df": df, "tau2": tau2, "I2_percent": i2,
            "tau2_raw_before_clamp": tau2_raw,
            "interpretation": (
                "thấp" if i2 < 25 else "vừa" if i2 < 50 else
                "đáng kể" if i2 < 75 else "cao"),
        },
    }
    if k >= 3:
        t_val = _t_from_alpha_df(alpha, k - 2)
        pi_halfwidth = t_val * math.sqrt(var_re + tau2)
        out["prediction_interval"] = {
            "pi": [pooled_re - pi_halfwidth, pooled_re + pi_halfwidth],
            "note": "Khoảng dự báo (Higgins/Thompson/Spiegelhalter; IntHout 2016) — "
                    "độ phân tán hiệu ứng THẬT giữa nghiên cứu, KHÔNG phải CI của trung bình.",
        }
    else:
        out["prediction_interval"] = {"pi": None, "note": "Cần ≥3 nghiên cứu để tính PI đáng tin."}
    return out


def egger_test(effects: List[float], variances: List[float]) -> Dict:
    """Egger's test — hồi quy (hiệu ứng chuẩn hóa / SE) theo (1/SE), kiểm hệ số chặn
    ≠ 0 (bất đối xứng phễu → nghi publication bias). CHỈ nên chạy khi ≥10 nghiên cứu
    (agent quyết định ngưỡng này — công cụ chỉ tính, không tự áp ngưỡng)."""
    k = len(effects)
    if k < 3:
        raise MetaCalcError(f"Cần ≥3 nghiên cứu để hồi quy Egger, nhận {k}.")
    if len(variances) != k:
        raise MetaCalcError("effects và variances phải cùng độ dài.")
    se = [math.sqrt(v) for v in variances]
    std_effect = [y / s for y, s in zip(effects, se)]
    precision = [1 / s for s in se]

    n = k
    mean_x = sum(precision) / n
    mean_y = sum(std_effect) / n
    sxx = sum((x - mean_x) ** 2 for x in precision)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(precision, std_effect))
    if sxx == 0:
        raise MetaCalcError("Độ chính xác (1/SE) không đổi giữa các nghiên cứu — không hồi quy được.")
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x

    resid_ss = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(precision, std_effect))
    dof = n - 2
    mse = resid_ss / dof
    se_intercept = math.sqrt(mse * (1 / n + mean_x ** 2 / sxx))
    t_stat = intercept / se_intercept

    try:
        from scipy.stats import t as t_dist
        p_val = 2 * (1 - t_dist.cdf(abs(t_stat), dof))
    except ImportError:
        p_val = None

    return {
        "intercept": intercept, "se_intercept": se_intercept, "t": t_stat,
        "dof": dof, "p_value": p_val,
        "interpretation": ("nghi bất đối xứng phễu (p<0.10, quy ước Egger)"
                          if (p_val is not None and p_val < 0.10) else
                          "không đủ bằng chứng bất đối xứng phễu" if p_val is not None
                          else "[CẦN scipy để tính p-value chính xác]"),
    }


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def _floats(s: str) -> List[float]:
    return [float(x) for x in s.split(",") if x.strip()]


def _print(result: Dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"\n{DISCLAIMER}")


def main() -> int:
    # Vá 2026-07-04 (red-team): thiếu dòng này khiến print(DISCLAIMER) (chứa dấu tiếng
    # Việt) crash UnicodeEncodeError trên console Windows mặc định (cp1252) — kể cả khi
    # SỐ LIỆU đã tính đúng, script vẫn exit 1 và in traceback ngay dưới kết quả đúng.
    _gate_contract.ensure_utf8_stdout()
    ap = argparse.ArgumentParser(description="Máy tính phân tích gộp (meta-analysis).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("pool", help="Gộp fixed+random (DerSimonian-Laird) + heterogeneity + PI")
    p.add_argument("--effects", required=True, help="vd: 0.1,0.55,-0.2 (log-OR/log-RR/MD/SMD — CÙNG thang)")
    p.add_argument("--variances", required=True, help="Phương sai từng nghiên cứu (SE²)")
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--json", action="store_true")

    e = sub.add_parser("egger", help="Egger's test (publication bias)")
    e.add_argument("--effects", required=True)
    e.add_argument("--variances", required=True)
    e.add_argument("--json", action="store_true")

    o = sub.add_parser("or2x2", help="log-OR + SE từ bảng 2x2")
    for c in ("a", "b", "c", "d"):
        o.add_argument(f"--{c}", type=int, required=True)
    o.add_argument("--json", action="store_true")

    r = sub.add_parser("rr2x2", help="log-RR + SE từ bảng 2x2")
    for c in ("a", "b", "c", "d"):
        r.add_argument(f"--{c}", type=int, required=True)
    r.add_argument("--json", action="store_true")

    h = sub.add_parser("hr", help="log-HR + SE từ HR + khoảng tin cậy 95%% đã công bố (Parmar 1998/Tierney 2007)")
    h.add_argument("--hr", type=float, required=True)
    h.add_argument("--ci_lower", type=float, required=True)
    h.add_argument("--ci_upper", type=float, required=True)
    h.add_argument("--json", action="store_true")

    s = sub.add_parser("smd", help="Hedges' g (SMD) + SE từ 2 nhóm")
    s.add_argument("--mean1", type=float, required=True)
    s.add_argument("--sd1", type=float, required=True)
    s.add_argument("--n1", type=int, required=True)
    s.add_argument("--mean2", type=float, required=True)
    s.add_argument("--sd2", type=float, required=True)
    s.add_argument("--n2", type=int, required=True)
    s.add_argument("--json", action="store_true")

    m = sub.add_parser("md", help="Mean difference thô + SE từ 2 nhóm")
    m.add_argument("--mean1", type=float, required=True)
    m.add_argument("--sd1", type=float, required=True)
    m.add_argument("--n1", type=int, required=True)
    m.add_argument("--mean2", type=float, required=True)
    m.add_argument("--sd2", type=float, required=True)
    m.add_argument("--n2", type=int, required=True)
    m.add_argument("--json", action="store_true")

    args = ap.parse_args()
    try:
        if args.cmd == "pool":
            res = pool_effects(_floats(args.effects), _floats(args.variances), args.alpha)
        elif args.cmd == "egger":
            res = egger_test(_floats(args.effects), _floats(args.variances))
        elif args.cmd == "or2x2":
            res = log_or_from_2x2(args.a, args.b, args.c, args.d)
        elif args.cmd == "rr2x2":
            res = log_rr_from_2x2(args.a, args.b, args.c, args.d)
        elif args.cmd == "hr":
            res = log_hr_from_ci(args.hr, args.ci_lower, args.ci_upper)
        elif args.cmd == "smd":
            res = smd_from_groups(args.mean1, args.sd1, args.n1, args.mean2, args.sd2, args.n2)
        elif args.cmd == "md":
            res = md_from_groups(args.mean1, args.sd1, args.n1, args.mean2, args.sd2, args.n2)
    except MetaCalcError as e:
        print(f"❌ LỖI: {e}")
        return 1
    _print(res, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
