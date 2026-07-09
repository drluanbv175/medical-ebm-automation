"""
artifact_registry — Đăng ký artifact nghiên cứu (DRAFT) với truy nguyên đầy đủ.

Mỗi artifact BẮT BUỘC có source_agent_hash + workflow_run_id (truy nguyên về
agent source đã hash-verify và lần chạy orchestrator). Mọi artifact draft_only.
"""

from __future__ import annotations

import dataclasses
from typing import List, Optional

from .project_schema import ReviewStatus


class ArtifactIntegrityError(ValueError):
    """Artifact thiếu trường truy nguyên bắt buộc (vd source_agent_hash)."""


@dataclasses.dataclass
class ResearchArtifact:
    artifact_id: str
    project_id: str
    artifact_type: str                  # vd "RESEARCH_BRIEF_DRAFT"
    artifact_version: str
    source_agent_id: str
    source_agent_hash: Optional[str]    # PHẢI có (None → BLOCK)
    workflow_run_id: str
    evidence_reference: str
    review_status: ReviewStatus = ReviewStatus.PENDING_HUMAN_REVIEW
    draft_only: bool = True
    human_review_required: bool = True
    content_summary: str = ""           # tóm tắt synthetic, KHÔNG PII
    # V4.3.1: mức quản trị của artifact. Studio chỉ tạo mức A = DRAFT_CREATION.
    governance_level: str = "DRAFT_CREATION"
    # V4.3.1: mức A KHÔNG dùng approval cổng nào (G2/G4/G9 chỉ cho thực thi thật/release).
    # False = không có approval (kể cả synthetic) đứng sau artifact này.
    gate_approvals_synthetic: bool = False

    def is_traceable(self) -> bool:
        return bool(
            self.artifact_id and self.project_id and self.artifact_type
            and self.source_agent_id and self.source_agent_hash
            and self.workflow_run_id
        )

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["review_status"] = self.review_status.value
        return d


class ArtifactRegistry:
    """Append-only registry artifact. Fail-closed nếu thiếu truy nguyên."""

    def __init__(self):
        self._artifacts: List[ResearchArtifact] = []

    def register(self, artifact: ResearchArtifact) -> ResearchArtifact:
        """Thêm artifact; raise nếu thiếu hash/bất biến vi phạm."""
        if not artifact.source_agent_hash:
            raise ArtifactIntegrityError(
                f"ARTIFACT_MISSING_AGENT_HASH:{artifact.artifact_id}"
            )
        if not artifact.workflow_run_id:
            raise ArtifactIntegrityError(
                f"ARTIFACT_MISSING_WORKFLOW_RUN_ID:{artifact.artifact_id}"
            )
        if not artifact.draft_only or not artifact.human_review_required:
            raise ArtifactIntegrityError(
                f"ARTIFACT_MUST_BE_DRAFT_AND_REVIEW_REQUIRED:{artifact.artifact_id}"
            )
        if not artifact.is_traceable():
            raise ArtifactIntegrityError(
                f"ARTIFACT_NOT_TRACEABLE:{artifact.artifact_id}"
            )
        self._artifacts.append(artifact)
        return artifact

    def for_project(self, project_id: str) -> List[ResearchArtifact]:
        return [a for a in self._artifacts if a.project_id == project_id]

    def all(self) -> List[ResearchArtifact]:
        return list(self._artifacts)

    def count(self) -> int:
        return len(self._artifacts)

    def types_for_project(self, project_id: str) -> List[str]:
        return [a.artifact_type for a in self.for_project(project_id)]
