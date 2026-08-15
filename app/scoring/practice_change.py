"""Practice Change Score (0–100).

Đo khả năng làm thay đổi chẩn đoán/điều trị/theo dõi/chuyển tuyến, đặc biệt ở
ngoại trú và các nhóm dễ tổn thương (cao tuổi/CKD/bệnh gan/đa bệnh/đa thuốc),
an toàn thuốc, thay đổi liều/chống chỉ định/tương tác, lựa chọn kháng sinh,
thang điểm/cut-off.
"""
from __future__ import annotations

from typing import Dict, Tuple


def _text(item: Dict, *keys: str) -> str:
    return " ".join(str(item.get(k, "") or "") for k in keys).lower()


def practice_change_score(item: Dict) -> Tuple[float, Dict[str, float]]:
    breakdown: Dict[str, float] = {}
    text = _text(item, "title", "abstract", "document_type", "safety_signal")
    study_type = (item.get("study_type") or "").lower()

    # Nền theo nguồn: guideline/cảnh báo quản lý mặc định có tiềm năng đổi thực hành
    if study_type == "guideline":
        breakdown["guideline_base"] = 50
    elif study_type == "regulatory_alert":
        breakdown["regulatory_base"] = 50
    elif study_type == "systematic_review":
        breakdown["sr_base"] = 35
    elif study_type == "rct":
        breakdown["rct_base"] = 35
    else:
        breakdown["other_base"] = 15

    # Tín hiệu thay đổi điều trị/chẩn đoán/theo dõi/chuyển tuyến
    change_kw = ("recommend", "should", "no longer", "first-line", "khuyến cáo",
                 "thay đổi", "ngưng", "chỉ định", "chống chỉ định", "đổi", "ưu tiên")
    if any(k in text for k in change_kw):
        breakdown["change_signal"] = 10

    # Ngoại trú
    if any(k in text for k in ("outpatient", "primary care", "ngoại trú", "community")):
        breakdown["outpatient"] = 8

    # Nhóm dễ tổn thương
    if any(k in text for k in ("older", "elderly", "ckd", "renal", "hepatic", "cirrhosis",
                               "polypharmacy", "cao tuổi", "thận", "gan", "đa thuốc")):
        breakdown["vulnerable_pop"] = 6

    # An toàn thuốc / liều / tương tác
    if item.get("safety_signal") or any(k in text for k in ("dose adjustment", "contraindicat",
                                                            "interaction", "liều", "tương tác")):
        breakdown["drug_safety"] = 8

    # Kháng sinh
    if any(k in text for k in ("antibiotic", "antimicrobial", "stewardship", "kháng sinh", "aware")):
        breakdown["antibiotic"] = 6

    # Thang điểm/cut-off
    if any(k in text for k in ("score", "cut-off", "cutoff", "threshold", "thang điểm", "cha2ds2")):
        breakdown["score_tool"] = 5

    # Trừ điểm cho nguồn không nên đổi thực hành
    if study_type in ("preprint", "animal_invitro", "case_series",
                      "retrospective_single_center", "narrative_review", "editorial"):
        breakdown["weak_design_penalty"] = -25

    score = max(0.0, min(100.0, sum(breakdown.values())))
    return round(score, 1), breakdown
