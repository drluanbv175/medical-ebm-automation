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
Bổ sung 21/11/2026 (11 thang verified + phân giai đoạn KDIGO): FIB-4, APRI, khoảng trống anion, HOMA-IR,
Maddrey (một công thức số học công bố, không hệ số hồi quy), PHQ-9, GAD-7, AUDIT-C, FRAIL, TIMI (UA/NSTEMI),
GOLD ABE, kdigo-stage — công thức/ngưỡng chép từ `app/clinical_scores/verified.py`; bảng
`BO_TINH_THEO_SCORE_ID`/`KHONG_CO_BO_TINH` khai MỌI thang verified (có bộ tính hay lý do chưa có).
Bổ sung 08/11/2026 (lý do khám ngoại trú): Wells DVT (Wells 2003 NEJM); Centor/McIsaac
(McIsaac 1998 CMAJ; NICE NG84); Marburg Heart Score (Bösner 2010 CMAJ); FeverPAIN (Little
2013 BMJ Open; NICE NG84); CRB-65 (Bauer 2006 J Intern Med; NICE NG250); Ottawa cổ chân/bàn
chân (Stiell 1993 JAMA) và Ottawa gối (Stiell 1996 JAMA) — hai quy tắc Ottawa là CÓ/KHÔNG.

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

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
from typing import Dict

import gate_contract as _gate_contract

for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


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


def _require_finite(name: str, value: float) -> float:
    """Chặn NaN/Inf TRƯỚC khi so sánh range — vá 2026-07-04 (red-team, systemic bug):
    so sánh `NaN < 0`/`NaN > 130` trong Python luôn trả False nên MỌI validate dạng
    `if x < lo or x > hi: raise` bị NaN "lách qua" hoàn toàn; sau đó `max(1.0, nan)`
    trả về 1.0 (không phải NaN, do cách so sánh nội bộ của max/min) khiến giá trị rác
    bị âm thầm thay bằng "1.0/bình thường" — tính ra một điểm cụ thể trông hợp lệ mà
    KHÔNG có dấu hiệu nào cho biết input gốc là dữ liệu lỗi/thiếu (parse CSV/HL7 rỗng).
    math.isfinite() loại cả NaN VÀ ±Inf bằng MỘT lần kiểm, không phụ thuộc so sánh trực
    tiếp — cũng chặn luôn OverflowError khi Inf lọt tới round()/log() phía sau (vd
    meld(bilirubin=inf) từng crash bằng traceback Python thô thay vì RiskScoreError).
    """
    if not math.isfinite(value):
        raise RiskScoreError(f"{name}={value} không phải số hữu hạn hợp lệ (NaN/Inf).")
    return value


_BOOL_CLI_TRUE = {"true", "1", "yes", "y"}
_BOOL_CLI_FALSE = {"false", "0", "no", "n"}


def _parse_bool_cli(s: str) -> bool:
    """`type=` callable cho cờ CLI boolean lâm sàng — vá 2026-09-04 (audit đối kháng):
    bản cũ `lambda s: s.lower() == "true"` coi MỌI chuỗi khác "true" là False, kể cả
    "1"/"yes"/lỗi gõ — `--dialysis-2x-past-week 1` và `--dialysis-2x-past-week yes` ÂM
    THẦM trở thành False (score MELD sai — creatinine không bị ép về 4.0 mg/dL theo quy
    ước OPTN cho bệnh nhân đang lọc máu ≥2 lần/tuần), không một cảnh báo/lỗi nào.
    Đúng nguyên tắc của module này (RiskScoreError: "TỪ CHỐI tính thay vì bịa giá trị
    mặc định") — input KHÔNG nhận diện được phải làm CLI báo lỗi rõ ràng, không được
    âm thầm đoán thành False."""
    v = s.strip().lower()
    if v in _BOOL_CLI_TRUE:
        return True
    if v in _BOOL_CLI_FALSE:
        return False
    raise argparse.ArgumentTypeError(
        f"{s!r} không phải giá trị boolean hợp lệ — dùng true/false (hoặc 1/0, yes/no)."
    )


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
    _require_finite("age", age)
    if age < 0 or age > 130:
        raise RiskScoreError(f"age={age} ngoài miền hợp lệ.")

    age_points = 2 if age >= 75 else (1 if age >= 65 else 0)
    non_sex_points = (chf + hypertension + age_points + diabetes
                      + 2 * stroke_tia_thromboembolism + vascular_disease)
    # Nữ đơn độc (không kèm yếu tố nào khác) KHÔNG tính điểm — tránh phóng đại nguy cơ.
    sex_points = 1 if (sex == "female" and non_sex_points >= 1) else 0
    total = non_sex_points + sex_points

    # SỬA 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 22, phát hiện HIGH — đã xác
    # minh qua guideline gốc): trước đây total>=2 ở NỮ trả về CÙNG category
    # "khuyến cáo kháng đông" như NAM total>=2 — SAI so với 2023 ACC/AHA/ACCP/HRS
    # (Joglar JA et al., Circulation 2024;149(1):e1-e156, PMID 38033089): Class 1
    # (khuyến cáo mạnh, nguy cơ đột quỵ ≥2%/năm) ứng với ≥2 Ở NAM nhưng ≥3 Ở NỮ —
    # điểm 2 ở nữ (do sex_points=1 chỉ cộng khi non_sex_points>=1, nên total=2 ở nữ
    # nghĩa là chỉ có 1 yếu tố khác + điểm giới) chỉ là Class IIb (cân nhắc/chia sẻ
    # quyết định), KHÔNG phải chỉ định mạnh như cùng điểm số ở nam.
    if sex == "male":
        category = "rất thấp — cân nhắc không kháng đông" if total == 0 else \
                   "thấp — cân nhắc kháng đông" if total == 1 else \
                   "khuyến cáo kháng đông (theo guideline nguồn)"
    else:
        category = "rất thấp (nữ, không yếu tố khác) — cân nhắc không kháng đông" if total <= 1 else \
                   ("trung gian (nữ, điểm 2) — CÂN NHẮC/chia sẻ quyết định, KHÔNG phải chỉ định "
                    "mạnh (2023 ACC/AHA/ACCP/HRS Mỹ: Class IIb ở nữ khi điểm=2, khác nam cùng điểm)"
                    if total == 2 else
                    "khuyến cáo kháng đông (theo guideline nguồn — Class 1 ở nữ khi điểm≥3)")

    return {
        "score": total, "max_score": 9, "category": category,
        "components": {"chf": chf, "hypertension": hypertension, "age_points": age_points,
                       "diabetes": diabetes, "stroke_tia_thromboembolism_x2": 2 * stroke_tia_thromboembolism,
                       "vascular_disease": vascular_disease, "sex_points": sex_points},
        "note": "% nguy cơ đột quỵ/năm theo ĐIỂM này thay đổi theo cohort kiểm định — "
                "lấy từ nguồn agent trích dẫn (PMID/DOI), KHÔNG phải hằng số cố định. "
                "THÊM 2026-07-23 (vòng lặp kiểm tra-hoàn thiện vòng 13, phát hiện MEDIUM): "
                "ESC 2024 AF guidelines đã ban hành thang thay thế CHA₂DS₂-VA — LOẠI BỎ HOÀN "
                "TOÀN điểm giới tính (không chỉ 'nữ đơn độc không tính' như bản này, mà bỏ "
                "điểm nữ cho MỌI trường hợp), khuyến cáo kháng đông ở điểm ≥2 bất kể giới. "
                "Hàm này tính đúng CHA₂DS₂-VASc KINH ĐIỂN (Lip 2010; ESC 2012-2020; vẫn dùng ở "
                "ACC/AHA/ACCP/HRS 2023 Mỹ) — KHÔNG phải bản mới nhất. "
                "SỬA 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 22, phát hiện HIGH): 2023 "
                "ACC/AHA/ACCP/HRS (Joglar JA et al., Circulation 2024;149(1):e1-e156, "
                "PMID 38033089) đổi ngưỡng Class 1 theo GIỚI TÍNH — ≥2 ở nam, ≥3 ở nữ (điểm 2 "
                "ở nữ chỉ Class IIb). Diễn giải category ở trên đã phản ánh khác biệt này.",
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
    _require_finite("age", age)
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
    _require_finite("age", age)
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
    _require_finite("bilirubin", bilirubin)
    _require_finite("albumin", albumin)
    _require_finite("inr", inr)
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
    _require_finite("bilirubin", bilirubin)
    _require_finite("inr", inr)
    _require_finite("creatinine", creatinine)
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
                + NOT_IMPLEMENTED_HIGH_RISK
                + " THÊM 2026-07-23 (vòng lặp kiểm tra-hoàn thiện vòng 13, phát hiện MEDIUM): "
                  "OPTN đã CHÍNH THỨC thay MELD-Na bằng MELD 3.0 (Kim WR et al., Gastroenterology "
                  "2021;161(6):1887-1895.e4 — thêm giới tính+albumin+số hạng tương tác) cho phân bổ "
                  "ghép gan thật tại Mỹ từ 2023 — MELD-Na (thứ note này nói 'chưa triển khai') bản "
                  "thân nó ĐÃ bị thay thêm một lớp nữa. Công thức MELD gốc ở đây (2001, không đổi) "
                  "phù hợp ước lượng độ nặng/tiên lượng lâm sàng ngoại trú, KHÔNG phản ánh điểm ưu "
                  "tiên ghép gan hiện hành nếu bối cảnh liên quan ghép tạng thật.",
        "source": "Kamath PS et al. Hepatology. 2001;33(2):464-70; công thức chuẩn OPTN/UNOS.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# BỔ SUNG 08/11/2026 — thang cho lý do khám ngoại trú thường gặp. Thành phần +
# ngưỡng KHỚP mục tương ứng trong app/clinical_scores/verified.py (một nguồn sự
# thật); chỉ trả ĐIỂM + PHÂN LOẠI ĐỊNH TÍNH, không bịa % nguy cơ tuyệt đối.
# ═══════════════════════════════════════════════════════════════════════════

def _age(age: float, lo: int = 0, hi: int = 130) -> float:
    _require_finite("age", age)
    if age < lo or age > hi:
        raise RiskScoreError(f"age={age} ngoài miền hợp lệ ({lo}–{hi}).")
    return age


def wells_dvt(active_cancer: int, paralysis_or_cast: int, bedridden_or_surgery: int,
              deep_vein_tenderness: int, entire_leg_swollen: int, calf_swelling_3cm: int,
              pitting_edema: int, collateral_veins: int, previous_dvt: int,
              alternative_dx_as_likely: int) -> Dict:
    """Wells DVT (mô hình 2 mức) — Wells PS et al. N Engl J Med. 2003;349(13):1227-35.
    9 tiêu chí +1 điểm; chẩn đoán khác có khả năng ≥ DVT: −2 điểm.
    ≤1: ít khả năng (làm D-dimer); ≥2: nhiều khả năng (siêu âm ép)."""
    plus = {"active_cancer": active_cancer, "paralysis_or_cast": paralysis_or_cast,
            "bedridden_or_surgery": bedridden_or_surgery,
            "deep_vein_tenderness": deep_vein_tenderness,
            "entire_leg_swollen": entire_leg_swollen, "calf_swelling_3cm": calf_swelling_3cm,
            "pitting_edema": pitting_edema, "collateral_veins": collateral_veins,
            "previous_dvt": previous_dvt}
    for k, v in plus.items():
        plus[k] = _bit(k, v)
    alt = _bit("alternative_dx_as_likely", alternative_dx_as_likely)
    total = sum(plus.values()) - 2 * alt
    if total <= 1:
        category = "DVT ít khả năng (unlikely) — làm D-dimer; âm tính ⇒ loại trừ"
    else:
        category = "DVT nhiều khả năng (likely) — siêu âm ép tĩnh mạch"
    note = ("Người đang có UNG THƯ: tổ hợp Wells thấp + D-dimer âm KHÔNG an toàn — siêu âm thẳng "
            "(Geersing GJ et al. BMJ 2014;348:g1340)." if plus["active_cancer"] else
            "Nghi DVT TÁI PHÁT: chỉ dùng Wells sửa đổi (+1 tiền sử) — Geersing 2014.")
    return {"score": total, "min_score": -2, "max_score": 9, "category": category,
            "components": {**plus, "alternative_dx_as_likely": -2 * alt},
            "note": note, "source": "Wells PS et al. N Engl J Med. 2003;349(13):1227-35."}


def centor_mcisaac(fever_over_38: int, absence_of_cough: int, tender_anterior_nodes: int,
                   tonsillar_swelling_exudate: int, age: float) -> Dict:
    """Centor gốc (0–4) và McIsaac (−1 đến 5) — McIsaac WJ et al. CMAJ 1998;158(1):75-83.
    Tuổi (McIsaac): 3–14 = +1; 15–44 = 0; ≥45 = −1. Ngưỡng hành động theo verified.py
    (McIsaac) và NICE NG84 (Centor gốc 0–2 / 3–4)."""
    f = {"fever_over_38": fever_over_38, "absence_of_cough": absence_of_cough,
         "tender_anterior_nodes": tender_anterior_nodes,
         "tonsillar_swelling_exudate": tonsillar_swelling_exudate}
    for k, v in f.items():
        f[k] = _bit(k, v)
    _age(age)
    if age < 3:
        raise RiskScoreError("age<3: thang chỉ dùng cho người ≥3 tuổi.")
    age_adj = 1 if age <= 14 else (0 if age <= 44 else -1)
    centor = sum(f.values())
    mcisaac = centor + age_adj
    if mcisaac <= 1:
        cat = "thấp — không xét nghiệm, không kháng sinh"
    elif mcisaac <= 3:
        cat = "trung gian — xét nghiệm nhanh liên cầu (RADT)"
    else:
        cat = "cao — xét nghiệm; điều trị nếu dương tính (không kháng sinh theo kinh nghiệm thường quy)"
    nice = ("Centor 0–2: NICE NG84 — không kê kháng sinh" if centor <= 2 else
            "Centor 3–4: NICE NG84 — cân nhắc kháng sinh ngay hoặc kê đơn dự phòng")
    return {"score": mcisaac, "min_score": -1, "max_score": 5, "category": cat,
            "centor_score": centor, "centor_nice_ng84": nice,
            "components": {**f, "age_adjustment": age_adj},
            "source": "McIsaac WJ et al. CMAJ. 1998;158(1):75-83; NICE NG84 (2018)."}


def marburg_heart(age: float, sex: str, known_vascular_disease: int,
                  pain_worse_on_exercise: int, pain_not_reproducible_by_palpation: int,
                  patient_assumes_cardiac: int) -> Dict:
    """Marburg Heart Score — Bösner S et al. CMAJ. 2010;182(12):1295-300.
    Tuổi/giới: nữ ≥65 hoặc nam ≥55 = 1. Ngưỡng 3: 0–2 âm tính, 3–5 dương tính."""
    _age(age, 18, 130)
    if sex not in ("male", "female"):
        raise RiskScoreError("sex phải là 'male' hoặc 'female'.")
    age_sex = 1 if (sex == "female" and age >= 65) or (sex == "male" and age >= 55) else 0
    f = {"known_vascular_disease": known_vascular_disease,
         "pain_worse_on_exercise": pain_worse_on_exercise,
         "pain_not_reproducible_by_palpation": pain_not_reproducible_by_palpation,
         "patient_assumes_cardiac": patient_assumes_cardiac}
    for k, v in f.items():
        f[k] = _bit(k, v)
    total = age_sex + sum(f.values())
    cat = ("âm tính (0–2) — khả năng bệnh mạch vành thấp; kết hợp phán đoán lâm sàng" if total <= 2
           else "dương tính (3–5) — cần đánh giá thêm bệnh mạch vành")
    return {"score": total, "max_score": 5, "category": cat,
            "components": {"age_sex": age_sex, **f},
            "note": "Chỉ cho đau ngực tại chăm sóc ban đầu; KHÔNG dùng để loại trừ hội chứng vành cấp — "
                    "đau ngực cấp nghi HCVC ⇒ chuyển nơi có ECG và troponin.",
            "source": "Bösner S et al. CMAJ. 2010;182(12):1295-300."}


def feverpain(fever_24h: int, purulence: int, attend_within_3_days: int,
              severely_inflamed_tonsils: int, no_cough_or_coryza: int) -> Dict:
    """FeverPAIN — Little P et al. BMJ Open. 2013;3(10):e003943; ngưỡng hành động NICE NG84.
    Mỗi tiêu chí 1 điểm (0–5): 0–1 / 2–3 / 4–5."""
    f = {"fever_24h": fever_24h, "purulence": purulence,
         "attend_within_3_days": attend_within_3_days,
         "severely_inflamed_tonsils": severely_inflamed_tonsils,
         "no_cough_or_coryza": no_cough_or_coryza}
    for k, v in f.items():
        f[k] = _bit(k, v)
    total = sum(f.values())
    if total <= 1:
        cat = "thấp (0–1) — NICE NG84: không kê kháng sinh"
    elif total <= 3:
        cat = "trung gian (2–3) — NICE NG84: cân nhắc không kê hoặc kê đơn dự phòng (back-up)"
    else:
        cat = "cao (4–5) — NICE NG84: cân nhắc kháng sinh ngay hoặc kê đơn dự phòng"
    return {"score": total, "max_score": 5, "category": cat, "components": f,
            "source": "Little P et al. BMJ Open. 2013;3(10):e003943; NICE NG84 (2018)."}


def crb65(confusion: int, rr_high: int, bp_low: int, age: float) -> Dict:
    """CRB-65 — Bauer TT et al. J Intern Med. 2006;260(1):93-101; phân tầng NICE NG250 (2025).
    rr_high: nhịp thở ≥30/phút. bp_low: HA tâm trương ≤60 HOẶC tâm thu <90 mmHg."""
    f = {"confusion": confusion, "rr_high": rr_high, "bp_low": bp_low}
    for k, v in f.items():
        f[k] = _bit(k, v)
    _age(age, 18, 130)
    age_point = 1 if age >= 65 else 0
    total = sum(f.values()) + age_point
    if total == 0:
        cat = "nguy cơ thấp (0) — NICE NG250: chăm sóc ban đầu có dặn dò an toàn"
    elif total <= 2:
        cat = ("nguy cơ trung gian (1–2) — NICE NG250: 1 điểm ⇒ chăm sóc ban đầu có dặn dò an toàn "
               "hoặc chuyển dịch vụ cấp cứu trong ngày/bệnh viện; 2 điểm ⇒ cân nhắc chuyển viện")
    else:
        cat = "nguy cơ cao (3–4) — NICE NG250: cân nhắc chuyển viện"
    return {"score": total, "max_score": 4, "category": cat,
            "components": {**f, "age_geq_65": age_point},
            "note": "Kết hợp phán đoán lâm sàng, SpO₂, bệnh nền, thai kỳ; có ure thì dùng CURB-65.",
            "source": "Bauer TT et al. J Intern Med. 2006;260(1):93-101; NICE NG250 (2025)."}


def ottawa_ankle(malleolar_pain: int, lateral_malleolus_tenderness: int,
                 medial_malleolus_tenderness: int, midfoot_pain: int,
                 fifth_metatarsal_tenderness: int, navicular_tenderness: int,
                 unable_bear_weight: int) -> Dict:
    """Ottawa Ankle and Foot Rules (bản tinh chỉnh) — Stiell IG et al. JAMA. 1993;269(9):1127-32.
    Quy tắc CÓ/KHÔNG, không cộng điểm. Ấn đau xương: bờ sau hoặc đỉnh mắt cá (6 cm dưới);
    không chịu sức nặng: không đi được 4 bước cả ngay sau chấn thương lẫn lúc khám."""
    f = {"malleolar_pain": malleolar_pain,
         "lateral_malleolus_tenderness": lateral_malleolus_tenderness,
         "medial_malleolus_tenderness": medial_malleolus_tenderness,
         "midfoot_pain": midfoot_pain, "fifth_metatarsal_tenderness": fifth_metatarsal_tenderness,
         "navicular_tenderness": navicular_tenderness, "unable_bear_weight": unable_bear_weight}
    for k, v in f.items():
        f[k] = _bit(k, v)
    ankle = bool(f["malleolar_pain"] and (f["lateral_malleolus_tenderness"]
                 or f["medial_malleolus_tenderness"] or f["unable_bear_weight"]))
    foot = bool(f["midfoot_pain"] and (f["fifth_metatarsal_tenderness"]
                or f["navicular_tenderness"] or f["unable_bear_weight"]))
    return {"ankle_xray_indicated": ankle, "foot_xray_indicated": foot,
            "category": ("chỉ định X-quang: " + ", ".join(x for x, b in
                         (("cổ chân", ankle), ("bàn chân", foot)) if b)) if (ankle or foot)
            else "quy tắc âm tính — không cần X-quang thường quy",
            "components": f,
            "note": "Quy tắc độ nhạy cao để LOẠI TRỪ; độ đặc hiệu thấp — dương tính không có nghĩa là gãy.",
            "source": "Stiell IG et al. JAMA. 1993;269(9):1127-32."}


def ottawa_knee(age: float, fibular_head_tenderness: int, isolated_patellar_tenderness: int,
                unable_flex_90: int, unable_bear_weight: int) -> Dict:
    """Ottawa Knee Rule — Stiell IG et al. JAMA. 1996;275(8):611-5 (dẫn xuất Ann Emerg Med 1995).
    ≥1 tiêu chí (tuổi ≥55, ấn đau đầu xương mác, ấn đau khu trú xương bánh chè, không gấp
    được 90°, không đi được 4 bước) ⇒ chỉ định X-quang gối. Dẫn xuất ở NGƯỜI LỚN."""
    _age(age, 0, 130)
    if age < 18:
        raise RiskScoreError("age<18: quy tắc dẫn xuất và kiểm định ở người lớn.")
    f = {"fibular_head_tenderness": fibular_head_tenderness,
         "isolated_patellar_tenderness": isolated_patellar_tenderness,
         "unable_flex_90": unable_flex_90, "unable_bear_weight": unable_bear_weight}
    for k, v in f.items():
        f[k] = _bit(k, v)
    age55 = 1 if age >= 55 else 0
    indicated = bool(age55 or any(f.values()))
    return {"knee_xray_indicated": indicated,
            "category": "chỉ định X-quang gối" if indicated
            else "quy tắc âm tính — không cần X-quang gối",
            "components": {"age_geq_55": age55, **f},
            "source": "Stiell IG et al. JAMA. 1996;275(8):611-5."}


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# BỔ SUNG 21/11/2026 — 11 thang ĐÃ VERIFIED + phân giai đoạn KDIGO G/A.
# Công thức, luật cộng điểm và ngưỡng chép NGUYÊN NGHĨA từ `app/clinical_scores/verified.py`
# (mục `calculation_method` / `interpretation` / `action_thresholds` cùng PMID/DOI của mục đó) —
# không lấy từ trí nhớ. Bối cảnh: bài viết bác sĩ gửi 21/11 nhấn mạnh «AI gọi công thức lập
# trình sẵn thay vì tự nhẩm»; đo cùng ngày 37 thang verified chỉ 15 có bộ tính.
# KHÔNG làm (xem KHONG_CO_BO_TINH dưới): sổ dặn «dùng công cụ chính thức, không nhập hệ số tay»
# (CKD-EPI, MELD-Na, SCORE2/ASCVD) hoặc sổ CHƯA ghi bảng điểm (NEWS2, Glasgow-Blatchford,
# FINDRISC, ô màu KDIGO) — thêm khi bảng điểm được chép vào sổ kèm nguồn.
# ═══════════════════════════════════════════════════════════════════════════

def _so_trong_mien(name: str, value: float, lo: float, hi: float, *, lo_mo: bool = False) -> float:
    """Số hữu hạn trong [lo, hi] (lo_mo=True ⇒ (lo, hi]). Ngoài miền ⇒ từ chối, không kẹp giá trị."""
    _require_finite(name, value)
    if (value <= lo if lo_mo else value < lo) or value > hi:
        khoang = f"({lo}, {hi}]" if lo_mo else f"[{lo}, {hi}]"
        raise RiskScoreError(f"{name}={value} ngoài miền hợp lệ {khoang} — kiểm đơn vị/giá trị nhập.")
    return float(value)


def _muc_0_n(name: str, v: int, n: int) -> int:
    if isinstance(v, bool) or not isinstance(v, int) or v < 0 or v > n:
        raise RiskScoreError(f"{name}={v} phải là số nguyên 0–{n}.")
    return v


def fib4(age: float, ast: float, alt: float, platelets: float, context: str = "masld") -> Dict:
    """FIB-4 = (Tuổi × AST) / (Tiểu cầu × √ALT). AST/ALT U/L; tiểu cầu 10^9/L.
    context="masld" (AASLD 2023, chăm sóc ban đầu): <1,3 nguy cơ thấp; ≥1,3 đánh giá bước 2 (đàn hồi gan/ELF);
    người >65 tuổi dùng ngưỡng >2,0; >2,67 nhiều khả năng xơ hoá tiến triển.
    context="hcv" (Sterling 2006): <1,45 / >3,25.
    Nguồn: Sterling RK, Hepatology 2006 (PMID 16729309); AASLD MASLD 2023."""
    a = _so_trong_mien("age", age, 0, 130)
    ast_ = _so_trong_mien("ast", ast, 0, 20000, lo_mo=True)
    alt_ = _so_trong_mien("alt", alt, 0, 20000, lo_mo=True)
    plt = _so_trong_mien("platelets", platelets, 0, 3000, lo_mo=True)
    val = round(a * ast_ / (plt * math.sqrt(alt_)), 2)
    ghi_chu = []
    if context == "masld":
        nguong_thap = 2.0 if a > 65 else 1.3
        thap = (val <= 2.0) if a > 65 else (val < 1.3)
        if val > 2.67:
            category = "nhiều khả năng xơ hoá tiến triển (>2,67) — đánh giá bước 2/chuyên khoa"
        elif thap:
            them = " cho người >65 tuổi" if a > 65 else ""
            category = f"nguy cơ THẤP xơ hoá tiến triển (ngưỡng {nguong_thap:g}{them})"
        else:
            category = "cần đánh giá bước 2 (đàn hồi gan/ELF)"
    elif context == "hcv":
        if val < 1.45:
            category = "thấp (<1,45 — Sterling 2006, viêm gan C)"
        elif val > 3.25:
            category = "cao (>3,25 — Sterling 2006, viêm gan C)"
        else:
            category = "vùng không xác định (1,45–3,25)"
    else:
        raise RiskScoreError(f"context={context!r} phải là 'masld' hoặc 'hcv'.")
    if a < 35 or a > 65:
        ghi_chu.append("Kém chính xác ở <35 và >65 tuổi (giới hạn ghi trong sổ).")
    return {"score": val, "category": category, "context": context,
            "components": {"age": a, "ast": ast_, "alt": alt_, "platelets": plt}, "notes": ghi_chu,
            "source": "Sterling RK et al. Hepatology. 2006;43:1317-1325 (PMID 16729309); AASLD MASLD 2023."}


def apri(ast: float, ast_uln: float, platelets: float) -> Dict:
    """APRI = [(AST / ULN_AST) × 100] / Tiểu cầu (10^9/L). WHO: >0,5 gợi ý xơ hoá đáng kể; >1,0 gợi ý xơ gan.
    ULN là của CHÍNH phòng xét nghiệm — không có giá trị mặc định. Nguồn: Wai CT, Hepatology 2003 (PMID 12883497)."""
    ast_ = _so_trong_mien("ast", ast, 0, 20000, lo_mo=True)
    uln = _so_trong_mien("ast_uln", ast_uln, 0, 500, lo_mo=True)
    plt = _so_trong_mien("platelets", platelets, 0, 3000, lo_mo=True)
    val = round((ast_ / uln) * 100 / plt, 2)
    if val > 1.0:
        category = "gợi ý xơ gan (>1,0 — WHO; cân nhắc theo bối cảnh)"
    elif val > 0.5:
        category = "gợi ý xơ hoá đáng kể (>0,5 — WHO)"
    else:
        category = "không vượt ngưỡng WHO (≤0,5)"
    return {"score": val, "category": category,
            "components": {"ast": ast_, "ast_uln": uln, "platelets": plt},
            "notes": ["Độ chính xác trung bình; phối hợp FIB-4/đàn hồi gan khi có."],
            "source": "Wai CT et al. Hepatology. 2003;38:518-526 (PMID 12883497)."}


def anion_gap(na: float, cl: float, hco3: float, albumin_g_l: float | None = None) -> Dict:
    """AG = Na⁺ − (Cl⁻ + HCO₃⁻) (mmol/L). Hiệu chỉnh albumin: +2,5 cho mỗi 10 g/L albumin giảm dưới 40 g/L.
    Khoảng bình thường phụ thuộc phương pháp đo của phòng xét nghiệm (thường ~8–12) ⇒ công cụ KHÔNG tự phán cao/thấp.
    Nguồn: Kraut JA, Madias NE. Clin J Am Soc Nephrol 2007 (PMID 17699401)."""
    na_ = _so_trong_mien("na", na, 80, 220)
    cl_ = _so_trong_mien("cl", cl, 40, 180)
    hco3_ = _so_trong_mien("hco3", hco3, 0, 70)
    ag = round(na_ - (cl_ + hco3_), 1)
    res = {"score": ag, "unit": "mmol/L",
           "category": "so với khoảng tham chiếu của phòng xét nghiệm (thường ~8–12 mmol/L)",
           "components": {"na": na_, "cl": cl_, "hco3": hco3_}, "notes": [],
           "source": "Kraut JA, Madias NE. Clin J Am Soc Nephrol. 2007;2:162-174 (PMID 17699401)."}
    if albumin_g_l is not None:
        alb = _require_finite("albumin_g_l", albumin_g_l)
        if alb < 10 or alb > 70:
            raise RiskScoreError(f"albumin_g_l={alb} ngoài [10, 70] — đơn vị là g/L (nhập 35, không phải 3,5 g/dL).")
        hieu_chinh = round(ag + 2.5 * (40 - alb) / 10, 1) if alb < 40 else ag
        res["albumin_corrected"] = hieu_chinh
        res["components"]["albumin_g_l"] = alb
    else:
        res["notes"].append("Chưa hiệu chỉnh albumin — sổ dặn LUÔN hiệu chỉnh ở người giảm albumin.")
    return res


def homa_ir(glucose: float, insulin: float, glucose_unit: str = "mmol") -> Dict:
    """HOMA-IR = (Glucose mmol/L × Insulin µU/mL) / 22,5 hoặc (Glucose mg/dL × Insulin) / 405.
    KHÔNG có ngưỡng chẩn đoán phổ quát (theo sổ) ⇒ chỉ trả giá trị. Không dùng khi đang điều trị insulin.
    Nguồn: Matthews DR, Diabetologia 1985 (PMID 3899825)."""
    if glucose_unit == "mmol":
        g = _so_trong_mien("glucose", glucose, 1, 50)
        val = g * _so_trong_mien("insulin", insulin, 0, 2000, lo_mo=True) / 22.5
    elif glucose_unit == "mgdl":
        g = _so_trong_mien("glucose", glucose, 18, 900)
        val = g * _so_trong_mien("insulin", insulin, 0, 2000, lo_mo=True) / 405
    else:
        raise RiskScoreError(f"glucose_unit={glucose_unit!r} phải là 'mmol' hoặc 'mgdl'.")
    return {"score": round(val, 2),
            "category": "không có ngưỡng phổ quát — diễn giải theo khoảng tham chiếu địa phương",
            "components": {"glucose": g, "glucose_unit": glucose_unit, "insulin": insulin},
            "notes": ["Không dùng khi đang điều trị insulin; biến thiên giữa các xét nghiệm insulin."],
            "source": "Matthews DR et al. Diabetologia. 1985;28:412-419 (PMID 3899825)."}


def maddrey_df(pt_patient: float, pt_control: float, bilirubin_mg_dl: float) -> Dict:
    """mDF = 4,6 × (PT bệnh nhân − PT chứng, giây) + Bilirubin (mg/dL). ≥32: viêm gan rượu NẶNG.
    Bilirubin phải ở mg/dL (µmol/L ⇒ đổi trước). Nguồn: Maddrey WC, Gastroenterology 1978 (PMID 352788)."""
    ptp = _so_trong_mien("pt_patient", pt_patient, 5, 200)
    ptc = _so_trong_mien("pt_control", pt_control, 5, 60)
    bili = _so_trong_mien("bilirubin_mg_dl", bilirubin_mg_dl, 0, 80)
    val = round(4.6 * (ptp - ptc) + bili, 1)
    category = ("NẶNG (≥32) — cân nhắc corticosteroid nếu không chống chỉ định; loại trừ nhiễm khuẩn/XHTH trước; "
                "đánh giá đáp ứng bằng Lille sau 7 ngày") if val >= 32 else "dưới ngưỡng nặng (<32)"
    return {"score": val, "category": category,
            "components": {"pt_patient": ptp, "pt_control": ptc, "bilirubin_mg_dl": bili},
            "source": "Maddrey WC et al. Gastroenterology. 1978;75:193-199 (PMID 352788)."}


def phq9(items: list[int]) -> Dict:
    """PHQ-9: 9 mục 0–3, tổng 0–27. 0–4 tối thiểu · 5–9 nhẹ · 10–14 trung bình · 15–19 trung bình-nặng · 20–27 nặng.
    ≥10: cân nhắc trầm cảm cần điều trị. Mục 9 (ý tưởng tự sát) >0 ⇒ ĐÁNH GIÁ NGUY CƠ NGAY.
    Nguồn: Kroenke K, J Gen Intern Med 2001 (PMID 11556941)."""
    if len(items) != 9:
        raise RiskScoreError(f"PHQ-9 cần đúng 9 mục (nhận {len(items)}).")
    v = [_muc_0_n(f"muc_{i + 1}", x, 3) for i, x in enumerate(items)]
    t = sum(v)
    category = ("tối thiểu" if t <= 4 else "nhẹ" if t <= 9 else "trung bình" if t <= 14
                else "trung bình-nặng" if t <= 19 else "nặng")
    canh_bao = []
    if t >= 10:
        canh_bao.append("≥10: cân nhắc trầm cảm nặng cần điều trị (sàng lọc — không thay chẩn đoán).")
    if v[8] > 0:
        canh_bao.append("MỤC 9 DƯƠNG TÍNH (ý tưởng tự sát/tự hại) — ĐÁNH GIÁ NGUY CƠ NGAY (sang-loc-co-do).")
    return {"score": t, "max_score": 27, "category": category, "components": {"muc": v}, "alerts": canh_bao,
            "source": "Kroenke K, Spitzer RL, Williams JBW. J Gen Intern Med. 2001;16:606-613 (PMID 11556941)."}


def gad7(items: list[int]) -> Dict:
    """GAD-7: 7 mục 0–3, tổng 0–21. 0–4 tối thiểu · 5–9 nhẹ · 10–14 trung bình · 15–21 nặng;
    ≥10 gợi ý cần đánh giá thêm.
    Điểm thấp KHÔNG loại trừ (độ nhạy hạn chế — sổ). Nguồn: Spitzer RL, Arch Intern Med 2006 (PMID 16717171)."""
    if len(items) != 7:
        raise RiskScoreError(f"GAD-7 cần đúng 7 mục (nhận {len(items)}).")
    v = [_muc_0_n(f"muc_{i + 1}", x, 3) for i, x in enumerate(items)]
    t = sum(v)
    category = "tối thiểu" if t <= 4 else "nhẹ" if t <= 9 else "trung bình" if t <= 14 else "nặng"
    return {"score": t, "max_score": 21, "category": category, "components": {"muc": v},
            "alerts": ["≥10: ngưỡng gợi ý cần đánh giá/điều trị thêm."] if t >= 10 else [],
            "notes": ["Điểm thấp không loại trừ rối loạn lo âu."],
            "source": "Spitzer RL et al. Arch Intern Med. 2006;166:1092-1097 (PMID 16717171)."}


def audit_c(q1: int, q2: int, q3: int, sex: str) -> Dict:
    """AUDIT-C: 3 câu, mỗi câu 0–4 (tổng 0–12). Dương tính ≥4 (nam) / ≥3 (nữ) ⇒ tư vấn ngắn/đánh giá AUDIT đầy đủ.
    Nguồn: Bush K, Arch Intern Med 1998 (PMID 9738608)."""
    v = [_muc_0_n("q1", q1, 4), _muc_0_n("q2", q2, 4), _muc_0_n("q3", q3, 4)]
    if sex not in ("male", "female"):
        raise RiskScoreError(f"sex={sex!r} phải là 'male' hoặc 'female'.")
    t = sum(v)
    nguong = 4 if sex == "male" else 3
    duong = t >= nguong
    return {"score": t, "max_score": 12, "positive": duong,
            "category": (f"DƯƠNG TÍNH (≥{nguong} ở {'nam' if sex == 'male' else 'nữ'}) — "
                         "tư vấn ngắn/đánh giá AUDIT đầy đủ"
                         if duong else f"âm tính (<{nguong})"),
            "components": {"q1": v[0], "q2": v[1], "q3": v[2], "sex": sex},
            "source": "Bush K et al. Arch Intern Med. 1998;158:1789-1795 (PMID 9738608)."}


def frail_scale(fatigue: int, resistance: int, ambulation: int, illnesses: int, loss_of_weight: int) -> Dict:
    """FRAIL: 5 mục, mỗi mục 1 điểm (0–5). 0 khoẻ · 1–2 tiền suy yếu · 3–5 suy yếu
    (≥3 ⇒ CGA, rà đa thuốc/té ngã/dinh dưỡng). illnesses = >5 bệnh; loss_of_weight = sụt >5% trong năm.
    Nguồn: Morley JE, J Nutr Health Aging 2012 (PMID 22836700)."""
    f = {"fatigue": fatigue, "resistance": resistance, "ambulation": ambulation,
         "illnesses": illnesses, "loss_of_weight": loss_of_weight}
    for k, v in f.items():
        f[k] = _bit(k, v)
    t = sum(f.values())
    category = ("khoẻ (robust)" if t == 0 else "tiền suy yếu" if t <= 2
                else "suy yếu (frail) — đánh giá lão khoa toàn diện (CGA), rà đa thuốc, té ngã, dinh dưỡng")
    return {"score": t, "max_score": 5, "category": category, "components": f,
            "source": "Morley JE et al. J Nutr Health Aging. 2012;16:601-608 (PMID 22836700)."}


def timi_ua_nstemi(age_ge_65: int, ge_3_cad_risk_factors: int, known_cad_ge_50: int, aspirin_7d: int,
                   ge_2_angina_24h: int, st_deviation_ge_05mm: int, positive_marker: int) -> Dict:
    """TIMI (UA/NSTEMI): 7 tiêu chí, mỗi tiêu chí 1 điểm (0–7). Điểm cao (≥3) gợi ý chiến lược xâm lấn sớm —
    LUÔN kết hợp lâm sàng + ECG + troponin. Nguồn: Antman EM, JAMA 2000 (PMID 10938172)."""
    f = {"age_ge_65": age_ge_65, "ge_3_cad_risk_factors": ge_3_cad_risk_factors, "known_cad_ge_50": known_cad_ge_50,
         "aspirin_7d": aspirin_7d, "ge_2_angina_24h": ge_2_angina_24h,
         "st_deviation_ge_05mm": st_deviation_ge_05mm, "positive_marker": positive_marker}
    for k, v in f.items():
        f[k] = _bit(k, v)
    t = sum(f.values())
    category = ("điểm cao (≥3) — gợi ý chiến lược can thiệp xâm lấn sớm; kết hợp lâm sàng + ECG + troponin"
                if t >= 3 else "điểm thấp (<3) — vẫn đánh giá theo lâm sàng/ECG/troponin")
    return {"score": t, "max_score": 7, "category": category, "components": f,
            "notes": ["Đơn giản hoá; GRACE phân biệt tốt hơn ở một số nhóm (sổ)."],
            "source": "Antman EM et al. JAMA. 2000;284:835-842 (PMID 10938172)."}


def gold_abe(moderate_exacerbations_12m: int, hospitalized_exacerbations_12m: int,
             mmrc: int | None = None, cat: int | None = None) -> Dict:
    """GOLD ABE (2023+, sổ ghi GOLD 2025): E = ≥2 đợt cấp vừa HOẶC ≥1 đợt nhập viện (bất kể triệu chứng);
    còn lại A (mMRC 0–1 / CAT <10) hoặc B (mMRC ≥2 / CAT ≥10). Cần ít nhất một trong mMRC/CAT. Hai thước đo cho
    hai nhóm KHÁC NHAU ⇒ KHÔNG tự chọn (trả nhóm None, ghi lệch) — bác sĩ quyết. Chỉ cho bệnh nhân COPD đã xác định
    bằng hô hấp ký; phục vụ điều trị KHỞI ĐẦU. Nguồn: GOLD Report 2025."""
    mod = _muc_0_n("moderate_exacerbations_12m", moderate_exacerbations_12m, 50)
    hosp = _muc_0_n("hospitalized_exacerbations_12m", hospitalized_exacerbations_12m, 50)
    if mmrc is None and cat is None:
        raise RiskScoreError("Cần mMRC hoặc CAT để phân nhóm A/B.")
    trieu_chung = {}
    if mmrc is not None:
        trieu_chung["mmrc_nhieu"] = _muc_0_n("mmrc", mmrc, 4) >= 2
    if cat is not None:
        trieu_chung["cat_nhieu"] = _muc_0_n("cat", cat, 40) >= 10
    ghi_chu = []
    if mod >= 2 or hosp >= 1:
        nhom = "E"
    elif len(set(trieu_chung.values())) > 1:
        nhom = None
        ghi_chu.append("mMRC và CAT cho hai nhóm khác nhau (A vs B) — công cụ không tự chọn; bác sĩ quyết.")
    else:
        nhom = "B" if next(iter(trieu_chung.values())) else "A"
    dieu_tri = {"A": "1 thuốc giãn phế quản", "B": "LABA+LAMA",
                "E": "LABA+LAMA; có thể bắt đầu bộ ba LABA+LAMA+ICS ngay nếu eosinophil ≥300 (GOLD 2025)"}
    return {"group": nhom, "category": (f"nhóm {nhom} — khởi đầu: {dieu_tri[nhom]}" if nhom else "chưa phân được A/B"),
            "components": {"moderate_exacerbations_12m": mod, "hospitalized_exacerbations_12m": hosp,
                           "mmrc": mmrc, "cat": cat},
            "notes": ghi_chu + ["Chỉ cho COPD đã xác định bằng hô hấp ký; phân nhóm khởi đầu, không thay theo dõi."],
            "source": "GOLD Report 2025 (ABE)."}


def kdigo_stage(egfr: float, acr_mg_g: float | None = None) -> Dict:
    """Phân giai đoạn KDIGO từ eGFR ĐÃ CÓ (mL/phút/1,73m²) và albumin niệu ACR (mg/g) — KHÔNG tính eGFR (sổ dặn dùng
    công cụ đã thẩm định cho phương trình CKD-EPI 2021). G1 ≥90 · G2 60–89 · G3a 45–59 · G3b 30–44 · G4 15–29 · G5 <15;
    A1 <30 · A2 30–300 · A3 >300. G3b–G5 hoặc A3 ⇒ cân nhắc chuyên khoa thận + rà liều thuốc theo eGFR.
    Ô màu nguy cơ (heat map) KHÔNG trả — sổ chưa ghi bảng ô. Nguồn: Inker LA, NEJM 2021 (PMID 34554658); KDIGO 2024."""
    e = _so_trong_mien("egfr", egfr, 0, 250)
    g = ("G1" if e >= 90 else "G2" if e >= 60 else "G3a" if e >= 45 else "G3b" if e >= 30
         else "G4" if e >= 15 else "G5")
    a = None
    if acr_mg_g is not None:
        acr = _so_trong_mien("acr_mg_g", acr_mg_g, 0, 50000)
        a = "A1" if acr < 30 else "A2" if acr <= 300 else "A3"
    canh_bao = []
    if g in ("G3b", "G4", "G5") or a == "A3":
        canh_bao.append("G3b–G5 hoặc A3: chuyển/nhắc chuyên khoa thận tùy bối cảnh; "
                        "rà hiệu chỉnh liều thuốc theo eGFR.")
    return {"g_stage": g, "a_stage": a, "category": f"{g}{' ' + a if a else ''}", "alerts": canh_bao,
            "components": {"egfr": e, "acr_mg_g": acr_mg_g},
            "notes": ["eGFR phải lấy từ công cụ/phòng xét nghiệm đã thẩm định (CKD-EPI 2021); "
                      "ô màu nguy cơ tra bảng KDIGO 2024."],
            "source": "Inker LA et al. N Engl J Med. 2021;385:1737-1749 (PMID 34554658); KDIGO 2024 CKD."}


# ── Sổ bao phủ: MỌI thang verified phải nằm ở ĐÚNG MỘT trong hai bảng dưới (test chốt) ─────────────
# Thêm thang verified mới ⇒ phải khai ở đây: có bộ tính, hoặc lý do chưa có — không để agent lặng lẽ tự nhẩm.
BO_TINH_THEO_SCORE_ID: Dict[str, str] = {
    "curb65": "curb65", "cha2ds2_vasc": "cha2ds2vasc", "has_bled": "hasbled", "wells_dvt": "wells-dvt",
    "wells_pe": "wells-pe", "perc": "perc", "qsofa": "qsofa", "child_pugh": "child-pugh",
    "centor_mcisaac": "centor-mcisaac", "marburg_heart": "marburg", "ottawa_ankle": "ottawa-ankle",
    "ottawa_knee": "ottawa-knee", "feverpain": "feverpain", "crb65": "crb65",
    "fib4": "fib4", "apri": "apri", "anion_gap": "anion-gap", "homa_ir": "homa-ir", "maddrey_df": "maddrey",
    "phq9": "phq9", "gad7": "gad7", "audit_c": "audit-c", "frail_scale": "frail", "timi": "timi",
    "gold_abe": "gold-abe",
}
KHONG_CO_BO_TINH: Dict[str, str] = {
    "ckd_epi": ("sổ dặn KHÔNG tự nhập hệ số tay — dùng công cụ đã thẩm định cho eGFR; "
                "phân giai đoạn G/A từ eGFR có sẵn: kdigo-stage"),
    "kdigo_grid": "sổ chưa ghi bảng ô màu G×A; phân giai đoạn G/A: kdigo-stage",
    "meld_na": "sổ dặn dùng công cụ chính thức (MELD-Na/MELD 3.0), không nhập hệ số tay",
    "ascvd_pce": "hệ số hồi quy đa biến — dùng máy tính chính thức",
    "score2": "hệ số hồi quy đa biến tái chuẩn hoá theo vùng — dùng máy tính chính thức",
    "score2_diabetes": "hệ số hồi quy đa biến — dùng máy tính chính thức",
    "news2": "sổ chưa ghi bảng điểm từng thông số (RCP 2017) — dùng biểu đồ NEWS2 chính thức",
    "blatchford": "sổ chưa ghi bảng điểm (Blatchford 2000) — dùng bảng gốc/công cụ chính thức",
    "findrisc": "sổ chưa ghi bảng điểm từng mục (Lindström 2003) — dùng phiếu FINDRISC chính thức",
    "nyha": "phân loại lâm sàng do bác sĩ chọn — không có phép tính",
    "beers": "bộ TIÊU CHÍ thuốc (không phải thang tính điểm) — ke-don-an-toan tra",
    "stopp_start": "bộ TIÊU CHÍ thuốc (không phải thang tính điểm) — ke-don-an-toan tra",
}


def _print(result: Dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"\n{DISCLAIMER}")


def main() -> int:
    # Vá 2026-07-04 (red-team): tránh crash UnicodeEncodeError khi in DISCLAIMER tiếng
    # Việt trên console Windows mặc định (cp1252) — kể cả khi số liệu đã tính đúng.
    _gate_contract.ensure_utf8_stdout()
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
    md.add_argument("--dialysis-2x-past-week", type=_parse_bool_cli,
                    default=False, dest="dialysis")
    md.add_argument("--json", action="store_true")

    wd = sub.add_parser("wells-dvt")
    for name in ("active-cancer", "paralysis-or-cast", "bedridden-or-surgery",
                 "deep-vein-tenderness", "entire-leg-swollen", "calf-swelling-3cm",
                 "pitting-edema", "collateral-veins", "previous-dvt", "alternative-dx-as-likely"):
        wd.add_argument(f"--{name}", type=int, required=True, dest=name.replace("-", "_"))
    wd.add_argument("--json", action="store_true")

    cm = sub.add_parser("centor-mcisaac")
    for name in ("fever-over-38", "absence-of-cough", "tender-anterior-nodes",
                 "tonsillar-swelling-exudate"):
        cm.add_argument(f"--{name}", type=int, required=True, dest=name.replace("-", "_"))
    cm.add_argument("--age", type=float, required=True)
    cm.add_argument("--json", action="store_true")

    mh = sub.add_parser("marburg")
    mh.add_argument("--age", type=float, required=True)
    mh.add_argument("--sex", required=True, choices=["male", "female"])
    for name in ("known-vascular-disease", "pain-worse-on-exercise",
                 "pain-not-reproducible-by-palpation", "patient-assumes-cardiac"):
        mh.add_argument(f"--{name}", type=int, required=True, dest=name.replace("-", "_"))
    mh.add_argument("--json", action="store_true")

    fp = sub.add_parser("feverpain")
    for name in ("fever-24h", "purulence", "attend-within-3-days",
                 "severely-inflamed-tonsils", "no-cough-or-coryza"):
        fp.add_argument(f"--{name}", type=int, required=True, dest=name.replace("-", "_"))
    fp.add_argument("--json", action="store_true")

    cr = sub.add_parser("crb65")
    cr.add_argument("--confusion", type=int, required=True)
    cr.add_argument("--rr-high", type=int, required=True, dest="rr_high")
    cr.add_argument("--bp-low", type=int, required=True, dest="bp_low")
    cr.add_argument("--age", type=float, required=True)
    cr.add_argument("--json", action="store_true")

    oa = sub.add_parser("ottawa-ankle")
    for name in ("malleolar-pain", "lateral-malleolus-tenderness", "medial-malleolus-tenderness",
                 "midfoot-pain", "fifth-metatarsal-tenderness", "navicular-tenderness",
                 "unable-bear-weight"):
        oa.add_argument(f"--{name}", type=int, required=True, dest=name.replace("-", "_"))
    oa.add_argument("--json", action="store_true")

    ok = sub.add_parser("ottawa-knee")
    ok.add_argument("--age", type=float, required=True)
    for name in ("fibular-head-tenderness", "isolated-patellar-tenderness", "unable-flex-90",
                 "unable-bear-weight"):
        ok.add_argument(f"--{name}", type=int, required=True, dest=name.replace("-", "_"))
    ok.add_argument("--json", action="store_true")

    # ── bổ sung 21/11/2026 ──
    f4 = sub.add_parser("fib4")
    f4.add_argument("--age", type=float, required=True)
    f4.add_argument("--ast", type=float, required=True)
    f4.add_argument("--alt", type=float, required=True)
    f4.add_argument("--platelets", type=float, required=True, help="10^9/L")
    f4.add_argument("--context", choices=["masld", "hcv"], default="masld")
    f4.add_argument("--json", action="store_true")

    ap_ = sub.add_parser("apri")
    ap_.add_argument("--ast", type=float, required=True)
    ap_.add_argument("--ast-uln", type=float, required=True, dest="ast_uln", help="giới hạn trên AST của phòng XN")
    ap_.add_argument("--platelets", type=float, required=True, help="10^9/L")
    ap_.add_argument("--json", action="store_true")

    ag = sub.add_parser("anion-gap")
    ag.add_argument("--na", type=float, required=True)
    ag.add_argument("--cl", type=float, required=True)
    ag.add_argument("--hco3", type=float, required=True)
    ag.add_argument("--albumin-g-l", type=float, default=None, dest="albumin_g_l", help="g/L (vd 35)")
    ag.add_argument("--json", action="store_true")

    hi = sub.add_parser("homa-ir")
    hi.add_argument("--glucose", type=float, required=True)
    hi.add_argument("--insulin", type=float, required=True, help="µU/mL")
    hi.add_argument("--glucose-unit", choices=["mmol", "mgdl"], required=True, dest="glucose_unit")
    hi.add_argument("--json", action="store_true")

    mdf = sub.add_parser("maddrey")
    mdf.add_argument("--pt-patient", type=float, required=True, dest="pt_patient")
    mdf.add_argument("--pt-control", type=float, required=True, dest="pt_control")
    mdf.add_argument("--bilirubin-mg-dl", type=float, required=True, dest="bilirubin_mg_dl")
    mdf.add_argument("--json", action="store_true")

    p9 = sub.add_parser("phq9")
    p9.add_argument("--muc", type=int, nargs=9, required=True, metavar="0-3")
    p9.add_argument("--json", action="store_true")

    g7 = sub.add_parser("gad7")
    g7.add_argument("--muc", type=int, nargs=7, required=True, metavar="0-3")
    g7.add_argument("--json", action="store_true")

    ac = sub.add_parser("audit-c")
    for name in ("q1", "q2", "q3"):
        ac.add_argument(f"--{name}", type=int, required=True)
    ac.add_argument("--sex", required=True, choices=["male", "female"])
    ac.add_argument("--json", action="store_true")

    fr = sub.add_parser("frail")
    for name in ("fatigue", "resistance", "ambulation", "illnesses", "loss-of-weight"):
        fr.add_argument(f"--{name}", type=int, required=True, dest=name.replace("-", "_"))
    fr.add_argument("--json", action="store_true")

    ti = sub.add_parser("timi")
    for name in ("age-ge-65", "ge-3-cad-risk-factors", "known-cad-ge-50", "aspirin-7d",
                 "ge-2-angina-24h", "st-deviation-ge-05mm", "positive-marker"):
        ti.add_argument(f"--{name}", type=int, required=True, dest=name.replace("-", "_"))
    ti.add_argument("--json", action="store_true")

    ga = sub.add_parser("gold-abe")
    ga.add_argument("--moderate-exacerbations-12m", type=int, required=True, dest="moderate_exacerbations_12m")
    ga.add_argument("--hospitalized-exacerbations-12m", type=int, required=True, dest="hospitalized_exacerbations_12m")
    ga.add_argument("--mmrc", type=int, default=None)
    ga.add_argument("--cat", type=int, default=None)
    ga.add_argument("--json", action="store_true")

    ks = sub.add_parser("kdigo-stage")
    ks.add_argument("--egfr", type=float, required=True)
    ks.add_argument("--acr-mg-g", type=float, default=None, dest="acr_mg_g")
    ks.add_argument("--json", action="store_true")

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
        elif args.cmd == "wells-dvt":
            res = wells_dvt(args.active_cancer, args.paralysis_or_cast, args.bedridden_or_surgery,
                            args.deep_vein_tenderness, args.entire_leg_swollen,
                            args.calf_swelling_3cm, args.pitting_edema, args.collateral_veins,
                            args.previous_dvt, args.alternative_dx_as_likely)
        elif args.cmd == "centor-mcisaac":
            res = centor_mcisaac(args.fever_over_38, args.absence_of_cough,
                                 args.tender_anterior_nodes, args.tonsillar_swelling_exudate,
                                 args.age)
        elif args.cmd == "marburg":
            res = marburg_heart(args.age, args.sex, args.known_vascular_disease,
                                args.pain_worse_on_exercise,
                                args.pain_not_reproducible_by_palpation,
                                args.patient_assumes_cardiac)
        elif args.cmd == "feverpain":
            res = feverpain(args.fever_24h, args.purulence, args.attend_within_3_days,
                            args.severely_inflamed_tonsils, args.no_cough_or_coryza)
        elif args.cmd == "crb65":
            res = crb65(args.confusion, args.rr_high, args.bp_low, args.age)
        elif args.cmd == "ottawa-ankle":
            res = ottawa_ankle(args.malleolar_pain, args.lateral_malleolus_tenderness,
                               args.medial_malleolus_tenderness, args.midfoot_pain,
                               args.fifth_metatarsal_tenderness, args.navicular_tenderness,
                               args.unable_bear_weight)
        elif args.cmd == "ottawa-knee":
            res = ottawa_knee(args.age, args.fibular_head_tenderness,
                              args.isolated_patellar_tenderness, args.unable_flex_90,
                              args.unable_bear_weight)
        elif args.cmd == "fib4":
            res = fib4(args.age, args.ast, args.alt, args.platelets, args.context)
        elif args.cmd == "apri":
            res = apri(args.ast, args.ast_uln, args.platelets)
        elif args.cmd == "anion-gap":
            res = anion_gap(args.na, args.cl, args.hco3, args.albumin_g_l)
        elif args.cmd == "homa-ir":
            res = homa_ir(args.glucose, args.insulin, args.glucose_unit)
        elif args.cmd == "maddrey":
            res = maddrey_df(args.pt_patient, args.pt_control, args.bilirubin_mg_dl)
        elif args.cmd == "phq9":
            res = phq9(args.muc)
        elif args.cmd == "gad7":
            res = gad7(args.muc)
        elif args.cmd == "audit-c":
            res = audit_c(args.q1, args.q2, args.q3, args.sex)
        elif args.cmd == "frail":
            res = frail_scale(args.fatigue, args.resistance, args.ambulation, args.illnesses,
                              args.loss_of_weight)
        elif args.cmd == "timi":
            res = timi_ua_nstemi(args.age_ge_65, args.ge_3_cad_risk_factors, args.known_cad_ge_50,
                                 args.aspirin_7d, args.ge_2_angina_24h, args.st_deviation_ge_05mm,
                                 args.positive_marker)
        elif args.cmd == "gold-abe":
            res = gold_abe(args.moderate_exacerbations_12m, args.hospitalized_exacerbations_12m,
                           args.mmrc, args.cat)
        elif args.cmd == "kdigo-stage":
            res = kdigo_stage(args.egfr, args.acr_mg_g)
    except RiskScoreError as e:
        print(f"❌ LỖI: {e}")
        return 1
    _print(res, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
