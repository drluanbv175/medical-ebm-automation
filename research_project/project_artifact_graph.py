"""
project_artifact_graph — Đồ thị phụ thuộc artifact (V4.3.3).

Khi một artifact thay đổi, mọi artifact downstream bị đánh dấu
STALE_REQUIRES_REVISION. OFFLINE · deterministic · KHÔNG PII / API.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, List, Set

from .project_config import ArtifactID, ArtifactStatus

# ---------------------------------------------------------------------------
# Đồ thị phụ thuộc (upstream → {downstream})
# Thứ tự tuyến tính: Charter → PICO → Protocol → Evidence → Methods
#   → CRF → DD → SAP → Tables → ReadyCheck → Reporting → Manuscript
#   → Governance → ReviewPack → Traceability → QA → ChangeImpact → Decisions
# ---------------------------------------------------------------------------
_DEPENDENCY_GRAPH: Dict[ArtifactID, List[ArtifactID]] = {
    ArtifactID.RESEARCH_CHARTER: [
        ArtifactID.RESEARCH_QUESTION_AND_PICO,
        ArtifactID.PROTOCOL_DRAFT,
        ArtifactID.GOVERNANCE_AND_CAPA_PACK,
        ArtifactID.PROJECT_TRACEABILITY_MATRIX,
    ],
    ArtifactID.RESEARCH_QUESTION_AND_PICO: [
        ArtifactID.PROTOCOL_DRAFT,
        ArtifactID.EVIDENCE_PLAN,
        ArtifactID.METHODS_AND_SAMPLE_SIZE,
        ArtifactID.SAP_DRAFT,
        ArtifactID.REPORTING_CHECKLIST_DRAFT,
        ArtifactID.MANUSCRIPT_OUTLINE_DRAFT,
        ArtifactID.PROJECT_TRACEABILITY_MATRIX,
    ],
    ArtifactID.PROTOCOL_DRAFT: [
        ArtifactID.METHODS_AND_SAMPLE_SIZE,
        ArtifactID.CRF_DRAFT,
        ArtifactID.DATA_DICTIONARY,
        ArtifactID.SAP_DRAFT,
        ArtifactID.GOVERNANCE_AND_CAPA_PACK,
        ArtifactID.PROJECT_TRACEABILITY_MATRIX,
    ],
    ArtifactID.EVIDENCE_PLAN: [
        ArtifactID.METHODS_AND_SAMPLE_SIZE,
        ArtifactID.MANUSCRIPT_OUTLINE_DRAFT,
        ArtifactID.PROJECT_TRACEABILITY_MATRIX,
    ],
    ArtifactID.METHODS_AND_SAMPLE_SIZE: [
        ArtifactID.CRF_DRAFT,
        ArtifactID.SAP_DRAFT,
        ArtifactID.TABLE_AND_FIGURE_SHELLS,
        ArtifactID.SYNTHETIC_ANALYSIS_READINESS,
        ArtifactID.PROJECT_TRACEABILITY_MATRIX,
    ],
    ArtifactID.CRF_DRAFT: [
        ArtifactID.DATA_DICTIONARY,
        ArtifactID.SAP_DRAFT,
        ArtifactID.SYNTHETIC_ANALYSIS_READINESS,
        ArtifactID.PROJECT_TRACEABILITY_MATRIX,
    ],
    ArtifactID.DATA_DICTIONARY: [
        ArtifactID.SAP_DRAFT,
        ArtifactID.TABLE_AND_FIGURE_SHELLS,
        ArtifactID.SYNTHETIC_ANALYSIS_READINESS,
        ArtifactID.PROJECT_TRACEABILITY_MATRIX,
    ],
    ArtifactID.SAP_DRAFT: [
        ArtifactID.TABLE_AND_FIGURE_SHELLS,
        ArtifactID.SYNTHETIC_ANALYSIS_READINESS,
        ArtifactID.REPORTING_CHECKLIST_DRAFT,
        ArtifactID.MANUSCRIPT_OUTLINE_DRAFT,
        ArtifactID.PROJECT_TRACEABILITY_MATRIX,
    ],
    ArtifactID.TABLE_AND_FIGURE_SHELLS: [
        ArtifactID.SYNTHETIC_ANALYSIS_READINESS,
        ArtifactID.REPORTING_CHECKLIST_DRAFT,
        ArtifactID.MANUSCRIPT_OUTLINE_DRAFT,
    ],
    ArtifactID.SYNTHETIC_ANALYSIS_READINESS: [
        ArtifactID.MANUSCRIPT_OUTLINE_DRAFT,
        ArtifactID.PROJECT_QA_REPORT,
    ],
    ArtifactID.REPORTING_CHECKLIST_DRAFT: [
        ArtifactID.MANUSCRIPT_OUTLINE_DRAFT,
        ArtifactID.PROJECT_TRACEABILITY_MATRIX,
    ],
    ArtifactID.MANUSCRIPT_OUTLINE_DRAFT: [
        ArtifactID.GOVERNANCE_AND_CAPA_PACK,
        ArtifactID.REVIEW_PACK,
    ],
    ArtifactID.GOVERNANCE_AND_CAPA_PACK: [
        ArtifactID.REVIEW_PACK,
        ArtifactID.PROJECT_TRACEABILITY_MATRIX,
    ],
    # Leaf nodes — không có downstream
    ArtifactID.REVIEW_PACK: [],
    ArtifactID.PROJECT_TRACEABILITY_MATRIX: [],
    ArtifactID.PROJECT_QA_REPORT: [],
    ArtifactID.CHANGE_IMPACT_REPORT: [],
    ArtifactID.DECISION_REGISTER: [],
    ArtifactID.VERSION_REGISTER: [],
}

# ---------------------------------------------------------------------------
# API công khai
# ---------------------------------------------------------------------------

def get_downstream(artifact_id: ArtifactID) -> FrozenSet[ArtifactID]:
    """Trả về tập TẤT CẢ artifact downstream (đệ quy) của artifact_id."""
    visited: Set[ArtifactID] = set()
    _collect_downstream(artifact_id, visited)
    visited.discard(artifact_id)
    return frozenset(visited)


def _collect_downstream(node: ArtifactID, visited: Set[ArtifactID]) -> None:
    if node in visited:
        return
    visited.add(node)
    for child in _DEPENDENCY_GRAPH.get(node, []):
        _collect_downstream(child, visited)


def get_direct_downstream(artifact_id: ArtifactID) -> List[ArtifactID]:
    """Trả về danh sách direct downstream (không đệ quy)."""
    return list(_DEPENDENCY_GRAPH.get(artifact_id, []))


def mark_stale(
    changed_artifact: ArtifactID,
    statuses: Dict[str, ArtifactStatus],
) -> List[str]:
    """
    Đánh dấu mọi artifact downstream là STALE_REQUIRES_REVISION.
    Trả về danh sách tên artifact đã bị đánh dấu.
    statuses: dict artifact_id_str → ArtifactStatus (mutated in-place).
    """
    downstream = get_downstream(changed_artifact)
    marked: List[str] = []
    for art in downstream:
        key = art.value
        if key in statuses and statuses[key] != ArtifactStatus.STALE_REQUIRES_REVISION:
            statuses[key] = ArtifactStatus.STALE_REQUIRES_REVISION
            marked.append(key)
    return marked


def topological_build_order() -> List[ArtifactID]:
    """Kahn's algorithm — thứ tự xây dựng artifact đảm bảo dependency trước."""
    in_degree: Dict[ArtifactID, int] = {a: 0 for a in ArtifactID}
    for parent, children in _DEPENDENCY_GRAPH.items():
        for child in children:
            in_degree[child] = in_degree.get(child, 0) + 1

    queue: List[ArtifactID] = [a for a, d in in_degree.items() if d == 0]
    order: List[ArtifactID] = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        for child in _DEPENDENCY_GRAPH.get(node, []):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    # Thêm node chưa xuất hiện (leaf nodes không có upstream trong graph)
    seen = set(order)
    for a in ArtifactID:
        if a not in seen:
            order.append(a)

    return order
