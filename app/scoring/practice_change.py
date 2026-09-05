"""Practice Change Score (0–100).

Đo khả năng làm thay đổi chẩn đoán/điều trị/theo dõi/chuyển tuyến, đặc biệt ở
ngoại trú và các nhóm dễ tổn thương (cao tuổi/CKD/bệnh gan/đa bệnh/đa thuốc),
an toàn thuốc, thay đổi liều/chống chỉ định/tương tác, lựa chọn kháng sinh,
thang điểm/cut-off.
"""
from __future__ import annotations

import re
from typing import Dict, Tuple

from app.services.filtering import is_antibiotic_text

# SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 19) — từ khóa "gan" (bệnh
# gan/tiếng Việt) trước đây được kiểm bằng substring thô (`"gan" in text`),
# khớp BỪA bên trong hàng loạt từ tiếng Anh chứa chuỗi con "gan": "organ",
# "organic", "reorganize", "afghan", "morgan", "arrogant"... — một bài hoàn
# toàn không liên quan bệnh gan/nhóm dễ tổn thương (vd bàn về "organ
# transplant" hay "organic compound") vẫn bị cộng breakdown["vulnerable_pop"].
# `\bgan\b` yêu cầu ranh giới từ ở CẢ hai đầu nên vẫn khớp đúng "gan" đứng
# một mình trong các cụm tiếng Việt ("bệnh gan", "suy gan", "xơ gan", "viêm
# gan" — luôn cách nhau bằng khoảng trắng) mà KHÔNG khớp bừa vào giữa một từ
# tiếng Anh liền mạch như "organ" (trước "gan" trong "organ" là "r", không
# phải ranh giới từ).
_GAN_RE = re.compile(r"\bgan\b")


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

    # Nhóm dễ tổn thương ("gan" kiểm riêng bằng regex ranh giới từ — xem _GAN_RE).
    if any(k in text for k in ("older", "elderly", "ckd", "renal", "hepatic", "cirrhosis",
                               "polypharmacy", "cao tuổi", "thận", "đa thuốc")) or _GAN_RE.search(text):
        breakdown["vulnerable_pop"] = 6

    # An toàn thuốc / liều / tương tác
    if item.get("safety_signal") or any(k in text for k in ("dose adjustment", "contraindicat",
                                                            "interaction", "liều", "tương tác")):
        breakdown["drug_safety"] = 8

    # Kháng sinh
    # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 19) — module này từng
    # tự duy trì tuple từ khóa RIÊNG kết thúc bằng "aware" (đơn), khớp bừa
    # bên trong bất kỳ câu tiếng Anh nào chứa "aware"/"awareness" không liên
    # quan kháng sinh (vd "Clinicians should be aware of falls risk in
    # elderly patients"). Đây CHÍNH LÀ bug đã được vá ở
    # app.services.filtering.ANTIBIOTIC_KEYWORDS (vòng 14, "aware" ->
    # "aware classification") và ở app/reports/safety_reports.py (vòng 18)
    # — nhưng module này KHÔNG được cập nhật theo vì tự chép danh sách độc
    # lập thay vì gọi hàm chuẩn. Đổi sang gọi thẳng is_antibiotic_text() để
    # không còn bản sao trôi dạt (đúng cách weekly_ebm.py đã làm đúng từ đầu).
    if is_antibiotic_text(item.get("title"), item.get("abstract"),
                          item.get("document_type"), item.get("safety_signal")):
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
