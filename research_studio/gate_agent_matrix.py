# ruff: noqa: I001
"""
gate_agent_matrix — Ma trận agent theo cổng nghiên cứu y khoa.

Gate này kiểm chính cấu hình điều phối: mỗi work package phải có lead agent thật,
supporting agents thật, hash truy nguyên, artifact kỳ vọng và human-review role.
"""

from __future__ import annotations

import dataclasses
from typing import Iterable, List, Sequence

from .artifact_registry import ResearchArtifact
from .research_quality_checks import ResearchGateDecision
from .research_workflow import WORK_PACKAGES, WorkPackage


_REVIEW_ROLE_BY_ARTIFACT = {
    "RESEARCH_BRIEF_DRAFT": "PI/Research Lead",
    "PROTOCOL_DRAFT": "PI/Methodologist",
    "EVIDENCE_PLAN_DRAFT": "Evidence Reviewer",
    "METHODS_SAMPLE_SIZE_DRAFT": "Biostatistician",
    "CRF_DRAFT": "Data Manager",
    "SAP_DRAFT": "Biostatistician",
    "SYNTHETIC_ANALYSIS_READINESS_DRAFT": "Biostatistician",
    "MANUSCRIPT_OUTLINE_DRAFT": "PI/Author",
    "REPORTING_CHECKLIST_DRAFT": "Reporting Guideline Reviewer",
    "GOVERNANCE_PACK_DRAFT": "Research Governance",
}
_DEFAULT_REVIEW_ROLE = "Research Reviewer"


@dataclasses.dataclass
class GateAgentRow:
    wp_id: str
    gate_state: str
    lead_agent: str
    supporting_agents: List[str]
    artifact_type: str
    extra_artifact_types: List[str]
    expected_review_role: str
    lead_hash12: str
    supporting_missing: List[str]
    artifact_present: bool
    extra_artifacts_present: List[str]
    decision: ResearchGateDecision
    reason_codes: List[str]

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["decision"] = self.decision.value
        return d


@dataclasses.dataclass
class GateAgentMatrixReport:
    decision: ResearchGateDecision
    rows: List[GateAgentRow]
    reason_codes: List[str]

    def to_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "reason_codes": list(self.reason_codes),
            "rows": [row.to_dict() for row in self.rows],
        }


def expected_artifacts_for_wp(wp: WorkPackage) -> list[str]:
    """WP-08 sinh thêm reporting checklist để khóa chuẩn CONSORT/STROBE/PRISMA."""
    artifacts = [wp.artifact_type]
    if wp.wp_id == "WP-08":
        artifacts.append("REPORTING_CHECKLIST_DRAFT")
    return artifacts


def review_role_for_artifact(artifact_type: str) -> str:
    return _REVIEW_ROLE_BY_ARTIFACT.get(artifact_type, _DEFAULT_REVIEW_ROLE)


def build_gate_agent_matrix(
    *,
    full_registry,
    draft_registry,
    artifacts: Sequence[ResearchArtifact] | Iterable[ResearchArtifact] = (),
    project_id: str | None = None,
) -> GateAgentMatrixReport:
    """Tạo và kiểm ma trận agent-cổng. BLOCK nếu thiếu agent/hash/artifact."""
    artifact_list = list(artifacts)
    if project_id is not None:
        artifact_types = {
            a.artifact_type for a in artifact_list
            if a.project_id == project_id
        }
    else:
        artifact_types = {a.artifact_type for a in artifact_list}

    rows: list[GateAgentRow] = []
    global_reasons: list[str] = []
    for wp in WORK_PACKAGES:
        row_reasons: list[str] = []
        try:
            lead = draft_registry.get(wp.lead_agent)
        except Exception:  # noqa: BLE001
            lead = None
        if lead is None:
            row_reasons.append(f"LEAD_AGENT_MISSING:{wp.lead_agent}")

        lead_hash = getattr(lead, "agent_source_hash", "") if lead is not None else ""
        if not lead_hash:
            row_reasons.append(f"LEAD_AGENT_HASH_MISSING:{wp.lead_agent}")

        supporting_missing: list[str] = []
        for agent_id in wp.supporting_agents:
            try:
                supporting = full_registry.get(agent_id)
            except Exception:  # noqa: BLE001
                supporting = None
            if supporting is None:
                supporting_missing.append(agent_id)
                continue
            if not getattr(supporting, "agent_source_hash", ""):
                supporting_missing.append(agent_id)
        if supporting_missing:
            row_reasons.append(
                "SUPPORTING_AGENT_MISSING_OR_UNHASHED:"
                + ",".join(sorted(supporting_missing))
            )

        expected = expected_artifacts_for_wp(wp)
        artifact_present = wp.artifact_type in artifact_types
        extra_present = [
            artifact_type for artifact_type in expected[1:]
            if artifact_type in artifact_types
        ]
        if artifact_list and not artifact_present:
            row_reasons.append(f"EXPECTED_ARTIFACT_MISSING:{wp.artifact_type}")
        for artifact_type in expected[1:]:
            if artifact_list and artifact_type not in artifact_types:
                row_reasons.append(f"EXPECTED_EXTRA_ARTIFACT_MISSING:{artifact_type}")

        decision = (
            ResearchGateDecision.BLOCK
            if row_reasons
            else ResearchGateDecision.PASS
        )
        rows.append(GateAgentRow(
            wp_id=wp.wp_id,
            gate_state=wp.research_state.value,
            lead_agent=wp.lead_agent,
            supporting_agents=list(wp.supporting_agents),
            artifact_type=wp.artifact_type,
            extra_artifact_types=expected[1:],
            expected_review_role=review_role_for_artifact(wp.artifact_type),
            lead_hash12=lead_hash[:12],
            supporting_missing=supporting_missing,
            artifact_present=artifact_present,
            extra_artifacts_present=extra_present,
            decision=decision,
            reason_codes=row_reasons,
        ))
        global_reasons.extend(row_reasons)

    report_decision = (
        ResearchGateDecision.BLOCK
        if global_reasons
        else ResearchGateDecision.PASS
    )
    return GateAgentMatrixReport(report_decision, rows, global_reasons)
