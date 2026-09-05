"""Rule engine vận hành cho Chronic Care Phase 3A synthetic shadow mode."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Mapping

from app.chronic_care.constants import ENVIRONMENT
from app.chronic_care.synthetic_cases import SyntheticChronicCareCase


@dataclass(frozen=True)
class ChronicCareRule:
    rule_id: str
    rule_version: str
    purpose: str
    scope: str
    inputs: List[str]
    output: str
    owner_role: str
    approval_requirement: str
    feature_flag_requirement: str
    evidence_requirement: str
    effective_date: str
    review_date: str
    status: str
    approved_by: str
    clinical_decision: bool = False
    patient_facing_output: bool = False
    emr_write: bool = False


@dataclass(frozen=True)
class RuleAction:
    rule_id: str
    action_type: str
    task_type: str = ""
    priority: str = "MEDIUM"
    owner_role: str = "care_coordinator"
    blocked_reason: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)


CHRONIC_CARE_RULES: Dict[str, ChronicCareRule] = {
    "CC-001": ChronicCareRule(
        "CC-001", "2026.06", "Detect overdue synthetic follow-up", ENVIRONMENT,
        ["next_review_due_at"], "Create REVIEW_OVERDUE_CASE task", "care_coordinator",
        "approved_shadow_rule", "no_risky_flags", "not_required", "2026-06-18", "2026-09-18",
        "approved_for_test", "system_owner_shadow",
    ),
    "CC-002": ChronicCareRule(
        "CC-002", "2026.06", "Detect stale pending care-plan draft", ENVIRONMENT,
        ["care_plan_draft_status"], "Create REQUEST_PHYSICIAN_REVIEW task", "physician",
        "approved_shadow_rule", "no_risky_flags", "not_required", "2026-06-18", "2026-09-18",
        "approved_for_test", "system_owner_shadow",
    ),
    "CC-003": ChronicCareRule(
        "CC-003", "2026.06", "Escalate RED risk draft for review", ENVIRONMENT,
        ["risk_label"], "Create high-priority physician review task and dashboard alert", "physician",
        "approved_shadow_rule", "no_risky_flags", "not_required", "2026-06-18", "2026-09-18",
        "approved_for_test", "system_owner_shadow",
    ),
    "CC-004": ChronicCareRule(
        "CC-004", "2026.06", "Detect medication review due", ENVIRONMENT,
        ["medication_review_status"], "Create MEDICATION_LIST_REVIEW task", "pharmacist",
        "approved_shadow_rule", "no_risky_flags", "not_required", "2026-06-18", "2026-09-18",
        "approved_for_test", "system_owner_shadow",
    ),
    "CC-005": ChronicCareRule(
        "CC-005", "2026.06", "Detect post-discharge synthetic flag", ENVIRONMENT,
        ["post_discharge_flag"], "Create POST_DISCHARGE_REVIEW task", "care_coordinator",
        "physician_review_required", "no_risky_flags", "not_required", "2026-06-18", "2026-09-18",
        "approved_for_test", "system_owner_shadow",
    ),
}


def evaluate_chronic_care_rules(case: SyntheticChronicCareCase, now: datetime | None = None) -> List[RuleAction]:
    now = now or datetime.now(timezone.utc)
    status = case.synthetic_status_fields
    actions: List[RuleAction] = []
    # SỬA 2026-07-23 (vòng lặp kiểm tra-hoàn thiện vòng 11, phát hiện LOW):
    # trước đây không kiểm tra key tồn tại/định dạng hợp lệ trước khi parse —
    # nếu thiếu "next_review_due_at" (str(None) = "None") hoặc giá trị không
    # phải ISO datetime, fromisoformat() ném ValueError không được bắt, sập
    # toàn bộ evaluate_chronic_care_rules()/seed_synthetic_cases(). Hiện tại
    # được che chắn vì build_synthetic_case_pack() luôn set trường này cho
    # mọi ca tổng hợp, nhưng bọc try/except để an toàn nếu hàm này được tái sử
    # dụng với nguồn dữ liệu khác không đảm bảo trường này (fail-closed: bỏ
    # qua rule CC-001 thay vì sập cả luồng, không coi thiếu dữ liệu = quá hạn).
    raw_due_at = status.get("next_review_due_at")
    due_at = None
    if raw_due_at:
        try:
            due_at = datetime.fromisoformat(str(raw_due_at))
        except ValueError:
            due_at = None
    if due_at is not None and due_at < now:
        actions.append(RuleAction("CC-001", "CREATE_TASK", "REVIEW_OVERDUE_CASE", _priority_for(case.synthetic_risk_label)))
    if case.synthetic_care_plan_draft_status == "PENDING_REVIEW":
        actions.append(RuleAction("CC-002", "CREATE_TASK", "REQUEST_PHYSICIAN_REVIEW", "MEDIUM", "physician"))
    if case.synthetic_risk_label == "RED":
        actions.append(RuleAction("CC-003", "CREATE_TASK", "REQUEST_PHYSICIAN_REVIEW", "HIGH", "physician", metadata={"dashboard_alert": True, "safety_queue_item": True}))
    if status.get("medication_review_status") == "OVERDUE":
        actions.append(RuleAction("CC-004", "CREATE_TASK", "MEDICATION_LIST_REVIEW", "MEDIUM", "pharmacist"))
    if status.get("post_discharge_flag") is True:
        actions.append(RuleAction("CC-005", "CREATE_TASK", "POST_DISCHARGE_REVIEW", "HIGH", "care_coordinator", metadata={"physician_review_required": True}))
    return actions


def assert_rule_approved_for_test(rule_id: str, action: RuleAction | None = None) -> None:
    rule = CHRONIC_CARE_RULES[rule_id]
    if not rule.approved_by or rule.status not in {"approved_for_test", "approved_for_shadow"}:
        raise PermissionError(f"Rule {rule_id} is not approved for test/shadow execution")
    # SỬA 2026-09-04 (Workflow đối kháng đa-agent) — trường `approval_requirement`
    # của ChronicCareRule (vd CC-005: "physician_review_required", khác 4 luật
    # còn lại đều "approved_shadow_rule") CHƯA TỪNG được hàm này đọc — chỉ
    # `approved_by`/`status` được kiểm, nên khai báo yêu cầu MẠNH HƠN của một
    # luật không tạo ra khác biệt nào so với luật thường. Đây KHÔNG phải lỗi
    # cô lập: CC-005 cũng tự gắn `metadata={"physician_review_required": True}`
    # vào chính RuleAction nó sinh ra (đặt tên GIỐNG HỆT giá trị của
    # `approval_requirement`) — dấu hiệu rõ ràng ý định ban đầu là hai nơi khai
    # phải KHỚP NHAU, chỉ là chưa có chỗ nào đối chiếu. Nay đối chiếu: luật khai
    # `physician_review_required` mà action sinh ra KHÔNG mang cờ tương ứng
    # (hoặc ngược lại) là hai nơi khai LỆCH NHAU — chặn cứng thay vì âm thầm bỏ
    # qua sự lệch đó, đúng nguyên tắc BH39 (một trường được khai báo phải có
    # nơi kiểm THẬT, không chỉ nằm trong dataclass để trang trí).
    if action is not None:
        rule_needs_physician = rule.approval_requirement == "physician_review_required"
        action_flags_physician = bool(action.metadata.get("physician_review_required"))
        if rule_needs_physician != action_flags_physician:
            raise PermissionError(
                f"Rule {rule_id} khai approval_requirement={rule.approval_requirement!r} "
                f"nhưng action tạo ra {'CÓ' if action_flags_physician else 'KHÔNG'} mang cờ "
                "physician_review_required trong metadata — hai nơi khai lệch nhau"
            )


def _priority_for(risk_label: str) -> str:
    if risk_label == "RED":
        return "HIGH"
    if risk_label == "YELLOW":
        return "MEDIUM"
    return "LOW"
