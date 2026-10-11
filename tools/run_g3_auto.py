#!/usr/bin/env python3
"""
run_g3_auto.py — Cổng G3: Tính cỡ mẫu tự động
Đọc G0+G1 checkpoints → tính cỡ mẫu với công thức thật → A4 .md + .docx + G3_checkpoint.json
"""
import argparse
import json
import math
import re
import sys

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
from datetime import datetime
from pathlib import Path

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parent.parent
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(TOOLS))

import chuan_trinh_bay as _CTB  # noqa: E402  (chuẩn trình bày tài liệu — font/ký tự, 01/09/2026)
import g3_quality_gate as G3Q  # noqa: E402  (hợp đồng CHẤT LƯỢNG riêng G3)
import gate_contract as GC  # noqa: E402  (hợp đồng DỪNG dùng chung)
import skill_standards as S  # noqa: E402  (bản đồ chuẩn báo cáo theo thiết kế)

# THÊM 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG): 3 thiết kế KHÔNG dùng
# công thức cỡ mẫu power/effect size truyền thống — n_adjusted=0 là CÓ CHỦ
# ĐÍCH (kèm formula_used giải thích phương pháp thay thế: RIS/TSA cho sr_ma,
# pmsampsize cho prediction, bão hòa dữ liệu cho qualitative), KHÔNG phải
# "thiếu effect size" (lỗi thật). Hằng số DÙNG CHUNG giữa guardrail (không
# hard-block) và generate_artifact (không hiện nhầm thông báo "chưa tính
# được — cần effect size").
N_NOT_APPLICABLE_DESIGNS = {"sr_ma", "prediction", "qualitative"}

# Hệ số z phổ biến (6 chữ số thập phân — khớp scipy.stats.norm.ppf để tránh
# lệch 1 đơn vị ở biên math.ceil() khi phải dùng bảng dự phòng không scipy)
Z_TABLE = {
    0.20: 0.841621,
    0.15: 1.036433,
    0.10: 1.281552,
    0.05: 1.644854,
    0.025: 1.959964,
    0.01: 2.326348,
    0.005: 2.575829,
}

def z(p):
    """
    Tính z-score từ xác suất một phía.
    SỬA 2026-07-06: khi không có scipy, tra Z_TABLE bằng key float thô
    (vd `1 - power`) sai lệch do sai số dấu phẩy động — `1 - 0.80` cho
    ra 0.19999999999999996, không khớp khóa 0.20 → âm thầm rơi về mặc
    định 1.960 (sai gần gấp đôi cho power=80%), làm MỌI cỡ mẫu tính ra
    lớn gấp ~2 lần giá trị đúng. Nay làm tròn khóa trước khi tra, và
    báo lỗi rõ ràng thay vì âm thầm dùng giá trị mặc định sai khi thiếu
    scipy lẫn giá trị trong bảng.
    """
    try:
        from scipy.stats import norm
        return norm.ppf(1 - p)
    except ImportError:
        key = round(p, 4)
        if key not in Z_TABLE:
            raise InvalidEffectSizeError(
                f"Không có scipy và p={p} (làm tròn {key}) không có trong Z_TABLE dự phòng "
                "— cài `pip install scipy` hoặc bổ sung giá trị vào Z_TABLE; "
                "không tự ý dùng z mặc định vì sẽ làm sai cỡ mẫu."
            )
        return Z_TABLE[key]

def n_two_proportion(p1, p2, alpha=0.05, power=0.80, continuity_correction=False):
    """Cỡ mẫu so sánh hai tỷ lệ (two-sided).

    continuity_correction=False (mặc định, KHÔNG đổi để không phá vỡ giá trị
    đã khóa ở tests/test_gate_g3_formulas.py::test_known_case) giữ nguyên xấp
    xỉ chuẩn cổ điển. Khi True, áp hiệu chỉnh liên tục Fleiss-Tytun-Ubhaya
    (1980) — xem n_two_proportion_auto() để tự động quyết định khi nào cần,
    theo đúng ngưỡng doctrine co-mau-nghien-cuu.md dòng 69 ("với cỡ mẫu nhỏ/
    tỷ lệ gần biên dùng hiệu chỉnh liên tục")."""
    if not (0 < p1 < 1) or not (0 < p2 < 1):
        raise InvalidEffectSizeError(f"p1, p2 phải trong (0,1), nhận được p1={p1}, p2={p2}")
    if abs(p1 - p2) < 0.001:
        raise InvalidEffectSizeError(
            f"p1={p1} và p2={p2} gần như bằng nhau (không có hiệu quả để phát hiện) — "
            "cần chênh lệch tỷ lệ thực tế khác 0."
        )
    za = z(alpha / 2)
    zb = z(1 - power)
    pooled = (p1 + p2) / 2
    num = (za * math.sqrt(2 * pooled * (1 - pooled)) + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    denom = (p1 - p2) ** 2
    n = num / denom
    if continuity_correction:
        # SỬA 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 15, phát hiện
        # MEDIUM): Fleiss JL, Levin B, Paik MC. Statistical Methods for Rates
        # and Proportions, 3rd ed., 2003 — công thức 3.19 (Fleiss-Tytun-Ubhaya
        # 1980): n' = n/4 × [1 + sqrt(1 + 4/(n×δ))]², δ=|p1-p2|. Luôn cho
        # n' ≥ n (bảo thủ hơn) — chính xác hơn xấp xỉ chuẩn khi n nhỏ/tỷ lệ
        # gần biên (kiểm định z rời rạc, không liên tục).
        delta = abs(p1 - p2)
        n = n / 4 * (1 + math.sqrt(1 + 4 / (n * delta))) ** 2
    return math.ceil(n)


def n_two_proportion_auto(p1, p2, alpha=0.05, power=0.80):
    """Như n_two_proportion(), nhưng TỰ ĐỘNG áp hiệu chỉnh liên tục Fleiss khi
    cỡ mẫu cơ sở nhỏ (<100) HOẶC tỷ lệ gần biên (min(p1,p2,1-p1,1-p2)<0.10) —
    đúng ngưỡng co-mau-nghien-cuu.md dòng 69. Trả về (n, đã_hiệu_chỉnh: bool)
    để gọi nơi cần ghi rõ trong artifact A4 việc hiệu chỉnh này có áp dụng
    hay không (SỬA 2026-07-24, vòng lặp kiểm tra-hoàn thiện vòng 15, phát
    hiện MEDIUM — trước đây n_two_proportion() KHÔNG có hiệu chỉnh liên tục ở
    BẤT KỲ lời gọi nào trong main(), dù đây là công thức dùng chung cho ≥6
    nhánh thiết kế, khiến N bị ước lượng thấp hơn thực tế cần ~5-15%)."""
    n_base = n_two_proportion(p1, p2, alpha, power, continuity_correction=False)
    near_boundary = min(p1, p2, 1 - p1, 1 - p2) < 0.10
    small_n = n_base < 100
    if near_boundary or small_n:
        return n_two_proportion(p1, p2, alpha, power, continuity_correction=True), True
    return n_base, False

class InvalidEffectSizeError(ValueError):
    """Effect size/tham số nằm ngoài miền công thức có thể tính hợp lệ."""


CHIEU_KET_CUC = ("higher_better", "lower_better")
_BI_DANH_CHIEU = {
    "higher_better": "higher_better", "higher": "higher_better", "cao_la_tot": "higher_better",
    "cao_tot": "higher_better", "response": "higher_better",
    "lower_better": "lower_better", "lower": "lower_better", "thap_la_tot": "lower_better",
    "thap_tot": "lower_better", "failure": "lower_better",
}


def chuan_hoa_chieu_ket_cuc(raw):
    """«higher_better»/«lower_better» (hoặc None nếu không nhận ra — KHÔNG mặc định).

    VÁ 04/10/2026 (soát từng cổng, G3-01): chiều của kết cục (tỷ lệ CAO là tốt — đáp ứng; hay THẤP là tốt — biến cố
    bất lợi) đổi hẳn mẫu số của công thức non-inferiority. Bỏ dấu tiếng Việt: «cao là tốt» ≡ cao_la_tot."""
    if raw is None:
        return None
    import unicodedata as _ud
    khong_dau = "".join(c for c in _ud.normalize("NFD", str(raw)) if not _ud.combining(c)).replace("đ", "d")
    key = re.sub(r"[\s\-]+", "_", khong_dau.strip().lower())
    return _BI_DANH_CHIEU.get(key)


def n_two_proportion_ni(p_test, p_control, margin, alpha=0.05, power=0.80, outcome_direction="higher_better"):
    """Cỡ mẫu MỖI NHÓM cho kiểm định NON-INFERIORITY hai tỷ lệ (one-sided).

    VÁ 04/10/2026 (soát từng cổng, G3-01): công thức cũ chỉ đúng khi tỷ lệ CAO là tốt (tỷ lệ đáp ứng) trong khi CLI,
    needs_input và doctrine gọi tham số là «tỷ lệ biến cố» — với biến cố bất lợi N bị ước lượng thấp ~5 lần
    (p_test=0,10, p_control=0,08, Δ=0,05: 207/nhóm thay vì 1124/nhóm). Nay bắt buộc khai chiều:
      • higher_better (đáp ứng): H0 p_test − p_control ≤ −Δ  → mẫu số (p_test − p_control + Δ)²
      • lower_better (biến cố bất lợi): H0 p_test − p_control ≥ Δ → mẫu số (Δ − (p_test − p_control))²
    Tham chiếu: Chow SC, Shao J, Wang H. Sample Size Calculations in Clinical Research, 2008 (NI hai tỷ lệ).

    SỬA 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 15, phát hiện HIGH):
    trước đây run_g3_auto.py KHÔNG có bất kỳ nhánh nào cho non-inferiority/
    equivalence dù co-mau-nghien-cuu.md liệt kê đây là bước PHÂN BIỆT bắt
    buộc ("chọn nhầm là sai toàn bộ"). Công thức (Wald, không gộp phương
    sai — H0: p_test - p_control ≤ δ, δ=-margin, margin>0 là mức "kém hơn
    tối đa chấp nhận được"):
        n = (z_{1-alpha} + z_{1-beta})² × [p_test(1-p_test)+p_control(1-p_control)]
            / (p_test - p_control - δ)²
    z_{1-alpha} dùng MỘT PHÍA (không phải alpha/2, khác superiority) vì NI
    chỉ kiểm định một chiều. Đã kiểm chứng bằng ví dụ số cụ thể (HyLown
    powerandsamplesize.com/Calculators/Compare-2-Proportions/2-Sample-Non-
    Inferiority-or-Superiority, tham chiếu Chow/Shao/Wang 2008): p_test=0.85,
    p_control=0.65, margin=0.10, alpha=0.05, power=0.80 → n=25/nhóm (khớp
    chính xác kết quả tính bằng công thức này)."""
    if not (0 < p_test < 1) or not (0 < p_control < 1):
        raise InvalidEffectSizeError(
            f"p_test, p_control phải trong (0,1), nhận được p_test={p_test}, p_control={p_control}")
    if margin is None or margin <= 0:
        raise InvalidEffectSizeError(f"Biên (margin) phải dương, nhận được margin={margin}")
    if outcome_direction not in CHIEU_KET_CUC:
        raise InvalidEffectSizeError(
            f"Non-inferiority cần khai CHIỀU kết cục (--outcome-direction higher_better | lower_better), nhận được "
            f"{outcome_direction!r} — chiều sai làm N lệch nhiều lần; hệ KHÔNG đoán.")
    za = z(alpha)  # MỘT PHÍA — khác n_two_proportion() (alpha/2, hai phía)
    zb = z(1 - power)
    if outcome_direction == "higher_better":
        denom = (p_test - p_control) + margin
        bieu_thuc = "p_test−p_control+Δ"
    else:
        denom = margin - (p_test - p_control)
        bieu_thuc = "Δ−(p_test−p_control)"
    if denom <= 0:
        raise InvalidEffectSizeError(
            f"{bieu_thuc} = {denom:.4f} ≤ 0 — với p_test={p_test}, p_control={p_control}, margin={margin}, "
            f"chiều {outcome_direction}, KHÔNG thể chứng minh non-inferiority về mặt toán học (biên đã bị vi phạm "
            "ngay ở giá trị kỳ vọng). Kiểm tra lại chiều kết cục/margin/p_test hoặc chọn margin khác có biện minh "
            "lâm sàng."
        )
    variance_term = p_test * (1 - p_test) + p_control * (1 - p_control)
    return math.ceil((za + zb) ** 2 * variance_term / denom ** 2)


def apply_fpc_and_cluster_de(n_total, population_n=None, icc=None, cluster_size=None):
    """Áp hiệu chỉnh QUẦN THỂ HỮU HẠN (FPC) rồi CLUSTER DESIGN EFFECT (DE) lên
    n_total — ĐÚNG THỨ TỰ doctrine co-mau-nghien-cuu.md dòng 34 (M4): "Tính cỡ
    mẫu từng nhóm → hiệu chỉnh FPC → cluster DE → dropout → tổng tối thiểu".

    SỬA 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 15, phát hiện MEDIUM):
    trước đây KHÔNG có CLI flag/dòng code nào tính FPC hay design effect/ICC
    trong toàn bộ run_g3_auto.py — một cắt ngang tại MỘT cơ sở với quần thể
    hữu hạn xác định (N nhỏ), hoặc một RCT ngẫu nhiên hóa THEO CỤM (cluster-
    randomized) sẽ nhận N SAI (quá cỡ vì thiếu FPC, hoặc thiếu lực vì thiếu
    design effect). FPC: n_fpc = n/(1+n/N) (Cochran 1977, công thức hiệu
    chỉnh quần thể hữu hạn chuẩn). Cluster DE: DE=1+(m-1)×ICC, n_cluster=n×DE
    (Donner & Klar 2000, "Design and Analysis of Cluster Randomization Trials
    in Health Research" — công thức design effect chuẩn cho cluster RCT).
    Trả về (n_int, ghi_chú: str)."""
    note = ""
    n = float(n_total)
    if population_n and population_n > 0:
        n_fpc = n / (1 + n / population_n)
        note += (f" Đã áp hiệu chỉnh quần thể hữu hạn (FPC, N quần thể={population_n}): "
                 f"n {n:.0f}→{math.ceil(n_fpc)}.")
        n = n_fpc
    if icc is not None and cluster_size:
        de = 1 + (cluster_size - 1) * icc
        n_cluster = n * de
        num_clusters = math.ceil(n_cluster / cluster_size)
        small_k_warning = (
            " ⚠️ Số cụm nhỏ (<15-20) — cân nhắc dùng phân phối t với (k-2) bậc tự do "
            "thay vì z, đối chiếu với thống kê viên (Donner & Klar 2000)."
            if num_clusters < 15 else ""
        )
        note += (f" Đã áp design effect cụm (DE=1+(m-1)×ICC={de:.2f}, m={cluster_size}, "
                 f"ICC={icc}): n {n:.0f}→{math.ceil(n_cluster)} (~{num_clusters} cụm).{small_k_warning}")
        n = n_cluster
    return math.ceil(n), note


def n_log_rank(hr, alpha=0.05, power=0.80, p_event=0.30):
    """
    Số biến cố (Schoenfeld) + cỡ mẫu từ tỷ lệ biến cố.
    SỬA: hr=1.0 → log(1)=0 → chia cho 0 → OverflowError khi ép sang int;
    hr âm → log(số âm) → ValueError. Cả hai trước đây làm crash toàn bộ G3
    không ghi lại artifact/checkpoint nào. Nay validate trước, báo lỗi rõ
    ràng thay vì traceback khó hiểu.
    """
    if hr is None or hr <= 0:
        raise InvalidEffectSizeError(f"HR phải dương, nhận được HR={hr}")
    if 0.98 <= hr <= 1.02:
        raise InvalidEffectSizeError(
            f"HR={hr} quá gần 1.0 (không có hiệu quả để phát hiện) — "
            "công thức Schoenfeld cho ra cỡ mẫu vô hạn. Cần effect size thực tế khác 1.0."
        )
    za = z(alpha / 2)
    zb = z(1 - power)
    # SỬA: công thức Schoenfeld (1983) cho phân bổ 1:1 cần hệ số 4
    # (= 1/[ψ(1-ψ)] với ψ=0.5) ở tử số — thiếu hệ số này làm số biến cố
    # (và do đó N) bị đánh giá thấp đúng 4 lần. Kiểm chứng: HR=0.5,
    # alpha=0.05, power=80% → thiếu hệ số 4 cho d≈16 (sai); có hệ số 4
    # cho d≈65 (khớp textbook Machin/Campbell).
    n_events = math.ceil(4 * (za + zb) ** 2 / (math.log(hr)) ** 2)
    if p_event is None or p_event <= 0:
        raise InvalidEffectSizeError(f"Tỷ lệ biến cố (p_event) phải dương, nhận được p_event={p_event}")
    n_total = math.ceil(n_events / p_event)
    return n_total, n_events

def n_prevalence(p, e=0.05, alpha=0.05):
    """Cỡ mẫu ước lượng tỷ lệ: n = zα/2² × p(1-p) / e².

    SỬA 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 6, phát hiện MEDIUM):
    docstring/nhãn cũ ghi "(Wilson)" nhưng công thức thật là xấp xỉ CHUẨN/
    Wald cổ điển (Cochran) suy từ nới rộng CI kiểu Wald (e = zα/2·√(p(1-p)/n))
    — KHÔNG phải công thức Wilson score interval thật (Wilson không có dạng
    đóng đơn giản n=z²p(1-p)/e², chính vì Wilson được thiết kế để tránh
    nhược điểm của xấp xỉ chuẩn ở p gần 0/1). Đổi nhãn cho đúng — KHÔNG đổi
    công thức (đã có test khóa số tests/test_gate_g3_formulas.py); với p rất
    gần 0/1 (bệnh hiếm), công thức này có thể ước lượng kém hơn Wilson thật —
    cần thống kê viên đối chiếu nếu p nằm ngoài khoảng 0.1-0.9."""
    if not (0 < p < 1):
        raise InvalidEffectSizeError(f"Tỷ lệ p phải trong (0,1), nhận được p={p}")
    if not (0 < e < 1):
        raise InvalidEffectSizeError(f"Sai số biên e phải trong (0,1), nhận được e={e}")
    za = z(alpha / 2)
    return math.ceil(za ** 2 * p * (1 - p) / e ** 2)

def _phuong_sai_auc_hanley_mcneil(auc, n_benh, n_khong_benh):
    """Phương sai AUC theo Hanley & McNeil 1982 (Radiology 143(1):29-36, PMID 7063747,
    doi:10.1148/radiology.143.1.7063747): Var = [A(1−A) + (nA−1)(Q1−A²) + (nN−1)(Q2−A²)] / (nA·nN),
    Q1 = A/(2−A), Q2 = 2A²/(1+A)."""
    q1 = auc / (2 - auc)
    q2 = 2 * auc * auc / (1 + auc)
    return (auc * (1 - auc) + (n_benh - 1) * (q1 - auc * auc) + (n_khong_benh - 1) * (q2 - auc * auc)) / (
        n_benh * n_khong_benh)


def n_auc_hanley_mcneil(auc, alpha=0.05, power=0.80, kappa=1.0, n_toi_da=200000):
    """(số ca BỆNH, số ca KHÔNG BỆNH) tối thiểu để kiểm định AUC so với 0,5 (hai phía).

    VÁ 04/10/2026 (soát từng cổng, G3-04): công thức cũ dùng σ²=A(1−A)+(A−0,5)²/3 («xấp xỉ Hanley-McNeil» — KHÔNG phải
    phương sai Hanley–McNeil) và không dùng tỷ lệ hiện mắc: AUC=0,75 cho 27 tổng (lực thật ≈ 0,64). Nay tìm số ca bệnh
    nhỏ nhất thoả  z(α/2)·√V0 + z(β)·√V1 ≤ |A − 0,5|  với V0 = phương sai Hanley–McNeil tại A=0,5 và V1 tại A giả
    định, số ca không bệnh = ⌈κ × số ca bệnh⌉ (κ = (1−p)/p khi tuyển liên tiếp với tỷ lệ hiện mắc p). Kiểm tay:
    AUC=0,75, α=0,05, lực 80%, κ=1 ⇒ 19 ca/nhóm chưa đủ (0,2533 > 0,25), 20 ca/nhóm đủ (0,2467 ≤ 0,25).
    Phần mềm khác (PASS/MedCalc/pROC — Obuchowski) có thể cho N hơi khác do giả định phương sai khác."""
    if not (0 < auc < 1):
        raise InvalidEffectSizeError(f"AUC phải trong (0,1), nhận được AUC={auc}")
    if auc <= 0.51:
        raise InvalidEffectSizeError(
            f"AUC={auc} ≤ 0.51 — test không phân biệt được bệnh/không bệnh (hoặc đảo chiều); cần AUC giả định > 0.5 "
            "có nguồn.")
    if kappa is None or kappa <= 0:
        raise InvalidEffectSizeError(f"Tỷ số không bệnh/bệnh κ phải dương, nhận được {kappa}")
    za = z(alpha / 2)
    zb = z(1 - power)
    hieu = abs(auc - 0.5)
    for n_benh in range(2, n_toi_da + 1):
        n_khong = max(2, math.ceil(kappa * n_benh))
        v0 = _phuong_sai_auc_hanley_mcneil(0.5, n_benh, n_khong)
        v1 = _phuong_sai_auc_hanley_mcneil(auc, n_benh, n_khong)
        if za * math.sqrt(v0) + zb * math.sqrt(max(v1, 0.0)) <= hieu:
            return n_benh, n_khong
    raise InvalidEffectSizeError(f"Không tìm được cỡ mẫu ≤ {n_toi_da} ca bệnh cho AUC={auc}")


def n_auc(auc, alpha=0.05, power=0.80, prevalence=0.5):
    """TỔNG cỡ mẫu nghiên cứu chẩn đoán (một nhóm tuyển liên tiếp) để kiểm định AUC so với 0,5.

    prevalence = tỷ lệ hiện mắc trong quần thể tuyển (BẮT BUỘC có nguồn — nơi gọi không được mặc định im lặng);
    tổng N = số ca bệnh + số ca không bệnh theo n_auc_hanley_mcneil với κ = (1−p)/p."""
    if prevalence is None or not (0 < prevalence < 1):
        raise InvalidEffectSizeError(f"Tỷ lệ hiện mắc phải trong (0,1), nhận được {prevalence}")
    n_benh, n_khong = n_auc_hanley_mcneil(auc, alpha, power, kappa=(1 - prevalence) / prevalence)
    return n_benh + n_khong

def n_continuous_md(md, sd, alpha=0.05, power=0.80):
    """
    Cỡ mẫu so sánh HAI TRUNG BÌNH độc lập (kết cục LIÊN TỤC — vd thang đau
    NRS/VAS, WOMAC, chất lượng sống), 2 nhóm cỡ bằng nhau, giả định phương
    sai bằng nhau (Machin/Campbell/Fayers — công thức chuẩn dùng trong PASS/
    G*Power cho superiority trial kết cục liên tục):
        n mỗi nhóm = 2 × (SD/MD)² × (zα/2 + zβ)²
    THÊM 2026-07-06: trước đây design RCT/cohort + effect_type=MD (kết cục
    liên tục) KHÔNG có công thức tự động nào — rơi vào nhánh "chưa có công
    thức", dù đây là loại kết cục PHỔ BIẾN NHẤT cho thử nghiệm về triệu chứng
    (đau, chức năng, chất lượng sống). Phát hiện qua chạy thật G0→G10 trên
    một đề tài RCT mới (đau khớp gối, kết cục NRS liên tục).
    """
    if sd is None or sd <= 0:
        raise InvalidEffectSizeError(f"SD phải dương, nhận được SD={sd}")
    if md is None or abs(md) < 1e-9:
        raise InvalidEffectSizeError(
            f"MD={md} bằng 0 (không có hiệu quả để phát hiện) — cần chênh lệch "
            "trung bình thực tế khác 0."
        )
    za = z(alpha / 2)
    zb = z(1 - power)
    return math.ceil(2 * (sd / abs(md)) ** 2 * (za + zb) ** 2)

def extract_best_effect(effect_samples):
    """
    Trích xuất ước lượng hiệu quả tốt nhất từ danh sách G1.
    Trả về (value, type, quality) — quality "labeled" (có 95%CI đi kèm, đáng
    tin) hoặc "crude" (chỉ số % thô không CI, có thể lẫn ARR/RR).
    SỬA: trước đây bỏ qua hoàn toàn trường "quality" mà G1 đã gắn nhãn —
    chọn effect đầu tiên khớp type bất kể lấy từ pattern có nhãn hay thô,
    khiến việc phân biệt labeled/crude ở G1 vô nghĩa với phép tính cỡ mẫu
    thật (G3 mới là nơi con số này được DÙNG, không phải chỉ hiển thị).
    """
    if not effect_samples:
        return None, None, None
    # Ưu tiên: HR/OR/RR loại "labeled" > HR/OR/RR loại "crude" > ARR% "labeled"
    # > ARR% "crude" — luôn ưu tiên quality trước, bất kể thứ tự trong list.
    for want_quality in ("labeled", "crude"):
        for ef in effect_samples:
            if ef.get("type") in ("HR", "OR", "RR") and ef.get("quality", "crude") == want_quality:
                val = ef.get("value")
                if val and 0.3 < float(val) < 3.0:
                    return float(val), ef.get("type"), want_quality
    for want_quality in ("labeled", "crude"):
        for ef in effect_samples:
            if ef.get("type") == "ARR%" and ef.get("quality", "crude") == want_quality:
                # SỬA: .get("value", 0.10) không dùng default khi key tồn
                # tại với giá trị null — bọc "or 0.10" tránh float(None) crash
                # (nhánh HR/OR/RR phía trên đã có "if val" guard, nhánh này
                # thiếu, cùng loại lỗi None-unsafe đã sửa ở nhiều nơi khác).
                val = ef.get("value")
                if val is not None:
                    return float(val), "ARR%", want_quality
    return None, None, None

ONE_GROUP_DESIGNS = frozenset({"cross_sectional", "diagnostic", "prediction", "qualitative", "sr_ma"})


def tinh_n_loi(design_code, effect_type, effect_val, alpha, power, *, p0=0.30, p_event=0.30, sd=None,
               precision=0.05, prevalence=None, hypothesis_type="superiority", margin=None,
               outcome_direction=None):
    """MỘT nơi tính cỡ mẫu LÕI (trước FPC/cụm/dropout) cho mọi nhánh — main() và bảng độ nhạy cùng gọi.

    VÁ 04/10/2026 (soát từng cổng, G3-06): trước đây bảng độ nhạy tự tính lại theo cách riêng (không Fleiss, không làm
    tròn theo nhóm, d cố định 0,05, không FPC/cụm, NI không có bảng) nên ô cơ sở lệch N đã kết luận và G3-AUTO-09 REVIEW
    vĩnh viễn ở nhiều đường hợp lệ. Trả dict: n_per_group, n_total, formula, missing_sd, n_benh, n_khong_benh.
    Ném InvalidEffectSizeError khi tham số ngoài miền (không kẹp im lặng)."""
    kq = {"n_per_group": 0, "n_total": 0, "formula": "", "missing_sd": False, "n_benh": None, "n_khong_benh": None}
    if hypothesis_type in ("non_inferiority", "equivalence"):
        if margin is None or margin <= 0:
            raise InvalidEffectSizeError(
                f"--hypothesis-type={hypothesis_type} BẮT BUỘC có --margin dương "
                "(biên Δ có biện minh lâm sàng + nguồn) — KHÔNG bịa margin.")
        if effect_val is None or not (0 < effect_val < 1):
            raise InvalidEffectSizeError(
                f"--hypothesis-type={hypothesis_type} cần --effect-size là TỶ LỆ kết cục nhóm thử nghiệm "
                f"(p_test) trong (0,1), nhận được {effect_val} — KHÔNG phải OR/RR/HR như superiority.")
        if hypothesis_type == "equivalence":
            kq["formula"] = (
                "[CẦN — Equivalence (TOST — Two One-Sided Tests) CHƯA được tự động hóa ở "
                "đây vì công thức closed-form chưa được xác minh bằng ví dụ số cụ thể từ "
                "nguồn công khai tại thời điểm này (khác non_inferiority — đã xác minh). "
                "Dùng phần mềm chuyên dụng (PASS 'Equivalence Tests', R TOSTER/PowerTOST) "
                "theo Chow SC, Shao J, Wang H. Sample Size Calculations in Clinical "
                "Research, 2nd ed., 2008, Chương 3 (tr.86) — cần bác sĩ/thống kê viên tính "
                "TRỰC TIẾP bằng phần mềm đó. KHÔNG bịa N ở đây.]"
            )
            return kq
        n = n_two_proportion_ni(effect_val, p0, margin, alpha, power, outcome_direction)
        kq.update(n_per_group=n, n_total=n * 2)
        _chieu = ("tỷ lệ CAO là tốt — đáp ứng" if outcome_direction == "higher_better"
                  else "tỷ lệ THẤP là tốt — biến cố bất lợi")
        kq["formula"] = (
            f"Non-inferiority two-proportion (one-sided, Wald): p_test={effect_val:.2f}, "
            f"p_control={p0:.2f}, margin={margin:.2f}, chiều kết cục={outcome_direction} ({_chieu}), "
            f"zα(một phía)={z(alpha):.3f}. [CẦN — --margin PHẢI có biện minh lâm sàng "
            "(không phải giá trị thống kê thuận tiện) và được Hội đồng/thống kê viên "
            "xác nhận TRƯỚC khi khóa SAP.]"
        )
        return kq
    if effect_val is None:
        return kq
    if design_code in ("cohort", "rct") and effect_type == "HR":
        ev = effect_val if effect_val < 1.0 else 1 / effect_val
        n_total_raw, n_events = n_log_rank(ev, alpha, power, p_event)
        n = math.ceil(n_total_raw / 2)
        kq.update(n_per_group=n, n_total=n * 2)
        kq["formula"] = (f"Schoenfeld log-rank: d = (zα/2+zβ)²/ln(HR)² = {n_events} biến cố → N={n * 2}"
                         if design_code == "cohort" else f"Schoenfeld log-rank: d={n_events} biến cố")
    elif design_code in ("cohort", "rct") and effect_type in ("OR", "RR"):
        if effect_type == "OR":
            odds1 = effect_val * (p0 / (1 - p0))
            p1 = odds1 / (1 + odds1)
        else:
            p1 = p0 * effect_val
            # VÁ 04/10/2026 (G3-10): RR×p0 ≥ 1 là bất khả (tỷ lệ > 100%) — trước đây bị kẹp im lặng về ≈1.
            if not (0 < p1 < 1):
                raise InvalidEffectSizeError(
                    f"RR={effect_val} × p0={p0} = {p1:.3f} — tỷ lệ nhóm {'phơi nhiễm' if design_code == 'cohort' else 'can thiệp'} "
                    "ngoài (0,1). Kiểm lại RR/p0, hoặc dùng OR.")
        n, fleiss = n_two_proportion_auto(p1, p0, alpha, power)
        kq.update(n_per_group=n, n_total=n * 2)
        _g = "phơi nhiễm" if design_code == "cohort" else "can thiệp"
        _g0 = "không phơi nhiễm" if design_code == "cohort" else "chứng/không can thiệp"
        kq["formula"] = (f"Two-proportion ({design_code}, {effect_type}={effect_val:.2f} → "
                         f"tỷ lệ biến cố {_g}≈{p1:.2f} vs {_g0}={p0:.2f})."
                         + (" Đã áp hiệu chỉnh liên tục Fleiss (cỡ mẫu nhỏ/tỷ lệ gần biên)." if fleiss else "")
                         + f" [CẦN — --p0 ở đây là TỶ LỆ BIẾN CỐ NỀN của nhóm {_g0}; nếu đề tài "
                         "thật sự có dữ liệu thời gian-đến-biến-cố và effect size là HR "
                         "thật (không phải OR/RR), dùng --effect-type HR để tính bằng "
                         "Schoenfeld log-rank thay vì công thức này.]")
    elif design_code == "case_control" and effect_type in ("OR", "RR", "HR"):
        odds1 = effect_val * (p0 / (1 - p0))
        p1 = odds1 / (1 + odds1)
        n, fleiss = n_two_proportion_auto(p1, p0, alpha, power)
        kq.update(n_per_group=n, n_total=n * 2)
        kq["formula"] = (f"Two-proportion (case-control, {effect_type}={effect_val:.2f} → "
                         f"tỷ lệ phơi nhiễm ca≈{p1:.2f} vs chứng={p0:.2f})."
                         + (" Đã áp hiệu chỉnh liên tục Fleiss (cỡ mẫu nhỏ/tỷ lệ gần biên)." if fleiss else "")
                         + " [CẦN — --p0 ở đây được diễn giải là TỶ LỆ PHƠI NHIỄM NỀN của "
                         "nhóm chứng (không phải tỷ lệ biến cố như ở cohort/RCT); bác sĩ "
                         "xác nhận con số này đúng với đề tài, mặc định 0.30 chỉ là khởi tạo.]")
    elif design_code in ("rct", "cohort") and effect_type == "MD":
        if sd is None or sd <= 0:
            kq["missing_sd"] = True
            kq["formula"] = (f"[CẦN — có MD={effect_val:.2f} (kết cục liên tục) nhưng THIẾU SD "
                             "(độ lệch chuẩn) để tính cỡ mẫu. Bác sĩ/thống kê viên cấp qua "
                             "--sd <giá_trị> (lấy từ pilot/y văn cùng kết cục, ghi rõ nguồn "
                             "PMID/DOI) — hệ KHÔNG bịa SD.]")
            return kq
        n = n_continuous_md(effect_val, sd, alpha, power)
        kq.update(n_per_group=n, n_total=n * 2)
        kq["formula"] = (f"Two-sample continuous (Machin/Campbell/Fayers): "
                         f"n=2×(SD/MD)²×(zα/2+zβ)² với MD={effect_val:.2f}, SD={sd:.2f}")
    elif design_code in ("rct", "cohort", "case_control") and effect_type == "ARR%":
        p1, p2 = p0, p0 - effect_val / 100
        # VÁ 04/10/2026 (G3-10): ARR% làm p2 ≤ 0 từng bị kẹp im lặng về 0,05 (ARR hiệu dụng khác hẳn yêu cầu).
        if not (0 < p2 < 1):
            raise InvalidEffectSizeError(
                f"ARR%={effect_val} với p0={p0:.2f} cho p2={p2:.3f} ngoài (0,1) — kiểm lại ARR%/p0.")
        n, fleiss = n_two_proportion_auto(p1, p2, alpha, power)
        kq.update(n_per_group=n, n_total=n * 2)
        kq["formula"] = (f"Two-proportion z-test: p1={p1:.2f}, p2={p2:.2f}"
                         + (" Đã áp hiệu chỉnh liên tục Fleiss (cỡ mẫu nhỏ/tỷ lệ gần biên)." if fleiss else ""))
    elif design_code == "cross_sectional":
        if not (0 < effect_val < 1):
            raise InvalidEffectSizeError(
                f"Thiết kế cắt ngang cần TỶ LỆ ước lượng p trong (0,1), nhận được {effect_val}.")
        n = n_prevalence(effect_val, precision, alpha)
        kq.update(n_per_group=n, n_total=n)
        _p_label = "tỷ lệ hiện mắc ước lượng" if effect_type == "PREVALENCE" else "tỷ lệ"
        kq["formula"] = (f"Cỡ mẫu ước lượng một tỷ lệ theo độ chính xác "
                         f"(Lwanga & Lemeshow/Cochran, xấp xỉ chuẩn): {_p_label} p={effect_val:.2f}, "
                         f"sai số cho phép d={precision}, alpha={alpha}")
    elif design_code == "diagnostic":
        if effect_type != "AUC":
            raise InvalidEffectSizeError(
                f"Thiết kế chẩn đoán cần --effect-type AUC (nhận được {effect_type}) — hệ KHÔNG thay bằng AUC mặc định.")
        if prevalence is None or not (0 < prevalence < 1):
            raise InvalidEffectSizeError(
                "Thiết kế chẩn đoán cần TỶ LỆ HIỆN MẮC p của quần thể tuyển (--prevalence, có nguồn) để quy số ca "
                "bệnh ra tổng N — hệ KHÔNG mặc định.")
        n_benh, n_khong = n_auc_hanley_mcneil(effect_val, alpha, power, kappa=(1 - prevalence) / prevalence)
        kq.update(n_per_group=n_benh + n_khong, n_total=n_benh + n_khong, n_benh=n_benh, n_khong_benh=n_khong)
        kq["formula"] = (f"Hanley–McNeil 1982 (PMID 7063747): kiểm định AUC={effect_val:.2f} so với 0,5 (hai phía) — "
                         f"{n_benh} ca bệnh + {n_khong} ca không bệnh (tỷ lệ hiện mắc p={prevalence:.2f}, "
                         f"κ=(1−p)/p={(1 - prevalence) / prevalence:.2f}). [CẦN — phần mềm khác (PASS/MedCalc/pROC) có "
                         "thể cho N hơi khác do giả định phương sai khác; nếu cỡ mẫu phụ thuộc chủ yếu vào con số này, "
                         "nhờ thống kê viên đối chiếu.]")
    else:
        kq["formula"] = (f"[CẦN CÔNG THỨC CỤ THỂ — tổ hợp design_code={design_code} + "
                         f"effect_type={effect_type} chưa có công thức tự động. "
                         "Bác sĩ/thống kê viên cần chọn công thức phù hợp thủ công.]")
    return kq


def ap_fpc_cum(n_total, design_code, population_n=None, icc=None, cluster_size=None):
    """(n_total sau FPC/cụm, n_per_group tương ứng, ghi chú, design_effect hoặc None, số cụm hoặc None,
    N NGAY TRƯỚC khi nhân DE — tức sau FPC nếu có)."""
    if not n_total or not (population_n or (icc is not None and cluster_size)):
        return n_total, (n_total if design_code in ONE_GROUP_DESIGNS else math.ceil(n_total / 2)), "", None, None, \
            n_total
    n2, note = apply_fpc_and_cluster_de(n_total, population_n, icc, cluster_size)
    de = (1 + (cluster_size - 1) * icc) if (icc is not None and cluster_size) else None
    so_cum = math.ceil(n2 / cluster_size) if de is not None else None
    n_truoc_de = math.ceil(n_total / (1 + n_total / population_n)) if population_n else n_total
    # VÁ 04/10/2026 (G3-06): thiết kế MỘT nhóm giữ n_per_group = n_total sau FPC/cụm (trước đây bị chia đôi).
    n_nhom = n2 if design_code in ONE_GROUP_DESIGNS else math.ceil(n2 / 2)
    return n2, n_nhom, note, de, so_cum, n_truoc_de


def sensitivity_table(design_code, base_n, effect_val, effect_type, alpha, p_event=0.30, p0=0.30, sd=None, *,
                      power=0.80, precision=0.05, prevalence=None, hypothesis_type="superiority", margin=None,
                      outcome_direction=None, population_n=None, icc=None, cluster_size=None):
    """Bảng độ nhạy N tổng (TRƯỚC dropout, SAU FPC/cụm như N chính): hàng = power, cột = biến thiên tham số chính.

    Superiority: ES × 0,8/1,0/1,2 (AUC: biến thiên phần vượt 0,5). Non-inferiority: biên Δ × 0,8/1,0/1,2. Mọi ô gọi
    CHÍNH tinh_n_loi + ap_fpc_cum như main() ⇒ ô (power đang dùng, ×1,0) BẰNG N chính theo cấu trúc (G3-06).
    base_n giữ chỗ cho chữ ký cũ (không dùng)."""
    powers = sorted({0.70, 0.80, 0.90, round(float(power), 4)})
    mults = [0.80, 1.00, 1.20]
    rows = []
    ni = hypothesis_type in ("non_inferiority", "equivalence")
    for pwr in powers:
        row = []
        for m in mults:
            ev, mg = effect_val, margin
            if ni:
                mg = (margin or 0) * m
            elif effect_type == "AUC" and effect_val is not None:
                ev = 0.5 + (effect_val - 0.5) * m
            elif effect_val is not None:
                ev = effect_val * m
            try:
                kq = tinh_n_loi(design_code, effect_type, ev, alpha, pwr, p0=p0, p_event=p_event, sd=sd,
                                precision=precision, prevalence=prevalence, hypothesis_type=hypothesis_type,
                                margin=mg, outcome_direction=outcome_direction)
                n = kq["n_total"]
                if not n:
                    row.append("N/A")
                    continue
                n = ap_fpc_cum(n, design_code, population_n, icc, cluster_size)[0]
            except (InvalidEffectSizeError, ValueError, ZeroDivisionError, OverflowError):
                row.append("N/A")
                continue
            row.append(n)
        rows.append((pwr, row))
    return rows, mults


def load_checkpoint(path):
    """Đọc checkpoint JSON nếu tồn tại."""
    if Path(path).exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardrail_check(artifact, n_adjusted, effect_val, missing_sd=False):
    """Kiểm guardrail R1-R7 cho G3."""
    errors, warnings = [], []
    # R1 — Không bịa PMID
    if re.search(r'PMID:\d{8}(?!\d)', artifact):
        pmids = re.findall(r'PMID:(\d+)', artifact)
        if any(int(p) > 40000000 for p in pmids):
            errors.append("R1 🔴 Có thể có PMID không thật")
        else:
            warnings.append("R1 ✅ PMID nằm trong khoảng hợp lý")
    else:
        warnings.append("R1 ✅ Không có PMID bịa")
    # R2 — Không PII
    if re.search(r'\b(CMND|CCCD|CMT)\s*\d{9,12}', artifact, re.IGNORECASE):
        errors.append("R2 🔴 Phát hiện mẫu PII (CMND/CCCD)")
    else:
        warnings.append("R2 ✅ Không PII")
    # R3 — Không claim approved
    if "APPROVED_EXTERNALLY" in artifact or "G3_STATUS: LOCKED" in artifact:
        errors.append("R3 🔴 Không được tự claim APPROVED/LOCKED")
    else:
        warnings.append("R3 ✅ Không tự claim approved")
    # R4 — Có DRAFT
    # SỬA 2026-07-31 (audit tautology vòng 2): generate_artifact() in cứng
    # đúng 2 lần chuỗi "DRAFT" VÔ ĐIỀU KIỆN (tiêu đề + dòng trạng thái) cho
    # MỌI design_code/effect_val/hypothesis_type — đã xác nhận thực nghiệm
    # 12 tổ hợp thiết kế khác nhau, draft_count LUÔN=2, R4 LUÔN PASS. R4
    # KHÔNG BAO GIỜ có thể BLOCK qua pipeline thật; giá trị hẹp DUY NHẤT là
    # bắt được nếu ai đó XÓA nhãn DRAFT khỏi file .md sau khi sinh
    # (tampering) — không thẩm định N/effect size có đáng tin.
    draft_count = artifact.count("DRAFT")
    if draft_count < 1:
        errors.append("R4 🔴 Thiếu nhãn DRAFT")
    else:
        warnings.append(f"R4 ✅ Nhãn DRAFT đủ ({draft_count} lần)")
    # R5 — Sensitivity analysis
    # SỬA 2026-07-31: luật này chỉ kiểm SỰ HIỆN DIỆN của tiêu đề mục "PHẦN 3
    # — PHÂN TÍCH ĐỘ NHẠY" (luôn có, generate_artifact() in cứng), KHÔNG
    # kiểm NỘI DUNG bảng — PASS ngay cả khi 100% ô là "N/A" (thiếu SD khiến
    # mọi kịch bản không tính được số thật, đã xác nhận thực nghiệm). Thẩm
    # định nội dung bảng THẬT thuộc g3_quality_gate.py::G3-AUTO-09 (đọc số
    # qua parse_sensitivity_table()/cells_na) — không nhân đôi logic đó ở
    # đây.
    if "sensitivity" in artifact.lower() or "độ nhạy" in artifact.lower():
        warnings.append("R5 ✅ Sensitivity analysis gồm nhiều kịch bản")
    else:
        errors.append("R5 🔴 Thiếu sensitivity analysis")
    # R6 — Có [CẦN]
    # SỬA 2026-07-31: generate_artifact() luôn in tối thiểu 4 chuỗi "[CẦN"
    # VÔ ĐIỀU KIỆN (1 ở bảng dropout + 3 ở checklist PHẦN 5 cố định) — đã
    # xác nhận thực nghiệm can_count dao động 5-11 nhưng LUÔN >=3 ở 12 tổ
    # hợp thử, R6 LUÔN PASS bất kể mức độ hoàn thiện thật của đề tài. Cùng
    # dạng lỗi "thưởng dán nhãn" đã đóng ở G0::guardrail_check_g0() R6.
    # KHÔNG thêm ngưỡng phụ thuộc dữ liệu mới ở đây — PHẦN 5 giữ checklist
    # tĩnh dù bác sĩ đã xác nhận xong qua gate_params.G3, nên đếm "[CẦN"
    # không phản ánh đúng tiến độ; đánh giá hoàn thiện ĐÚNG đã có sẵn ở
    # g3_quality_gate.py (G3-HUMAN-01..07).
    can_count = len(re.findall(r'\[CẦN', artifact))
    if can_count < 3:
        errors.append(f"R6 🔴 Quá ít trường [CẦN...] ({can_count})")
    else:
        warnings.append(f"R6 ✅ {can_count}+ trường [CẦN...] đã gắn nhãn")
    # R7 — Disclaimer
    # SỬA 2026-07-31: dòng disclaimer được generate_artifact() in cứng VÔ
    # ĐIỀU KIỆN ở cuối artifact — R7 chỉ bắt được tampering (xóa dòng sau
    # khi sinh), không thẩm định bác sĩ có thực sự kiểm chứng nội dung hay
    # chưa. Cùng khuôn R7 đã đóng ở G0/G1/G2/G6/G8/G9 trong đợt audit này.
    if "Cần bác sĩ kiểm chứng" not in artifact:
        errors.append("R7 🔴 Thiếu disclaimer")
    else:
        warnings.append("R7 ✅ Có disclaimer")
    # R8 — Không âm thầm báo N=0 như thể đã tính xong (SỬA: trước đây tổ hợp
    # design/effect chưa có công thức bị fabricate N=100/200 và vẫn PASS lặng
    # lẽ; nay N=0 hợp lệ nhưng PHẢI hiện rõ để bác sĩ biết cần tính thủ công)
    if effect_val and n_adjusted == 0:
        if missing_sd:
            warnings.append("R8 ⚠️ N=0 — có MD nhưng THIẾU SD (độ lệch chuẩn), "
                             "cần bác sĩ/thống kê viên cấp SD từ pilot/y văn (xem formula_used)")
        else:
            warnings.append("R8 ⚠️ N=0 — công thức tự động chưa hỗ trợ tổ hợp design/effect này, "
                             "cần bác sĩ/thống kê viên tính thủ công (xem formula_used)")
    return errors, warnings

def generate_artifact(study, topic, design_code, design_primary, alpha, power, effect_val, effect_type,
                      n_per_group, n_total, n_adjusted, dropout, formula_used, sens_rows, sens_mults,
                      p_event, run_date, sd=None, design_ambiguous=False, confirmed_n=None,
                      hypothesis_type="superiority", nguon_tham_so=None, nguon_hieu_qua=None,
                      outcome_direction=None, margin=None, precision=0.05, prevalence=None, n_benh=None,
                      n_khong_benh=None, population_n=None, icc=None, cluster_size=None, nguon_mo_ta=None):
    """Sinh A4 — Kế hoạch cỡ mẫu.

    VÁ 04/10/2026 (soát từng cổng, G3-08): cột «Nguồn» in theo XUẤT XỨ THẬT của từng tham số (CLI / study_meta / đặc
    tả G1 / trích từ G1-G0 / mặc định máy) — trước đây in cứng «Trích từ y văn G0» cho mọi giá trị, kể cả p=0,5 mặc
    định. Thiết kế một nhóm/mô tả không có câu lực thống kê và chữ «mỗi nhóm»."""
    nguon_tham_so = nguon_tham_so or {}
    nguon_mo_ta = {k: v for k, v in (nguon_mo_ta or {}).items() if v}
    mo_ta_chinh_xac = effect_type == "PREVALENCE" or hypothesis_type == "descriptive_precision"
    mot_nhom = design_code in ONE_GROUP_DESIGNS

    def _nguon(ten, mac_dinh="[CẦN XÁC NHẬN — mặc định máy]"):
        goc = nguon_tham_so.get(ten)
        if not goc or str(goc).startswith("mặc định"):
            return f"{goc} — [CẦN XÁC NHẬN]" if goc else mac_dinh
        return {"CLI": "do bác sĩ/thống kê viên cấp (dòng lệnh)", "study_meta": "ghim trong study_meta"}.get(goc, goc)
    study_safe = study.replace(" ", "-")
    # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 15): non_inferiority
    # dùng z MỘT PHÍA (xem n_two_proportion_ni()) — nhãn "two-sided" cứng cho
    # MỌI thiết kế trước đây sẽ sai/gây nhầm lẫn cho hypothesis_type khác
    # superiority.
    _alpha_sidedness = "one-sided" if hypothesis_type == "non_inferiority" else "two-sided"
    if mo_ta_chinh_xac:
        _hang_gia_thuyet = ("| Khung cỡ mẫu | Ước lượng theo ĐỘ CHÍNH XÁC (không kiểm định giả thuyết) | "
                            f"{_nguon('hypothesis_type')} |")
        _hang_alpha = f"| Độ tin cậy | {int(round((1 - alpha) * 100))}% (α = {alpha}, hai phía) | Quy ước |"
        _hang_luc = []
    else:
        _hang_gia_thuyet = f"| Loại giả thuyết | {hypothesis_type} | {_nguon('hypothesis_type')} |"
        _hang_alpha = f"| Mức ý nghĩa (α) | {alpha} ({_alpha_sidedness}) | Quy ước |"
        _hang_luc = [f"| Lực thống kê (1−β) | {int(power*100)}% | Quy ước |"]
    lines = [
        "# A4 — KẾ HOẠCH CỠ MẪU (DRAFT)",
        f"**Đề tài:** {topic}  ",
        f"**Mã:** {study_safe} | **Ngày sinh:** {run_date} | **Trạng thái:** DRAFT — CHỜ BÁC SĨ XÁC NHẬN",
        "",
        "---",
        "",
        "## PHẦN 1 — THÔNG SỐ ĐẦU VÀO",
        "",
        "| Thông số | Giá trị | Nguồn |",
        "|---|---|---|",
        _hang_gia_thuyet,
        _hang_alpha,
        *_hang_luc,
        f"| Tỷ lệ {'không trả lời' if mo_ta_chinh_xac else 'bỏ cuộc'} dự kiến | {int(dropout*100)}% | "
        "[CẦN BÁC SĨ XÁC NHẬN] |",
    ]
    if effect_val:
        if effect_type == "PREVALENCE":
            _ng = ("mặc định quy ước p=0,5 (thận trọng nhất) — [CẦN XÁC NHẬN]"
                   if str(nguon_hieu_qua or "").startswith("mặc định") else
                   (_nguon("prevalence") + (f"; nguồn: {nguon_mo_ta['prevalence_source']}"
                                            if nguon_mo_ta.get("prevalence_source") else "")))
            lines += [
                f"| Tỷ lệ ước lượng p | {effect_val:.2f} | {_ng} |",
                f"| Sai số tuyệt đối cho phép d | ±{precision * 100:g}% | {_nguon('precision')} |",
            ]
        else:
            if str(nguon_hieu_qua or "").startswith("trích từ"):
                _ng = f"{nguon_hieu_qua} — [CẦN đọc toàn văn xác nhận]"
            else:
                _ng = _nguon("effect_size", "[CẦN NGUỒN]")
            if nguon_mo_ta.get("effect_source"):
                _ng += f"; nguồn: {nguon_mo_ta['effect_source']}"
            _ten_hq = "Tỷ lệ kết cục nhóm thử nghiệm (p_test)" if effect_type == "NI_PROPORTION" else "Effect size ước lượng"
            lines += [
                f"| {_ten_hq} | {effect_type} = {effect_val:.2f} | {_ng} |",
            ]
        if hypothesis_type in ("non_inferiority", "equivalence"):
            lines += [
                f"| Biên Δ | {margin} | {_nguon('margin', '[CẦN NGUỒN]')}"
                + (f"; nguồn: {nguon_mo_ta['margin_source']}" if nguon_mo_ta.get("margin_source") else "") + " |",
                f"| Chiều kết cục | {outcome_direction or '[CẦN — higher_better/lower_better]'} | "
                f"{_nguon('outcome_direction', '[CẦN KHAI]')} |",
            ]
        if design_code == "diagnostic" and prevalence is not None:
            lines.append(f"| Tỷ lệ hiện mắc trong quần thể tuyển | {prevalence:.2f} | {_nguon('prevalence', '[CẦN NGUỒN]')} |")
        if design_code in ("cohort", "rct") and effect_type == "HR":
            lines.append(f"| Tỷ lệ biến cố nền | {p_event*100:.0f}% | [CẦN XÁC NHẬN — từ y văn/pilot] |")
        if design_code in ("cohort", "rct") and effect_type == "MD":
            if sd is not None and sd > 0:
                lines.append(f"| Độ lệch chuẩn (SD) kết cục | {sd:.2f} | [CẦN XÁC NHẬN — từ y văn/pilot] |")
            else:
                lines.append("| Độ lệch chuẩn (SD) kết cục | **[CẦN BÁC SĨ ẤN ĐỊNH]** | Không thể tự trích từ abstract |")
    else:
        lines += [
            "| Effect size | **[CẦN BÁC SĨ ẤN ĐỊNH]** | Không tìm được từ G0 |",
            "| Gợi ý: dùng MCID của kết cục chính | — | [CẦN PMID/DOI hỗ trợ] |",
        ]
    lines += [
        "",
        f"> **Thiết kế:** {design_primary}  ",
        f"> **Công thức:** {formula_used}",
        "",
        "---",
        "",
        "## PHẦN 2 — KẾT QUẢ TÍNH TOÁN",
        "",
    ]
    if effect_val and n_total and mot_nhom:
        lines += [
            "| Chỉ số | Kết quả |",
            "|---|---|",
            *([f"| Số ca bệnh | **{n_benh}** |", f"| Số ca không bệnh | **{n_khong_benh}** |"]
              if n_benh is not None else []),
            f"| N cần (chưa bù {'không trả lời' if mo_ta_chinh_xac else 'bỏ cuộc'}) | **{n_total}** |",
            f"| N điều chỉnh ({int(dropout*100)}%) | **{n_adjusted}** |",
            "",
            f"**KẾT LUẬN:** Nghiên cứu cần tuyển **{n_adjusted} người tham gia**.",
        ]
    elif effect_val and n_total:
        lines += [
            "| Chỉ số | Kết quả |",
            "|---|---|",
            f"| N mỗi nhóm | **{n_per_group}** |",
            f"| N tổng (không dropout) | **{n_total}** |",
            f"| N điều chỉnh (dropout {int(dropout*100)}%) | **{n_adjusted}** |",
            "",
            f"**KẾT LUẬN:** Nghiên cứu cần tuyển **{n_adjusted} người tham gia** (chia đều {n_per_group} mỗi nhóm).",
        ]
        if design_ambiguous:
            lines += [
                "",
                f"> ⚠️ **[CẦN BÁC SĨ XÁC NHẬN THIẾT KẾ TRƯỚC KHI DÙNG N NÀY]** — G1 gán thiết kế "
                f"`{design_code}` làm PLACEHOLDER TẠM (lĩnh vực đã bão hòa cả RCT lẫn SR/MA, bác sĩ "
                "CHƯA xác nhận khoảng trống thật — xem G1 A2 §khoảng trống). N ở trên tính đúng công "
                f"thức cho thiết kế `{design_code}` NHƯNG có thể phải tính LẠI nếu bác sĩ chọn thiết kế "
                "khác (SR/MA cập nhật không cần cỡ mẫu kiểu này, hoặc RCT nhắm phân nhóm cụ thể).",
            ]
    elif design_code in N_NOT_APPLICABLE_DESIGNS:
        # SỬA 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG): trước bản vá này,
        # nhánh `else` phía dưới ("⚠ Chưa tính được — cần effect size") hiện
        # SAI cho sr_ma/prediction/qualitative — 3 thiết kế này effect_val
        # LUÔN None (không áp dụng), N=0 là CÓ CHỦ ĐÍCH với phương pháp thay
        # thế đã giải thích ở PHẦN 1 (formula_used), không phải "thiếu".
        lines += [
            f"**ℹ️ N=0 CÓ CHỦ ĐÍCH** — thiết kế `{design_code}` không dùng công thức "
            "cỡ mẫu power/effect size truyền thống. Xem PHẦN 1 (mục Công thức) để "
            "biết phương pháp đúng cho thiết kế này.",
            "",
            "| Chỉ số | Kết quả |",
            "|---|---|",
            "| N mỗi nhóm | **[N/A — xem Công thức]** |",
            "| N tổng | **[N/A — xem Công thức]** |",
            "| N điều chỉnh | **[N/A — xem Công thức]** |",
        ]
    else:
        lines += [
            ("**⚠ Chưa tính được** — " + (formula_used if formula_used.startswith(("[LỖI", "[CẦN"))
                                         else "bác sĩ cần cung cấp effect size.")),
            "",
            "| Chỉ số | Kết quả |",
            "|---|---|",
            "| N mỗi nhóm | **[CẦN EFFECT SIZE]** |",
            "| N tổng | **[CẦN EFFECT SIZE]** |",
            "| N điều chỉnh | **[CẦN EFFECT SIZE]** |",
        ]
    if confirmed_n is not None:
        lines += [
            "",
            "## PHẦN 2b — CỠ MẪU THỰC TẾ ĐÃ CHỐT (bác sĩ/chủ nhiệm quyết định)",
            "",
            f"**N thực tế đã chốt:** **{confirmed_n}** người tham gia — quyết định của "
            "bác sĩ/chủ nhiệm đề tài (vd theo khả năng thu thập/thời gian/hành chính), "
            "KHÔNG thay thế công thức tính N tối thiểu ở PHẦN 2, chỉ ghi SONG SONG để "
            "đối chiếu.",
            "",
        ]
        if n_adjusted > 0:
            if confirmed_n >= n_adjusted:
                margin = ""
                if design_code == "cross_sectional":
                    moe = 1.96 * math.sqrt(0.5 * 0.5 / confirmed_n) * 100
                    margin = (
                        f" Với N={confirmed_n} (giả định p=0.50, xấu nhất), sai số biên "
                        f"(margin of error) 95% CI ước lượng tỷ lệ ≈ ±{moe:.1f} điểm phần "
                        "trăm — chặt hơn mức tối thiểu PHẦN 2 (N tối thiểu cho ±5%)."
                    )
                lines.append(
                    f"✅ **ĐẠT** — N chốt ({confirmed_n}) ≥ N tối thiểu tính theo thống kê "
                    f"({n_adjusted}), đủ hoặc dư lực thống kê/độ chính xác so với yêu cầu tối "
                    f"thiểu.{margin}"
                )
            else:
                lines.append(
                    f"🔴 **CẢNH BÁO** — N chốt ({confirmed_n}) THẤP HƠN N tối thiểu tính theo "
                    f"thống kê ({n_adjusted}) — nguy cơ THIẾU LỰC THỐNG KÊ (underpowered). Bác "
                    "sĩ/thống kê viên cần xác nhận đây là quyết định có chủ đích (vd nghiên cứu "
                    "thăm dò/pilot) và ghi rõ giới hạn này trong đề cương, hoặc tăng N/điều "
                    "chỉnh effect size kỳ vọng."
                )
        else:
            lines.append(
                "[CẦN BỔ SUNG] — chưa có N tối thiểu tính theo thống kê để đối chiếu (thiếu "
                "effect size ở PHẦN 1); N chốt ở trên vẫn được ghi nhận nhưng KHÔNG có cơ sở "
                "so sánh."
            )
    lines += [
        "",
        "---",
        "",
        "## PHẦN 3 — PHÂN TÍCH ĐỘ NHẠY (Sensitivity Analysis)",
        "",
    ]
    # SỬA 2026-07-31: bảng "Power × Effect size" vô nghĩa với thiết kế MÔ TẢ —
    # cỡ mẫu theo độ chính xác không phụ thuộc power (ba dòng power cho cùng một
    # số), và nhãn "ES" sai ngữ nghĩa vì tham số là tỷ lệ p chứ không phải effect
    # size. Bảng đúng cho thiết kế này là p × d, giống bảng mà đề cương mô tả nào
    # cũng phải có. Tiêu đề cũ còn tự khai "điều chỉnh N% dropout" trong khi các ô
    # là N TRƯỚC dropout (chính G3-AUTO-09 bắt được mâu thuẫn này).
    if effect_type == "PREVALENCE":
        _d_list = [round(precision / 2, 4), precision, round(precision * 2, 4)]
        _p_list = sorted({0.10, 0.30, 0.50, round(float(effect_val), 4)})
        # VÁ 09/10/2026: mỗi ô đi CÙNG đường tính với N chính (n_prevalence → FPC → hiệu ứng thiết kế cụm), nên PHẢI
        # truyền đủ population_n, icc, cluster_size. Bản cũ chỉ truyền population_n ⇒ đề tài cụm (C1a: ICC 0,02, m=20)
        # in ô cơ sở 385 trong khi N chính là 532 (G3-AUTO-09 REVIEW). DE do chính ap_fpc_cum trả (None nếu không có cụm).
        _ket_qua = {(_p, _d): ap_fpc_cum(n_prevalence(_p, _d, alpha), design_code, population_n, icc, cluster_size)
                    for _p in _p_list for _d in _d_list}
        _de_cum = next(iter(_ket_qua.values()))[3]
        lines += [
            f"Bảng: tỷ lệ ước lượng p × sai số cho phép d → N tối thiểu "
            f"(TRƯỚC khi bù {int(dropout*100)}% không trả lời"
            + (f"; đã hiệu chỉnh quần thể hữu hạn N={population_n}" if population_n else "")
            + (f"; đã nhân hiệu ứng thiết kế cụm DE = {_de_cum:.2f} (= 1+(m−1)×ICC, m = {cluster_size}, ICC = {icc})"
               if _de_cum is not None else "") + ")",
            "",
            "| p ước lượng | " + " | ".join(f"d = ±{d * 100:g}%" for d in _d_list) + " |",
            "|---|" + "---|" * len(_d_list),
        ]
        for _p in _p_list:
            _cells = " | ".join(str(_ket_qua[(_p, _d)][0]) for _d in _d_list)
            _mark = " (cơ sở)" if abs(_p - float(effect_val)) < 1e-9 else ""
            lines.append(f"| {_p:.2f}{_mark} | {_cells} |")
        lines += [
            "",
            "> *p = 0,50 cho N lớn nhất vì phương sai p(1−p) đạt cực đại tại đó; đây là lựa chọn "
            "thận trọng khi chưa biết tỷ lệ thật. Thu hẹp d làm N tăng nhanh theo bình phương.*",
            "",
        ]
    else:
        _tham = "Δ" if hypothesis_type in ("non_inferiority", "equivalence") else (
            "(AUC − 0,5)" if effect_type == "AUC" else "ES")
        lines += [
            f"Bảng: Power × {_tham} → N tổng (TRƯỚC khi bù {int(dropout*100)}% dropout"
            + ("; đã áp FPC/hệ số thiết kế cụm như N chính" if (population_n or icc is not None) else "") + ")",
            "",
            f"| Power | {_tham} × {sens_mults[0]} ({int(sens_mults[0]*100)}%) | {_tham} × {sens_mults[1]} (cơ sở) | "
            f"{_tham} × {sens_mults[2]} ({int(sens_mults[2]*100)}%) |",
            "|---|---|---|---|",
        ]
        for pwr, row in sens_rows:
            r = [str(v) if v != "N/A" else "N/A" for v in row]
            lines.append(f"| {int(pwr*100)}% | {r[0]} | {r[1]} | {r[2]} |")
        lines += [
            "",
            "> *Lưu ý: Nếu bác sĩ điều chỉnh effect size, cỡ mẫu thay đổi theo bảng trên.*",
            "",
        ]
    lines += [
        "",
        "---",
        "",
        "## PHẦN 4 — KHỐI CỠ MẪU (dán vào đề cương)",
        "",
        "```",
        f"Cỡ mẫu được tính theo {formula_used}.",
    ]
    # SỬA 2026-07-29 (phát hiện qua kiểm định độc lập, HIGH): dòng "α = ...,
    # lực thống kê ..." trước đây in VÔ ĐIỀU KIỆN cho MỌI thiết kế, kể cả
    # sr_ma/prediction/qualitative — 3 thiết kế KHÔNG dùng kiểm định power theo
    # doctrine (xem N_NOT_APPLICABLE_DESIGNS). Hệ quả: khối PHẦN 4 của một đề
    # tài ĐỊNH TÍNH luôn chứa chữ "α ="/"lực thống kê", nên
    # g3_quality_gate.py::G3-AUTO-17 (kiểm "khối cỡ mẫu định tính không được
    # chứa ngôn ngữ power") KHÔNG BAO GIỜ đạt được — khóa cứng mọi đề tài định
    # tính ở DRAFT_NEEDS_HUMAN_PARAMETERS vĩnh viễn. Chỉ in câu alpha/power khi
    # thiết kế thật sự dùng công thức power.
    if mo_ta_chinh_xac:
        lines.append(f"Với độ tin cậy {int(round((1 - alpha) * 100))}% (α = {alpha}) và sai số tuyệt đối cho phép "
                     f"d = ±{precision * 100:g}%,")
    elif design_code not in N_NOT_APPLICABLE_DESIGNS:
        lines.append(
            f"Với mức ý nghĩa {_alpha_sidedness} α = {alpha}, lực thống kê "
            f"1−β = {int(power*100)}%,"
        )
    if effect_val and n_total:
        # SỬA: dòng "{effect_type} = {effect_val} (lấy từ y văn [CẦN PMID/DOI])"
        # đúng cho cohort/case_control/RCT (effect_val THẬT LÀ effect size
        # trích từ 1 bài báo cụ thể) nhưng SAI ngữ cảnh cho cross_sectional
        # (effect_val ở đó là TỶ LỆ HIỆN MẮC GIẢ ĐỊNH p cho công thức Wilson,
        # không phải effect size từ 1 bài báo — ghi "lấy từ y văn [CẦN PMID]"
        # khiến bác sĩ tưởng cần trích dẫn nguồn cho con số quy ước thống kê).
        if design_code == "cross_sectional":
            _ng_p = (nguon_mo_ta.get("prevalence_source") or
                     ("quy ước thận trọng khi chưa có ước tính" if str(nguon_hieu_qua or "").startswith("mặc định")
                      else "[CẦN NGUỒN — khảo sát tương tự/y văn]"))
            lines.append(f"với tỷ lệ ước lượng p = {effect_val:.2f} ({_ng_p}),")
            lines.append(f"cần {n_total} người.")
            lines.append(f"Tính thêm {int(dropout*100)}% không trả lời dự kiến, cỡ mẫu cuối = {n_adjusted} người.")
        elif design_code == "diagnostic":
            lines.append(f"với AUC giả định = {effect_val:.2f} (nguồn: "
                         f"{nguon_mo_ta.get('effect_source') or '[CẦN — nghiên cứu chẩn đoán tương tự, PMID/DOI]'}) "
                         f"và tỷ lệ hiện mắc p = {prevalence:.2f},")
            lines.append(f"cần {n_benh} người bệnh và {n_khong_benh} người không bệnh (N = {n_total}).")
            lines.append(f"Tính thêm {int(dropout*100)}% bỏ cuộc dự kiến, cỡ mẫu cuối = {n_adjusted} người.")
        else:
            lines.append(f"và {effect_type} = {effect_val:.2f} (nguồn: "
                         f"{nguon_mo_ta.get('effect_source') or '[CẦN PMID/DOI/MCID]'}),")
            lines.append(f"cần {n_per_group} người mỗi nhóm (N tổng = {n_total}).")
            lines.append(f"Tính thêm {int(dropout*100)}% bỏ cuộc dự kiến, cỡ mẫu cuối = {n_adjusted} người.")
    else:
        lines.append("cỡ mẫu = [CẦN EFFECT SIZE từ bác sĩ].")
    if confirmed_n is not None:
        lines.append(
            f"N THỰC TẾ đã được bác sĩ/chủ nhiệm CHỐT = {confirmed_n} người "
            f"({'≥' if (n_adjusted > 0 and confirmed_n >= n_adjusted) else '—'} N tối thiểu tính toán)."
        )
    lines += [
        "```",
        "",
    ]
    # SỬA 2026-07-29 (phát hiện qua kiểm định độc lập, CRITICAL): PHẦN 4 trước
    # đây KHÔNG BAO GIỜ nhắc tên chuẩn báo cáo, dù doctrine co-mau-nghien-cuu.md
    # khẳng định lặp lại rằng công cụ "xuất khối cỡ mẫu CONSORT 2025/STROBE" —
    # và g3_quality_gate.py::G3-AUTO-10 kiểm ĐÚNG chuỗi chuẩn báo cáo này trong
    # artifact. Hai điều đó cộng lại nghĩa là G3-AUTO-10 KHÔNG THỂ PASS qua bất
    # kỳ lần chạy pipeline thật nào (xác nhận bằng cách chạy thật run_g3_auto.py
    # trên một ca RCT: artifact không có chữ "CONSORT" ở đâu cả) — PASS_G3_
    # CONFIRMED vĩnh viễn không đạt được. Lấy nguồn chuẩn TRỰC TIẾP từ
    # skill_standards (cùng bảng mà g3_quality_gate.py dùng để chấm) để hai bên
    # luôn khớp nhau bằng cấu trúc, không phải bằng cách đoán đúng chuỗi.
    _reporting = S.reporting_standards_for(design_code)
    _reporting_primary = str(_reporting.get("primary") or "")
    if _reporting_primary and "CẦN KIỂM CHỨNG" not in _reporting_primary.upper():
        lines.append(
            f"> Trình bày cỡ mẫu theo mục cỡ mẫu của **{_reporting_primary}** khi đưa "
            "vào đề cương/bản thảo (vd CONSORT 2025 mục 16a, SPIRIT 2025 mục 19, "
            "STROBE mục 10, STARD 2015 mục 18, TRIPOD+AI mục 10 — tùy thiết kế)."
        )
        lines.append("")
    lines += [
        "---",
        "",
        "## PHẦN 5 — TIÊU CHÍ QUA CỔNG G3",
        "",
        "- [ ] Bác sĩ xác nhận effect size (nguồn: PMID/DOI) [CẦN BÁC SĨ]",
        "- [ ] Bác sĩ xác nhận tỷ lệ dropout [CẦN BÁC SĨ]",
        "- [ ] Bác sĩ xác nhận tỷ lệ biến cố nền (với thiết kế sống còn) [CẦN BÁC SĨ]",
        "- [ ] Cập nhật G3_checkpoint.json với N đã duyệt",
        "- [ ] Copy khối cỡ mẫu vào đề cương (PHẦN 4)",
        "",
        "---",
        "*Cần bác sĩ kiểm chứng. Mọi số liệu cỡ mẫu phải được bác sĩ duyệt trước khi đưa vào đề cương chính thức.*",
    ]
    return "\n".join(lines)

def write_docx(artifact, out_path):
    """Xuất DOCX."""
    try:
        from docx import Document
        from docx.shared import RGBColor
        doc = Document()
        doc.add_heading("A4 — KẾ HOẠCH CỠ MẪU", 0)
        for line in artifact.split("\n"):
            if line.startswith("# "):
                doc.add_heading(line[2:], 1)
            elif line.startswith("## "):
                doc.add_heading(line[3:], 2)
            elif line.startswith("### "):
                doc.add_heading(line[4:], 3)
            elif "[CẦN" in line:
                p = doc.add_paragraph()
                run = p.add_run(line)
                run.font.color.rgb = RGBColor(0xCC, 0x44, 0x00)
            elif line.strip():
                doc.add_paragraph(line)
        _CTB.ap_dinh_dang_tai_lieu(doc)  # chuẩn trình bày: Times New Roman 13pt + sạch ký tự lạ
        doc.save(out_path)
        return True
    except ImportError:
        return False

# SỬA 2026-07-21 (vòng lặp kiểm tra-hoàn thiện vòng 5, phát hiện HIGH+MEDIUM):
# cùng họ bug design_code (run_g1_auto.py::_canonicalize_pinned_design_code). CLI
# --effect-type có argparse choices=["HR","OR","RR","ARR%","AUC","MD"] chặn giá trị
# sai, nhưng nhánh phục hồi từ study_meta.json (bác sĩ tự điền đè placeholder
# needs_input, vd effect_type="hr" chữ thường) bỏ qua HOÀN TOÀN bước chuẩn hoá đó —
# làm vỡ mọi so khớp chuỗi CHÍNH XÁC effect_type=="HR"/in (...) rải khắp file, rơi
# nhầm vào nhánh else báo SAI "chưa có công thức tự động" dù công thức thật sự tồn
# tại. --effect-size/--sd cũng gặp vấn đề song song nhưng khác dạng: argparse
# type=float CHỈ áp khi truyền qua CLI — nhánh JSON gán thẳng giá trị thô (có thể
# vẫn là chuỗi placeholder "<CẦN BÁC SĨ CẤP...>" nếu bác sĩ quên thay), khiến so
# sánh str<float ở downstream (nhánh Cox/log-rank) ném TypeError KHÔNG được except
# InvalidEffectSizeError bắt — crash cả script thay vì báo lỗi rõ ràng.
_EFFECT_TYPE_CANON = {"HR", "OR", "RR", "ARR%", "AUC", "MD"}
_EFFECT_TYPE_ALIASES = {
    "ARR": "ARR%",
    "HAZARD RATIO": "HR",
    "ODDS RATIO": "OR",
    "RELATIVE RISK": "RR",
    "RISK RATIO": "RR",
    "MEAN DIFFERENCE": "MD",
    "AUROC": "AUC",
    "AUC-ROC": "AUC",
}


def _canonicalize_pinned_effect_type(raw):
    """Chuẩn hoá effect_type đọc từ study_meta.json về đúng 1 trong 6 mã canon."""
    key = str(raw).strip().upper()
    if key in _EFFECT_TYPE_CANON:
        return key
    return _EFFECT_TYPE_ALIASES.get(key, key)


def _coerce_pinned_float(raw, field_name):
    """Ép kiểu float cho effect_size/sd đọc từ study_meta.json. Coi giá trị
    không ép được (vẫn là placeholder [CẦN...] bác sĩ chưa thay) là 'chưa
    cấp' (None) — nhất quán với hành vi khi bác sĩ không điền gì, thay vì để
    TypeError crash script ở downstream."""
    try:
        return float(raw)
    except (TypeError, ValueError):
        print(f"  ⚠️  {field_name}='{raw}' trong study_meta.json không phải số hợp lệ "
              "(có thể còn là placeholder [CẦN...] chưa được bác sĩ thay) — coi như CHƯA CẤP.")
        return None


def main():
    parser = argparse.ArgumentParser(description="G3 — Tính cỡ mẫu tự động")
    parser.add_argument("--study", required=True, help="Mã đề tài")
    # VÁ 04/10/2026 (soát từng cổng, đo trên C1a): mặc định None để phân biệt «không truyền» — chạy lại chỉ với --study
    # từng LẶNG LẼ đưa α/lực/p0/tỷ lệ biến cố/tỷ lệ bỏ cuộc về mặc định máy (C1a: bỏ cuộc 15% → 20%). Thứ tự lấy giá trị:
    # dòng lệnh → study_meta (ghim) → checkpoint lượt trước → mặc định (ghi rõ nguồn).
    parser.add_argument("--alpha", type=float, default=None)
    parser.add_argument("--power", type=float, default=None)
    parser.add_argument("--effect-size", type=float, default=None)
    # VÁ 04/10/2026 (G3-09): nhận cả PREVALENCE (run_pipeline chạy lại đề tài mô tả truyền đúng loại đã ghim).
    parser.add_argument("--effect-type", default=None, choices=["HR", "OR", "RR", "ARR%", "AUC", "MD", "PREVALENCE"])
    parser.add_argument("--p0", type=float, default=None, help="Tỷ lệ biến cố nhóm chứng (mặc định 0.30)")
    # Hai tham số của cỡ mẫu theo ĐỘ CHÍNH XÁC (thiết kế mô tả). Cố ý TÁCH khỏi
    # --p0: p0 là "tỷ lệ nhóm chứng" trong so sánh hai nhóm, còn --prevalence là
    # "tỷ lệ hiện mắc ước lượng" của quần thể — hai đại lượng khác nhau, gộp lại
    # sẽ khiến artifact ghi sai tên tham số trong phần công thức.
    parser.add_argument("--prevalence", type=float, default=None,
                        help="Tỷ lệ hiện mắc ƯỚC LƯỢNG của quần thể. Cắt ngang: không truyền thì dùng 0.5 (thận "
                             "trọng nhất). Chẩn đoán: BẮT BUỘC (quy số ca bệnh ra tổng N) — không mặc định.")
    parser.add_argument("--precision", type=float, default=None,
                        help="Sai số cho phép d (nửa rộng khoảng tin cậy mong muốn) của cỡ mẫu "
                             "theo độ chính xác. Không truyền: lấy gate_params.G3.precision, rồi 0.05 (±5%%).")
    parser.add_argument("--dropout", type=float, default=None, help="Tỷ lệ bỏ cuộc dự kiến (mặc định 0.20)")
    parser.add_argument("--p-event", type=float, default=None, help="Tỷ lệ biến cố tổng thể (log-rank, mặc định 0.30)")
    parser.add_argument("--sd", type=float, default=None,
                         help="Độ lệch chuẩn kết cục liên tục (bắt buộc khi --effect-type MD)")
    # THÊM 2026-07-17: trước đây G3 CHỈ tính N từ effect size — không có chỗ
    # ghi nhận khi bác sĩ/chủ nhiệm CHỐT một N thực tế khác (vd theo khả năng
    # thu thập/hành chính, thường ≥ N tối thiểu để dư an toàn) như phát hiện
    # thật khi bác sĩ báo "Mẫu được chốt là 1000 mẫu". KHÔNG thay thế N tính
    # theo thống kê — chỉ ghi SONG SONG cả hai, so sánh và cảnh báo nếu N chốt
    # < N tối thiểu (thiếu lực thống kê).
    parser.add_argument("--confirmed-n", type=int, default=None,
                         help="N thực tế bác sĩ/chủ nhiệm đã CHỐT (vd theo khả năng thu thập/hành "
                              "chính) — ghi kèm N tối thiểu tính theo thống kê, KHÔNG thay thế công thức")
    # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 15, phát hiện HIGH):
    # co-mau-nghien-cuu.md yêu cầu phân biệt superiority vs non-inferiority/
    # equivalence TRƯỚC khi tính (chọn nhầm là sai toàn bộ) — trước đây G3
    # không có tham số nào cho việc này, mọi thiết kế đều tính như superiority.
    # VÁ 04/10/2026 (G3-03, CHUNG-F): mặc định None — lấy giả thuyết đã GHIM (study_meta) hoặc khối đặc tả thiết kế
    # của G1 trước khi rơi về «superiority»; chạy lại chỉ với --study từng LẶNG LẼ đổi NI đã ghim thành superiority.
    parser.add_argument("--hypothesis-type", default=None,
                         choices=["superiority", "non_inferiority", "equivalence", "descriptive_precision"],
                         help="Loại giả thuyết — quyết định công thức + z một phía/hai phía. Không truyền: "
                              "gate_params.G3.hypothesis_type → đặc tả thiết kế G1 → superiority (đánh dấu mặc định)")
    parser.add_argument("--outcome-direction", default=None,
                         help="Chiều kết cục cho non-inferiority: higher_better (tỷ lệ CAO là tốt — đáp ứng) | "
                              "lower_better (tỷ lệ THẤP là tốt — biến cố bất lợi). BẮT BUỘC khi không phải "
                              "superiority (G3-01).")
    parser.add_argument("--margin", type=float, default=None,
                         help="Biên Δ (BẮT BUỘC nếu --hypothesis-type khác superiority) — mức "
                              "'kém hơn tối đa chấp nhận được' (đơn vị TỶ LỆ, vd 0.1 = 10 điểm %%), "
                              "PHẢI có biện minh lâm sàng + nguồn, KHÔNG bịa")
    # THÊM 2026-07-24 (cùng vòng, phát hiện MEDIUM): FPC (quần thể hữu hạn) +
    # cluster design effect — xem apply_fpc_and_cluster_de().
    parser.add_argument("--population-n", type=int, default=None,
                         help="Cỡ quần thể hữu hạn N (áp hiệu chỉnh FPC) — CHỈ dùng khi quần thể "
                              "ĐÍCH nhỏ/xác định (vd toàn bộ bệnh nhân của 1 cơ sở trong 1 khoảng "
                              "thời gian), KHÔNG dùng cho quần thể vô hạn/không xác định")
    parser.add_argument("--icc", type=float, default=None,
                         help="Hệ số tương quan nội cụm (ICC/rho) — dùng khi ngẫu nhiên hóa/lấy "
                              "mẫu THEO CỤM (cluster-randomized), PHẢI đi cùng --cluster-size")
    parser.add_argument("--cluster-size", type=int, default=None,
                         help="Cỡ cụm trung bình (m) — bắt buộc cùng --icc để tính design effect")
    args = parser.parse_args()
    GC.ensure_utf8_stdout()
    _cli_da_truyen = {k for k in ("effect_size", "effect_type", "sd", "confirmed_n") if getattr(args, k) is not None}

    # Audit 2026-07-11: G0/G1/G2 đều làm sạch --study (chặn '/', '..' ghi ra ngoài
    # exports/) — G3 trước đây dùng thẳng args.study, lệch chuẩn với 3 cổng anh em.
    study = re.sub(r'[^\w\-]', '_', args.study.strip().replace(" ", "-"))
    out_dir = BASE / "exports" / study
    out_dir.mkdir(parents=True, exist_ok=True)
    run_date = datetime.now().strftime("%Y-%m-%d")

    # THÊM 2026-07-08 (CRIT-05): trước đây chỉ run_pipeline.py (_recover_params)
    # mới đọc lại study_meta.json['gate_params']['G3'] khi CHẠY LẠI — gọi
    # THẲNG run_g3_auto.py --study X (không qua orchestrator) vẫn MẤT effect
    # size/type/SD bác sĩ đã pin, rơi về extract_best_effect() từ G1 (nguồn
    # khác hẳn). Nay G3 tự đọc study_meta trực tiếp làm fallback — chỉ điền
    # khi CLI không truyền (None), KHÔNG bao giờ ghi đè giá trị CLI đã cho.
    _study_meta = GC.load_study_meta(out_dir)
    _g3_pinned = (_study_meta.get("gate_params") or {}).get("G3") or {}
    if args.effect_size is None and _g3_pinned.get("effect_size") is not None:
        args.effect_size = _coerce_pinned_float(_g3_pinned["effect_size"], "effect_size")
        if args.effect_size is not None:
            print(f"  → Khôi phục effect_size={args.effect_size} từ study_meta.json (chạy lại không mất)")
    if args.effect_type is None and _g3_pinned.get("effect_type"):
        args.effect_type = _canonicalize_pinned_effect_type(_g3_pinned["effect_type"])
        print(f"  → Khôi phục effect_type={args.effect_type} từ study_meta.json")
    if args.sd is None and _g3_pinned.get("sd") is not None:
        args.sd = _coerce_pinned_float(_g3_pinned["sd"], "sd")
        if args.sd is not None:
            print(f"  → Khôi phục sd={args.sd} từ study_meta.json")
    if args.confirmed_n is None and _g3_pinned.get("confirmed_n") is not None:
        # VÁ 04/10/2026 (G3-11): ép kiểu — chuỗi «300» từng làm so sánh confirmed_n >= n_adjusted crash TypeError.
        _cn = _coerce_pinned_float(_g3_pinned["confirmed_n"], "confirmed_n")
        args.confirmed_n = int(_cn) if _cn is not None and float(_cn).is_integer() and _cn > 0 else None
        if args.confirmed_n is not None:
            print(f"  → Khôi phục confirmed_n={args.confirmed_n} từ study_meta.json (chạy lại không mất)")
        else:
            print(f"  ⚠️  confirmed_n ghim trong study_meta ({_g3_pinned['confirmed_n']!r}) không phải số nguyên dương "
                  "— bỏ qua, cần bác sĩ sửa.")
    # VÁ 04/10/2026 (soát từng cổng, G3-02/G3-03/CHUNG-F): khôi phục MỌI tham số quyết định N từ study_meta khi CLI
    # vắng (trước đây chỉ effect_size/effect_type/sd/confirmed_n) — giả thuyết, biên, chiều kết cục, cụm (ICC/cỡ cụm),
    # quần thể hữu hạn, tỷ lệ hiện mắc, độ chính xác. Khối đặc tả thiết kế của G1 là nguồn kế tiếp cho giả thuyết/biên/
    # chiều. Ghi lại NGUỒN của từng tham số để artifact và cổng thấy giá trị nào là mặc định máy.
    nguon_tham_so = {}
    for _ten in ("effect_size", "effect_type", "sd", "confirmed_n"):
        nguon_tham_so[_ten] = "CLI" if _ten in _cli_da_truyen else ("study_meta" if _g3_pinned.get(_ten) is not None
                                                                     else None)
    _dac_ta = S.dac_ta_thiet_ke(out_dir)
    for _ten, _kieu in (("hypothesis_type", "str"), ("margin", "float"), ("outcome_direction", "str"),
                        ("icc", "float"), ("cluster_size", "int"), ("population_n", "int"),
                        ("prevalence", "float"), ("precision", "float")):
        _attr = _ten
        if getattr(args, _attr) is not None:
            nguon_tham_so[_ten] = "CLI"
            continue
        _gia_tri = _g3_pinned.get(_ten)
        _nguon = "study_meta"
        if _gia_tri is None and _ten in ("hypothesis_type", "margin", "outcome_direction"):
            _gia_tri = _dac_ta.get(_ten)
            _nguon = f"đặc tả thiết kế G1 ({_dac_ta.get('nguon')})"
        if _gia_tri is None:
            continue
        if _kieu == "float":
            _gia_tri = _coerce_pinned_float(_gia_tri, _ten)
        elif _kieu == "int":
            _f = _coerce_pinned_float(_gia_tri, _ten)
            _gia_tri = int(_f) if _f is not None and float(_f).is_integer() else None
        elif _ten == "hypothesis_type":
            _gia_tri = S.chuan_hoa_hypothesis_type(_gia_tri)
        if _gia_tri is not None:
            setattr(args, _attr, _gia_tri)
            nguon_tham_so[_ten] = _nguon
            print(f"  → Khôi phục {_ten}={_gia_tri} từ {_nguon}")
    _cp_cu = load_checkpoint(out_dir / "G3_checkpoint.json")
    for _ten, _mac_dinh in (("alpha", 0.05), ("power", 0.80), ("p0", 0.30), ("dropout", 0.20), ("p_event", 0.30)):
        if getattr(args, _ten) is not None:
            nguon_tham_so[_ten] = "CLI"
            continue
        _gia_tri, _nguon = _coerce_pinned_float(_g3_pinned.get(_ten), _ten) if _g3_pinned.get(_ten) is not None \
            else None, "study_meta"
        if _gia_tri is None and isinstance(_cp_cu.get(_ten), (int, float)) and not isinstance(_cp_cu.get(_ten), bool):
            _gia_tri, _nguon = float(_cp_cu[_ten]), "checkpoint lượt trước"
        if _gia_tri is None:
            _gia_tri, _nguon = _mac_dinh, f"mặc định {_mac_dinh}"
        setattr(args, _ten, _gia_tri)
        nguon_tham_so[_ten] = _nguon
        if _nguon != f"mặc định {_mac_dinh}":
            print(f"  → Khôi phục {_ten}={_gia_tri} từ {_nguon}")
    if args.outcome_direction is not None:
        _chieu = chuan_hoa_chieu_ket_cuc(args.outcome_direction)
        if _chieu is None:
            print(f"❌ LỖI: --outcome-direction={args.outcome_direction!r} không nhận ra — dùng higher_better "
                  "(tỷ lệ CAO là tốt) hoặc lower_better (tỷ lệ THẤP là tốt).")
            sys.exit(1)
        args.outcome_direction = _chieu
    if args.effect_type == "PREVALENCE":
        # VÁ 04/10/2026 (G3-09): PREVALENCE là tham số của cỡ mẫu theo độ chính xác, không phải effect size.
        if args.prevalence is None and args.effect_size is not None:
            args.prevalence = args.effect_size
            nguon_tham_so["prevalence"] = nguon_tham_so.get("effect_size") or "CLI"
        args.effect_size, args.effect_type = None, None

    print(f"🔢 G3 — Tính cỡ mẫu: {study}")
    print("📂 Bước 1/6: Đọc checkpoints...")
    g0_cp = load_checkpoint(out_dir / "G0_checkpoint.json")
    g1_cp = load_checkpoint(out_dir / "G1_checkpoint.json")
    # SỬA (2 lỗi cùng lúc):
    # 1) topic đọc bằng .get("topic", study) không có "or" bọc ngoài — nếu
    #    checkpoint có key "topic" nhưng giá trị null, .get() trả về None
    #    (KHÔNG dùng default), làm crash topic[:60] ngay sau. Bọc "or study".
    # 2) design_code/design_primary đọc SAI đường dẫn key — G1 lưu lồng
    #    trong "design": {"internal_code":..., "primary":...}, KHÔNG PHẢI
    #    top-level "design_code"/"design_primary". Trước đây .get() luôn
    #    miss (key không tồn tại) nên luôn rơi về default "cohort" — MỌI
    #    đề tài RCT/chẩn đoán/sr_ma đều bị tính cỡ mẫu như thể là cohort mà
    #    không cảnh báo gì (bug bị che giấu vì mọi ca test trong phiên này
    #    tình cờ đều là cohort). Sửa: đọc đúng "design"."internal_code".
    topic = (g0_cp.get("topic") or study)
    # VÁ 2026-07-27: dùng bộ giải quyết DÙNG CHUNG. Trước đây cổng này chỉ đọc
    # G1_checkpoint rồi mặc định "cohort", nên `--design` bác sĩ truyền TƯỜNG MINH ở
    # G2 bị NUỐT — chuẩn báo cáo/công thức cỡ mẫu chọn sai mà không cảnh báo.
    # Xem gate_contract.resolve_design_code().
    design_code, _design_warn = GC.resolve_design_code(out_dir)
    if _design_warn:
        print(_design_warn)
    design_primary = g1_cp.get("design", {}).get("primary") or "Cohort tiến cứu"
    # THÊM 2026-07-08: G1 gắn cờ ambiguous=True khi "cohort" chỉ là placeholder
    # tạm (lĩnh vực bão hòa RCT+SR, bác sĩ CHƯA xác nhận khoảng trống thật) —
    # N tính ra dưới đây vẫn là số thật theo công thức, nhưng PHẢI cảnh báo
    # NGAY cạnh giá trị N rằng thiết kế nền chưa được xác nhận (CRIT-06).
    design_ambiguous = bool(g1_cp.get("design", {}).get("ambiguous", False))
    effect_samples = g1_cp.get("effect_size_samples", [])
    print(f"  → Topic: {topic[:60]}")
    print(f"  → Design: {design_code} | {design_primary}")

    print("⚙️  Bước 2/6: Xác định tham số...")
    effect_quality = None
    if args.hypothesis_type is None:
        # G0-06 (06/10/2026): loại kiểm định PI đã khai ở G0 (gate_params.G0.test_type — G0-06 chấm) là quyết định của
        # người, đứng TRƯỚC mặc định máy. Khối đặc tả G1 dựng trước khi G0 khai thì không mang nó ⇒ đọc thẳng
        # study_meta. Có xét thiết kế: định tính/SR-MA/tiên lượng không dùng khung giả thuyết.
        _tu_g0 = S.gia_thuyet_tu_test_type(
            ((_study_meta.get("gate_params") or {}).get("G0") or {}).get("test_type"), design_code)
        if _tu_g0:
            args.hypothesis_type = _tu_g0
            nguon_tham_so["hypothesis_type"] = "G0 test_type (study_meta.gate_params.G0)"
            print(f"  → hypothesis_type={_tu_g0} từ G0 test_type (study_meta)")
    if args.hypothesis_type is None:
        # Mặc định MÁY (không phải quyết định): thiết kế cắt ngang tính theo độ chính xác ⇒ không kiểm định giả thuyết.
        args.hypothesis_type = "descriptive_precision" if design_code == "cross_sectional" else "superiority"
        nguon_tham_so["hypothesis_type"] = "mặc định máy"
    elif design_code == "cross_sectional" and args.hypothesis_type == "superiority":
        args.hypothesis_type = "descriptive_precision"
    nguon_hieu_qua = nguon_tham_so.get("effect_size")
    # SỬA: "if args.effect_size and ..." coi 0.0 là falsy (Python) — nếu bác
    # sĩ cố tình/nhầm truyền --effect-size 0.0, điều kiện này bị bỏ qua âm
    # thầm, hệ thống tự chuyển sang dùng effect size khác từ G1 mà KHÔNG báo
    # cho bác sĩ biết giá trị họ nhập đã bị bỏ qua. Dùng "is not None" để chỉ
    # phân biệt "không truyền" (None) với "có truyền" (kể cả 0.0).
    if args.effect_size is not None and args.hypothesis_type != "superiority":
        # SỬA 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 15): non_inferiority/
        # equivalence dùng --effect-size làm p_test TRỰC TIẾP (tỷ lệ, không
        # phải OR/RR/HR/ARR%/AUC/MD) — KHÔNG cần --effect-type đi kèm, khác
        # nhánh superiority ngay dưới.
        # VÁ 04/10/2026 (G3-07): mã loại hiệu quả tường minh «NI_PROPORTION» (thay «p_test» — không thuộc tập hợp lệ
        # của rct/cohort nên G3-AUTO-03 REVIEW mãi).
        effect_val, effect_type = args.effect_size, "NI_PROPORTION"
        print(f"  → p_test (từ tham số, {args.hypothesis_type}) = {effect_val}")
    elif args.effect_size is not None and args.effect_type:
        effect_val, effect_type = args.effect_size, args.effect_type
        print(f"  → Effect size (từ tham số): {effect_type} = {effect_val}")
    elif design_code not in ("rct", "cohort", "case_control"):
        # VÁ 04/10/2026 (soát từng cổng, G3-08): cắt ngang/chẩn đoán/thiết kế không dùng power KHÔNG được mượn thước đo
        # liên hệ (HR/OR/RR/ARR%) trích từ G1 làm tham số — một RR 0,80 từng thành «tỷ lệ hiện mắc 80%».
        effect_val, effect_type = None, None
    else:
        effect_val, effect_type, effect_quality = extract_best_effect(effect_samples)
        if effect_val:
            nguon_hieu_qua = f"trích từ y văn G1/G0 (chất lượng {effect_quality})"
            print(f"  → Effect size (từ G1/G0): {effect_type} = {effect_val:.3f} (quality={effect_quality})")
            if effect_quality == "crude":
                print("  ⚠️  Effect size này là loại THÔ (không có 95%CI đi kèm khi trích "
                      "từ abstract) — có thể lẫn ARR%/RR%, ĐỘ TIN CẬY THẤP HƠN. "
                      "Khuyến nghị bác sĩ đọc toàn văn PMID xác nhận trước khi dùng "
                      "để khóa cỡ mẫu, hoặc cung cấp --effect-size/--effect-type thủ công.")
        else:
            print("  ⚠ Không tìm được effect size — bác sĩ cần ấn định")

    # SỬA 2026-07-31 (đề tài THẬT đầu tiên đi qua G3 — hài lòng người bệnh C1a):
    # nghiên cứu MÔ TẢ cắt ngang tính cỡ mẫu theo ĐỘ CHÍNH XÁC (Lwanga & Lemeshow,
    # WHO 1991), tham số là tỷ lệ ước lượng p và sai số cho phép d — nó KHÔNG có
    # "effect size" theo nghĩa hiệu quả can thiệp. Trước bản vá này, mọi đề tài
    # mô tả không truyền --effect-size đều BLOCKED ở G3 dù về phương pháp không
    # thiếu gì; muốn chạy được phải nhét p vào ô --effect-size (chính bộ test
    # tests/test_g3_confirmed_n.py cũng phải làm vậy — dấu hiệu ô này sai ngữ
    # nghĩa cho thiết kế mô tả). Nhánh dưới đây nhận p từ --p0 đúng tên gọi của
    # nó, và KHÔNG đổi hành vi khi bác sĩ có truyền --effect-size.
    if design_code == "cross_sectional" and effect_val is None:
        _p_est = args.prevalence if args.prevalence is not None else 0.5
        if not (0 < _p_est < 1):
            print(f"❌ LỖI: --prevalence={args.prevalence} phải trong khoảng (0,1) — đây là tỷ lệ "
                  "hiện mắc ước lượng của quần thể, dùng cho công thức cỡ mẫu theo độ chính xác.")
            sys.exit(1)
        if args.precision is not None and not (0 < args.precision < 1):
            print(f"❌ LỖI: --precision={args.precision} phải trong khoảng (0,1).")
            sys.exit(1)
        # Tên "PREVALENCE" là tên mà g3_quality_gate.EFFECT_TYPES_BY_DESIGN đã
        # khai từ trước cho cross_sectional. Trước bản vá này run_g3_auto.py
        # chưa bao giờ sinh ra tên đó, nên tiêu chí G3-AUTO-03 không có đường
        # nào đạt được với thiết kế mô tả — hai module đã viết cho nhau nhưng
        # chưa từng nối, vì chưa có đề tài mô tả thật nào chạy qua G3.
        effect_val, effect_type = _p_est, "PREVALENCE"
        nguon_hieu_qua = (nguon_tham_so.get("prevalence") or "CLI") if args.prevalence is not None else (
            "mặc định quy ước p=0,5")
        _src = ("tham số --prevalence" if args.prevalence is not None
                else "mặc định 0.5 — thận trọng nhất, cho N lớn nhất")
        print(f"  → Thiết kế mô tả: cỡ mẫu theo ĐỘ CHÍNH XÁC, tỷ lệ ước lượng p = {effect_val} ({_src})")
        print(f"     Sai số cho phép d = {args.precision if args.precision is not None else 0.05}. "
              "Thiết kế này không cần effect size.")

    alpha = args.alpha
    power = args.power
    dropout = args.dropout
    p_event = args.p_event

    # Validate tham số đầu vào — SỬA: dropout=1.0 gây ZeroDivisionError,
    # dropout gần 1.0 (vd 0.99) không crash nhưng âm thầm nhân N lên gấp
    # hàng chục/trăm lần vô lý mà không cảnh báo.
    if not (0 <= dropout < 0.5):
        print(f"❌ LỖI: --dropout={dropout} không hợp lệ. Phải trong [0, 0.5) — "
              "dropout ≥50% cho thấy thiết kế nghiên cứu có vấn đề nghiêm trọng "
              "hơn là vấn đề cỡ mẫu, cần bác sĩ xem lại trước khi tính.")
        sys.exit(1)
    if not (0 < alpha < 1) or not (0 < power < 1):
        print(f"❌ LỖI: alpha={alpha} và power={power} phải trong khoảng (0,1).")
        sys.exit(1)

    print("🧮 Bước 3/6: Tính cỡ mẫu...")
    n_per_group, n_total, n_adjusted = 0, 0, 0
    formula_used = ""
    sens_rows, sens_mults = [], [0.80, 1.00, 1.20]
    missing_sd = False  # THÊM: cờ riêng cho ca "có MD nhưng thiếu SD" — khác "chưa có công thức"
    n_benh = n_khong_benh = None
    design_effect = n_clusters = n_total_truoc_de = None
    precision = args.precision if args.precision is not None else 0.05
    if args.precision is None:
        nguon_tham_so["precision"] = "mặc định 0.05"

    # SỬA 2026-07-17 (round audit gate): "sr_ma"/"prediction" KHÔNG dùng cỡ mẫu
    # kiểu so-sánh-2-nhóm (HR/OR/RR/MD/AUC) nên KHÔNG được đặt trong nhánh
    # "elif design_code == ..." lồng bên trong "if effect_val:" như trước —
    # nếu G1 không trích được effect_val nào cho đề tài (rất có thể xảy ra với
    # sr_ma/prediction, vì effect_val ở 2 thiết kế này vốn KHÔNG có ý nghĩa
    # thống kê tương ứng), code rơi thẳng xuống else "[CẦN EFFECT SIZE từ bác
    # sĩ]" chung chung — bỏ lỡ hoàn toàn lời giải thích RIS/TSA hoặc pmsampsize
    # đã viết riêng cho 2 thiết kế này. Kiểm design_code == sr_ma/prediction
    # TRƯỚC, không phụ thuộc effect_val còn hay không.
    if design_code == "sr_ma":
        # THÊM 2026-07-06: sr_ma là nhánh G1 gán THƯỜNG GẶP (topic có ≥2
        # RCT chưa có SR/MA, hoặc câu hỏi tường minh yêu cầu tổng quan)
        # nhưng G3 trước đây rơi vào else chung chung. SR/MA KHÔNG dùng
        # công thức cỡ mẫu 1 nghiên cứu đơn lẻ — "cỡ mẫu" của SR/MA là
        # SỐ NGHIÊN CỨU/số bệnh nhân cộng dồn cần để đạt power cho pooled
        # estimate, tính bằng required information size (RIS) / Trial
        # Sequential Analysis (TSA). Đây phụ thuộc dị biệt (I²), phương
        # sai giữa nghiên cứu (τ²) — cần dữ liệu chỉ có SAU khi trích
        # xuất, nên KHÔNG tự động hóa hoàn toàn được ở G3; ta chỉ chỉ rõ
        # phương pháp đúng thay vì thông báo generic vô hướng.
        n_per_group = n_total = n_adjusted = 0
        formula_used = (
            "[CẦN — SR/MA KHÔNG dùng công thức cỡ mẫu 1 nghiên cứu đơn lẻ. "
            "Cỡ mẫu SR/MA = Required Information Size (RIS) / Trial Sequential "
            "Analysis (TSA): số bệnh nhân cộng dồn cần để pooled estimate đạt "
            "power, phụ thuộc dị biệt I²/τ² (chỉ biết SAU khi trích xuất dữ liệu). "
            "Dùng phần mềm TSA (Copenhagen Trial Unit) hoặc metafor::power. "
            "Bác sĩ/thống kê viên tính RIS sau bước trích xuất, KHÔNG bịa N ở đây.]"
        )
        print("  ⚠️  design=sr_ma → cần RIS/TSA (không phải công thức 1 nghiên cứu) "
              "— KHÔNG bịa số, xem hướng dẫn trong artifact A4")
    elif design_code == "prediction":
        # THÊM 2026-07-17 (round audit gate — tiếp nối vòng 5): "prediction"
        # (mô hình tiên lượng/TRIPOD+AI) trước đây rơi vào else chung chung.
        # Cỡ mẫu mô hình tiên lượng KHÔNG dùng công thức so sánh 2 nhóm (HR/
        # OR/RR/MD) — cần phương pháp riêng theo Riley RD, Ensor J, Snell KIE,
        # et al. "Calculating the sample size required for developing a
        # clinical prediction model." BMJ 2020;368:m441 (PMID 32188600) —
        # đòi hỏi ước lượng trước C-statistic/R² kỳ vọng, số tham số tiên
        # đoán ứng viên, và tỷ lệ hiện mắc/biến cố — những con số CHỈ bác
        # sĩ/thống kê viên mới có thể ấn định cho đề tài cụ thể (không thể
        # suy ra từ effect_val/effect_type như các thiết kế so sánh 2 nhóm).
        # KHÔNG bịa công thức từ trí nhớ — chỉ dẫn đúng phương pháp + gói
        # phần mềm (pmsampsize, R/Stata) thay vì thông báo generic vô hướng.
        n_per_group = n_total = n_adjusted = 0
        formula_used = (
            "[CẦN — Mô hình tiên lượng (TRIPOD+AI) KHÔNG dùng công thức so "
            "sánh 2 nhóm (HR/OR/RR/MD). Cỡ mẫu tính theo Riley RD et al. "
            "'Calculating the sample size required for developing a clinical "
            "prediction model.' BMJ 2020;368:m441 (PMID 32188600) — cần bác "
            "sĩ/thống kê viên cung cấp: C-statistic hoặc R² kỳ vọng, số tham "
            "số tiên đoán ứng viên, tỷ lệ hiện mắc/biến cố trong quần thể "
            "đích. Dùng gói phần mềm pmsampsize (R hoặc Stata) để tính. "
            "KHÔNG bịa N ở đây.]"
        )
        print("  ⚠️  design=prediction → cần pmsampsize (Riley 2020, PMID "
              "32188600), không phải công thức so sánh 2 nhóm — KHÔNG bịa "
              "số, xem hướng dẫn trong artifact A4")
    elif design_code == "qualitative":
        # THÊM 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG, cùng khuôn vá
        # sr_ma/prediction 2026-07-06/07-17): trước bản vá này, "qualitative"
        # rơi thẳng vào nhánh else "[CẦN EFFECT SIZE từ bác sĩ]" chung chung —
        # SAI phương pháp luận hoàn toàn. Định tính KHÔNG dùng power/effect
        # size — cỡ mẫu xác định bằng BÃO HÒA DỮ LIỆU (data saturation, không
        # ấn định cứng trước khi thu thập). n_adjusted=0 CÓ CHỦ Ý (không phải
        # thiếu dữ liệu) — G4 phải nhận diện design_code="qualitative" để
        # KHÔNG hard-block như với N=0 của thiết kế định lượng thật.
        n_per_group = n_total = n_adjusted = 0
        formula_used = (
            "[Nghiên cứu định tính KHÔNG dùng công thức cỡ mẫu power/effect size. "
            "Cỡ mẫu xác định bằng QUY TẮC BÃO HÒA DỮ LIỆU (data saturation) — dừng "
            "phỏng vấn/nhóm tiêu điểm khi không còn chủ đề mới xuất hiện (thường "
            "12-20 người tham gia cho phỏng vấn sâu, 4-6 nhóm cho focus group — "
            "kinh nghiệm chung, KHÔNG phải ngưỡng cứng). Xem `nghien-cuu-dinh-tinh` "
            "để lập kế hoạch lấy mẫu có chủ đích + tiêu chí dừng bão hòa cụ thể. "
            "KHÔNG áp công thức power cho thiết kế này.]"
        )
        print("  ℹ️  design=qualitative → cỡ mẫu theo BÃO HÒA DỮ LIỆU (không phải "
              "power/effect size) — N=0 có chủ đích, xem artifact A4/nghien-cuu-dinh-tinh")
    else:
        # VÁ 04/10/2026 (soát từng cổng, G3-06): MỌI nhánh công thức nằm ở tinh_n_loi() — cùng hàm mà bảng độ nhạy gọi.
        try:
            kq = tinh_n_loi(design_code, effect_type, effect_val, alpha, power, p0=args.p0, p_event=p_event,
                            sd=args.sd, precision=precision, prevalence=args.prevalence,
                            hypothesis_type=args.hypothesis_type, margin=args.margin,
                            outcome_direction=args.outcome_direction)
            n_per_group, n_total = kq["n_per_group"], kq["n_total"]
            formula_used, missing_sd = kq["formula"], kq["missing_sd"]
            n_benh, n_khong_benh = kq["n_benh"], kq["n_khong_benh"]
            if args.hypothesis_type == "equivalence":
                print("  ⚠️  hypothesis_type=equivalence → CHƯA tự động hóa (công thức TOST "
                      "chưa xác minh đủ chắc chắn) — dùng PASS/TOSTER, xem artifact A4")
            elif missing_sd:
                print(f"  ⚠️  Có MD={effect_val} nhưng THIẾU --sd — KHÔNG bịa SD, cần bác sĩ cấp")
            elif formula_used.startswith("[CẦN CÔNG THỨC"):
                print(f"  ⚠️  Không có công thức tự động cho design={design_code} + "
                      f"effect_type={effect_type} — KHÔNG bịa số, cần bác sĩ tính thủ công")
            elif effect_val is None:
                formula_used = "[CẦN EFFECT SIZE từ bác sĩ để tính]"
                print("  → N: [CẦN BÁC SĨ ẤN ĐỊNH EFFECT SIZE]")
        except InvalidEffectSizeError as e:
            print(f"❌ LỖI EFFECT SIZE/THAM SỐ: {e}")
            print("   → KHÔNG tính được cỡ mẫu với tham số này. Kiểm tra lại "
                  "--effect-size/--effect-type/--p0/--prevalence/--margin/--outcome-direction.")
            n_per_group = n_total = n_adjusted = 0
            formula_used = f"[LỖI — {e}]"
        except (TypeError, ValueError) as e:
            print(f"❌ LỖI DỮ LIỆU EFFECT SIZE: {e}")
            print("   → effect_size/sd có kiểu dữ liệu không hợp lệ (có thể còn sót "
                  "placeholder chưa thay). KHÔNG tính được cỡ mẫu — cần bác sĩ kiểm tra lại.")
            n_per_group = n_total = n_adjusted = 0
            formula_used = f"[LỖI DỮ LIỆU — {e}]"

    # FPC → cụm → dropout (đúng thứ tự doctrine). VÁ 04/10/2026 (G3-02): tham số cụm/quần thể hữu hạn lấy cả từ
    # study_meta (không chỉ CLI) và được GHI vào checkpoint (design_effect, N trước DE, số cụm) để cổng kiểm số học.
    if n_total:
        n_total, n_per_group, _fpc_cluster_note, design_effect, n_clusters, n_total_truoc_de = ap_fpc_cum(
            n_total, design_code, args.population_n, args.icc, args.cluster_size)
        formula_used += _fpc_cluster_note
        n_adjusted = math.ceil(n_total / (1 - dropout))
        if _fpc_cluster_note:
            print(f"  → Sau FPC/cluster DE: N mỗi nhóm={n_per_group}, N tổng={n_total}, "
                  f"N điều chỉnh dropout={n_adjusted}")
        sens_rows, sens_mults = sensitivity_table(
            design_code, n_total, effect_val, effect_type, alpha, p_event, args.p0, args.sd, power=power,
            precision=precision, prevalence=args.prevalence, hypothesis_type=args.hypothesis_type,
            margin=args.margin, outcome_direction=args.outcome_direction, population_n=args.population_n,
            icc=args.icc, cluster_size=args.cluster_size)
        print(f"  → N mỗi nhóm: {n_per_group}, N tổng: {n_total}, N điều chỉnh: {n_adjusted}")

    print("📝 Bước 4/6: Sinh artifact A4...")
    artifact = generate_artifact(
        study, topic, design_code, design_primary, alpha, power,
        effect_val, effect_type, n_per_group, n_total, n_adjusted,
        dropout, formula_used, sens_rows, sens_mults, p_event, run_date, args.sd,
        design_ambiguous=design_ambiguous, confirmed_n=args.confirmed_n,
        hypothesis_type=args.hypothesis_type,
        nguon_tham_so=nguon_tham_so, nguon_hieu_qua=nguon_hieu_qua, outcome_direction=args.outcome_direction,
        margin=args.margin, precision=precision, prevalence=args.prevalence, n_benh=n_benh,
        n_khong_benh=n_khong_benh, population_n=args.population_n, icc=args.icc, cluster_size=args.cluster_size,
        nguon_mo_ta={k: _g3_pinned.get(k) for k in ("effect_source", "prevalence_source", "margin_source")},
    )
    md_path = out_dir / f"G3_A4_SAMPLE_SIZE_{study}.md"
    md_path.write_text(artifact, encoding="utf-8", newline="\n")
    print(f"  → Lưu: {md_path} ({len(artifact)//1000}KB)")

    print("🛡️  Bước 5/6: Kiểm guardrail R1-R7...")
    errors, warnings = guardrail_check(artifact, n_adjusted, effect_val, missing_sd)
    for w in warnings:
        print(f"  {w}")
    for e in errors:
        print(f"  {e}")

    # ── HỢP ĐỒNG DỪNG (blocked contract) ──────────────────────────────────────
    # Ba trạng thái RỜI NGHĨA thay cho "✅ PASS im lặng trên artifact rỗng":
    #   1) errors R1–R7 (liêm chính) → GUARDRAIL FAIL (exit 3).
    #   2) n_adjusted <= 0 (GIÁ TRỊ LÕI RỖNG — chưa tính được cỡ mẫu) → BLOCKED
    #      (exit 2) + khối needs_input máy-đọc-được; KHÔNG bao giờ báo PASS.
    #   3) n_adjusted > 0 + không lỗi R → PASS (exit 0) — đường thành công cũ.
    # SỬA lỗi false-PASS đã xác nhận: trước đây n=0 (thiếu effect size) vẫn ghi
    # guardrail "✅ PASS", làm cả chuỗi tưởng G3 xong rồi kẹt ở G4.
    #
    # SỬA 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG, xác nhận bằng thực
    # nghiệm chạy thật G3→G4 cho sr_ma/prediction): với sr_ma/prediction/
    # qualitative, effect_size KHÔNG áp dụng (n_adjusted=0 CÓ CHỦ ĐÍCH, kèm
    # formula_used hướng dẫn phương pháp riêng: RIS/TSA, pmsampsize, bão hòa
    # dữ liệu). Test cũ (2026-07-17, test_gate_prediction_design_coverage.py)
    # CÓ CHỦ Ý giữ BLOCKED cho tới khi bác sĩ tự tính N (ngoài hệ thống, theo
    # phương pháp đã hướng dẫn) rồi CHỐT qua `--confirmed-n` — không bỏ hẳn
    # yêu cầu hành động của bác sĩ trước khi khóa SAP (đúng triết lý "liêm
    # chính > tiến độ" của toàn hệ). Vấn đề THẬT không phải "có nên chặn" mà
    # là (a) thông báo SAI ("thiếu effect size" — effect size không hề áp
    # dụng) và (b) `--confirmed-n` TRƯỚC ĐÂY KHÔNG có tác dụng cho 3 thiết kế
    # này (is_empty chỉ nhìn n_adjusted, bỏ qua confirmed_n hoàn toàn — bug
    # thật, khác bản chất so với D1 nhưng phát hiện được khi vá D1). Nay: đã
    # CHỐT --confirmed-n → PASS (dùng N đã chốt); CHƯA chốt → vẫn BLOCKED,
    # nhưng thông báo đúng (xem nhánh needs_input bên dưới).
    core_is_empty = (n_adjusted <= 0) and not (
        design_code in N_NOT_APPLICABLE_DESIGNS and args.confirmed_n is not None
    )
    core = GC.core_value("n_adjusted", n_adjusted, is_empty=core_is_empty)
    need = None
    if errors:
        status = f"⚠ {len(errors)} LỖI (R1–R7)"
        exit_code = GC.EXIT_GUARDRAIL_FAIL
    elif core["is_empty"]:
        status = GC.BLOCKED_GUARDRAIL_STR
        exit_code = GC.EXIT_BLOCKED
        cmd = (f'python tools/run_g3_auto.py --study {study} '
               '--effect-size <giá_trị> --effect-type <HR|OR|RR|ARR%|AUC>')
        if design_code in N_NOT_APPLICABLE_DESIGNS:
            # THÊM 2026-07-19 (audit vòng 3, D1 — NGHIÊM TRỌNG): sr_ma/
            # prediction/qualitative KHÔNG dùng effect_size — thông báo
            # "thiếu effect size" ở nhánh dưới SAI hoàn toàn cho 3 thiết kế
            # này. Đúng quy trình: bác sĩ/thống kê viên tự tính N NGOÀI hệ
            # thống theo phương pháp đã hướng dẫn trong artifact (RIS/TSA,
            # pmsampsize, hoặc quy tắc bão hòa dữ liệu), rồi CHỐT qua
            # `--confirmed-n` (cờ có sẵn, trước bản vá này KHÔNG có tác dụng
            # cho 3 thiết kế này — is_empty chỉ nhìn n_adjusted).
            _method_hint = {
                "sr_ma": "Required Information Size (RIS)/TSA — dùng metafor::power hoặc phần mềm TSA (Copenhagen Trial Unit)",
                "prediction": "pmsampsize theo Riley RD et al. BMJ 2020;368:m441 (PMID 32188600)",
                "qualitative": "quy tắc bão hòa dữ liệu (data saturation) — xem nghien-cuu-dinh-tinh",
            }[design_code]
            need = GC.needs_input(
                GC.REASON_MISSING_SAMPLE_SIZE,
                f"G3 (thiết kế `{design_code}`) KHÔNG dùng effect_size/power truyền thống "
                f"— cần bác sĩ/thống kê viên tự tính N theo {_method_hint} (NGOÀI hệ "
                "thống, xem hướng dẫn chi tiết trong artifact A4), rồi chốt qua --confirmed-n. "
                "Hệ KHÔNG tự tính/bịa N cho thiết kế này.",
                f'python tools/run_g3_auto.py --study {study} --confirmed-n <N_đã_tự_tính>',
                must_not_fabricate=["n_adjusted", "confirmed_n"],
                study_meta_patch={"gate_params": {"G3": {
                    "confirmed_n": f"<CẦN BÁC SĨ/THỐNG KÊ VIÊN CẤP — tự tính bằng {_method_hint}>"}}},
            )
        elif effect_val is None:
            need = GC.needs_input(
                GC.REASON_MISSING_EFFECT_SIZE,
                "G3 chưa tính được cỡ mẫu vì THIẾU effect size. Không tìm được "
                "ước lượng hiệu quả từ y văn G0/G1 và bác sĩ chưa cấp. Hệ KHÔNG "
                "bịa effect size để 'đi cho hết' (liêm chính > tiến độ).",
                cmd,
                must_not_fabricate=["effect_size", "PMID"],
                study_meta_patch={"gate_params": {"G3": {
                    "effect_size": "<CẦN BÁC SĨ CẤP — kèm PMID/DOI nguồn hoặc MCID>",
                    "effect_type": "<HR|OR|RR|ARR%|AUC>"}}},
            )
        elif args.hypothesis_type == "equivalence":
            # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 15): phân biệt
            # với nhánh else chung chung phía dưới — equivalence KHÔNG phải
            # "tổ hợp thiếu công thức tình cờ", mà là quyết định CÓ CHỦ Ý
            # không tự tính (công thức TOST chưa xác minh đủ chắc bằng ví dụ
            # số công khai — xem formula_used để biết lý do đầy đủ).
            need = GC.needs_input(
                GC.REASON_MISSING_SAMPLE_SIZE,
                "G3 CHƯA tự động hóa cỡ mẫu cho equivalence (TOST) — công thức "
                "closed-form chưa được xác minh bằng ví dụ số cụ thể từ nguồn công "
                "khai (khác non_inferiority, đã xác minh). Dùng phần mềm chuyên "
                "dụng (PASS 'Equivalence Tests', R TOSTER/PowerTOST) theo Chow SC, "
                "Shao J, Wang H. Sample Size Calculations in Clinical Research, "
                "2nd ed., 2008, Chương 3 (tr.86), rồi CHỐT qua --confirmed-n.",
                f'python tools/run_g3_auto.py --study {study} --confirmed-n <N_đã_tự_tính_bằng_PASS/TOSTER>',
                must_not_fabricate=["n_adjusted", "confirmed_n"],
                study_meta_patch={"gate_params": {"G3": {
                    "confirmed_n": "<CẦN BÁC SĨ/THỐNG KÊ VIÊN CẤP — tính bằng PASS/TOSTER theo TOST>"}}},
            )
        elif args.hypothesis_type == "non_inferiority":
            # THÊM 2026-07-24 (cùng vòng): non_inferiority CÓ công thức (đã
            # xác minh) nhưng n_adjusted vẫn có thể =0 nếu thiếu --margin/
            # --effect-size hợp lệ hoặc margin vi phạm ngay ở giá trị kỳ vọng
            # (xem InvalidEffectSizeError trong n_two_proportion_ni()) — thông
            # báo đúng nguyên nhân thay vì "chưa có công thức" (SAI, công thức
            # đã có).
            need = GC.needs_input(
                GC.REASON_MISSING_EFFECT_SIZE,
                f"G3 (non_inferiority) chưa tính được N — kiểm tra lại: {formula_used}",
                f'python tools/run_g3_auto.py --study {study} --effect-size <p_test 0-1> '
                '--hypothesis-type non_inferiority --margin <Δ dương> --p0 <p_control 0-1>',
                must_not_fabricate=["effect_size", "margin"],
                study_meta_patch={"gate_params": {"G3": {
                    "effect_size": "<CẦN BÁC SĨ CẤP — p_test, tỷ lệ kết cục nhóm thử nghiệm>",
                    "margin": "<CẦN BÁC SĨ/HỘI ĐỒNG CẤP — biên Δ có biện minh lâm sàng>",
                    "outcome_direction": "<CẦN — higher_better (tỷ lệ cao là tốt) | lower_better (biến cố bất lợi)>"}}},
            )
        elif design_code == "diagnostic" and not (args.prevalence is not None and 0 < args.prevalence < 1):
            # VÁ 04/10/2026 (G3-04): chẩn đoán cần tỷ lệ hiện mắc để quy số ca bệnh ra tổng N — không mặc định.
            need = GC.needs_input(
                GC.REASON_MISSING_EFFECT_SIZE,
                "G3 (chẩn đoán) chưa tính được N vì THIẾU tỷ lệ hiện mắc trong quần thể tuyển — cần để quy số ca "
                "bệnh (Hanley–McNeil) ra tổng N. Hệ KHÔNG mặc định.",
                f'python tools/run_g3_auto.py --study {study} --effect-size <AUC> --effect-type AUC '
                '--prevalence <p 0-1>',
                must_not_fabricate=["prevalence"],
                study_meta_patch={"gate_params": {"G3": {
                    "prevalence": "<CẦN BÁC SĨ CẤP — tỷ lệ hiện mắc kèm nguồn>",
                    "prevalence_source": "<CẦN PMID/DOI hoặc số liệu cơ sở>"}}},
            )
        elif missing_sd:
            # THÊM 2026-07-06: phân biệt "có MD nhưng thiếu SD" (CÓ công thức,
            # chỉ thiếu 1 tham số) với "tổ hợp chưa có công thức tự động" —
            # thông báo chung chung ở nhánh else phía dưới sẽ SAI (nói "chưa
            # có công thức" trong khi thật ra có, chỉ thiếu SD).
            need = GC.needs_input(
                GC.REASON_MISSING_EFFECT_SIZE,
                f"G3 có MD={effect_val:.2f} (kết cục liên tục) nhưng THIẾU SD "
                "(độ lệch chuẩn) để tính cỡ mẫu. Hệ KHÔNG bịa SD — bác sĩ/thống "
                "kê viên cần cấp SD từ pilot/y văn cùng kết cục (ghi nguồn "
                "PMID/DOI hoặc MCID).",
                f'python tools/run_g3_auto.py --study {study} --effect-size {effect_val} '
                '--effect-type MD --sd <giá_trị>',
                must_not_fabricate=["sd"],
                study_meta_patch={"gate_params": {"G3": {
                    "sd": "<CẦN BÁC SĨ CẤP — kèm PMID/DOI nguồn hoặc MCID>"}}},
            )
        else:
            need = GC.needs_input(
                GC.REASON_MISSING_SAMPLE_SIZE,
                f"G3 có effect size ({effect_type}={effect_val}) nhưng tổ hợp "
                f"thiết kế={design_code} + loại hiệu quả={effect_type} chưa có "
                "công thức tự động (hoặc effect size ngoài miền tính hợp lệ). "
                "Cần thống kê viên chọn công thức/tính thủ công — hệ KHÔNG bịa N.",
                cmd,
                must_not_fabricate=["n_adjusted"],
            )
    else:
        status = "✅ PASS"
        exit_code = GC.EXIT_OK
    print(f"  → Guardrail: {status}")

    print("📄 Bước 6/6: Xuất DOCX...")
    docx_path = out_dir / f"G3_A4_SAMPLE_SIZE_{study}.docx"
    ok = write_docx(artifact, docx_path)
    if ok:
        print(f"  → Lưu: {docx_path}")
    else:
        print("  ⚠ python-docx không có — bỏ qua DOCX")

    # PIN durable: nếu bác sĩ cấp effect size qua CLI → ghi vào study_meta.json để
    # CHẠY LẠI (chỉ với --study) KHÔNG mất input (đóng vòng param-loss ở re-run).
    seed_g3 = {}
    if args.effect_size is not None and args.effect_type:
        seed_g3.update({"effect_size": args.effect_size, "effect_type": args.effect_type,
                        "dropout": dropout, "p_event": p_event})
        if args.sd is not None:
            seed_g3["sd"] = args.sd
    elif args.effect_size is not None and effect_type == "NI_PROPORTION":
        # VÁ 04/10/2026 (soát từng cổng — lộ khi dựng chuỗi tổng hợp): nhánh không-kém-hơn/tương đương dùng --effect-size
        # làm p_test KHÔNG cần --effect-type ⇒ bản cũ không ghim gì ⇒ G3-AUTO-14 («tham số đã ghim») REVIEW mãi.
        seed_g3.update({"effect_size": args.effect_size, "effect_type": "NI_PROPORTION",
                        "dropout": dropout, "p_event": p_event})
    if args.confirmed_n is not None:
        # Bác sĩ có thể chốt N thực tế TRƯỚC khi effect size sẵn sàng — vẫn ghim
        # riêng để không mất khi chạy lại.
        seed_g3["confirmed_n"] = args.confirmed_n
    # VÁ 04/10/2026 (G3-02/03/09): ghim cả các tham số quyết định khác khi CHÍNH dòng lệnh này cấp (ensure_study_meta chỉ
    # điền khoá còn thiếu — không bao giờ đè bản bác sĩ đã ghim).
    for _ten in ("hypothesis_type", "margin", "outcome_direction", "precision", "prevalence", "icc", "cluster_size",
                 "population_n", "alpha", "power", "p0", "dropout", "p_event"):
        if nguon_tham_so.get(_ten) == "CLI" and getattr(args, _ten) is not None:
            seed_g3[_ten] = getattr(args, _ten)
    if seed_g3:
        GC.ensure_study_meta(out_dir, seed={"gate_params": {"G3": seed_g3}})

    cp = {
        "gate": "G3", "study": study, "run_date": run_date,
        "gate_status": ("BLOCKED — CHỜ EFFECT SIZE/CÔNG THỨC"
                        if exit_code == GC.EXIT_BLOCKED else "DRAFT — CHỜ BÁC SĨ XÁC NHẬN"),
        "design_code": design_code, "design_ambiguous": design_ambiguous, "alpha": alpha, "power": power,
        "effect_val": effect_val, "effect_type": effect_type,
        "effect_quality": effect_quality,  # "labeled" (có 95%CI) / "crude" (thô) / None (do bác sĩ cung cấp tay)
        "n_per_group": n_per_group, "n_total": n_total, "n_adjusted": n_adjusted,
        "confirmed_n": args.confirmed_n,
        "confirmed_n_adequate": (
            (args.confirmed_n >= n_adjusted) if (args.confirmed_n is not None and n_adjusted > 0) else None
        ),
        "dropout": dropout, "formula_used": formula_used, "p_event": p_event,
        "p0": args.p0,  # lưu tỷ lệ biến cố nhóm chứng → chạy lại KHÔNG mất (fix param recovery)
        "sd": args.sd,  # lưu SD kết cục liên tục (effect_type=MD) → chạy lại KHÔNG mất
        # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 16, phát hiện
        # HIGH): hypothesis_type/margin trước đây CHỈ tồn tại trong văn bản
        # .md/.docx — KHÔNG có trong JSON máy đọc được, nên run_g6_auto.py/
        # run_stats_analysis.py không có cách nào biết đề tài là non_
        # inferiority để diễn giải đúng (so cận CI với margin thay vì chỉ
        # p-value kiểu superiority). Ghi vào checkpoint để G6 đọc lại được.
        "hypothesis_type": args.hypothesis_type,
        "margin": args.margin,
        # VÁ 04/10/2026 (soát từng cổng G3-01/02/04/08): đủ tham số để cổng kiểm số học và tầng sau đọc lại.
        "outcome_direction": args.outcome_direction,
        "precision": precision if effect_type == "PREVALENCE" else None,
        "prevalence": args.prevalence,
        "n_benh": n_benh,
        "n_khong_benh": n_khong_benh,
        "icc": args.icc,
        "cluster_size": args.cluster_size,
        "design_effect": round(design_effect, 6) if design_effect is not None else None,
        "n_total_truoc_de": n_total_truoc_de,
        "n_clusters": n_clusters,
        "population_n": args.population_n,
        "nguon_tham_so": nguon_tham_so,
        "nguon_hieu_qua": nguon_hieu_qua,
        "guardrail": status,
        "core_value": core,
        "pending_doctor_actions": [
            "Xác nhận effect size (PMID/DOI từ y văn/pilot study)",
            "Xác nhận tỷ lệ bỏ cuộc dự kiến",
            "Xác nhận tỷ lệ biến cố nền (với log-rank)",
            "Copy khối cỡ mẫu vào đề cương",
        ] + (
            ["🔴 Effect size dùng để tính N là loại THÔ (không có 95%CI từ abstract) — "
             "PHẢI đọc toàn văn PMID xác nhận trước khi khóa cỡ mẫu (G4)"]
            if effect_quality == "crude" else []
        ),
    }
    if need is not None:
        cp["needs_input"] = need
    cp_path = out_dir / "G3_checkpoint.json"
    cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print("💾 Ghi checkpoint G3...")
    print(f"  → Lưu: {cp_path}")
    # ── HỢP ĐỒNG CHẤT LƯỢNG G3 ────────────────────────────────────────────
    # THÊM 2026-07-28: guardrail_check() ở trên chỉ soi VĂN BẢN do
    # generate_artifact() vừa sinh, nên phần lớn luật của nó là tự đúng (xem
    # docstring tools/g3_quality_gate.py). Lớp này kiểm CON SỐ và NGUỒN, rồi
    # tách bạch "máy đã tính được N" với "thống kê viên/chủ nhiệm đã xác nhận
    # từng giả định".
    #
    # ĐỔI QUY TRÌNH 2026-08-30 — BÁC SĨ ĐÃ QUYẾT «nâng G3 thành chặn cứng»
    # (trả lời AskUserQuestion, đợt «hoàn thiện cho xanh»; ghi chú cũ ở đây
    # từng CỐ Ý không đổi mã thoát và để ngỏ đúng quyết định này cho bác sĩ).
    # Luật mới, hẹp có chủ ý:
    # - quality BLOCKED (một tiêu chí tự động BLOCK — mâu thuẫn cứng như
    #   NI/equivalence không có biên Δ) ⇒ một lượt lẽ ra EXIT_OK KHÔNG được
    #   báo thành công nữa: nâng lên EXIT_GUARDRAIL_FAIL (3, mã đã có sẵn
    #   trong hợp đồng — không phát minh mã mới, consumer khỏi đổi).
    # - exit_code đã là 2/3 thì giữ nguyên: pipeline vốn đã dừng, đổi 2→3 chỉ
    #   làm sai NGHĨA (2 = chờ input đời thực, không phải vi phạm).
    # - DRAFT_NEEDS_HUMAN_PARAMETERS / DRAFT_READY... giữ mã cũ — đó là kết
    #   quả ĐÚNG của lượt tự động đầu tiên, không phải lỗi.
    # - Fail-closed cả khi CHÍNH lớp chấm crash: từ khi cổng này gánh việc
    #   chặn, một exception nuốt im lặng là fail-open kiểu BH27 (cổng "đạt"
    #   vì chưa hề chạy tới luật cần chạy) — lượt EXIT_OK cũng phải nâng 3.
    quality = None
    quality_eval_error = None
    try:
        quality = G3Q.evaluate_study(study, out_dir, write=True)
    except Exception as exc:  # noqa: BLE001 - fail-closed, không nuốt im lặng
        quality_eval_error = exc
        print(f"  ⚠️ Không chấm được hợp đồng chất lượng G3: {exc}")
    if exit_code == GC.EXIT_BLOCKED:
        print(f"\n🚧 G3 DỪNG — {study} (cần input đời thực, hệ KHÔNG tự vượt)")
        print(f"  → {GC.blocked_detail(cp)}")
    else:
        print(f"\n✅ G3 TÍNH XONG — {study} (công thức đã chạy; CHƯA phải 'đạt cổng')")
        print(f"  N mỗi nhóm: {n_per_group}, N tổng: {n_total}, N điều chỉnh (dropout {int(dropout*100)}%): {n_adjusted}")
        print(f"  Alpha: {alpha}, Power: {int(power*100)}%, {effect_type}: {effect_val}")
    print(f"  → Guardrail: {status}")
    if quality:
        pending = [
            row for row in quality["automatic_criteria"] + quality["human_criteria"]
            if row["status"] != "PASS"
        ]
        print(f"  🧭 Hợp đồng chất lượng G3: {quality['status']} "
              f"({len(pending)} mục chưa đạt)")
        for row in pending[:5]:
            print(f"      {row['status']:6} {row['id']} — {row['label']}")
        if len(pending) > 5:
            print(f"      … và {len(pending) - 5} mục nữa — xem G3_QUALITY_REPORT.md")
    # Phán quyết CUỐI của luật chặn cứng — in sau cùng để không bị dòng
    # "✅ G3 TÍNH XONG" phía trên gây hiểu nhầm là đã qua.
    if exit_code == GC.EXIT_OK:
        if quality is not None and quality.get("status") == G3Q.STATUS_BLOCKED:
            exit_code = GC.EXIT_GUARDRAIL_FAIL
            print(
                "\n⛔ HỢP ĐỒNG CHẤT LƯỢNG G3: BLOCKED — chặn cứng theo quyết "
                "định bác sĩ 30/08/2026 (mã thoát 3). Xem G3_QUALITY_REPORT.md."
            )
        elif quality is None:
            exit_code = GC.EXIT_GUARDRAIL_FAIL
            print(
                "\n⛔ Lớp chấm chất lượng G3 KHÔNG chạy được "
                f"({quality_eval_error}) — fail-closed, không báo thành công "
                "khi luật chưa hề chạy (mã thoát 3)."
            )
    return exit_code

if __name__ == "__main__":
    raise SystemExit(main() or 0)
