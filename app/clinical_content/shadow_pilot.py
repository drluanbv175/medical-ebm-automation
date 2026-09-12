"""Limited clinical shadow pilot Phase 2B.

Chỉ dùng draft/review mode, không ra quyết định thay bác sĩ và không ghi EMR/HIS.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from statistics import median
from typing import Iterable, List, Mapping
from uuid import uuid4

from app.core.policy_engine import contains_pii_text

FORBIDDEN_SHADOW_FIELDS = {
    "patient_name",
    "date_of_birth",
    "dob",
    "phone",
    "mrn",
    "medical_record_number",
    "address",
    "visit_date",
    "image",
    "identifiable_document",
}


def _thu_thap_moi_khoa(obj: object) -> set:
    """SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #86) — trước đây
    `validate()` chỉ so `FORBIDDEN_SHADOW_FIELDS` với `set(payload)`, mà
    `payload` là dict dựng từ CHÍNH TÊN TRƯỜNG CỐ ĐỊNH của dataclass
    (`shadow_case_id`, `red_flag_screen`...) — những tên này theo cấu trúc
    KHÔNG BAO GIỜ trùng một tên PII bị cấm, nên `forbidden` luôn là tập rỗng
    và kiểm tra này chết ngay từ đầu (vô hiệu, không phải chỉ yếu).
    Sửa: đệ quy thu thập MỌI khoá xuất hiện ở bất kỳ độ sâu nào bên trong
    các Mapping/list/tuple/set lồng nhau (vd một khoá tên `mrn` bị lỡ nhét
    vào `medication_context`), rồi mới đem giao với tập cấm — đây mới đúng
    chỗ một PII-named key có thể lọt vào."""
    khoa: set = set()
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            khoa.add(str(k))
            khoa |= _thu_thap_moi_khoa(v)
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            khoa |= _thu_thap_moi_khoa(item)
    return khoa


class OverrideReasonCategory(str, Enum):
    INSUFFICIENT_DATA = "insufficient_data"
    CLINICAL_CONTEXT_NOT_CAPTURED = "clinical_context_not_captured"
    GUIDELINE_NOT_APPLICABLE = "guideline_not_applicable"
    LOCAL_RESOURCE_CONSTRAINT = "local_resource_constraint"
    DRUG_SAFETY_CONCERN = "drug_safety_concern"
    SPECIALIST_INPUT_REQUIRED = "specialist_input_required"
    PHYSICIAN_PREFERENCE = "physician_preference"
    OTHER = "other"


@dataclass(frozen=True)
class ShadowCaseInput:
    shadow_case_id: str
    pathway_id: str
    environment: str
    question_type: str
    clinical_domain: str
    data_completeness: str
    red_flag_screen: Mapping[str, object]
    comorbidity_flags: Mapping[str, bool]
    medication_context: Mapping[str, object]
    evidence_snapshot_id: str
    physician_review_required: bool = True

    def validate(self) -> None:
        payload = {
            "shadow_case_id": self.shadow_case_id,
            "pathway_id": self.pathway_id,
            "environment": self.environment,
            "question_type": self.question_type,
            "clinical_domain": self.clinical_domain,
            "data_completeness": self.data_completeness,
            "red_flag_screen": self.red_flag_screen,
            "comorbidity_flags": self.comorbidity_flags,
            "medication_context": self.medication_context,
            "evidence_snapshot_id": self.evidence_snapshot_id,
        }
        forbidden = FORBIDDEN_SHADOW_FIELDS & _thu_thap_moi_khoa(payload)
        if forbidden:
            raise ValueError(f"Shadow input chứa trường PII bị cấm: {sorted(forbidden)}")
        if contains_pii_text(str(payload)):
            raise ValueError("Shadow input chứa PII-like text")
        if self.environment not in {"test", "review", "shadow"}:
            raise ValueError("Shadow pilot chỉ chạy trong test/review/shadow")
        if not self.physician_review_required:
            raise ValueError("Shadow pilot luôn cần bác sĩ review")


@dataclass(frozen=True)
class PhysicianOverrideLog:
    override_id: str
    shadow_case_id: str
    recommendation_status: str
    physician_action: str
    override_reason_category: OverrideReasonCategory
    free_text_reason_sanitized: str
    reviewer_role: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create(
        cls,
        *,
        shadow_case_id: str,
        recommendation_status: str,
        physician_action: str,
        override_reason_category: OverrideReasonCategory,
        free_text_reason: str,
        reviewer_role: str,
    ) -> "PhysicianOverrideLog":
        if contains_pii_text(free_text_reason):
            raise ValueError("Override reason không được chứa PII-like text")
        return cls(
            override_id=f"ovr_{uuid4().hex}",
            shadow_case_id=shadow_case_id,
            recommendation_status=recommendation_status,
            physician_action=physician_action,
            override_reason_category=override_reason_category,
            free_text_reason_sanitized=free_text_reason,
            reviewer_role=reviewer_role,
        )


@dataclass(frozen=True)
class PilotPathwayCandidate:
    pathway_id: str
    topic: str
    has_scope: bool
    has_input_requirements: bool
    has_red_flags: bool
    has_safety_rules: bool
    has_evidence_manifest: bool
    has_claim_traceability: bool
    has_approval_record: bool
    has_test_cases: bool
    has_unresolved_stale_or_retracted_source: bool = False

    @property
    def eligible(self) -> bool:
        return all([
            self.has_scope,
            self.has_input_requirements,
            self.has_red_flags,
            self.has_safety_rules,
            self.has_evidence_manifest,
            self.has_claim_traceability,
            self.has_approval_record,
            self.has_test_cases,
            not self.has_unresolved_stale_or_retracted_source,
        ])


def select_pilot_pathways(candidates: Iterable[PilotPathwayCandidate], limit: int = 3) -> List[PilotPathwayCandidate]:
    selected = [candidate for candidate in candidates if candidate.eligible]
    return selected[:limit]


def synthetic_pilot_workflow() -> PilotPathwayCandidate:
    return PilotPathwayCandidate(
        pathway_id="synthetic_generic_shadow_workflow",
        topic="Synthetic generic shadow pilot workflow",
        has_scope=True,
        has_input_requirements=True,
        has_red_flags=True,
        has_safety_rules=True,
        has_evidence_manifest=True,
        has_claim_traceability=True,
        has_approval_record=True,
        has_test_cases=True,
    )


def compute_shadow_metrics(cases: Iterable[Mapping[str, object]]) -> Mapping[str, object]:
    rows = list(cases)
    total = len(rows) or 1
    times = [
        float(row.get("time_to_draft_seconds") or 0)
        for row in rows
        if row.get("time_to_draft_seconds") is not None
    ]
    override_reasons: dict[str, int] = {}
    for row in rows:
        reason = str(row.get("override_reason_category") or "")
        if reason:
            override_reasons[reason] = override_reasons.get(reason, 0) + 1
    return {
        "red_flag_screen_completion": sum(bool(row.get("red_flag_screen_completed")) for row in rows) / total,
        "data_sufficiency_block_rate": sum(bool(row.get("data_sufficiency_blocked")) for row in rows) / total,
        "citation_verified_rate": sum(bool(row.get("citation_verified")) for row in rows) / total,
        "recommendation_block_rate": sum(bool(row.get("recommendation_blocked")) for row in rows) / total,
        "physician_override_rate": sum(bool(row.get("physician_override")) for row in rows) / total,
        "override_reason_distribution": override_reasons,
        "clinical_release_block_rate": sum(bool(row.get("clinical_release_blocked")) for row in rows) / total,
        "median_time_to_draft": median(times) if times else 0,
        "source_unavailable_rate": sum(bool(row.get("source_unavailable")) for row in rows) / total,
        "review_signal_only": True,
    }
