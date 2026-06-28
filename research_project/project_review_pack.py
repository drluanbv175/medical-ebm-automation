"""
project_review_pack — Gói human review có cấu trúc (V4.3.3).

Tổng hợp mọi mục cần PI quyết định: missing inputs, assumptions,
evidence items chưa xác minh, artifact STALE, change impact,
risk register, kết quả gate, danh sách quyết định.
OFFLINE · KHÔNG PII / API. Mọi output là DRAFT.
"""

from __future__ import annotations

import dataclasses
import pathlib
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .project_config import (
    ArtifactID, ArtifactStatus, ARTIFACT_FILENAME, DISCLAIMER,
    REQUIRE_HUMAN_INPUT_MARKER as RHI,
    ProjectConfig, EvidenceStatus, GateStatus,
)
from .project_evidence_intake import build_evidence_intake
from .project_qa_runner import QARunResult


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ReviewDecision:
    decision_id: str
    area: str
    question: str
    artifact_ref: str
    urgency: str    # HIGH / MEDIUM / LOW

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class ReviewPackResult:
    project_id: str
    generated_at: str
    total_decisions: int
    high_urgency_count: int
    missing_inputs: List[str]
    stale_artifacts: List[str]
    unverified_evidence: int
    decisions: List[ReviewDecision]
    qa_summary: Optional[str]

    def to_markdown(self) -> str:
        lines = [
            f"# REVIEW PACK — {self.project_id}",
            f"> **Ngày tạo:** {self.generated_at[:19]}",
            f"> **DRAFT** — [Dành cho PI/Người phê duyệt] — {DISCLAIMER}",
            "",
            "## Tóm tắt nhanh",
            f"- Tổng quyết định cần đưa ra: **{self.total_decisions}**",
            f"- Ưu tiên CAO: **{self.high_urgency_count}**",
            f"- Mục đầu vào còn thiếu: **{len(self.missing_inputs)}**",
            f"- Artifact cần cập nhật (STALE): **{len(self.stale_artifacts)}**",
            f"- Bằng chứng chưa xác minh: **{self.unverified_evidence}**",
            "",
        ]

        if self.qa_summary:
            lines += ["## Kết quả QA", self.qa_summary, ""]

        if self.missing_inputs:
            lines += ["## Mục đầu vào cần PI điền", ""]
            for i, item in enumerate(self.missing_inputs, 1):
                lines.append(f"{i}. {item}")
            lines.append("")

        if self.stale_artifacts:
            lines += ["## Artifact cần cập nhật (STALE)", ""]
            for a in self.stale_artifacts:
                lines.append(f"- ⚠️ `{a}` — STALE_REQUIRES_REVISION")
            lines.append("")

        if self.unverified_evidence > 0:
            lines += [
                "## Bằng chứng chưa xác minh",
                f"Có {self.unverified_evidence} bằng chứng cần VERIFIED_BY_HUMAN. "
                f"Xem `evidence/evidence_manifest.csv`.",
                "",
            ]

        lines += [
            "## Danh sách quyết định",
            "",
            "| # | Khu vực | Câu hỏi | Artifact | Ưu tiên |",
            "|---|---------|---------|----------|---------|",
        ]
        for i, d in enumerate(self.decisions, 1):
            urgency_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(d.urgency, "⚪")
            lines.append(
                f"| {i} | {d.area} | {d.question} | {d.artifact_ref} | "
                f"{urgency_icon} {d.urgency} |"
            )

        lines += [
            "",
            "## Bước tiếp theo cho PI",
            f"1. Điền mọi mục `{RHI}` trong các artifact.",
            "2. Xác minh bằng chứng trong `evidence/evidence_manifest.csv`.",
            "3. Ký và khóa SAP (07) → cổng G4.",
            "4. Xem xét artifact STALE nếu có.",
            "5. Chạy lại QA: `researchctl project-qa` sau khi cập nhật.",
            "",
            f"---",
            f"**Disclaimer:** {DISCLAIMER}",
        ]
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "generated_at": self.generated_at,
            "total_decisions": self.total_decisions,
            "high_urgency_count": self.high_urgency_count,
            "missing_inputs": self.missing_inputs,
            "stale_artifacts": self.stale_artifacts,
            "unverified_evidence": self.unverified_evidence,
            "decisions": [d.as_dict() for d in self.decisions],
            "qa_summary": self.qa_summary,
        }


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

class ReviewPackBuilder:
    """
    Tổng hợp thông tin từ toàn bộ project → ReviewPackResult.
    Gọi sau khi chạy QA.
    """

    def __init__(
        self,
        project_dir: pathlib.Path,
        config: ProjectConfig,
        qa_result: Optional[QARunResult] = None,
    ) -> None:
        self._dir = pathlib.Path(project_dir)
        self._cfg = config
        self._qa = qa_result

    def build(self) -> ReviewPackResult:
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

        missing_inputs = self._collect_missing_inputs()
        stale_artifacts = self._collect_stale_artifacts()
        unverified_evidence = self._count_unverified_evidence()
        decisions = self._build_decisions(missing_inputs, stale_artifacts)
        high_count = sum(1 for d in decisions if d.urgency == "HIGH")
        qa_summary = self._qa.summary_line() if self._qa else None

        return ReviewPackResult(
            project_id=self._cfg.project_id,
            generated_at=ts,
            total_decisions=len(decisions),
            high_urgency_count=high_count,
            missing_inputs=missing_inputs,
            stale_artifacts=stale_artifacts,
            unverified_evidence=unverified_evidence,
            decisions=decisions,
            qa_summary=qa_summary,
        )

    # ------------------------------------------------------------------
    # Thu thập mục thiếu
    # ------------------------------------------------------------------

    def _collect_missing_inputs(self) -> List[str]:
        missing: List[str] = []

        if not self._cfg.primary_objectives:
            missing.append("primary_objectives chưa được điền")
        else:
            rhi_count = sum(1 for o in self._cfg.primary_objectives if RHI in o)
            if rhi_count > 0:
                missing.append(f"{rhi_count} primary_objectives vẫn là placeholder")

        if not self._cfg.primary_outcomes:
            missing.append("primary_outcomes chưa được điền")
        else:
            rhi_count = sum(1 for o in self._cfg.primary_outcomes if RHI in o)
            if rhi_count > 0:
                missing.append(f"{rhi_count} primary_outcomes vẫn là placeholder")

        # Kiểm tra SAP lock reminder
        sap_path = self._dir / ARTIFACT_FILENAME[ArtifactID.SAP_DRAFT]
        if not sap_path.exists():
            missing.append("SAP_DRAFT (07) chưa được tạo")
        else:
            content = sap_path.read_bytes().decode("utf-8", errors="replace")
            if RHI in content:
                missing.append(f"SAP_DRAFT (07) vẫn còn {content.count(RHI)} mục {RHI}")

        # Kiểm tra PICO
        pico_path = self._dir / ARTIFACT_FILENAME[ArtifactID.RESEARCH_QUESTION_AND_PICO]
        if not pico_path.exists():
            missing.append("RESEARCH_QUESTION_AND_PICO (01) chưa được tạo")
        else:
            content = pico_path.read_bytes().decode("utf-8", errors="replace")
            if content.count(RHI) > 5:
                missing.append(
                    f"PICO (01) còn nhiều mục chưa điền ({content.count(RHI)} {RHI})"
                )

        # Sample size assumptions
        methods_path = self._dir / ARTIFACT_FILENAME[ArtifactID.METHODS_AND_SAMPLE_SIZE]
        if not methods_path.exists():
            missing.append("METHODS_AND_SAMPLE_SIZE (04) chưa được tạo")
        else:
            content = methods_path.read_bytes().decode("utf-8", errors="replace")
            if "giả định" not in content.lower() and "assumption" not in content.lower():
                missing.append(
                    "Giả định cỡ mẫu (effect size, α, β) chưa được PI xác nhận trong (04)"
                )

        return missing

    def _collect_stale_artifacts(self) -> List[str]:
        vr_path = self._dir / ARTIFACT_FILENAME[ArtifactID.VERSION_REGISTER]
        if not vr_path.exists():
            return []
        stale: List[str] = []
        for line in vr_path.read_bytes().decode("utf-8").splitlines()[1:]:
            parts = line.split(",")
            if len(parts) >= 3 and parts[2].strip() == ArtifactStatus.STALE_REQUIRES_REVISION.value:
                stale.append(parts[0].strip())
        return stale

    def _count_unverified_evidence(self) -> int:
        ev_dir = self._dir / "evidence"
        if not ev_dir.exists():
            return 0
        intake = build_evidence_intake(self._dir)
        return len(intake.unverified_items())

    # ------------------------------------------------------------------
    # Xây dựng danh sách quyết định
    # ------------------------------------------------------------------

    def _build_decisions(
        self,
        missing_inputs: List[str],
        stale_artifacts: List[str],
    ) -> List[ReviewDecision]:
        decisions: List[ReviewDecision] = []
        idx = 1

        # Quyết định từ QA failures
        if self._qa:
            for r in self._qa.gate_results:
                if r.status == GateStatus.FAIL:
                    decisions.append(ReviewDecision(
                        decision_id=f"DEC-{idx:03d}",
                        area="QA Gate",
                        question=f"[{r.gate_id} FAIL] {r.message}",
                        artifact_ref=r.gate_id,
                        urgency="HIGH",
                    ))
                    idx += 1
                elif r.status == GateStatus.WARN:
                    decisions.append(ReviewDecision(
                        decision_id=f"DEC-{idx:03d}",
                        area="QA Gate",
                        question=f"[{r.gate_id} WARN] {r.message}",
                        artifact_ref=r.gate_id,
                        urgency="MEDIUM",
                    ))
                    idx += 1

        # Quyết định từ missing inputs
        for m in missing_inputs:
            decisions.append(ReviewDecision(
                decision_id=f"DEC-{idx:03d}",
                area="Missing Input",
                question=m,
                artifact_ref="Nhiều artifact",
                urgency="HIGH",
            ))
            idx += 1

        # Quyết định từ STALE artifacts
        for art in stale_artifacts:
            decisions.append(ReviewDecision(
                decision_id=f"DEC-{idx:03d}",
                area="Stale Artifact",
                question=f"Cập nhật artifact STALE: `{art}`",
                artifact_ref=art,
                urgency="MEDIUM",
            ))
            idx += 1

        # Quyết định cứng — cổng G2 / G4
        if not (self._dir / ARTIFACT_FILENAME[ArtifactID.GOVERNANCE_AND_CAPA_PACK]).exists():
            decisions.append(ReviewDecision(
                decision_id=f"DEC-{idx:03d}",
                area="Governance",
                question="GOVERNANCE_AND_CAPA_PACK (12) chưa tồn tại — cần tạo trước G2",
                artifact_ref="12_GOVERNANCE_AND_CAPA_PACK",
                urgency="HIGH",
            ))
            idx += 1

        # Quyết định về bằng chứng chưa xác minh
        n_unverified = self._count_unverified_evidence()
        if n_unverified > 0:
            decisions.append(ReviewDecision(
                decision_id=f"DEC-{idx:03d}",
                area="Evidence",
                question=f"Xác minh {n_unverified} bằng chứng MANUAL_REVIEW_REQUIRED trong evidence_manifest.csv",
                artifact_ref="evidence/evidence_manifest.csv",
                urgency="HIGH",
            ))
            idx += 1

        # SAP lock decision
        sap_path = self._dir / ARTIFACT_FILENAME[ArtifactID.SAP_DRAFT]
        if sap_path.exists():
            content = sap_path.read_bytes().decode("utf-8", errors="replace")
            if RHI in content:
                decisions.append(ReviewDecision(
                    decision_id=f"DEC-{idx:03d}",
                    area="SAP Lock",
                    question="SAP_DRAFT (07) chưa hoàn chỉnh — điền hết RHI trước khi PI ký khóa (G4)",
                    artifact_ref="07_STATISTICAL_ANALYSIS_PLAN_DRAFT",
                    urgency="HIGH",
                ))
                idx += 1

        return decisions


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def generate_review_pack(
    project_dir: pathlib.Path,
    config: ProjectConfig,
    qa_result: Optional[QARunResult] = None,
    save: bool = True,
) -> ReviewPackResult:
    """Tạo Review Pack cho project. Tuỳ chọn lưu vào REVIEW_PACK (13)."""
    builder = ReviewPackBuilder(project_dir, config, qa_result)
    result = builder.build()

    if save:
        pack_path = pathlib.Path(project_dir) / ARTIFACT_FILENAME[ArtifactID.REVIEW_PACK]
        pack_path.write_bytes(result.to_markdown().encode("utf-8"))

    return result
