"""
research_completion_gates — Gate tổng hợp cho bộ hồ sơ đề tài y khoa.

Mục tiêu: xác nhận một project DRAFT đã có đủ artifact tối thiểu, truy nguyên đầy đủ,
đúng checklist báo cáo theo loại thiết kế, và vẫn bị chặn khỏi real research / external
release khi chưa có duyệt người thật.
"""

from __future__ import annotations

import dataclasses
from typing import Iterable, List, Sequence

from .artifact_registry import ResearchArtifact
from .gate_agent_matrix import build_gate_agent_matrix
from .governance import attempt_external_release, attempt_real_analysis, attempt_real_data_collection
from .project_schema import ResearchProject, ResearchWorkflowState, ReviewStatus, validate_project
from .research_quality_checks import ResearchGateDecision, gr6_reporting_completeness
from .study_type_router import get_template


@dataclasses.dataclass
class ResearchCompletionReport:
    project_id: str
    decision: ResearchGateDecision
    reason_codes: List[str]
    required_artifacts: List[str]
    present_artifacts: List[str]
    missing_artifacts: List[str]
    reporting_checklist: str
    artifact_count: int
    real_research_blocked: bool
    external_release_blocked: bool

    @property
    def structurally_complete(self) -> bool:
        # Vá 2026-09-06 (audit vòng 37, phát hiện #4): bản cũ chỉ kiểm
        # missing_artifacts + tiền tố "ARTIFACT_", bỏ sót các tiền tố khác mà
        # evaluate_research_completion() dùng để tính decision=BLOCK
        # ("MISSING_", "PROJECT_", "REAL_", "EXTERNAL_", "GATE_AGENT_MATRIX:")
        # — vd một project còn ở workflow_state=INTAKE (chưa DRAFT_COMPLETE)
        # với đủ artifact vẫn báo structurally_complete=True dù decision=BLOCK
        # với reason PROJECT_NOT_DRAFT_COMPLETE. Định nghĩa lại bằng đúng
        # decision đã tính, tránh hai nơi mã hoá cùng một khái niệm rồi lệch
        # nhau lần nữa khi danh sách tiền tố đổi trong tương lai.
        return self.decision != ResearchGateDecision.BLOCK


def _artifact_issue(a: ResearchArtifact) -> list[str]:
    issues: list[str] = []
    if not a.is_traceable():
        issues.append(f"ARTIFACT_NOT_TRACEABLE:{a.artifact_type}")
    if not a.draft_only:
        issues.append(f"ARTIFACT_NOT_DRAFT_ONLY:{a.artifact_type}")
    if not a.human_review_required:
        issues.append(f"ARTIFACT_HUMAN_REVIEW_FLAG_MISSING:{a.artifact_type}")
    if a.review_status != ReviewStatus.PENDING_HUMAN_REVIEW:
        issues.append(f"ARTIFACT_REVIEW_STATUS_NOT_PENDING:{a.artifact_type}")
    if a.governance_level != "DRAFT_CREATION":
        issues.append(f"ARTIFACT_GOVERNANCE_LEVEL_NOT_DRAFT:{a.artifact_type}")
    if a.gate_approvals_synthetic:
        issues.append(f"ARTIFACT_USES_SYNTHETIC_GATE_APPROVAL:{a.artifact_type}")
    return issues


def evaluate_research_completion(
    project: ResearchProject,
    artifacts: Sequence[ResearchArtifact] | Iterable[ResearchArtifact],
    reporting: dict | None = None,
    full_registry=None,
    draft_registry=None,
) -> ResearchCompletionReport:
    """Đánh giá dossier DRAFT trước khi coi một đề tài là đủ bộ để người thật duyệt.

    PASS không được dùng cho release thật. Nếu đủ cấu trúc, hàm trả
    REQUIRE_HUMAN_REVIEW vì G2/G4/G9 thật nằm ngoài tự động hóa offline.
    """
    artifact_list = list(artifacts)
    template = get_template(project.study_type)
    required = list(dict.fromkeys(template.minimum_artifact_set + [
        "MANUSCRIPT_OUTLINE_DRAFT",
        "GOVERNANCE_PACK_DRAFT",
    ]))
    present = [a.artifact_type for a in artifact_list if a.project_id == project.project_id]
    present_set = set(present)
    missing = [name for name in required if name not in present_set]

    reasons: list[str] = []
    schema_issues = validate_project(project)
    reasons.extend(schema_issues)
    if project.workflow_state != ResearchWorkflowState.DRAFT_COMPLETE:
        reasons.append(f"PROJECT_NOT_DRAFT_COMPLETE:{project.workflow_state.value}")
    if not project.draft_only or not project.not_valid_for_real_research:
        reasons.append("PROJECT_REAL_RESEARCH_FLAGS_NOT_LOCKED")
    if missing:
        reasons.append("MISSING_REQUIRED_ARTIFACTS:" + ",".join(missing))

    for artifact in artifact_list:
        if artifact.project_id == project.project_id:
            reasons.extend(_artifact_issue(artifact))

    if full_registry is not None and draft_registry is not None:
        matrix = build_gate_agent_matrix(
            full_registry=full_registry,
            draft_registry=draft_registry,
            artifacts=artifact_list,
            project_id=project.project_id,
        )
        if matrix.decision == ResearchGateDecision.BLOCK:
            reasons.append("GATE_AGENT_MATRIX:" + ",".join(matrix.reason_codes))

    reporting_payload = reporting or {}
    reporting_gate = gr6_reporting_completeness(project, reporting_payload)
    if reporting_gate.decision != ResearchGateDecision.PASS:
        reasons.append(f"REPORTING_CHECKLIST:{reporting_gate.reason_code}")

    data_decision = attempt_real_data_collection(has_g2_real=False)
    analysis_decision = attempt_real_analysis(has_sap_lock_real=False)
    release_decision = attempt_external_release(has_g9_real=False)
    real_research_blocked = (
        data_decision.decision == "BLOCKED"
        and analysis_decision.decision == "BLOCKED"
    )
    external_release_blocked = release_decision.decision == "BLOCKED"
    if not real_research_blocked:
        reasons.append("REAL_RESEARCH_NOT_BLOCKED")
    if not external_release_blocked:
        reasons.append("EXTERNAL_RELEASE_NOT_BLOCKED")

    structural_blockers = [
        reason for reason in reasons
        if not reason.startswith("REPORTING_CHECKLIST:")
    ]
    if schema_issues or missing or any(
        reason.startswith((
            "MISSING_",
            "ARTIFACT_",
            "PROJECT_",
            "REAL_",
            "EXTERNAL_",
            "GATE_AGENT_MATRIX:",
        ))
        for reason in structural_blockers
    ):
        decision = ResearchGateDecision.BLOCK
    elif reporting_gate.decision == ResearchGateDecision.PASS:
        reasons.append("HUMAN_REVIEW_REQUIRED_BEFORE_REAL_USE")
        decision = ResearchGateDecision.REQUIRE_HUMAN_REVIEW
    else:
        decision = ResearchGateDecision.REQUIRE_HUMAN_REVIEW

    return ResearchCompletionReport(
        project_id=project.project_id,
        decision=decision,
        reason_codes=reasons,
        required_artifacts=required,
        present_artifacts=present,
        missing_artifacts=missing,
        reporting_checklist=template.reporting_checklist,
        artifact_count=len(present),
        real_research_blocked=real_research_blocked,
        external_release_blocked=external_release_blocked,
    )
