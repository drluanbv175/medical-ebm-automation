"""Service layer cho Chronic Care Phase 3A synthetic shadow workflows."""
from __future__ import annotations

import csv
import io
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Mapping, Optional
from uuid import uuid4

from app.chronic_care.audit import ChronicCareAuditTrail, default_audit_trail, log_chronic_care_event
from app.chronic_care.constants import ENVIRONMENT, RISKY_FLAGS_MUST_STAY_FALSE
from app.chronic_care.rules import assert_rule_approved_for_test, evaluate_chronic_care_rules
from app.chronic_care.synthetic_cases import SyntheticChronicCareCase, build_synthetic_case_pack, validate_synthetic_case_pack
from app.core.approval_service import ApprovalCenter
from app.core.feature_flags import merge_feature_flags
from app.core.policy_engine import PolicyEngine, contains_pii_text
from app.core.run_packet import ApprovalStatus, InputCompleteness, Lane, PiiStatus, RiskLevel, new_run_packet


@dataclass
class ChronicCareEnrollment:
    id: str
    patient_reference_id: str
    program_code: str
    status: str
    enrolled_at: str
    assigned_physician_id: str
    assigned_care_coordinator_id: str
    current_risk_status: str
    next_review_due_at: str
    last_reviewed_at: str = ""
    created_by: str = "system"
    environment: str = ENVIRONMENT
    version: int = 1


@dataclass
class ChronicCareReview:
    id: str
    enrollment_id: str
    review_type: str
    review_status: str
    review_reason: str
    review_due_at: str
    physician_confirmation_required: bool
    environment: str = ENVIRONMENT
    version: int = 1


@dataclass
class ChronicCareTask:
    id: str
    enrollment_id: str
    task_type: str
    priority: str
    status: str
    assigned_role: str
    due_at: str
    completed_at: str = ""
    completion_note: str = ""
    escalation_level: int = 0
    escalated_at: str = ""
    closed_by: str = ""
    blocked_reason: str = ""
    environment: str = ENVIRONMENT
    version: int = 1


@dataclass
class ChronicCareRiskDraft:
    id: str
    enrollment_id: str
    risk_label: str
    risk_status: str
    risk_factors: List[str]
    trigger_summary: str
    suggested_non_clinical_actions: List[str]
    requires_physician_review: bool = True
    reviewed_by: str = ""
    approved_by: str = ""
    rejected_by: str = ""
    rejection_reason: str = ""
    environment: str = ENVIRONMENT
    version: int = 1


@dataclass
class ChronicCarePlanDraft:
    id: str
    enrollment_id: str
    status: str
    problem_list_reference: str
    goal_summary: str
    follow_up_summary: str
    pending_review_items: List[str] = field(default_factory=list)
    clinical_content_reference_ids: List[str] = field(default_factory=list)
    claim_reference_ids: List[str] = field(default_factory=list)
    evidence_reference_ids: List[str] = field(default_factory=list)
    physician_review_required: bool = True
    blocked_reason: str = ""
    approved_by: str = ""
    rejected_by: str = ""
    environment: str = ENVIRONMENT
    version: int = 1


@dataclass(frozen=True)
class ChronicCareTimelineEvent:
    id: str
    enrollment_id: str
    event_type: str
    event_timestamp: str
    source_type: str
    source_reference_id: str
    summary: str
    created_by: str
    environment: str = ENVIRONMENT
    version: int = 1


@dataclass(frozen=True)
class ChronicCareQualityMetric:
    id: str
    metric_code: str
    metric_name: str
    metric_category: str
    numerator: int
    denominator: int
    value: float
    measurement_period_start: str
    measurement_period_end: str
    program_code: str = "ALL"
    environment: str = ENVIRONMENT
    generated_by: str = "system"
    version: int = 1


@dataclass(frozen=True)
class ChronicCareDashboardState:
    total_enrollments: int
    enrollments_by_program: Mapping[str, int]
    risk_counts: Mapping[str, int]
    open_tasks: int
    overdue_tasks: int
    physician_review_pending: int
    care_plan_draft_pending: int
    post_discharge_synthetic_cases: int
    quality_metrics_count: int
    feature_flags: Mapping[str, bool]
    shadow_mode_status: str
    production_block_status: str
    care_coordinator_queue: List[Mapping[str, object]]
    physician_review_queue: List[Mapping[str, object]]
    quality_metrics: List[ChronicCareQualityMetric]
    safety_counters: Mapping[str, int]


class ChronicCareService:
    def __init__(
        self,
        *,
        audit_trail: Optional[ChronicCareAuditTrail] = None,
        policy_engine: Optional[PolicyEngine] = None,
        approval_center: Optional[ApprovalCenter] = None,
        feature_flags: Optional[Mapping[str, bool]] = None,
    ) -> None:
        self.audit_trail = audit_trail or default_audit_trail()
        self.policy_engine = policy_engine or PolicyEngine()
        self.approval_center = approval_center or ApprovalCenter()
        self.feature_flags = merge_feature_flags(feature_flags)
        for flag in RISKY_FLAGS_MUST_STAY_FALSE:
            self.feature_flags[flag] = False
        self.run_packet = new_run_packet(
            Lane.CLINICAL,
            "Phase 3A chronic care synthetic shadow pilot",
            risk_level=RiskLevel.MODERATE,
            input_completeness=InputCompleteness.SUFFICIENT_FOR_DRAFT,
            pii_status=PiiStatus.NONE_DETECTED,
            approval_status=ApprovalStatus.PENDING_PHYSICIAN,
            feature_flags=self.feature_flags,
            metadata={"module": "chronic_care_phase_3a", "environment": ENVIRONMENT},
        )
        self.enrollments: Dict[str, ChronicCareEnrollment] = {}
        self.reviews: Dict[str, ChronicCareReview] = {}
        self.tasks: Dict[str, ChronicCareTask] = {}
        self.risk_drafts: Dict[str, ChronicCareRiskDraft] = {}
        self.plan_drafts: Dict[str, ChronicCarePlanDraft] = {}
        self.timeline: List[ChronicCareTimelineEvent] = []
        self.blocked_exports = 0
        self.patient_facing_output_without_approval = 0
        self.clinical_release_flag_bypass = 0
        self.approval_bypass = 0
        self.unverified_evidence_released = 0
        self.recommendation_without_claim_id_released = 0
        self.audit_event_missing = 0

    def seed_synthetic_cases(self, cases: Optional[List[SyntheticChronicCareCase]] = None) -> None:
        cases = cases or build_synthetic_case_pack()
        validate_synthetic_case_pack(cases)
        for case in cases:
            enrollment = self.create_enrollment(case)
            self.create_review(enrollment.id, "INITIAL_REVIEW", "Synthetic initial shadow review")
            self.create_task(enrollment.id, "CARE_PLAN_REVIEW", "MEDIUM", "care_coordinator")
            self.create_risk_draft(enrollment.id, case.synthetic_risk_label, ["synthetic_status"], "Synthetic risk label only")
            self.create_care_plan_draft(
                enrollment.id,
                evidence_reference_ids=[] if case.synthetic_status_fields.get("evidence_status") == "MISSING" else ["ev_synthetic_verified"],
                claim_reference_ids=[] if case.synthetic_status_fields.get("claim_status") == "MISSING" else ["claim_synthetic_verified"],
            )
            for action in evaluate_chronic_care_rules(case):
                assert_rule_approved_for_test(action.rule_id, action)
                if action.action_type == "CREATE_TASK":
                    self.create_task(enrollment.id, action.task_type, action.priority, action.owner_role)
                    if action.task_type == "REVIEW_OVERDUE_CASE":
                        self.add_timeline(enrollment.id, "FOLLOW_UP_OVERDUE", "rule", action.rule_id, "Synthetic follow-up overdue detected")
                    if action.metadata.get("safety_queue_item"):
                        self.add_timeline(enrollment.id, "ESCALATION_CREATED", "rule", action.rule_id, "Synthetic RED risk review item")
                    # SỬA 2026-09-04 — cờ metadata này trước đây được SINH ra
                    # (rules.py::CC-005) nhưng KHÔNG NƠI NÀO đọc, nên "yêu cầu
                    # bác sĩ review" chỉ tồn tại trong dataclass, không tạo dấu
                    # vết nào trong timeline/audit trail của ca bệnh.
                    if action.metadata.get("physician_review_required"):
                        self.add_timeline(enrollment.id, "PHYSICIAN_REVIEW_REQUIRED", "rule", action.rule_id, "Synthetic post-discharge task requires physician review per rule approval_requirement")

    def create_enrollment(self, case: SyntheticChronicCareCase, actor: str = "system") -> ChronicCareEnrollment:
        self._ensure_no_pii(case.searchable_text())
        enrollment = ChronicCareEnrollment(
            id=f"cc_enr_{uuid4().hex}",
            patient_reference_id=case.patient_reference_id,
            program_code=case.program_code,
            status="ACTIVE",
            enrolled_at=_now(),
            assigned_physician_id="physician_shadow",
            assigned_care_coordinator_id="care_coord_shadow",
            current_risk_status=case.synthetic_risk_label,
            next_review_due_at=str(case.synthetic_status_fields.get(
                "next_review_due_at",
                (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
            )),
            created_by=actor,
        )
        self.enrollments[enrollment.id] = enrollment
        self.add_timeline(enrollment.id, "PROGRAM_ENROLLED", "synthetic_case", case.patient_reference_id, "Synthetic case enrolled")
        self._audit(actor, "create_enrollment", "ChronicCareEnrollment", enrollment.id, after=asdict(enrollment))
        return enrollment

    def create_review(self, enrollment_id: str, review_type: str, reason: str) -> ChronicCareReview:
        review = ChronicCareReview(
            id=f"cc_rev_{uuid4().hex}",
            enrollment_id=enrollment_id,
            review_type=review_type,
            review_status="PENDING_REVIEW",
            review_reason=reason,
            review_due_at=(datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            physician_confirmation_required=True,
        )
        self.reviews[review.id] = review
        self.add_timeline(enrollment_id, "REVIEW_CREATED", "review", review.id, reason)
        self._audit("system", "create_review", "ChronicCareReview", review.id, after=asdict(review))
        return review

    def create_task(self, enrollment_id: str, task_type: str, priority: str, assigned_role: str) -> ChronicCareTask:
        task = ChronicCareTask(
            id=f"cc_task_{uuid4().hex}",
            enrollment_id=enrollment_id,
            task_type=task_type,
            priority=priority,
            status="OPEN",
            assigned_role=assigned_role,
            due_at=(datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        )
        self.tasks[task.id] = task
        self.add_timeline(enrollment_id, "TASK_CREATED", "task", task.id, task_type)
        self._audit("system", "create_task", "ChronicCareTask", task.id, after=asdict(task))
        return task

    def complete_task(self, task_id: str, actor: str = "care_coordinator_shadow", note: str = "Completed in shadow mode") -> ChronicCareTask:
        task = self.tasks[task_id]
        before = asdict(task)
        task.status = "COMPLETED"
        task.completed_at = _now()
        task.completion_note = note
        task.closed_by = actor
        self.add_timeline(task.enrollment_id, "TASK_COMPLETED", "task", task.id, "Task completed in shadow mode")
        self._audit(actor, "complete_task", "ChronicCareTask", task.id, before=before, after=asdict(task))
        return task

    def escalate_task(self, task_id: str, actor: str = "system") -> ChronicCareTask:
        task = self.tasks[task_id]
        before = asdict(task)
        task.escalation_level += 1
        task.escalated_at = _now()
        task.assigned_role = "physician"
        self.add_timeline(task.enrollment_id, "ESCALATION_CREATED", "task", task.id, "Task escalated for physician review")
        self._audit(actor, "escalate_task", "ChronicCareTask", task.id, before=before, after=asdict(task))
        return task

    def create_risk_draft(self, enrollment_id: str, risk_label: str, risk_factors: List[str], trigger_summary: str) -> ChronicCareRiskDraft:
        draft = ChronicCareRiskDraft(
            id=f"cc_risk_{uuid4().hex}",
            enrollment_id=enrollment_id,
            risk_label=risk_label,
            risk_status="PENDING_REVIEW" if risk_label in {"RED", "YELLOW"} else "DRAFT",
            risk_factors=list(risk_factors),
            trigger_summary=trigger_summary,
            suggested_non_clinical_actions=["Needs physician review"] if risk_label in {"RED", "YELLOW"} else ["Routine operational tracking"],
        )
        self.risk_drafts[draft.id] = draft
        self.add_timeline(enrollment_id, "RISK_DRAFT_CREATED", "risk_draft", draft.id, trigger_summary)
        self._audit("system", "create_risk_draft", "ChronicCareRiskDraft", draft.id, after=asdict(draft))
        return draft

    def review_risk_draft(self, risk_draft_id: str, *, reviewer_role: str, approve: bool, note: str = "") -> ChronicCareRiskDraft:
        if reviewer_role != "physician":
            self.approval_bypass += 1
            raise PermissionError("Only physician can approve/reject Phase 3A risk draft")
        draft = self.risk_drafts[risk_draft_id]
        before = asdict(draft)
        approval = self.approval_center.submit(self.run_packet.run_id, "chronic_care_risk_draft", draft.trigger_summary)
        if approve:
            self.approval_center.approve(approval.approval_id, "physician", note)
            draft.risk_status = "APPROVED_FOR_SHADOW"
            draft.approved_by = reviewer_role
        else:
            self.approval_center.reject(approval.approval_id, "physician", note or "Rejected in shadow review")
            draft.risk_status = "REJECTED"
            draft.rejected_by = reviewer_role
            draft.rejection_reason = note
        draft.reviewed_by = reviewer_role
        self.add_timeline(draft.enrollment_id, "RISK_DRAFT_REVIEWED", "risk_draft", draft.id, draft.risk_status)
        self._audit(reviewer_role, "review_risk_draft", "ChronicCareRiskDraft", draft.id, before=before, after=asdict(draft), approval=approval.approval_id)
        return draft

    def create_care_plan_draft(
        self,
        enrollment_id: str,
        *,
        evidence_reference_ids: Optional[List[str]] = None,
        claim_reference_ids: Optional[List[str]] = None,
    ) -> ChronicCarePlanDraft:
        evidence_ids = list(evidence_reference_ids or [])
        claim_ids = list(claim_reference_ids or [])
        blocked_reason = "" if evidence_ids and claim_ids else "EVIDENCE_INSUFFICIENT_OR_UNVERIFIED"
        draft = ChronicCarePlanDraft(
            id=f"cc_plan_{uuid4().hex}",
            enrollment_id=enrollment_id,
            status="PENDING_REVIEW" if not blocked_reason else "BLOCKED",
            problem_list_reference="synthetic_program_labels_only",
            goal_summary="Shadow tracking goals only; no treatment recommendation.",
            follow_up_summary="Operational follow-up tracking only.",
            pending_review_items=[] if not blocked_reason else [blocked_reason],
            claim_reference_ids=claim_ids,
            evidence_reference_ids=evidence_ids,
            blocked_reason=blocked_reason,
        )
        self.plan_drafts[draft.id] = draft
        self.add_timeline(enrollment_id, "CARE_PLAN_DRAFT_CREATED", "care_plan_draft", draft.id, draft.status)
        self._audit("system", "create_care_plan_draft", "ChronicCarePlanDraft", draft.id, after=asdict(draft), blocked=blocked_reason)
        return draft

    def approve_care_plan_draft(self, plan_draft_id: str, *, reviewer_role: str = "physician") -> ChronicCarePlanDraft:
        if reviewer_role != "physician":
            self.approval_bypass += 1
            raise PermissionError("Only physician can approve Phase 3A care-plan draft")
        draft = self.plan_drafts[plan_draft_id]
        before = asdict(draft)
        blocked = self._care_plan_blocked_reason(draft)
        if blocked:
            draft.status = "BLOCKED"
            draft.blocked_reason = blocked
            # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 17) — bản gốc
            # tăng `unverified_evidence_released` (đọc bởi dashboard_state()
            # để quyết định production_block_status="SHADOW PILOT BLOCKED")
            # ngay TẠI NHÁNH BLOCK — tức đúng lúc hệ thống NGĂN THÀNH CÔNG
            # việc duyệt, không có gì được "released" cả. Dòng raise ngay bên
            # dưới đảm bảo draft KHÔNG BAO GIỜ chuyển sang APPROVED_FOR_SHADOW
            # trong nhánh này, nên đây không phải một vi phạm an toàn — nó là
            # cổng đang hoạt động đúng thiết kế. Hệ quả: mọi lần bác sĩ (theo
            # đúng gợi ý "required_action": "physician_review" của
            # `_physician_row()`) mở một draft đang BLOCKED để duyệt sẽ tự
            # kích một báo động sai ở TẦNG DASHBOARD, không phân biệt được với
            # một lần bypass thật (`approval_bypass`/`clinical_release_flag_
            # bypass`). Tái hiện: seed_synthetic_cases() → approve_care_plan_
            # draft(một draft BLOCKED) → PermissionError đúng như thiết kế,
            # nhưng dashboard_state().production_block_status vẫn nhảy sang
            # "SHADOW PILOT BLOCKED" dù KHÔNG có gì được duyệt/phát hành. Bỏ
            # dòng tăng bộ đếm này — các bộ đếm vi phạm THẬT khác
            # (`approval_bypass`, `clinical_release_flag_bypass` ở
            # `_care_plan_blocked_reason()`) không đổi.
            self._audit(reviewer_role, "approve_care_plan_draft_blocked", "ChronicCarePlanDraft", draft.id, before=before, after=asdict(draft), blocked=blocked)
            raise PermissionError(blocked)
        approval = self.approval_center.submit(self.run_packet.run_id, "chronic_care_plan_draft", draft.goal_summary)
        self.approval_center.approve(approval.approval_id, "physician", "Approved for shadow only")
        draft.status = "APPROVED_FOR_SHADOW"
        draft.approved_by = reviewer_role
        self.add_timeline(draft.enrollment_id, "CARE_PLAN_DRAFT_APPROVED", "care_plan_draft", draft.id, "Approved for shadow only")
        self._audit(reviewer_role, "approve_care_plan_draft", "ChronicCarePlanDraft", draft.id, before=before, after=asdict(draft), approval=approval.approval_id)
        return draft

    def quality_metrics(self) -> List[ChronicCareQualityMetric]:
        total = len(self.enrollments)
        open_tasks = len([task for task in self.tasks.values() if task.status == "OPEN"])
        completed_tasks = len([task for task in self.tasks.values() if task.status == "COMPLETED"])
        escalated_tasks = len([task for task in self.tasks.values() if task.escalation_level > 0])
        reviewed_risk = len([draft for draft in self.risk_drafts.values() if draft.risk_status in {"APPROVED_FOR_SHADOW", "REJECTED"}])
        reviewed_plans = len([draft for draft in self.plan_drafts.values() if draft.status in {"APPROVED_FOR_SHADOW", "REJECTED"}])
        evidence_complete = len([draft for draft in self.plan_drafts.values() if draft.evidence_reference_ids and draft.claim_reference_ids])
        start = datetime.now(timezone.utc).replace(day=1).isoformat()
        end = datetime.now(timezone.utc).isoformat()
        return [
            _metric("enrollment_completeness", "Enrollment completeness rate", total, total, start, end),
            _metric("task_completion", "Task completion rate", completed_tasks, max(len(self.tasks), 1), start, end),
            _metric("task_escalation", "Task escalation rate", escalated_tasks, max(len(self.tasks), 1), start, end),
            _metric("risk_draft_review_completion", "Risk draft review completion rate", reviewed_risk, max(len(self.risk_drafts), 1), start, end),
            _metric("care_plan_draft_review_completion", "Care-plan draft review completion rate", reviewed_plans, max(len(self.plan_drafts), 1), start, end),
            _metric("evidence_complete_draft", "Evidence-complete draft rate", evidence_complete, max(len(self.plan_drafts), 1), start, end),
            _metric("approval_bypass", "Approval bypass count", self.approval_bypass, 1, start, end, raw=True),
            _metric("pii_export", "PII export count", self.blocked_exports, 1, start, end, raw=True),
            _metric("clinical_release_flag_bypass", "Clinical release flag bypass count", self.clinical_release_flag_bypass, 1, start, end, raw=True),
            _metric("patient_facing_output_without_approval", "Patient-facing output without approval count", self.patient_facing_output_without_approval, 1, start, end, raw=True),
            _metric("open_tasks", "Open task count", open_tasks, 1, start, end, raw=True),
        ]

    def dashboard_state(self) -> ChronicCareDashboardState:
        risk_counts = {risk: len([d for d in self.risk_drafts.values() if d.risk_label == risk]) for risk in ["GREEN", "YELLOW", "RED", "UNASSESSED"]}
        by_program: Dict[str, int] = {}
        for enrollment in self.enrollments.values():
            by_program[enrollment.program_code] = by_program.get(enrollment.program_code, 0) + 1
        metrics = self.quality_metrics()
        safety_counters = {
            "approval_bypass": self.approval_bypass,
            "pii_export": self.blocked_exports,
            "clinical_release_flag_bypass": self.clinical_release_flag_bypass,
            "patient_facing_output_without_approval": self.patient_facing_output_without_approval,
            "unverified_evidence_released": self.unverified_evidence_released,
            "recommendation_without_claim_id_released": self.recommendation_without_claim_id_released,
            "audit_event_missing": self.audit_event_missing,
        }
        return ChronicCareDashboardState(
            total_enrollments=len(self.enrollments),
            enrollments_by_program=by_program,
            risk_counts=risk_counts,
            open_tasks=len([t for t in self.tasks.values() if t.status == "OPEN"]),
            overdue_tasks=len([t for t in self.tasks.values() if t.status == "OPEN" and _is_task_overdue(t)]),
            physician_review_pending=len([t for t in self.tasks.values() if t.status == "OPEN" and t.assigned_role == "physician"]),
            care_plan_draft_pending=len([p for p in self.plan_drafts.values() if p.status == "PENDING_REVIEW"]),
            post_discharge_synthetic_cases=len([e for e in self.enrollments.values() if e.program_code == "POST_DISCHARGE_REVIEW_PROGRAM"]),
            quality_metrics_count=len(metrics),
            feature_flags=self.feature_flags,
            shadow_mode_status="synthetic_shadow_read_only",
            production_block_status="SHADOW PILOT BLOCKED" if any(safety_counters.values()) else "production_blocked_by_design",
            care_coordinator_queue=[self._task_row(task) for task in self.tasks.values() if task.assigned_role in {"care_coordinator", "pharmacist"}],
            physician_review_queue=[self._physician_row(enrollment) for enrollment in self.enrollments.values()],
            quality_metrics=metrics,
            safety_counters=safety_counters,
        )

    def export_aggregate_json(self, actor: str = "quality_shadow") -> Mapping[str, object]:
        state = self.dashboard_state()
        payload = {
            "environment": ENVIRONMENT,
            "total_enrollments": state.total_enrollments,
            "enrollments_by_program": dict(state.enrollments_by_program),
            "risk_counts": dict(state.risk_counts),
            "quality_metrics": [
                {
                    "metric_code": metric.metric_code,
                    "metric_name": metric.metric_name,
                    "metric_category": metric.metric_category,
                    "numerator": metric.numerator,
                    "denominator": metric.denominator,
                    "value": metric.value,
                    "program_code": metric.program_code,
                    "environment": metric.environment,
                    "version": metric.version,
                }
                for metric in state.quality_metrics
            ],
            "safety_counters": dict(state.safety_counters),
        }
        self._policy_export(payload)
        self._audit(actor, "export_aggregate_report", "ChronicCareAggregateExport", "aggregate_json", after=payload)
        return payload

    def export_aggregate_csv(self, actor: str = "quality_shadow") -> str:
        payload = self.export_aggregate_json(actor)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["metric_code", "metric_name", "numerator", "denominator", "value"])
        writer.writeheader()
        for metric in payload["quality_metrics"]:  # type: ignore[index]
            writer.writerow({
                "metric_code": metric["metric_code"],
                "metric_name": metric["metric_name"],
                "numerator": metric["numerator"],
                "denominator": metric["denominator"],
                "value": metric["value"],
            })
        return output.getvalue()

    def attempt_export_with_pii_like_text(self) -> None:
        self._policy_export({"unsafe_probe": "0901234567", "environment": ENVIRONMENT})

    def attempt_patient_facing_output(self) -> None:
        self.patient_facing_output_without_approval += 1
        raise PermissionError("Patient-facing output is disabled in Phase 3A")

    def attempt_emr_write(self) -> None:
        raise PermissionError("EMR/HIS write-back is disabled in Phase 3A")

    def attempt_medication_change(self) -> None:
        raise PermissionError("Medication change workflow is disabled in Phase 3A")

    def _task_row(self, task: ChronicCareTask) -> Mapping[str, object]:
        enrollment = self.enrollments[task.enrollment_id]
        return {
            "synthetic_id": enrollment.patient_reference_id,
            "program": enrollment.program_code,
            "risk_status": enrollment.current_risk_status,
            "task_type": task.task_type,
            "priority": task.priority,
            "due_date": task.due_at,
            "assigned_role": task.assigned_role,
            "escalation_level": task.escalation_level,
            "current_status": task.status,
            "blocked_reason": task.blocked_reason,
        }

    def _physician_row(self, enrollment: ChronicCareEnrollment) -> Mapping[str, object]:
        risks = [draft for draft in self.risk_drafts.values() if draft.enrollment_id == enrollment.id]
        plans = [draft for draft in self.plan_drafts.values() if draft.enrollment_id == enrollment.id]
        latest_risk = risks[-1] if risks else None
        plan = plans[-1] if plans else None
        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 9) — bản gốc dùng
        # `enrollment.current_risk_status` (đặt DUY NHẤT một lần lúc
        # `create_enrollment()`, không bao giờ đổi) để quyết định "còn cần bác
        # sĩ xem lại không". `review_risk_draft()` đúng khi cập nhật
        # `draft.risk_status` (PENDING_REVIEW -> APPROVED_FOR_SHADOW/REJECTED)
        # nhưng KHÔNG đụng tới `enrollment.current_risk_status` — nên hàng đợi
        # xét duyệt của bác sĩ KHÔNG BAO GIỜ hết một ca RED/YELLOW dù đã duyệt
        # hay từ chối. Xác nhận bằng thực nghiệm: seed 1 ca RED, review_risk_
        # draft(approve=False) -> risk_draft_status đổi đúng thành REJECTED,
        # nhưng safety_flags/required_action vẫn "red_review"/"physician_
        # review" y hệt trước khi duyệt. Dùng đúng bản ghi risk draft MỚI
        # NHẤT (đã có sẵn ở `risk_draft_status` phía trên) làm nguồn sự thật
        # thay vì trường tĩnh của enrollment — còn PENDING_REVIEW mới cần
        # hành động, đã duyệt/từ chối thì hết.
        needs_risk_review = bool(
            latest_risk and latest_risk.risk_label in {"RED", "YELLOW"}
            and latest_risk.risk_status == "PENDING_REVIEW"
        )
        return {
            "synthetic_id": enrollment.patient_reference_id,
            "program": enrollment.program_code,
            "risk_draft_status": latest_risk.risk_status if latest_risk else "none",
            "care_plan_draft_status": plan.status if plan else "none",
            "evidence_status": "complete" if plan and plan.evidence_reference_ids else "missing",
            "claim_status": "complete" if plan and plan.claim_reference_ids else "missing",
            "approval_status": "shadow_only",
            "safety_flags": "red_review" if latest_risk and latest_risk.risk_label == "RED"
            and latest_risk.risk_status == "PENDING_REVIEW" else "",
            "required_action": "physician_review" if needs_risk_review
            or (plan and plan.status in {"PENDING_REVIEW", "BLOCKED"}) else "none",
            "blocked_reason": plan.blocked_reason if plan else "",
            "last_updated": _now(),
        }

    def _care_plan_blocked_reason(self, draft: ChronicCarePlanDraft) -> str:
        if not draft.evidence_reference_ids or not draft.claim_reference_ids:
            return "EVIDENCE_INSUFFICIENT_OR_UNVERIFIED"
        if self.feature_flags.get("v7_clinical_release"):
            self.clinical_release_flag_bypass += 1
            return "CLINICAL_RELEASE_FLAG_MUST_STAY_FALSE"
        return ""

    def _policy_export(self, payload: Mapping[str, object]) -> None:
        # SỬA 2026-09-04 (Workflow đối kháng đa-agent, phát hiện MEDIUM) — trước
        # đây hardcode {"v7_chatgpt_project_export": True} bất kể self.feature_flags
        # THẬT của service đang là gì. PolicyEngine.evaluate() gộp action "export"
        # và "chatgpt_export" vào CÙNG luật P010 (đọc chính flag này) — nên đây
        # không phải trùng tên tình cờ mà là CÙNG cổng an toàn với
        # app/export_bridge/chatgpt_project_bridge.py (bản đó truyền đúng
        # `feature_flags` thật, không hardcode). Cờ mặc định AN TOÀN là False
        # (DEFAULT_FEATURE_FLAGS), nên bản cũ khiến cổng P010 KHÔNG BAO GIỜ chặn
        # được xuất báo cáo tổng hợp — xác nhận bằng thực nghiệm: ChronicCareService()
        # mặc định (flag=False) vẫn export_aggregate_json() thành công.
        text = repr(payload)
        decision = self.policy_engine.evaluate({
            "action": "export",
            "feature_flags": self.feature_flags,
            "export_contains_raw_dataset": False,
            "export_contains_pii": contains_pii_text(text),
            "text": text,
        })
        if not decision.allowed:
            self.blocked_exports += 1
            raise PermissionError(";".join(v.code for v in decision.blockers))

    def _ensure_no_pii(self, text: str) -> None:
        if contains_pii_text(text):
            raise ValueError("PII-like text is not allowed in Phase 3A synthetic cases")

    def _audit(
        self,
        actor: str,
        action: str,
        entity_type: str,
        entity_id: str,
        *,
        before: Optional[Mapping[str, object]] = None,
        after: Optional[Mapping[str, object]] = None,
        approval: str = "",
        blocked: str = "",
    ) -> None:
        log_chronic_care_event(
            self.audit_trail,
            actor=actor,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            environment=ENVIRONMENT,
            run_id=self.run_packet.run_id,
            before_state=before,
            after_state=after,
            approval_reference=approval,
            blocked_reason=blocked,
        )

    def add_timeline(self, enrollment_id: str, event_type: str, source_type: str, source_reference_id: str, summary: str) -> ChronicCareTimelineEvent:
        event = ChronicCareTimelineEvent(
            id=f"cc_tl_{uuid4().hex}",
            enrollment_id=enrollment_id,
            event_type=event_type,
            event_timestamp=_now(),
            source_type=source_type,
            source_reference_id=source_reference_id,
            summary=summary,
            created_by="system",
        )
        self.timeline.append(event)
        return event


def build_shadow_pilot_state() -> ChronicCareDashboardState:
    service = ChronicCareService()
    service.seed_synthetic_cases()
    return service.dashboard_state()


def _metric(code: str, name: str, numerator: int, denominator: int, start: str, end: str, *, raw: bool = False) -> ChronicCareQualityMetric:
    value = float(numerator if raw else round((numerator / max(denominator, 1)) * 100, 2))
    return ChronicCareQualityMetric(
        id=f"cc_metric_{uuid4().hex}",
        metric_code=code,
        metric_name=name,
        metric_category="shadow_quality",
        numerator=numerator,
        denominator=denominator,
        value=value,
        measurement_period_start=start,
        measurement_period_end=end,
    )


def _is_task_overdue(task: ChronicCareTask) -> bool:
    """`due_at` của việc đã QUA HIỆN TẠI chưa — thứ chữ "overdue" thực sự nói.

    SỬA 2026-09-04 (Workflow đối kháng đa-agent, phát hiện MEDIUM) — trước đây
    `overdue_tasks` trong dashboard_state() đo `priority in {"HIGH","URGENT"}`
    thay vì đo NGÀY. Xác nhận bằng thực nghiệm: một việc REVIEW_OVERDUE_CASE
    với priority LOW (bệnh nhân GREEN, xem rules.py::_priority_for) và due_at
    quá khứ 5 ngày KHÔNG được đếm (0), trong khi 3 việc HIGH/URGENT có due_at
    3 NGÀY TRONG TƯƠNG LAI (mọi create_task() luôn đặt due_at = now+3 ngày)
    VẪN bị đếm là "overdue". Fail-closed như rules.py đã làm với chính
    due_at: rỗng/không parse được → KHÔNG coi là quá hạn (tránh dương tính
    giả từ dữ liệu hỏng, không phải bằng chứng đã quá hạn)."""
    if not task.due_at:
        return False
    try:
        due = datetime.fromisoformat(task.due_at)
    except ValueError:
        return False
    return due < datetime.now(timezone.utc)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
