"""Runtime lâm sàng V7 ở chế độ draft/review."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Mapping

from app.core.policy_engine import PolicyEngine
from app.safety.red_flag_engine import SafetySignal, detect_red_flags


@dataclass(frozen=True)
class ClinicalDraft:
    run_id: str
    summary: str
    red_flags: List[SafetySignal] = field(default_factory=list)
    required_review: bool = True
    disclaimer: str = "Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng."


def build_clinical_draft(
    run_id: str,
    case_text: str,
    claim_ids: List[str],
    context: Mapping[str, object],
) -> ClinicalDraft:
    red_flags = detect_red_flags(case_text)
    decision = PolicyEngine().evaluate({
        "lane": "clinical",
        "text": case_text,
        "claim_text": "clinical draft",
        "evidence_trace_ids": list(context.get("evidence_trace_ids") or []),
        "red_flag_unresolved": bool(red_flags),
    })
    if not decision.allowed and red_flags:
        return ClinicalDraft(
            run_id=run_id,
            summary="Dừng workflow thường quy vì có cờ đỏ; cần bác sĩ đánh giá ngay.",
            red_flags=red_flags,
        )
    if not claim_ids:
        return ClinicalDraft(run_id=run_id, summary="Chưa đủ claim đã thẩm định để tạo khuyến nghị.")
    return ClinicalDraft(
        run_id=run_id,
        summary="Bản nháp hỗ trợ quyết định lâm sàng, cần review trước khi áp dụng.",
        red_flags=red_flags,
    )
