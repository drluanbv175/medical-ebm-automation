"""Shadow pilot schema Phase 2C, không PII."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping
from uuid import uuid4

from app.core.policy_engine import contains_pii_text

FORBIDDEN_PHASE_2C_SHADOW_FIELDS = {
    "patient_name",
    "date_of_birth",
    "phone_number",
    "address",
    "medical_record_number",
    "exact_visit_date",
    "photo",
    "free_text_containing_identifiers",
}


def _thu_thap_moi_khoa(obj: object) -> set:
    """SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #86) — cùng lỗi và
    cùng bản vá như `app/clinical_content/shadow_pilot.py::_thu_thap_moi_khoa`:
    `payload = self.__dict__` chỉ mang tên trường CỐ ĐỊNH của dataclass, nên
    so với `FORBIDDEN_PHASE_2C_SHADOW_FIELDS` ở cấp đó luôn ra tập rỗng. Đệ
    quy xuống các Mapping/list/tuple/set lồng nhau mới bắt được khoá PII bị
    nhét vào các trường tự do (`red_flag_screen`, `medication_context`...)."""
    khoa: set = set()
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            khoa.add(str(k))
            khoa |= _thu_thap_moi_khoa(v)
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            khoa |= _thu_thap_moi_khoa(item)
    return khoa


class Phase2COverrideReason(str, Enum):
    INSUFFICIENT_DATA = "insufficient_data"
    CLINICAL_CONTEXT_NOT_CAPTURED = "clinical_context_not_captured"
    GUIDELINE_NOT_APPLICABLE = "guideline_not_applicable"
    LOCAL_RESOURCE_CONSTRAINT = "local_resource_constraint"
    DRUG_SAFETY_CONCERN = "drug_safety_concern"
    SPECIALIST_INPUT_REQUIRED = "specialist_input_required"
    PHYSICIAN_PREFERENCE = "physician_preference"
    OTHER = "other"


@dataclass(frozen=True)
class Phase2CShadowPilotCase:
    shadow_pilot_case_id: str
    pathway_id: str
    pathway_version: str
    environment: str
    clinical_domain: str
    question_type: str
    data_completeness: str
    red_flag_screen: Mapping[str, object]
    comorbidity_flags: Mapping[str, bool]
    medication_context: Mapping[str, object]
    evidence_snapshot_id: str
    physician_review_required: bool = True

    def validate(self) -> None:
        payload = self.__dict__
        if FORBIDDEN_PHASE_2C_SHADOW_FIELDS & _thu_thap_moi_khoa(payload):
            raise ValueError("Phase 2C shadow payload chứa field PII bị cấm")
        if contains_pii_text(str(payload)):
            raise ValueError("Phase 2C shadow payload chứa PII-like text")
        if self.environment not in {"review", "shadow", "test"}:
            raise ValueError("Phase 2C shadow environment không hợp lệ")
        if not self.physician_review_required:
            raise ValueError("Phase 2C shadow pilot luôn cần physician review")


@dataclass(frozen=True)
class Phase2CShadowReviewLog:
    shadow_review_id: str
    shadow_pilot_case_id: str
    pathway_result_status: str
    physician_agreement: str
    override_reason_category: Phase2COverrideReason
    free_text_reason_sanitized: str
    reviewer_role: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create(
        cls,
        *,
        shadow_pilot_case_id: str,
        pathway_result_status: str,
        physician_agreement: str,
        override_reason_category: Phase2COverrideReason,
        free_text_reason: str,
        reviewer_role: str,
    ) -> "Phase2CShadowReviewLog":
        if contains_pii_text(free_text_reason):
            raise ValueError("Phase 2C review reason không được chứa PII-like text")
        return cls(
            shadow_review_id=f"shadow_review_{uuid4().hex}",
            shadow_pilot_case_id=shadow_pilot_case_id,
            pathway_result_status=pathway_result_status,
            physician_agreement=physician_agreement,
            override_reason_category=override_reason_category,
            free_text_reason_sanitized=free_text_reason,
            reviewer_role=reviewer_role,
        )
