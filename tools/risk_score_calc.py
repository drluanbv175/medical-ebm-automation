#!/usr/bin/env python3
"""risk_score_calc.py — Máy tính THANG ĐIỂM NGUY CƠ lâm sàng chạy được (điểm chính xác,
không LLM tự cộng tay).

Vá khoảng trống đã xác nhận (kiểm tra trực tiếp 2026-07-04): `thang-diem-nguy-co.md`
liệt kê CHA₂DS₂-VASc·HAS-BLED·Wells·PERC·CURB-65·qSOFA·Child-Pugh·MELD... nhưng chỉ
tham chiếu `gen_research_docx.py` (xuất TÀI LIỆU, không phải máy tính) — không có công
cụ nào TÍNH ĐIỂM. Cùng lớp lỗi đã vá cho suy luận Bayes/NNT/GRADE (`clinical_calc.py`).

PHẠM VI CÓ CHỦ Ý (an toàn hơn là đủ):
  Module này CHỈ triển khai thang **điểm-cộng đơn giản** (mỗi tiêu chí = số điểm cố
  định, công khai, thống nhất giữa mọi nguồn y văn — rủi ro sai số CÔNG THỨC thấp) +
  MELD (công thức hồi quy log ĐƠN, hệ số gốc công bố rộng rãi, không đổi theo cohort).
  KHÔNG triển khai ASCVD Pooled Cohort Equations / FRAX / SCORE2 / MELD-Na — các thang
  này dùng hệ số hồi quy đa biến phức tạp/tái chuẩn hóa theo vùng/phiên bản dịch vụ độc
  quyền (FRAX) mà việc nhớ nhầm dù một hệ số nhỏ sẽ cho kết quả SAI mà không có cách
  nào tự phát hiện — rủi ro cao hơn lợi ích. Với các thang này, agent PHẢI dùng máy
  tính chính thức (MDCalc/công cụ hãng) hoặc đánh dấu `[CẦN CÔNG CỤ CHÍNH THỨC]`.

MỌI HÀM: chỉ tính ĐIỂM + PHÂN LOẠI ĐỊNH TÍNH theo ngưỡng gốc của thang (vd "nguy cơ
cao/thấp", "Child-Pugh A/B/C") — KHÔNG tự bịa % nguy cơ tuyệt đối cụ thể (con số đó
thay đổi theo cohort kiểm định, phải lấy từ nguồn agent trích, không phải hằng số
trong công cụ này).

Nguồn từng thang (trích trong docstring hàm): Lip et al. 2010 Chest (CHA₂DS₂-VASc);
Pisters et al. 2010 Chest (HAS-BLED); Lim et al. 2003 Thorax (CURB-65); Singer et al.
2016 JAMA — Sepsis-3 (qSOFA); Wells et al. 2000/2001 (Wells PE); Kline et al. 2004
(PERC); Child & Turcotte 1964 / Pugh 1973 (Child-Pugh); Kamath et al. 2001 / OPTN-UNOS
(MELD).

Dùng:
  python tools/risk_score_calc.py cha2ds2vasc --chf 0 --hypertension 1 --age 78 \\
      --diabetes 1 --stroke-tia-thromboembolism 0 --vascular-disease 0 --sex female
  python tools/risk_score_calc.py hasbled --hypertension 1 --abnormal-renal 0 \\
      --abnormal-liver 0 --stroke 0 --bleeding-history 0 --labile-inr 0 --age 78 \\
      --drugs 0 --alcohol 0
  python tools/risk_score_calc.py curb65 --confusion 0 --urea-high 1 --rr-high 0 \\
      --bp-low 0 --age 78
  python tools/risk_score_calc.py qsofa --rr-high 1 --altered-mentation 0 --sbp-low 0
  python tools/risk_score_calc.py wells-pe --dvt-signs 0 --pe-most-likely 1 \\
      --hr-over-100 1 --immobilization-surgery 0 --previous-dvt-pe 0 --hemoptysis 0 --malignancy 0
  python tools/risk_score_calc.py perc --age-under-50 1 --hr-under-100 1 --spo2-95-or-above 1 \\
      --no-hemoptysis 1 --no-estrogen 1 --no-prior-dvt-pe 1 --no-leg-swelling 1 --no-recent-surgery-trauma 1
  python tools/risk_score_calc.py child-pugh --bilirubin 2.5 --albumin 3.0 --inr 1.9 \\
      --ascites moderate --encephalopathy none
  python tools/risk_score_calc.py meld --bilirubin 2.5 --inr 1.9 --creatinine 1.8 --dialysis-2x-past-week false
"""

from __future__ import annotations

import argparse
import json
import math
from typing import Dict


class RiskScoreError(ValueError):
    """Input thiếu/ngoài miền hợp lệ — công cụ TỪ CHỐI tính thay vì bịa giá trị mặc định."""


DISCLAIMER = "Cần bác sĩ kiểm chứng."
NOT_IMPLEMENTED_HIGH_RISK = (
    "KHÔNG triển khai trong công cụ này (hệ số hồi quy đa biến phức tạp/độc quyền — "
    "rủi ro sai số cao hơn lợi ích). Dùng máy tính CHÍNH THỨC (MDCalc/công cụ hãng) "
    "hoặc đánh dấu [CẦN CÔNG CỤ CHÍNH THỨC]."
)


def _bit(name: str, v: int) -> int:
    if v not in (0, 1):
        raise RiskScoreError(f"{name}={v} phải là 0 (không) hoặc 1 (có).")
    return v


# ═══════════════════════════════════════════════════════════════════════════
# CHA₂DS₂-VASc — Lip GY et al. Chest. 2010;137(2):263-72.
# ═══════════════════════════════════════════════════════════════════════════

def cha2ds2vasc(chf: int, hypertension: int, age: int, diabetes: int,
               stroke_tia_thromboembolism: int, vascular_disease: int,
               sex: str) -> Dict:
    """CHA₂DS₂-VASc — nguy cơ đột quỵ trong rung nhĩ không do bệnh van tim.

    Điểm: CHF/RL chức năng thất trái(1) · THA(1) · Tuổi≥75(2)/65-74(1) · ĐTĐ(1) ·
    Đột quỵ/TIA/thuyên tắc trước(2) · Bệnh mạch máu(1) · Nữ(1, CHỈ TÍNH khi có ≥1
    yếu tố khác — nữ đơn độc KHÔNG tăng nguy cơ, theo khuyến cáo ESC 2012/2020).
    """
    chf = _bit("chf", chf)
    hypertension = _bit("hypertension", hypertension)
    diabetes = _bit("diabetes", diabetes)
    stroke_tia_thromboembolism = _bit("stroke_tia_thromboembolism", stroke_tia_thromboembolism)
    vascular_disease = _bit("vascular_disease", vascular_disease)
    if sex not in ("male", "female"):
        raise RiskScoreError("sex phải là 'male' hoặc 'female'.")
    if age < 0 or age > 130:
        raise RiskScoreError(f"age={age} ngoài miền hợp lệ.")

    age_points = 2 if age >= 75 else (1 if age >= 65 else 0)
    non_sex_points = (chf + hypertension + age_points + diabetes
                      + 2 * stroke_tia_thromboembolism + vascular_disease)
    # Nữ đơn độc (không kèm yếu tố nào khác) KHÔNG tính điểm — tránh phóng đại nguy cơ.
    sex_points = 1 if (sex == "female" and non_sex_points >= 1) else 0
    total = non_sex_points + sex_points

    if sex == "male":
        category = "rất thấp — cân nhắc không kháng đông" if total == 0 else \
                   "thấp — cân nhắc kháng đông" if total == 1 else \
                   "khuyến cáo kháng đông (theo guideline nguồn)"
    else:
        category = "rất thấp (nữ, không yếu tố khác) — cân nhắc không kháng đông" if total <= 1 else \
                   "khuyến cáo kháng đông (theo guideline nguồn)"

    return {
        "score": total, "max_score": 9, "category": category,
        "components": {"chf": chf, "hypertension": hypertension, "age_points": age_points,
                       "diabetes": diabetes, "stroke_tia_thromboembolism_x2": 2 * stroke_tia_thromboembolism,
                       "vascular_disease": vascular_disease, "sex_points": sex_points},
        "note": "% nguy cơ đột quỵ/năm theo ĐIỂM này thay đổi theo cohort kiểm định — "
                "lấy từ nguồn agent trích dẫn (PMID/DOI), KHÔNG phải hằng số cố định.",
        "source": "Lip GYH et al. Chest. 2010;137(2):263-72.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# HAS-BLED — Pisters R et al. Chest. 2010;138(5):1093-100.
# ═══════════════════════════════════════════════════════════════════════════

def hasbled(hypertension: int, abnormal_renal: int, abnormal_liver: int, stroke: int,
           bleeding_history: int, labile_inr: int, age: int, drugs: int, alcohol: int) -> Dict:
    """HAS-BLED — nguy cơ chảy máu khi dùng kháng đông. Mỗi tiêu chí = 1 điểm, tối đa 9."""
    fields = {"hypertension": hypertension, "abnormal_renal": abnormal_renal,
             "abnormal_liver": abnormal_liver, "stroke": stroke,
             "bleeding_history": bleeding_history, "labile_inr": labile_inr,
             "drugs": drugs, "alcohol": alcohol}
    for k, v in fields.items():
        fields[k] = _bit(k, v)
    if age < 0 or age > 130:
        raise RiskScoreError(f"age={age} ngoài miền hợp lệ.")
    elderly = 1 if age > 65 else 0
    total = sum(fields.values()) + elderly
    category = "cao (≥3) — thận trọng, theo dõi sát, không tự chống chỉ định" if total >= 3 else "thấp/vừa"
    return {
        "score": total, "max_score": 9, "category": category,
        "components": {**fields, "elderly_gt65": elderly},
        "note": "HAS-BLED cao KHÔNG tự động chống chỉ định kháng đông — chỉ báo hiệu cần "
                "theo dõi/xử lý yếu tố nguy cơ chảy máu có thể sửa được.",
        "source": "Pisters R et al. Chest. 2010;138(5):1093-100.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# CURB-65 — Lim WS et al. Thorax. 2003;58(5):377-82.
# ═══════════════════════════════════════════════════════════════════════════

def curb65(confusion: int, urea_high: int, rr_high: int, bp_low: int, age: int) -> Dict:
    """CURB-65 — độ nặng viêm phổi cộng đồng. urea_high: ure máu >7 mmol/L (>19mg/dL).
    rr_high: nhịp thở ≥30/phút. bp_low: HA tâm thu<90 HOẶC tâm trương≤60 mmHg."""
    fields = {"confusion": confusion, "urea_high": urea_high,
             "rr_high": rr_high, "bp_low": bp_low}
    for k, v in fields.items():
        fields[k] = _bit(k, v)
    if age < 0 or age > 130:
        raise RiskScoreError(f"age={age} ngoài miền hợp lệ.")
    age_point = 1 if age >= 65 else 0
    total = sum(fields.values()) + age_point
    if total <= 1:
        category = "nhẹ — cân nhắc điều trị ngoại trú"
    elif total == 2:
        category = "vừa — cân nhắc nhập viện ngắn/theo dõi sát"
    else:
        category = "nặng — nhập viện, cân nhắc ICU nếu 4-5 điểm"
    return {
        "score": total, "max_score": 5, "category": category,
        "components": {**fields, "age_geq_65": age_point},
        "source": "Lim WS et al. Thorax. 2003;58(5):377-82.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# qSOFA — Singer M et al. JAMA (Sepsis-3). 2016;315(8):801-10.
# ═══════════════════════════════════════════════════════════════════════════

def qsofa(rr_high: int, altered_mentation: int, sbp_low: int) -> Dict:
    """qSOFA — sàng lọc nhanh nguy cơ nặng nghi nhiễm trùng. rr_high: nhịp thở≥22/phút.
    sbp_low: HA tâm thu≤100 mmHg."""
    fields = {"rr_high": rr_high, "altered_mentation": altered_mentation, "sbp_low": sbp_low}
    for k, v in fields.items():
        fields[k] = _bit(k, v)
    total = sum(fields.values())
    category = ("nguy cơ tăng (≥2) — nghĩ nhiễm trùng nặng/sepsis, đánh giá SOFA đầy đủ + xử trí sớm"
               if total >= 2 else "nguy cơ thấp hơn theo qSOFA (không loại trừ nhiễm trùng nặng)")
    return {
        "score": total, "max_score": 3, "category": category, "components": fields,
        "source": "Singer M et al. JAMA. 2016;315(8):801-10 (Sepsis-3).",
    }


# ═══════════════════════════════════════════════════════════════════════════
# Wells score (PE, bản gốc) — Wells PS et al. Thromb Haemost. 2000;83(3):416-20.
# ═══════════════════════════════════════════════════════════════════════════

def wells_pe(dvt_signs: int, pe_most_likely: int, hr_over_100: int,
            immobilization_surgery: int, previous_dvt_pe: int,
            hemoptysis: int, malignancy: int) -> Dict:
    """Wells score (thuyên tắc phổi, bản gốc 7 tiêu chí). Điểm không nguyên
    (1.5/3) — dùng float, KHÔNG làm tròn."""
    fields = {"dvt_signs": (dvt_signs, 3.0), "pe_most_likely": (pe_most_likely, 3.0),
             "hr_over_100": (hr_over_100, 1.5), "immobilization_surgery": (immobilization_surgery, 1.5),
             "previous_dvt_pe": (previous_dvt_pe, 1.5), "hemoptysis": (hemoptysis, 1.0),
             "malignancy": (malignancy, 1.0)}
    total = 0.0
    components = {}
    for k, (v, w) in fields.items():
        v = _bit(k, v)
        pts = v * w
        components[k] = pts
        total += pts
    three_tier = "thấp (<2)" if total < 2 else "vừa (2-6)" if total <= 6 else "cao (>6)"
    two_tier = "PE không likely (≤4)" if total <= 4 else "PE likely (>4)"
    return {
        "score": total, "max_score": 12.5,
        "three_tier_category": three_tier, "two_tier_category": two_tier,
        "components": components,
        "source": "Wells PS et al. Thromb Haemost. 2000;83(3):416-20.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# PERC — Kline JA et al. J Thromb Haemost. 2004;2(8):1247-55.
# ═══════════════════════════════════════════════════════════════════════════

def perc(age_under_50: int, hr_under_100: int, spo2_95_or_above: int,
        no_hemoptysis: int, no_estrogen: int, no_prior_dvt_pe: int,
        no_leg_swelling: int, no_recent_surgery_trauma: int) -> Dict:
    """PERC (PE Rule-out Criteria) — CHỈ dùng khi bác sĩ ĐÃ đánh giá xác suất tiền
    nghiệm THẤP (<15%, phán đoán lâm sàng) — công cụ KHÔNG tự xác nhận điều này.
    Mỗi tham số = 1 nếu tiêu chí "an toàn" ĐÚNG (đạt), 0 nếu KHÔNG đạt. Đạt ĐỦ 8/8 →
    có thể loại trừ PE mà không cần xét nghiệm thêm (CHỈ ở nhóm tiền nghiệm thấp)."""
    fields = {"age_under_50": age_under_50, "hr_under_100": hr_under_100,
             "spo2_95_or_above": spo2_95_or_above, "no_hemoptysis": no_hemoptysis,
             "no_estrogen": no_estrogen, "no_prior_dvt_pe": no_prior_dvt_pe,
             "no_leg_swelling": no_leg_swelling, "no_recent_surgery_trauma": no_recent_surgery_trauma}
    for k, v in fields.items():
        fields[k] = _bit(k, v)
    all_pass = all(fields.values())
    return {
        "all_criteria_met": all_pass, "n_criteria_met": sum(fields.values()), "n_total": 8,
        "components": fields,
        "interpretation": ("Đạt đủ 8/8 — CÓ THỂ loại trừ PE mà KHÔNG cần xét nghiệm thêm, "
                          "NHƯNG CHỈ khi bác sĩ đã xác nhận xác suất tiền nghiệm THẤP (<15%). "
                          "PERC KHÔNG dùng để loại trừ PE ở bệnh nhân nguy cơ trung bình/cao."
                          if all_pass else
                          "KHÔNG đạt đủ tiêu chí — PERC không loại trừ được PE, cần đánh giá thêm "
                          "(D-dimer/CT theo Wells)."),
        "source": "Kline JA et al. J Thromb Haemost. 2004;2(8):1247-55.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# Child-Pugh — Child CG, Turcotte JG. 1964; Pugh RN et al. Br J Surg. 1973.
# ═══════════════════════════════════════════════════════════════════════════

def child_pugh(bilirubin: float, albumin: float, inr: float,
              ascites: str, encephalopathy: str) -> Dict:
    """Child-Pugh — độ nặng xơ gan. bilirubin (mg/dL), albumin (g/dL), inr.
    ascites/encephalopathy: 'none'|'mild'|'moderate_severe' (ascites) hoặc
    'none'|'grade_1_2'|'grade_3_4' (encephalopathy)."""
    if bilirubin <= 0:
        raise RiskScoreError(f"bilirubin={bilirubin} phải dương (mg/dL).")
    if albumin <= 0:
        raise RiskScoreError(f"albumin={albumin} phải dương (g/dL).")
    if inr <= 0:
        raise RiskScoreError(f"inr={inr} phải dương.")
    if ascites not in ("none", "mild", "moderate_severe"):
        raise RiskScoreError("ascites phải là 'none'|'mild'|'moderate_severe'.")
    if encephalopathy not in ("none", "grade_1_2", "grade_3_4"):
        raise RiskScoreError("encephalopathy phải là 'none'|'grade_1_2'|'grade_3_4'.")

    bili_pts = 1 if bilirubin < 2 else (2 if bilirubin <= 3 else 3)
    alb_pts = 1 if albumin > 3.5 else (2 if albumin >= 2.8 else 3)
    inr_pts = 1 if inr < 1.7 else (2 if inr <= 2.3 else 3)
    ascites_pts = {"none": 1, "mild": 2, "moderate_severe": 3}[ascites]
    enceph_pts = {"none": 1, "grade_1_2": 2, "grade_3_4": 3}[encephalopathy]
    total = bili_pts + alb_pts + inr_pts + ascites_pts + enceph_pts
    child_class = "A" if total <= 6 else ("B" if total <= 9 else "C")
    return {
        "score": total, "class": child_class,
        "components": {"bilirubin_points": bili_pts, "albumin_points": alb_pts,
                       "inr_points": inr_pts, "ascites_points": ascites_pts,
                       "encephalopathy_points": enceph_pts},
        "source": "Pugh RN et al. Br J Surg. 1973;60(8):646-9.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# MELD (gốc) — Kamath PS et al. Hepatology. 2001;33(2):464-70; công thức OPTN/UNOS.
# ═══════════════════════════════════════════════════════════════════════════

def meld(bilirubin: float, inr: float, creatinine: float,
        dialysis_2x_past_week: bool = False) -> Dict:
    """MELD (bản GỐC, KHÔNG phải MELD-Na — xem NOT_IMPLEMENTED_HIGH_RISK cho MELD-Na).
    MELD = 3.78·ln(bilirubin) + 11.2·ln(INR) + 9.57·ln(creatinine) + 6.43.
    Giá trị <1.0 được ép về 1.0 trước khi lấy log (quy ước OPTN, tránh log âm).
    Creatinine kẹp tại 4.0 mg/dL nếu đã lọc máu ≥2 lần/tuần qua trước (quy ước OPTN).
    Kết quả làm tròn nguyên, kẹp trong [6,40]."""
    if bilirubin <= 0 or inr <= 0 or creatinine <= 0:
        raise RiskScoreError("bilirubin/inr/creatinine phải dương.")
    bili = max(1.0, bilirubin)
    inr_v = max(1.0, inr)
    creat = max(1.0, creatinine)
    if dialysis_2x_past_week:
        creat = 4.0
    else:
        creat = min(creat, 4.0)
    raw = 3.78 * math.log(bili) + 11.2 * math.log(inr_v) + 9.57 * math.log(creat) + 6.43
    score = max(6, min(40, round(raw)))
    return {
        "score": score, "raw_before_rounding_and_clamp": raw,
        "inputs_used": {"bilirubin": bili, "inr": inr_v, "creatinine": creat,
                        "dialysis_adjustment_applied": dialysis_2x_past_week},
        "note": "Đây là MELD GỐC (không có natri). MELD-Na (dùng phân bổ ghép gan từ 2016) "
                + NOT_IMPLEMENTED_HIGH_RISK,
        "source": "Kamath PS et al. Hepatology. 2001;33(2):464-70; công thức chuẩn OPTN/UNOS.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def _print(result: Dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"\n{DISCLAIMER}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Máy tính thang điểm nguy cơ lâm sàng.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("cha2ds2vasc")
    c.add_argument("--chf", type=int, required=True)
    c.add_argument("--hypertension", type=int, required=True)
    c.add_argument("--age", type=int, required=True)
    c.add_argument("--diabetes", type=int, required=True)
    c.add_argument("--stroke-tia-thromboembolism", type=int, required=True, dest="stroke_tia")
    c.add_argument("--vascular-disease", type=int, required=True, dest="vascular")
    c.add_argument("--sex", required=True, choices=["male", "female"])
    c.add_argument("--json", action="store_true")

    h = sub.add_parser("hasbled")
    h.add_argument("--hypertension", type=int, required=True)
    h.add_argument("--abnormal-renal", type=int, required=True, dest="abnormal_renal")
    h.add_argument("--abnormal-liver", type=int, required=True, dest="abnormal_liver")
    h.add_argument("--stroke", type=int, required=True)
    h.add_argument("--bleeding-history", type=int, required=True, dest="bleeding_history")
    h.add_argument("--labile-inr", type=int, required=True, dest="labile_inr")
    h.add_argument("--age", type=int, required=True)
    h.add_argument("--drugs", type=int, required=True)
    h.add_argument("--alcohol", type=int, required=True)
    h.add_argument("--json", action="store_true")

    cu = sub.add_parser("curb65")
    cu.add_argument("--confusion", type=int, required=True)
    cu.add_argument("--urea-high", type=int, required=True, dest="urea_high")
    cu.add_argument("--rr-high", type=int, required=True, dest="rr_high")
    cu.add_argument("--bp-low", type=int, required=True, dest="bp_low")
    cu.add_argument("--age", type=int, required=True)
    cu.add_argument("--json", action="store_true")

    q = sub.add_parser("qsofa")
    q.add_argument("--rr-high", type=int, required=True, dest="rr_high")
    q.add_argument("--altered-mentation", type=int, required=True, dest="altered_mentation")
    q.add_argument("--sbp-low", type=int, required=True, dest="sbp_low")
    q.add_argument("--json", action="store_true")

    w = sub.add_parser("wells-pe")
    w.add_argument("--dvt-signs", type=int, required=True, dest="dvt_signs")
    w.add_argument("--pe-most-likely", type=int, required=True, dest="pe_most_likely")
    w.add_argument("--hr-over-100", type=int, required=True, dest="hr_over_100")
    w.add_argument("--immobilization-surgery", type=int, required=True, dest="immobilization_surgery")
    w.add_argument("--previous-dvt-pe", type=int, required=True, dest="previous_dvt_pe")
    w.add_argument("--hemoptysis", type=int, required=True)
    w.add_argument("--malignancy", type=int, required=True)
    w.add_argument("--json", action="store_true")

    pe = sub.add_parser("perc")
    for name in ("age-under-50", "hr-under-100", "spo2-95-or-above", "no-hemoptysis",
                "no-estrogen", "no-prior-dvt-pe", "no-leg-swelling", "no-recent-surgery-trauma"):
        pe.add_argument(f"--{name}", type=int, required=True, dest=name.replace("-", "_"))
    pe.add_argument("--json", action="store_true")

    cp = sub.add_parser("child-pugh")
    cp.add_argument("--bilirubin", type=float, required=True)
    cp.add_argument("--albumin", type=float, required=True)
    cp.add_argument("--inr", type=float, required=True)
    cp.add_argument("--ascites", required=True, choices=["none", "mild", "moderate_severe"])
    cp.add_argument("--encephalopathy", required=True, choices=["none", "grade_1_2", "grade_3_4"])
    cp.add_argument("--json", action="store_true")

    md = sub.add_parser("meld")
    md.add_argument("--bilirubin", type=float, required=True)
    md.add_argument("--inr", type=float, required=True)
    md.add_argument("--creatinine", type=float, required=True)
    md.add_argument("--dialysis-2x-past-week", type=lambda s: s.lower() == "true",
                    default=False, dest="dialysis")
    md.add_argument("--json", action="store_true")

    args = ap.parse_args()
    try:
        if args.cmd == "cha2ds2vasc":
            res = cha2ds2vasc(args.chf, args.hypertension, args.age, args.diabetes,
                              args.stroke_tia, args.vascular, args.sex)
        elif args.cmd == "hasbled":
            res = hasbled(args.hypertension, args.abnormal_renal, args.abnormal_liver,
                         args.stroke, args.bleeding_history, args.labile_inr, args.age,
                         args.drugs, args.alcohol)
        elif args.cmd == "curb65":
            res = curb65(args.confusion, args.urea_high, args.rr_high, args.bp_low, args.age)
        elif args.cmd == "qsofa":
            res = qsofa(args.rr_high, args.altered_mentation, args.sbp_low)
        elif args.cmd == "wells-pe":
            res = wells_pe(args.dvt_signs, args.pe_most_likely, args.hr_over_100,
                          args.immobilization_surgery, args.previous_dvt_pe,
                          args.hemoptysis, args.malignancy)
        elif args.cmd == "perc":
            res = perc(args.age_under_50, args.hr_under_100, args.spo2_95_or_above,
                      args.no_hemoptysis, args.no_estrogen, args.no_prior_dvt_pe,
                      args.no_leg_swelling, args.no_recent_surgery_trauma)
        elif args.cmd == "child-pugh":
            res = child_pugh(args.bilirubin, args.albumin, args.inr, args.ascites, args.encephalopathy)
        elif args.cmd == "meld":
            res = meld(args.bilirubin, args.inr, args.creatinine, args.dialysis)
    except RiskScoreError as e:
        print(f"❌ LỖI: {e}")
        return 1
    _print(res, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
