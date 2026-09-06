#!/usr/bin/env python3
"""clinical_calc.py — Máy tính SUY LUẬN LÂM SÀNG chạy được (Bayes · ngưỡng test/treat ·
NNT/ARR+CI · xếp hạng GRADE).

Vá khoảng trống A3 (đã xác nhận bằng đánh giá độc lập 2026-07-04): `chan-doan-xac-suat.md`
và `tham-dinh-grade-nnt.md` mô tả đúng CÔNG THỨC bằng văn xuôi nhưng KHÔNG có công cụ nào
tính ra số — số liệu do LLM tự nhẩm, dễ sai và không tái lặp được. Module này biến các
công thức đó thành hàm PYTHON CHẠY ĐƯỢC + kiểm được bằng test, để agent GỌI thay vì tự
tính tay.

BỐN NHÓM HÀM:
  1. Bayes:      bayes_posttest, lr_from_sensitivity_specificity, sequential_bayes
  2. Ngưỡng:     treatment_threshold, test_threshold   (Pauker–Kassirer 1980)
  3. NNT/ARR:    nnt_from_counts, nnt_from_rr, nnt_from_or   (Altman 1998 CI; Zhang–Yu 1998 OR→RR)
  4. GRADE:      grade_rating   (Guyatt et al., GRADE working group, BMJ 2008 series)

BẤT BIẾN LIÊM CHÍNH:
  - Công cụ CHỈ tính toán từ số bác sĩ/agent CUNG CẤP — KHÔNG bịa effect size, tỷ lệ
    biến cố, hay đánh giá domain GRADE. Mọi input mang tính GIÁ TRỊ (harm/benefit, đánh
    giá risk-of-bias...) phải do bác sĩ/nguồn cung cấp, gắn `[CẦN BÁC SĨ ẤN ĐỊNH]` nếu
    thiếu — công cụ TỪ CHỐI tính khi thiếu input bắt buộc (không tự điền giá trị mặc định
    ru ngủ).
  - Ngưỡng test/treat: dẫn xuất TỪ ĐẦU bằng phân tích cây quyết định kỳ vọng lợi ích
    (expected-utility decision tree — Pauker SG, Kassirer JP. N Engl J Med. 1980;
    302(20):1109-17) — KHÔNG chép công thức đóng từ trí nhớ không kiểm chứng được.
    SỬA 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 23, phát hiện HIGH): dòng cũ ở
    đây khẳng định "đã xác minh 64.659 lần thử ngẫu nhiên khớp 100% brute-force" —
    con số này KHÔNG có script/seed/log nào trong repo (kể cả lịch sử git) để tái lập,
    chỉ tồn tại dưới dạng văn xuôi từ commit gốc tạo file. Đây đúng kiểu "số liệu nghe
    khoa học vì rất cụ thể" mà chính nguyên tắc BẤT BIẾN LIÊM CHÍNH ở trên cấm áp dụng
    cho input y khoa — gỡ bỏ khẳng định không tái lập được. Công thức đã kiểm bằng các
    TRƯỜNG HỢP BIÊN GIẢI TÍCH cụ thể trong tests/test_clinical_calc.py (test hoàn hảo
    miễn phí → vùng test=[0,1]; test vô dụng se=sp=0.5 → vùng test co về đúng ngưỡng
    điều trị harm/(harm+benefit); test vô dụng có phí → vùng test biến mất) — CHƯA
    có mô phỏng Monte Carlo/brute-force quy mô lớn nào được viết/commit.
  - Mọi kết quả là CÔNG CỤ HỖ TRỢ RA QUYẾT ĐỊNH — không thay phán đoán lâm sàng.

Dùng:
  python tools/clinical_calc.py bayes --pretest 0.30 --lr 6
  python tools/clinical_calc.py threshold --harm 3 --benefit 5 --se 0.90 --sp 0.85 [--test-cost 0]
  python tools/clinical_calc.py nnt --cer 0.30 --eer 0.20 --n-control 500 --n-experimental 500
  python tools/clinical_calc.py nnt --cer 0.30 --rr 0.75 --rr-ci-lower 0.60 --rr-ci-upper 0.90
  python tools/clinical_calc.py grade --design rct --rob 1 --inconsistency 0 --indirectness 0 \\
      --imprecision 1 --publication-bias 0
  (thêm --json cho mọi lệnh để lấy JSON)
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


class ClinicalCalcError(ValueError):
    """Input ngoài miền hợp lệ hoặc thiếu tham số bắt buộc — KHÔNG tự điền mặc định."""


DISCLAIMER = "Cần bác sĩ kiểm chứng."


# ═══════════════════════════════════════════════════════════════════════════
# 1. BAYES — pretest → LR → posttest (dạng odds)
# ═══════════════════════════════════════════════════════════════════════════

def _validate_prob(p: float, name: str) -> None:
    if not (0.0 < p < 1.0):
        raise ClinicalCalcError(
            f"{name}={p} phải trong khoảng mở (0,1) — xác suất 0 hoặc 1 làm odds "
            "vô định/vô nghĩa cho phép cập nhật Bayes.")


def bayes_posttest(pretest: float, lr: float) -> float:
    """Xác suất hậu nghiệm từ xác suất tiền nghiệm + tỷ số khả dĩ (dạng odds).

    posttest_odds = (pretest / (1 − pretest)) × LR ; posttest = odds / (1 + odds).
    """
    _validate_prob(pretest, "pretest")
    if lr <= 0:
        raise ClinicalCalcError(f"LR={lr} phải dương (LR=0 hoặc âm không có ý nghĩa lâm sàng).")
    odds_pre = pretest / (1 - pretest)
    odds_post = odds_pre * lr
    return odds_post / (1 + odds_post)


def lr_from_sensitivity_specificity(se: float, sp: float) -> Dict[str, float]:
    """LR+ = Se/(1−Sp) ; LR− = (1−Se)/Sp — dùng khi nguồn chỉ cho Se/Sp, không cho LR trực tiếp."""
    for name, v in (("se", se), ("sp", sp)):
        if not (0.0 < v < 1.0):
            raise ClinicalCalcError(f"{name}={v} phải trong (0,1).")
    if sp >= 1.0:
        raise ClinicalCalcError("sp=1.0 làm LR+ vô định (chia cho 0).")
    return {"lr_positive": se / (1 - sp), "lr_negative": (1 - se) / sp}


def sequential_bayes(pretest: float, lrs: list, conditionally_independent: bool) -> Dict:
    """Áp NHIỀU LR liên tiếp (nhân odds tuần tự) — CHỈ hợp lệ khi các xét nghiệm ĐỘC LẬP
    có điều kiện (conditionally independent). Nếu không, nhân LR trực tiếp PHÓNG ĐẠI xác
    suất hậu nghiệm — công cụ từ chối tính khi `conditionally_independent=False`, chỉ cảnh báo.
    """
    if not conditionally_independent:
        raise ClinicalCalcError(
            "Các xét nghiệm KHÔNG được xác nhận độc lập có điều kiện — nhân LR tuần tự "
            "sẽ PHÓNG ĐẠI xác suất hậu nghiệm một cách giả tạo. Cần bác sĩ/thống kê viên "
            "xác nhận tính độc lập trước, hoặc dùng mô hình đa biến thay vì nhân LR.")
    _validate_prob(pretest, "pretest")
    p = pretest
    trail = [p]
    for lr in lrs:
        p = bayes_posttest(p, lr)
        trail.append(p)
    return {"pretest": pretest, "lrs": lrs, "posttest": p, "trail": trail}


# ═══════════════════════════════════════════════════════════════════════════
# 2. NGƯỠNG TEST/TREAT — Pauker–Kassirer (dẫn xuất cây quyết định kỳ vọng lợi ích)
# ═══════════════════════════════════════════════════════════════════════════

def treatment_threshold(harm: float, benefit: float) -> float:
    """Ngưỡng điều trị (không xét xét nghiệm): Pt = H / (H + B).

    H = tác hại điều trị NHẦM người không bệnh (đơn vị lợi ích/tác hại do bác sĩ ấn định,
    [CẦN BÁC SĨ ẤN ĐỊNH] — đây là GIÁ TRỊ, không phải số đo khách quan).
    B = lợi ích điều trị ĐÚNG người có bệnh.
    Dưới Pt: không điều trị (lợi ích kỳ vọng < 0). Trên Pt: điều trị luôn.
    Nguồn: Pauker SG, Kassirer JP. N Engl J Med. 1980;302(20):1109-17.
    """
    if harm <= 0 or benefit <= 0:
        raise ClinicalCalcError(f"harm={harm}, benefit={benefit} phải dương.")
    return harm / (harm + benefit)


def test_threshold(se: float, sp: float, harm: float, benefit: float,
                   test_cost: float = 0.0) -> Dict:
    """Vùng NGƯỠNG XÉT NGHIỆM (test threshold) — dưới ngưỡng dưới: không test/không điều
    trị; giữa hai ngưỡng: NÊN xét nghiệm; trên ngưỡng trên: điều trị luôn không cần test.

    Dẫn xuất TỪ ĐẦU bằng so sánh kỳ vọng lợi ích 3 chiến lược (treat-none/treat-all/test),
    KHÔNG chép công thức đóng ghi nhớ sẵn (xem docstring module — kiểm bằng các trường
    hợp biên giải tích trong tests/test_clinical_calc.py, KHÔNG phải mô phỏng brute-force
    quy mô lớn — SỬA 2026-07-24, vòng lặp kiểm tra-hoàn thiện vòng 23). test_cost = tác
    hại/rủi ro CỐ HỮU của việc làm xét nghiệm (0 nếu xét nghiệm không xâm lấn/không rủi ro).

    Trả {"lower": .., "upper": .., "valid_testing_zone": bool}. Nếu
    valid_testing_zone=False → xét nghiệm không đáng giá (chi phí/rủi ro test vượt lợi
    ích thông tin mang lại) — KHÔNG nên chỉ định.
    """
    for name, v in (("se", se), ("sp", sp)):
        if not (0.0 < v < 1.0):
            raise ClinicalCalcError(f"{name}={v} phải trong (0,1).")
    if harm <= 0 or benefit <= 0:
        raise ClinicalCalcError(f"harm={harm}, benefit={benefit} phải dương.")
    if test_cost < 0:
        raise ClinicalCalcError(f"test_cost={test_cost} không được âm.")

    lower = (test_cost + (1 - sp) * harm) / (se * benefit + (1 - sp) * harm)
    upper = (harm * sp - test_cost) / (benefit * (1 - se) + harm * sp)
    valid = lower < upper
    return {
        "lower": lower, "upper": upper, "valid_testing_zone": valid,
        "treatment_threshold": treatment_threshold(harm, benefit),
        "note": ("Vùng test hợp lệ — xét nghiệm giữa 2 ngưỡng này." if valid else
                 "KHÔNG có vùng test hợp lệ — chi phí/rủi ro xét nghiệm vượt giá trị "
                 "thông tin mang lại ở mọi mức xác suất tiền nghiệm; chọn treat-all "
                 "hoặc treat-none theo ngưỡng điều trị đơn thuần."),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 3. NNT / ARR — Altman 1998 (CI qua xấp xỉ chuẩn trên hiệu tỷ lệ); Zhang–Yu 1998 (OR→RR)
# ═══════════════════════════════════════════════════════════════════════════

def _nnt_from_arr(arr: float, lo: Optional[float], hi: Optional[float]) -> Dict:
    """Quy tắc Altman (1998) 'NNT sang NNH' khi CI của ARR vắt qua 0."""
    out: Dict = {"arr": arr}
    if lo is not None and hi is not None:
        out["arr_ci"] = [lo, hi]
        if lo <= 0 <= hi:
            # CI vắt qua 0 -> không có NNT/NNH đơn nhất; báo dạng "NNTB … đến vô cực đến NNTH …"
            nntb = 1 / hi if hi > 0 else None
            nnth = 1 / abs(lo) if lo < 0 else None
            out["straddles_zero"] = True
            out["nnt_point"] = (1 / arr) if arr != 0 else None
            out["report"] = (
                f"CI của ARR vắt qua 0 — không có NNT/NNH đơn nhất, báo dạng Altman: "
                f"NNTB={nntb:.1f} → vô cực → NNTH={nnth:.1f}" if (nntb and nnth) else
                "CI của ARR vắt qua 0 — không kết luận được NNT/NNH đơn nhất."
            )
            return out
        # không vắt 0: đảo cận (ARR cao hơn -> NNT thấp hơn)
        out["straddles_zero"] = False
    if arr == 0:
        raise ClinicalCalcError("ARR=0 (CER=EER) — NNT vô định (không có khác biệt để tính).")
    nnt = 1 / arr
    out["nnt"] = nnt
    out["direction"] = "NNT (lợi ích, ARR>0)" if arr > 0 else "NNH (tác hại, ARR<0)"
    if lo is not None and hi is not None and not out.get("straddles_zero"):
        bounds = sorted([1 / lo, 1 / hi]) if (lo != 0 and hi != 0) else [None, None]
        out["nnt_ci"] = bounds
    return out


def nnt_from_counts(events_control: int, n_control: int,
                    events_experimental: int, n_experimental: int,
                    alpha: float = 0.05) -> Dict:
    """NNT/ARR + 95%CI TRỰC TIẾP từ số liệu thô 2 nhóm (Altman 1998, xấp xỉ chuẩn Wald
    trên hiệu hai tỷ lệ). z mặc định 1.96 (alpha=0.05, hai phía)."""
    if n_control <= 0 or n_experimental <= 0:
        raise ClinicalCalcError("Cỡ mẫu mỗi nhóm phải dương.")
    if not (0 <= events_control <= n_control) or not (0 <= events_experimental <= n_experimental):
        raise ClinicalCalcError("Số biến cố phải nằm trong [0, cỡ mẫu nhóm tương ứng].")
    cer = events_control / n_control
    eer = events_experimental / n_experimental
    arr = cer - eer
    se = math.sqrt(cer * (1 - cer) / n_control + eer * (1 - eer) / n_experimental)
    z = _z_from_alpha(alpha)
    lo, hi = arr - z * se, arr + z * se
    out = {"cer": cer, "eer": eer, **_nnt_from_arr(arr, lo, hi)}
    out["method"] = "Altman 1998 (Wald CI trên hiệu tỷ lệ, từ số liệu thô)"
    return out


def nnt_from_rr(cer: float, rr: float, rr_ci_lower: Optional[float] = None,
               rr_ci_upper: Optional[float] = None) -> Dict:
    """NNT/ARR từ CER (tỷ lệ biến cố NỀN — quần thể/đối chứng) + RR (từ nguồn/meta-analysis).

    ARR = CER × (1 − RR). Nếu có CI của RR, lan truyền sang CI của ARR ở CER CỐ ĐỊNH
    (cách chuẩn khi CER lấy từ quần thể đích, RR+CI lấy từ nghiên cứu).
    """
    if not (0.0 < cer < 1.0):
        raise ClinicalCalcError(f"cer={cer} phải trong (0,1).")
    if rr <= 0:
        raise ClinicalCalcError(f"rr={rr} phải dương.")
    arr = cer * (1 - rr)
    lo = hi = None
    if rr_ci_lower is not None and rr_ci_upper is not None:
        if rr_ci_lower <= 0 or rr_ci_upper <= 0:
            raise ClinicalCalcError("Cận CI của RR phải dương.")
        arr_a = cer * (1 - rr_ci_lower)
        arr_b = cer * (1 - rr_ci_upper)
        lo, hi = min(arr_a, arr_b), max(arr_a, arr_b)
    out = {"cer": cer, "rr": rr, **_nnt_from_arr(arr, lo, hi)}
    out["method"] = "ARR = CER×(1−RR), CI lan truyền từ CI của RR ở CER cố định"
    return out


def or_to_rr(cer: float, orr: float) -> float:
    """Chuyển OR→RR ở CER đã biết (Zhang J, Yu KF. JAMA. 1998;280(19):1690-1).

    RR = OR / [(1 − CER) + (CER × OR)]. Đúng khi CER biết trước (không phải xấp xỉ
    'bệnh hiếm' — công thức Zhang–Yu áp dụng cho MỌI mức CER, không chỉ hiếm gặp.
    """
    if not (0.0 < cer < 1.0):
        raise ClinicalCalcError(f"cer={cer} phải trong (0,1).")
    if orr <= 0:
        raise ClinicalCalcError(f"or={orr} phải dương.")
    return orr / ((1 - cer) + cer * orr)


def nnt_from_or(cer: float, orr: float, or_ci_lower: Optional[float] = None,
               or_ci_upper: Optional[float] = None) -> Dict:
    """NNT/ARR từ CER + OR (chuyển OR→RR qua Zhang–Yu rồi tái dùng nnt_from_rr)."""
    rr = or_to_rr(cer, orr)
    rr_lo = or_to_rr(cer, or_ci_lower) if or_ci_lower is not None else None
    rr_hi = or_to_rr(cer, or_ci_upper) if or_ci_upper is not None else None
    out = nnt_from_rr(cer, rr, rr_lo, rr_hi)
    out["or"] = orr
    out["rr_derived_from_or"] = rr
    out["method"] = "OR→RR (Zhang–Yu 1998) rồi ARR=CER×(1−RR)"
    return out


def _z_from_alpha(alpha: float) -> float:
    """z_{alpha/2} hai phía — vá 2026-07-04 (red-team): bản cũ dùng bảng tra 3 giá trị
    cứng khi thiếu scipy, ÂM THẦM trả z của alpha=0.05 cho MỌI alpha khác (vd 0.10/0.20
    dùng phổ biến cho CI 90%/80%) — sai lệch khoảng tin cậy mà không báo lỗi. Nay dùng
    normal_dist.inv_phi() (xấp xỉ Acklam đã kiểm bằng Z-table, xem test_normal_dist.py)
    nên ĐÚNG cho MỌI alpha, không cần scipy.
    """
    if not (0 < alpha < 1):
        raise ClinicalCalcError(f"alpha={alpha} phải trong (0,1).")
    return _normal_dist.inv_phi(1 - alpha / 2)


# ═══════════════════════════════════════════════════════════════════════════
# 4. GRADE — thuật toán chính thức (Guyatt et al., GRADE working group, BMJ 2008 loạt bài)
# ═══════════════════════════════════════════════════════════════════════════

_GRADE_LABELS = {4: "Cao (High)", 3: "Trung bình (Moderate)", 2: "Thấp (Low)", 1: "Rất thấp (Very low)"}
# "dta" = độ chính xác chẩn đoán (diagnostic test accuracy) — 2026-07-12: thêm mức khởi điểm
# thiếu (rà kiến trúc phát hiện tham-dinh-do-chinh-xac-chan-doan.md kỳ vọng GRADE-cho-test
# nhưng công cụ này trước đó CHỈ có "rct"/"observational"). Bắt đầu CAO (4), KHÔNG PHẢI thấp
# như observational thường — đã xác minh qua PubMed TRƯỚC khi thêm (không suy đoán): nghiên
# cứu cắt ngang/đoàn hệ so sánh trực tiếp index test với reference standard "start as high
# certainty" (Schünemann HJ et al. "GRADE guidelines: 21 part 1. Study design, risk of bias,
# and indirectness in rating the certainty across a body of evidence for test accuracy."
# J Clin Epidemiol 2020;122:129-141. PMID:32060007 DOI:10.1016/j.jclinepi.2019.12.020).
_START_LEVEL = {"rct": 4, "observational": 2, "dta": 4}


def grade_rating(design: str, risk_of_bias: int = 0, inconsistency: int = 0,
                 indirectness: int = 0, imprecision: int = 0, publication_bias: int = 0,
                 large_effect: int = 0, dose_response: int = 0,
                 plausible_confounding_reduces_effect: int = 0) -> Dict:
    """Xếp hạng độ chắc chắn GRADE — TỔNG HỢP đánh giá 5 domain hạ bậc + 3 yếu tố nâng bậc
    (chỉ quan sát) mà BÁC SĨ/NGUỒN đã cung cấp, theo thuật toán CHÍNH THỨC của GRADE
    Working Group (Guyatt GH et al. BMJ 2008;336:924-6 và loạt bài liên quan).

    CÔNG CỤ KHÔNG TỰ ĐÁNH GIÁ risk-of-bias/inconsistency/... — mỗi tham số là mức độ
    NGHIÊM TRỌNG bác sĩ/nguồn đã chấm: 0=không có vấn đề, 1=nghiêm trọng (hạ 1 bậc),
    2=rất nghiêm trọng (hạ 2 bậc). Yếu tố nâng bậc (chỉ áp observational): 0=không có,
    1=có (nâng 1 bậc), large_effect có thể =2 (hiệu ứng RẤT lớn, nâng 2 bậc).

    design="dta" (2026-07-12, task_5a25a9c7): độ chính xác chẩn đoán (diagnostic test
    accuracy) — nghiên cứu cắt ngang/đoàn hệ so sánh trực tiếp index test với reference
    standard. Bắt đầu CAO (giống RCT — xác minh PMID:32060007, KHÔNG suy đoán), hạ bậc
    theo CÙNG 5 domain nhưng risk_of_bias chấm bằng QUADAS-3 hiện hành (không phải RoB 2;
    QUADAS-2 chỉ tương thích ngược). KHÔNG
    áp yếu tố nâng bậc observational (large_effect/dose_response/confounding) — nguồn
    GRADE-DTA không định nghĩa các yếu tố này cho thiết kế DTA.

    Kết quả kẹp trong [1,4] (Rất thấp…Cao) — không thể âm/vượt trần dù cộng dồn nhiều yếu tố.
    """
    design = design.lower().strip()
    if design not in _START_LEVEL:
        raise ClinicalCalcError(f"design='{design}' phải là 'rct', 'observational' hoặc 'dta'.")
    for name, v in (("risk_of_bias", risk_of_bias), ("inconsistency", inconsistency),
                    ("indirectness", indirectness), ("imprecision", imprecision),
                    ("publication_bias", publication_bias)):
        if v not in (0, 1, 2):
            raise ClinicalCalcError(f"{name}={v} phải là 0 (không), 1 (nghiêm trọng) hoặc 2 (rất nghiêm trọng).")
    for name, v, maxv in (("large_effect", large_effect, 2), ("dose_response", dose_response, 1),
                          ("plausible_confounding_reduces_effect", plausible_confounding_reduces_effect, 1)):
        if v not in range(0, maxv + 1):
            raise ClinicalCalcError(f"{name}={v} phải là 0..{maxv}.")

    start = _START_LEVEL[design]
    downgrade = risk_of_bias + inconsistency + indirectness + imprecision + publication_bias
    upgrade = 0
    if design == "observational":
        upgrade = large_effect + dose_response + plausible_confounding_reduces_effect
    final = max(1, min(4, start - downgrade + upgrade))
    _na_upgrade = f"N/A (chỉ observational áp dụng, không phải '{design}')"
    return {
        "design": design, "start_level": start, "start_label": _GRADE_LABELS[start],
        "total_downgrade": downgrade, "total_upgrade": upgrade,
        "final_level": final, "final_label": _GRADE_LABELS[final],
        "domains": {
            "risk_of_bias": risk_of_bias, "inconsistency": inconsistency,
            "indirectness": indirectness, "imprecision": imprecision,
            "publication_bias": publication_bias,
            "large_effect": large_effect if design == "observational" else _na_upgrade,
            "dose_response": dose_response if design == "observational" else _na_upgrade,
            "plausible_confounding_reduces_effect":
                plausible_confounding_reduces_effect if design == "observational" else _na_upgrade,
        },
        "note": ("Kết quả TỔNG HỢP từ đánh giá domain do bác sĩ/nguồn cung cấp theo thuật "
                 "toán chính thức GRADE — công cụ KHÔNG tự chấm risk-of-bias/inconsistency."
                 + (" Với design='dta': risk_of_bias chấm bằng QUADAS-3 hiện hành "
                    "(không phải RoB 2; QUADAS-2 chỉ tương thích ngược)."
                    if design == "dta" else "")),
    }


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def _print(result: Dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for k, v in result.items():
            print(f"  {k}: {v}")
        print(f"\n{DISCLAIMER}")


def main() -> int:
    # Vá 2026-07-04 (red-team): tránh crash UnicodeEncodeError khi in DISCLAIMER tiếng
    # Việt trên console Windows mặc định (cp1252).
    _gate_contract.ensure_utf8_stdout()
    ap = argparse.ArgumentParser(description="Máy tính suy luận lâm sàng (Bayes/ngưỡng/NNT/GRADE).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("bayes", help="Pretest -> LR -> posttest (odds form)")
    b.add_argument("--pretest", type=float, required=True)
    b.add_argument("--lr", type=float, help="LR trực tiếp (loại trừ --se/--sp)")
    b.add_argument("--se", type=float, help="Độ nhạy (dùng với --sp thay cho --lr)")
    b.add_argument("--sp", type=float, help="Độ đặc hiệu")
    b.add_argument("--positive", action="store_true", help="Dùng LR+ khi tính từ Se/Sp (mặc định)")
    b.add_argument("--negative", action="store_true", help="Dùng LR- khi tính từ Se/Sp")
    b.add_argument("--json", action="store_true")

    t = sub.add_parser("threshold", help="Ngưỡng điều trị + ngưỡng xét nghiệm (Pauker-Kassirer)")
    t.add_argument("--harm", type=float, required=True)
    t.add_argument("--benefit", type=float, required=True)
    t.add_argument("--se", type=float, help="Cần để tính ngưỡng TEST (bỏ qua = chỉ tính ngưỡng điều trị)")
    t.add_argument("--sp", type=float)
    t.add_argument("--test-cost", type=float, default=0.0)
    t.add_argument("--json", action="store_true")

    n = sub.add_parser("nnt", help="NNT/ARR + CI (từ số liệu thô, hoặc CER+RR, hoặc CER+OR)")
    n.add_argument("--cer", type=float, required=True, help="Tỷ lệ biến cố nền/đối chứng")
    n.add_argument("--eer", type=float, help="Tỷ lệ biến cố nhóm can thiệp (cần --n-control/--n-experimental cho CI)")
    n.add_argument("--n-control", type=int)
    n.add_argument("--n-experimental", type=int)
    n.add_argument("--rr", type=float)
    n.add_argument("--rr-ci-lower", type=float)
    n.add_argument("--rr-ci-upper", type=float)
    n.add_argument("--or", dest="orr", type=float)
    n.add_argument("--or-ci-lower", type=float)
    n.add_argument("--or-ci-upper", type=float)
    n.add_argument("--alpha", type=float, default=0.05)
    n.add_argument("--json", action="store_true")

    g = sub.add_parser("grade", help="Xếp hạng GRADE (thuật toán chính thức)")
    g.add_argument("--design", required=True, choices=["rct", "observational", "dta"])
    g.add_argument("--rob", type=int, default=0, dest="risk_of_bias")
    g.add_argument("--inconsistency", type=int, default=0)
    g.add_argument("--indirectness", type=int, default=0)
    g.add_argument("--imprecision", type=int, default=0)
    g.add_argument("--publication-bias", type=int, default=0)
    g.add_argument("--large-effect", type=int, default=0)
    g.add_argument("--dose-response", type=int, default=0)
    g.add_argument("--plausible-confounding-reduces-effect", type=int, default=0)
    g.add_argument("--json", action="store_true")

    args = ap.parse_args()
    try:
        if args.cmd == "bayes":
            if args.lr is not None:
                lr = args.lr
            elif args.se is not None and args.sp is not None:
                lrs = lr_from_sensitivity_specificity(args.se, args.sp)
                lr = lrs["lr_negative"] if args.negative else lrs["lr_positive"]
            else:
                raise ClinicalCalcError("Cần --lr HOẶC cả --se và --sp.")
            posttest = bayes_posttest(args.pretest, lr)
            result = {"pretest": args.pretest, "lr_used": lr, "posttest": posttest}
            # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 23, phát hiện MEDIUM):
            # trước đây ghi chú "SỬA 2026-07-23" ở chan-doan-xac-suat.md CHỈ thêm văn
            # xuôi nhắc bác sĩ tự xác nhận đã chia 100 — KHÔNG có backstop kỹ thuật nào
            # trong công cụ. Đa số bệnh cảnh ngoại trú thực tế có pretest THẤP (<30%);
            # cảnh báo (không chặn — bác sĩ vẫn có thể có pretest thật sự cao) khi vượt
            # ngưỡng này để bắt sớm lỗi gõ "0.5" (nghĩ "0,5%") thay vì "0.005".
            if args.pretest > 0.3:
                result["warning"] = (
                    f"pretest={args.pretest} > 0.3 (30%) — XÁC NHẬN đây không phải lỗi "
                    "nhập nhầm phần trăm-thành-thập phân (vd '0.5' khi ý là '0,5%' → "
                    "phải nhập '0.005'). Nếu pretest thật sự cao (vd bệnh cảnh lâm sàng "
                    "rõ ràng), bỏ qua cảnh báo này."
                )
            _print(result, args.json)
        elif args.cmd == "threshold":
            if args.se is not None and args.sp is not None:
                res = test_threshold(args.se, args.sp, args.harm, args.benefit, args.test_cost)
            else:
                res = {"treatment_threshold": treatment_threshold(args.harm, args.benefit),
                       "note": "Chỉ tính ngưỡng điều trị (không có --se/--sp để tính ngưỡng test)."}
            _print(res, args.json)
        elif args.cmd == "nnt":
            if args.orr is not None:
                res = nnt_from_or(args.cer, args.orr, args.or_ci_lower, args.or_ci_upper)
            elif args.rr is not None:
                res = nnt_from_rr(args.cer, args.rr, args.rr_ci_lower, args.rr_ci_upper)
            elif (
                args.eer is not None
                and args.n_control is not None
                and args.n_experimental is not None
            ):
                events_c = round(args.cer * args.n_control)
                events_e = round(args.eer * args.n_experimental)
                res = nnt_from_counts(events_c, args.n_control, events_e, args.n_experimental, args.alpha)
            else:
                raise ClinicalCalcError("Cần --rr, hoặc --or, hoặc (--eer + --n-control + --n-experimental).")
            _print(res, args.json)
        elif args.cmd == "grade":
            res = grade_rating(args.design, args.risk_of_bias, args.inconsistency,
                               args.indirectness, args.imprecision, args.publication_bias,
                               args.large_effect, args.dose_response,
                               args.plausible_confounding_reduces_effect)
            _print(res, args.json)
    except ClinicalCalcError as e:
        print(f"❌ LỖI: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
