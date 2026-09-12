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
    if not decision.allowed:
        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #87) — bản gốc chỉ
        # chặn khi `not decision.allowed AND red_flags`, nên một block của
        # PolicyEngine vì lý do KHÁC cờ đỏ (PII trong case_text — EBM-V7-P001,
        # thiếu evidence_trace_ids — EBM-V7-P002...) mà không kèm cờ đỏ nào bị
        # BỎ QUA HOÀN TOÀN — hàm rơi thẳng xuống nhánh sinh "Bản nháp hỗ trợ
        # quyết định lâm sàng" như thể PolicyEngine chưa từng chặn gì. Sửa:
        # MỌI quyết định `not decision.allowed` đều chặn workflow thường quy;
        # nhánh cờ đỏ giữ nguyên thông điệp riêng (test cũ phụ thuộc câu chữ
        # này), các lý do khác lấy nguyên văn message từ PolicyViolation.
        if red_flags:
            return ClinicalDraft(
                run_id=run_id,
                summary="Dừng workflow thường quy vì có cờ đỏ; cần bác sĩ đánh giá ngay.",
                red_flags=red_flags,
            )
        reasons = "; ".join(v.message for v in decision.blockers) or "PolicyEngine chặn workflow."
        return ClinicalDraft(
            run_id=run_id,
            summary=f"Dừng workflow thường quy: {reasons}",
            red_flags=red_flags,
        )
    if not claim_ids:
        return ClinicalDraft(run_id=run_id, summary="Chưa đủ claim đã thẩm định để tạo khuyến nghị.")
    return ClinicalDraft(
        run_id=run_id,
        summary="Bản nháp hỗ trợ quyết định lâm sàng, cần review trước khi áp dụng.",
        red_flags=red_flags,
    )
