"""
project_schema — Schema & enums cho ResearchProject (V4.3).

KHÔNG dùng tên người thật / bệnh nhân thật / dữ liệu thật. Mọi project là
synthetic fixture phục vụ mô phỏng & đào tạo.
"""

from __future__ import annotations

import dataclasses
import enum
from typing import List

# V4.3.1: state machine DRAFT là nguồn chân lý duy nhất (governance.py).
# Giữ tên cũ ResearchWorkflowState làm alias để tương thích import.
from .governance import DraftWorkflowState

ResearchWorkflowState = DraftWorkflowState


class StudyType(str, enum.Enum):
    CROSS_SECTIONAL = "cross_sectional"
    COHORT = "cohort"
    CASE_CONTROL = "case_control"
    RCT = "randomized_controlled_trial"
    DIAGNOSTIC_ACCURACY = "diagnostic_accuracy"
    SYSTEMATIC_REVIEW = "systematic_review_meta_analysis"
    QUALITATIVE = "qualitative_research"


class ComponentStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    DRAFT = "DRAFT"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    BLOCKED = "BLOCKED"


class ReviewStatus(str, enum.Enum):
    PENDING_HUMAN_REVIEW = "PENDING_HUMAN_REVIEW"   # mặc định — luôn cần người duyệt
    HUMAN_REVIEWED = "HUMAN_REVIEWED"               # chỉ người thật mới đặt được (ngoài phạm vi offline)


@dataclasses.dataclass
class ResearchProject:
    """Một đề tài nghiên cứu SYNTHETIC trong studio. Mọi field bắt buộc."""
    project_id: str
    title: str
    principal_investigator: str             # synthetic, vd "PI-SYNTH-01"
    research_domain: str
    study_type: StudyType
    clinical_question: str
    pico_or_equivalent: dict                 # PICO / PEO / SPIDER tuỳ study_type
    objectives: List[str]
    outcomes: List[str]
    protocol_version: str = "0.1-draft"
    evidence_status: ComponentStatus = ComponentStatus.NOT_STARTED
    methodology_status: ComponentStatus = ComponentStatus.NOT_STARTED
    data_plan_status: ComponentStatus = ComponentStatus.NOT_STARTED
    sap_status: ComponentStatus = ComponentStatus.NOT_STARTED
    manuscript_status: ComponentStatus = ComponentStatus.NOT_STARTED
    governance_status: ComponentStatus = ComponentStatus.NOT_STARTED
    workflow_state: ResearchWorkflowState = ResearchWorkflowState.INTAKE
    draft_only: bool = True
    not_valid_for_real_research: bool = True

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["study_type"] = self.study_type.value
        d["workflow_state"] = self.workflow_state.value
        for k in ("evidence_status", "methodology_status", "data_plan_status",
                  "sap_status", "manuscript_status", "governance_status"):
            d[k] = getattr(self, k).value
        return d


# ── Validation ────────────────────────────────────────────────────────────────

_PII_NAME_HINT = (
    # Heuristic họ Việt — nếu PI/title chứa họ thật + tên → nghi PII (conservative).
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ",
)


def validate_project(p: ResearchProject) -> List[str]:
    """Trả danh sách lỗi schema (rỗng = hợp lệ). KHÔNG raise."""
    issues: List[str] = []
    if not p.project_id or not p.project_id.strip():
        issues.append("MISSING_PROJECT_ID")
    if not p.title or not p.title.strip():
        issues.append("MISSING_TITLE")
    if not isinstance(p.study_type, StudyType):
        issues.append("INVALID_STUDY_TYPE")
    if not p.clinical_question or not p.clinical_question.strip():
        issues.append("MISSING_CLINICAL_QUESTION")
    if not p.objectives:
        issues.append("MISSING_OBJECTIVES")
    if not p.outcomes:
        issues.append("MISSING_OUTCOMES")
    if not isinstance(p.pico_or_equivalent, dict) or not p.pico_or_equivalent:
        issues.append("MISSING_PICO_OR_EQUIVALENT")
    # Bất biến studio
    if not p.draft_only:
        issues.append("DRAFT_ONLY_MUST_BE_TRUE")
    if not p.not_valid_for_real_research:
        issues.append("NOT_VALID_FOR_REAL_RESEARCH_MUST_BE_TRUE")
    # Conservative PII guard cho PI (phải là pseudonym synthetic)
    for hint in _PII_NAME_HINT:
        if hint.lower() in (p.principal_investigator or "").lower():
            issues.append("PI_LOOKS_LIKE_REAL_NAME_USE_SYNTHETIC_ID")
            break
    return issues


def is_valid(p: ResearchProject) -> bool:
    return not validate_project(p)
