"""Reliability Tier (A/B/C/D).

A: Có thể cân nhắc thay đổi thực hành ngay nếu phù hợp bối cảnh.
B: Cần đọc toàn văn/guideline gốc trước khi triển khai.
C: Chỉ theo dõi, chưa thay đổi thực hành.
D: Loại khỏi báo cáo chính.
"""
from __future__ import annotations

from typing import Dict

from app.utils.kho_luu_tru import kho_luu_tru_da_nang

# Các thiết kế bị loại khỏi phần "thay đổi thực hành" -> D.
# SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 19) — thiếu
# "expert_opinion": app.scoring.evidence_quality.DESIGN_BASE xếp
# expert_opinion=20 (yếu, cùng nhóm với editorial=15/narrative_review=25),
# nhưng tập này trước đây bỏ sót nó -> một bản ghi expert_opinion không rơi
# vào nhánh chặn Tier D ở đây, trong khi editorial/narrative_review (cùng
# nhóm chứng cứ yếu) bị chặn. Thêm vào để khớp đúng thứ bậc DESIGN_BASE.
EXCLUDED_DESIGNS = {
    "preprint", "animal_invitro", "editorial", "narrative_review", "expert_opinion",
}


def reliability_tier(item: Dict, evidence_q: float, practice_c: float) -> str:
    study_type = (item.get("study_type") or "").lower()

    # D: loại trừ rõ ràng
    if study_type in EXCLUDED_DESIGNS:
        return "D"
    if item.get("reason_for_exclusion"):
        return "D"
    # Kho lưu trữ đa năng (Zenodo/figshare/OSF…, 25/10/2026): không phải nơi phát hành ⇒ tối đa C, bất kể study_type
    # hay điểm đã lưu — câu trả lời AI trên Zenodo từng lên A «actionable» và vào hub EBM_MASTER (18/10/2026).
    if kho_luu_tru_da_nang(item.get("doi"), item.get("journal_or_organization")):
        return "C"

    # A: nguồn rất mạnh + tiềm năng đổi thực hành cao.
    # regulatory_alert KHÔNG nằm đây: cảnh báo cơ quan quản lý cần đọc toàn văn (tối đa Tier B),
    # tránh 1 tin feed ngắn tự lên "actionable".
    strong_source = study_type in ("guideline", "systematic_review", "rct")
    if strong_source and evidence_q >= 75 and practice_c >= 60:
        return "A"

    # B: đủ mạnh nhưng cần đọc toàn văn/guideline gốc
    if evidence_q >= 60 and practice_c >= 45:
        return "B"

    # C: chỉ theo dõi
    return "C"
