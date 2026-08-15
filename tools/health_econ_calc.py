#!/usr/bin/env python3
"""health_econ_calc.py — Máy tính KINH TẾ Y TẾ chạy được: ICER · mô hình Markov cohort
(chi phí/QALY chiết khấu qua nhiều chu kỳ) · phân tích độ nhạy một chiều (tornado) ·
PSA Monte Carlo → đường cong CEAC.

Vá khoảng trống đã xác nhận (audit 2026-07-04): `kinh-te-y-te.md` yêu cầu tính ICER,
mô hình Markov (transition probability × chiết khấu qua nhiều chu kỳ), PSA/Monte Carlo,
CEAC, tornado — TẤT CẢ bằng lời văn LLM, không công cụ nào tính. Sai ICER/mô hình có
thể dẫn đến kết luận sai "đáng tiền" ảnh hưởng quyết định chi trả/chính sách thật.

BẤT BIẾN LIÊM CHÍNH:
  - Công cụ CHỈ tính từ chi phí/tiện ích/xác suất bác sĩ/chủ nhiệm CUNG CẤP — KHÔNG
    bịa đơn giá/utility/ngưỡng WTP (đúng bất biến đã có trong kinh-te-y-te.md).
  - PSA dùng phân phối THAM SỐ HÓA từ input (mean+se) — không tự chọn "phân phối đẹp"
    thay bác sĩ; agent phải cung cấp loại phân phối phù hợp bản chất biến (Gamma cho
    chi phí ≥0, Beta cho xác suất/utility trong [0,1], Normal cho phần còn lại).
  - `--seed` mặc định cố định (2026) để KẾT QUẢ TÁI LẶP ĐƯỢC (CHEERS 2022 yêu cầu báo
    cáo seed) — không dùng random hệ thống không kiểm soát được.

Dùng:
  python tools/health_econ_calc.py icer --cost1 100 --effect1 0.8 --cost2 150 --effect2 0.9 [--wtp 50000]
  python tools/health_econ_calc.py markov --states Healthy,Sick,Dead \\
      --transitions "0.90,0.08,0.02;0.00,0.85,0.15;0,0,1" --costs 100,500,0 --utilities 1.0,0.6,0 \\
      --initial 1,0,0 --cycles 20 --cycle-length-years 1 --discount-rate 0.03
  python tools/health_econ_calc.py tornado --base-cost1 100 --base-effect1 0.8 \\
      --base-cost2 150 --base-effect2 0.9 --param cost2 120 180 --param effect2 0.85 0.95
  python tools/health_econ_calc.py psa --cost1-mean 100 --cost1-se 20 --cost1-dist gamma \\
      --effect1-mean 0.8 --effect1-se 0.05 --effect1-dist beta \\
      --cost2-mean 150 --cost2-se 25 --cost2-dist gamma \\
      --effect2-mean 0.9 --effect2-se 0.04 --effect2-dist beta \\
      --n-iterations 10000 --wtp-range 0,100000,5000 --seed 2026
"""

from __future__ import annotations

import argparse
import json
from typing import Dict, List, Optional

import gate_contract as _gate_contract

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


class HealthEconError(ValueError):
    """Input thiếu/ngoài miền hợp lệ — KHÔNG tự bịa chi phí/utility/xác suất."""


DISCLAIMER = "Cần bác sĩ kiểm chứng."


# ═══════════════════════════════════════════════════════════════════════════
# 1. ICER — Incremental Cost-Effectiveness Ratio
# ═══════════════════════════════════════════════════════════════════════════

def icer(cost1: float, effect1: float, cost2: float, effect2: float,
         wtp: Optional[float] = None) -> Dict:
    """ICER = Δchi phí/Δhiệu quả giữa 2 lựa chọn (1=chứng/hiện hành, 2=can thiệp mới).
    Xác định GÓC PHẦN TƯ trên mặt phẳng chi phí-hiệu quả (chuẩn CHEERS/Drummond)."""
    delta_cost = cost2 - cost1
    delta_effect = effect2 - effect1

    # Vá 2026-07-04 (red-team): so `delta_effect == 0` TUYỆT ĐỐI bỏ lọt trường hợp RẤT
    # THỰC TẾ khi effect1/effect2 là output của markov_cohort() (không phải số nhập
    # tay) — sai số làm tròn dấu phẩy động tích lũy qua nhiều chu kỳ chiết khấu khiến
    # delta_effect ~1e-15 thay vì đúng 0 tuyệt đối, khiến ICER "nổ" thành một số vô
    # nghĩa (vd 1.69e18) mà không có cảnh báo nào. Dung sai kết hợp tuyệt đối+tương đối
    # (chuẩn numerical practice) coi 2 hiệu quả "thực chất bằng nhau" khi sai khác nhỏ
    # hơn ngưỡng nhiễu số học so với độ lớn của chính effect1/effect2.
    effect_scale = max(1.0, abs(effect1), abs(effect2))
    if abs(delta_effect) < 1e-9 * effect_scale:
        quadrant = "hiệu quả BẰNG NHAU — ICER vô định, so chi phí trực tiếp"
        icer_val = None
    elif delta_cost >= 0 and delta_effect > 0:
        quadrant = "Đông Bắc (tốn hơn, hiệu quả hơn) — tính ICER, so ngưỡng WTP"
        icer_val = delta_cost / delta_effect
    elif delta_cost <= 0 and delta_effect > 0:
        quadrant = "Đông Nam — CAN THIỆP MỚI THỐNG TRỊ (rẻ hơn VÀ hiệu quả hơn)"
        icer_val = delta_cost / delta_effect
    elif delta_cost >= 0 and delta_effect < 0:
        quadrant = "Tây Bắc — CAN THIỆP MỚI BỊ THỐNG TRỊ (tốn hơn VÀ kém hiệu quả hơn)"
        icer_val = delta_cost / delta_effect
    else:
        quadrant = "Tây Nam (rẻ hơn, kém hiệu quả hơn) — tính ICER, cân nhắc đánh đổi"
        icer_val = delta_cost / delta_effect

    out = {
        "delta_cost": delta_cost, "delta_effect": delta_effect,
        "icer": icer_val, "quadrant": quadrant,
    }
    if wtp is not None:
        if wtp < 0:
            raise HealthEconError(f"wtp={wtp} không được âm.")
        # NMB tương đối so với lựa chọn 1 (tham chiếu = 0): nmb2 = Δhiệu quả×WTP − Δchi phí.
        nmb2 = delta_effect * wtp - delta_cost
        out["nmb_incremental_at_wtp"] = nmb2
        out["cost_effective_at_wtp"] = nmb2 > 0
    return out


# ═══════════════════════════════════════════════════════════════════════════
# 2. MÔ HÌNH MARKOV COHORT — chi phí/QALY chiết khấu qua nhiều chu kỳ
# ═══════════════════════════════════════════════════════════════════════════

def _validate_transition_row(row: List[float]) -> None:
    """Vá 2026-07-04 (red-team): kiểm tổng hàng=1.0 KHÔNG đủ — một phần tử ÂM và một
    phần tử >1 vẫn có thể cộng lại đúng 1.0 (vd [-0.1, 1.0, 0.1]), lọt qua validate cũ,
    khiến occupancy trạng thái ÂM (vô nghĩa vật lý) lan truyền âm thầm vào chi phí/QALY.
    Mỗi phần tử của ma trận CHUYỂN TIẾP phải là XÁC SUẤT — bắt buộc ∈[0,1]."""
    for p in row:
        if not (0.0 <= p <= 1.0):
            raise HealthEconError(
                f"Hàng chuyển tiếp {row} có phần tử {p} ngoài [0,1] — mỗi phần tử "
                "ma trận chuyển tiếp PHẢI là xác suất hợp lệ, không chỉ tổng hàng=1.0.")


def _parse_matrix(s: str, n: int) -> List[List[float]]:
    rows = [r for r in s.split(";") if r.strip()]
    if len(rows) != n:
        raise HealthEconError(f"Ma trận chuyển tiếp cần {n} hàng (khớp số trạng thái), nhận {len(rows)}.")
    mat = []
    for r in rows:
        vals = [float(x) for x in r.split(",") if x.strip() != ""]
        if len(vals) != n:
            raise HealthEconError(f"Mỗi hàng ma trận chuyển tiếp cần {n} giá trị, nhận {len(vals)}.")
        s_row = sum(vals)
        if abs(s_row - 1.0) > 1e-6:
            raise HealthEconError(f"Hàng chuyển tiếp {vals} có tổng={s_row}, phải =1.0 (xác suất).")
        _validate_transition_row(vals)
        mat.append(vals)
    return mat


def markov_cohort(state_names: List[str], transition_matrix: List[List[float]],
                  costs_per_cycle: List[float], utilities_per_cycle: List[float],
                  initial_distribution: List[float], n_cycles: int,
                  cycle_length_years: float, discount_rate: float) -> Dict:
    """Mô phỏng cohort Markov: nhân véc-tơ trạng thái với ma trận chuyển tiếp mỗi chu
    kỳ, cộng dồn chi phí/QALY CHIẾT KHẤU (chuẩn: chiết khấu áp dụng từ chu kỳ 1, hệ số
    = 1/(1+r)^(cycle_index × cycle_length_years) — quy ước CHEERS 2022/ISPOR)."""
    n = len(state_names)
    if len(transition_matrix) != n or any(len(row) != n for row in transition_matrix):
        raise HealthEconError("Ma trận chuyển tiếp phải vuông, kích thước = số trạng thái.")
    for row in transition_matrix:
        row_sum = sum(row)
        if abs(row_sum - 1.0) > 1e-6:
            raise HealthEconError(f"Hàng chuyển tiếp {row} có tổng={row_sum}, phải =1.0 (xác suất).")
        _validate_transition_row(row)
    if len(costs_per_cycle) != n or len(utilities_per_cycle) != n:
        raise HealthEconError("costs_per_cycle/utilities_per_cycle phải cùng độ dài số trạng thái.")
    if len(initial_distribution) != n:
        raise HealthEconError("initial_distribution phải cùng độ dài số trạng thái.")
    if abs(sum(initial_distribution) - 1.0) > 1e-6:
        raise HealthEconError(f"initial_distribution phải tổng =1.0, nhận {sum(initial_distribution)}.")
    if n_cycles < 1:
        raise HealthEconError("n_cycles phải ≥1.")
    if cycle_length_years <= 0:
        raise HealthEconError("cycle_length_years phải dương.")
    if discount_rate < 0:
        raise HealthEconError("discount_rate không được âm.")

    state = list(initial_distribution)
    total_cost, total_qaly = 0.0, 0.0
    trace = []
    for cycle in range(1, n_cycles + 1):
        # Nhân véc-tơ trạng thái với ma trận chuyển tiếp (cập nhật TRƯỚC khi cộng dồn
        # chi phí/QALY của chu kỳ này — quy ước "chi phí phát sinh trong chu kỳ đang ở").
        new_state = [sum(state[i] * transition_matrix[i][j] for i in range(n)) for j in range(n)]
        state = new_state
        disc_factor = 1.0 / ((1 + discount_rate) ** (cycle * cycle_length_years))
        cycle_cost = sum(state[i] * costs_per_cycle[i] for i in range(n))
        cycle_qaly = sum(state[i] * utilities_per_cycle[i] * cycle_length_years for i in range(n))
        total_cost += cycle_cost * disc_factor
        total_qaly += cycle_qaly * disc_factor
        trace.append({"cycle": cycle, "state_distribution": dict(zip(state_names, state)),
                      "discount_factor": disc_factor})
    return {
        "total_discounted_cost": total_cost, "total_discounted_qaly": total_qaly,
        "n_cycles": n_cycles, "cycle_length_years": cycle_length_years,
        "discount_rate": discount_rate, "final_state_distribution": dict(zip(state_names, state)),
        "trace": trace,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 3. TORNADO — độ nhạy một chiều trên ICER 2 nhánh
# ═══════════════════════════════════════════════════════════════════════════

def tornado_two_arm(base_cost1: float, base_effect1: float, base_cost2: float,
                    base_effect2: float, param_ranges: Dict[str, tuple]) -> Dict:
    """Độ nhạy MỘT CHIỀU (tornado) trên ICER 2 nhánh — param_ranges: {tên tham số
    ∈ {'cost1','effect1','cost2','effect2'}: (giá_trị_thấp, giá_trị_cao)}. Mỗi tham số
    thay lần lượt (giữ 3 tham số còn lại ở base case), tính lại ICER, xếp hạng theo
    độ rộng |ICER_cao − ICER_thấp| (tham số ảnh hưởng nhiều nhất lên đầu)."""
    base = {"cost1": base_cost1, "effect1": base_effect1, "cost2": base_cost2, "effect2": base_effect2}
    valid_params = set(base.keys())
    base_icer = icer(**base)["icer"]
    if base_icer is None:
        raise HealthEconError("ICER cơ sở vô định (delta_effect=0) — không tính độ nhạy được.")

    results = []
    for name, (lo, hi) in param_ranges.items():
        if name not in valid_params:
            raise HealthEconError(f"Tham số '{name}' không hợp lệ — phải thuộc {valid_params}.")
        low_case = dict(base)
        low_case[name] = lo
        high_case = dict(base)
        high_case[name] = hi
        r_low = icer(**low_case)
        r_high = icer(**high_case)
        icer_low, icer_high = r_low["icer"], r_high["icer"]
        if icer_low is None or icer_high is None:
            continue
        # Vá 2026-07-04 (red-team): |ICER_cao − ICER_thấp| CHỈ có ý nghĩa khi 2 đầu nằm
        # CÙNG góc phần tư kinh tế học (dấu ICER không đơn điệu theo "tốt hơn/xấu hơn"
        # khi đổi góc — vd góc Tây Bắc "bị thống trị" cho ICER âm với Ý NGHĨA HOÀN TOÀN
        # KHÁC góc Đông Bắc). Một param_range hợp lý (vd theo 95%CI của RCT) hoàn toàn
        # có thể bắc ngang điểm hòa effect và đổi góc — trước đây range_width vẫn tính
        # mù, xếp hạng sai tham số nào "ảnh hưởng ICER nhiều nhất".
        quadrant_crossed = r_low["quadrant"] != r_high["quadrant"]
        results.append({
            "parameter": name, "low_value": lo, "high_value": hi,
            "icer_at_low": icer_low, "icer_at_high": icer_high,
            "quadrant_at_low": r_low["quadrant"], "quadrant_at_high": r_high["quadrant"],
            "quadrant_crossed": quadrant_crossed,
            "range_width": None if quadrant_crossed else abs(icer_high - icer_low),
            "note": ("⚠ 2 đầu nằm KHÁC góc phần tư kinh tế học — KHÔNG so sánh trực tiếp "
                     "độ lớn ICER được; xem quadrant_at_low/quadrant_at_high, không dùng "
                     "range_width (=None) để xếp hạng." if quadrant_crossed else ""),
        })
    # Tham số quadrant_crossed=True xếp ĐẦU (không phải cuối) — đây thường là phát hiện
    # LÂM SÀNG quan trọng nhất (đổi kết luận kinh tế y tế), không phải hạng thấp vì
    # range_width=None; trong mỗi nhóm, xếp theo range_width giảm dần.
    results.sort(key=lambda r: (not r["quadrant_crossed"],
                                -(r["range_width"] if r["range_width"] is not None else 0)))
    return {"base_case_icer": base_icer, "tornado_ranked": results}


# ═══════════════════════════════════════════════════════════════════════════
# 4. PSA MONTE CARLO → CEAC
# ═══════════════════════════════════════════════════════════════════════════

def _sample(dist: str, mean: float, se: float, n: int, rng) -> "list":
    """Sinh N mẫu ngẫu nhiên theo phân phối chỉ định, tham số hóa bằng (mean, se) —
    KHÔNG bịa phân phối, agent/bác sĩ phải chọn loại phù hợp bản chất biến."""
    if dist == "normal":
        return rng.normal(mean, se, n)
    if dist == "gamma":
        # Tham số hóa Gamma qua (mean, se): shape=(mean/se)^2, scale=se^2/mean.
        if mean <= 0 or se <= 0:
            raise HealthEconError("Phân phối Gamma cần mean>0 và se>0 (dùng cho chi phí ≥0).")
        shape = (mean / se) ** 2
        scale = se ** 2 / mean
        return rng.gamma(shape, scale, n)
    if dist == "beta":
        # Tham số hóa Beta qua (mean, se), mean∈(0,1): alpha=mean*(mean(1-mean)/se^2-1);
        # beta=(1-mean)*(mean(1-mean)/se^2-1) — phương pháp mô-men chuẩn (dùng cho xác
        # suất/utility trong [0,1]).
        if not (0 < mean < 1):
            raise HealthEconError("Phân phối Beta cần 0<mean<1 (dùng cho xác suất/utility).")
        common = mean * (1 - mean) / (se ** 2) - 1
        if common <= 0:
            raise HealthEconError(f"se={se} quá lớn so với mean={mean} cho phân phối Beta hợp lệ.")
        a = mean * common
        b = (1 - mean) * common
        return rng.beta(a, b, n)
    raise HealthEconError(f"dist='{dist}' phải là 'normal'|'gamma'|'beta'.")


def psa_monte_carlo(cost1_mean: float, cost1_se: float, cost1_dist: str,
                    effect1_mean: float, effect1_se: float, effect1_dist: str,
                    cost2_mean: float, cost2_se: float, cost2_dist: str,
                    effect2_mean: float, effect2_se: float, effect2_dist: str,
                    n_iterations: int, wtp_values: List[float], seed: int = 2026) -> Dict:
    """PSA Monte Carlo: lấy mẫu chi phí/hiệu quả mỗi nhánh theo phân phối chỉ định,
    tính ICER/NMB mỗi lần lặp, dựng đường cong CEAC (% lần lặp chi phí-hiệu quả tại
    mỗi ngưỡng WTP). seed CỐ ĐỊNH để tái lặp (yêu cầu báo cáo của CHEERS 2022)."""
    import numpy as np
    if n_iterations < 100:
        raise HealthEconError("n_iterations nên ≥100 để CEAC ổn định (khuyến nghị ≥1000).")
    rng = np.random.default_rng(seed)

    c1 = _sample(cost1_dist, cost1_mean, cost1_se, n_iterations, rng)
    e1 = _sample(effect1_dist, effect1_mean, effect1_se, n_iterations, rng)
    c2 = _sample(cost2_dist, cost2_mean, cost2_se, n_iterations, rng)
    e2 = _sample(effect2_dist, effect2_mean, effect2_se, n_iterations, rng)

    delta_cost = c2 - c1
    delta_effect = e2 - e1

    ceac = []
    for wtp in wtp_values:
        nmb = delta_effect * wtp - delta_cost
        pct_cost_effective = float(np.mean(nmb > 0))
        ceac.append({"wtp": wtp, "probability_cost_effective": pct_cost_effective})

    return {
        "n_iterations": n_iterations, "seed": seed,
        "mean_delta_cost": float(np.mean(delta_cost)),
        "mean_delta_effect": float(np.mean(delta_effect)),
        "mean_icer": float(np.mean(delta_cost) / np.mean(delta_effect)) if np.mean(delta_effect) != 0 else None,
        "ceac": ceac,
        "note": "CEAC = % lần lặp mà NMB>0 tại mỗi ngưỡng WTP — KHÔNG phải xác suất "
                "Bayes thật, là tần suất mô phỏng (quy ước CHEERS 2022).",
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
    ap = argparse.ArgumentParser(description="Máy tính kinh tế y tế (ICER/Markov/tornado/PSA).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("icer")
    i.add_argument("--cost1", type=float, required=True)
    i.add_argument("--effect1", type=float, required=True)
    i.add_argument("--cost2", type=float, required=True)
    i.add_argument("--effect2", type=float, required=True)
    i.add_argument("--wtp", type=float, default=None)
    i.add_argument("--json", action="store_true")

    m = sub.add_parser("markov")
    m.add_argument("--states", required=True, help="Tên trạng thái, phẩy cách (vd Healthy,Sick,Dead)")
    m.add_argument("--transitions", required=True, help="Ma trận NxN, hàng cách ';', cột cách ','")
    m.add_argument("--costs", required=True, help="Chi phí/chu kỳ mỗi trạng thái, phẩy cách")
    m.add_argument("--utilities", required=True, help="Utility/năm mỗi trạng thái, phẩy cách")
    m.add_argument("--initial", required=True, help="Phân bố ban đầu, phẩy cách, tổng=1")
    m.add_argument("--cycles", type=int, required=True)
    m.add_argument("--cycle-length-years", type=float, required=True, dest="cycle_length")
    m.add_argument("--discount-rate", type=float, required=True, dest="discount")
    m.add_argument("--json", action="store_true")

    t = sub.add_parser("tornado")
    t.add_argument("--base-cost1", type=float, required=True, dest="base_cost1")
    t.add_argument("--base-effect1", type=float, required=True, dest="base_effect1")
    t.add_argument("--base-cost2", type=float, required=True, dest="base_cost2")
    t.add_argument("--base-effect2", type=float, required=True, dest="base_effect2")
    t.add_argument("--param", action="append", nargs=3, metavar=("NAME", "LOW", "HIGH"),
                   help="Lặp lại cho mỗi tham số: --param cost2 120 180")
    t.add_argument("--json", action="store_true")

    p = sub.add_parser("psa")
    for arm in ("cost1", "effect1", "cost2", "effect2"):
        p.add_argument(f"--{arm}-mean", type=float, required=True, dest=f"{arm}_mean")
        p.add_argument(f"--{arm}-se", type=float, required=True, dest=f"{arm}_se")
        p.add_argument(f"--{arm}-dist", required=True, choices=["normal", "gamma", "beta"], dest=f"{arm}_dist")
    p.add_argument("--n-iterations", type=int, default=10000, dest="n_iterations")
    p.add_argument("--wtp-range", required=True, help="min,max,step (vd 0,100000,5000)")
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--json", action="store_true")

    args = ap.parse_args()
    try:
        if args.cmd == "icer":
            res = icer(args.cost1, args.effect1, args.cost2, args.effect2, args.wtp)
        elif args.cmd == "markov":
            states = [s.strip() for s in args.states.split(",")]
            trans = _parse_matrix(args.transitions, len(states))
            costs = [float(x) for x in args.costs.split(",")]
            utils = [float(x) for x in args.utilities.split(",")]
            init = [float(x) for x in args.initial.split(",")]
            res = markov_cohort(states, trans, costs, utils, init, args.cycles,
                                args.cycle_length, args.discount)
        elif args.cmd == "tornado":
            ranges = {}
            for name, lo, hi in (args.param or []):
                ranges[name] = (float(lo), float(hi))
            res = tornado_two_arm(args.base_cost1, args.base_effect1,
                                  args.base_cost2, args.base_effect2, ranges)
        elif args.cmd == "psa":
            lo, hi, step = (float(x) for x in args.wtp_range.split(","))
            wtp_values = []
            v = lo
            while v <= hi + 1e-9:
                wtp_values.append(round(v, 6))
                v += step
            res = psa_monte_carlo(
                args.cost1_mean, args.cost1_se, args.cost1_dist,
                args.effect1_mean, args.effect1_se, args.effect1_dist,
                args.cost2_mean, args.cost2_se, args.cost2_dist,
                args.effect2_mean, args.effect2_se, args.effect2_dist,
                args.n_iterations, wtp_values, args.seed)
    except HealthEconError as e:
        print(f"❌ LỖI: {e}")
        return 1
    _print(res, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
