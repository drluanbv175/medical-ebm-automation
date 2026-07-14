"""
project_review_operations — Human Review Operating Model (V4.3.4).

Roles: PI_PROJECT_OWNER · IRB_ETHICS_COMMITTEE · METHODS_STATISTICS_REVIEWER ·
       INDEPENDENT_PEER_REVIEWER · EVIDENCE_CITATION_REVIEWER ·
       DATA_GOVERNANCE_QA_REVIEWER
Modes: SELF_REVIEW · HUMAN_REVIEW_INDEPENDENCE_NOT_ESTABLISHED
Decisions: REQUEST_HUMAN_INPUT · REVISION_REQUIRED ·
           ACCEPT_DRAFT_FOR_NEXT_INTERNAL_STAGE · REJECT_DRAFT · ARCHIVE_DRAFT

OFFLINE · SYNTHETIC ONLY · KHÔNG API / PII / dữ liệu thật.
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE.
Mọi output là DRAFT — REQUIRE HUMAN REVIEW.
"""

from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
import pathlib
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .project_artifact_graph import get_downstream
from .project_config import (
    ARTIFACT_FILENAME,
    DISCLAIMER,
    ArtifactID,
    ProjectConfig,
    contains_pii,
)
from .project_config import (
    REQUIRE_HUMAN_INPUT_MARKER as RHI,
)

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ReviewRole(str, enum.Enum):
    PI_PROJECT_OWNER              = "PI_PROJECT_OWNER"
    IRB_ETHICS_COMMITTEE          = "IRB_ETHICS_COMMITTEE"
    METHODS_STATISTICS_REVIEWER   = "METHODS_STATISTICS_REVIEWER"
    INDEPENDENT_PEER_REVIEWER     = "INDEPENDENT_PEER_REVIEWER"
    EVIDENCE_CITATION_REVIEWER    = "EVIDENCE_CITATION_REVIEWER"
    DATA_GOVERNANCE_QA_REVIEWER   = "DATA_GOVERNANCE_QA_REVIEWER"


class ReviewMode(str, enum.Enum):
    SELF_REVIEW                              = "SELF_REVIEW"
    HUMAN_REVIEW_INDEPENDENCE_NOT_ESTABLISHED = "HUMAN_REVIEW_INDEPENDENCE_NOT_ESTABLISHED"
    # Forbidden modes — ghi rõ để test có thể phát hiện vi phạm:
    # INDEPENDENT_REVIEW_APPROVED — không được dùng
    # ETHICS_APPROVED             — không được dùng
    # PI_APPROVED                 — không được dùng
    # FINAL_APPROVED              — không được dùng


class HumanDecision(str, enum.Enum):
    REQUEST_HUMAN_INPUT              = "REQUEST_HUMAN_INPUT"
    REVISION_REQUIRED                = "REVISION_REQUIRED"
    ACCEPT_DRAFT_FOR_NEXT_INTERNAL_STAGE = "ACCEPT_DRAFT_FOR_NEXT_INTERNAL_STAGE"
    REJECT_DRAFT                     = "REJECT_DRAFT"
    ARCHIVE_DRAFT                    = "ARCHIVE_DRAFT"


class RiskLevel(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH     = "HIGH"
    MEDIUM   = "MEDIUM"
    LOW      = "LOW"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class AutoReviewForbidden(RuntimeError):
    """Automation không được phép tạo review decision."""


class ForbiddenReviewMode(ValueError):
    """ReviewMode này bị cấm trong V4.3.4."""


class UnauthorizedReviewRole(ValueError):
    """Role không được route cho artifact nên không được ghi review decision."""


class MissingReviewActorReference(ValueError):
    """Thiếu mã định danh giả của người/đơn vị review."""


class PIIInReviewRecord(ValueError):
    """Review ledger không được chứa PII trong reviewer_ref/reason/actions."""


# ---------------------------------------------------------------------------
# ReviewRecord
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ReviewRecord:
    """Bản ghi review decision — append-only, không xóa/sửa sau khi tạo."""
    review_id: str
    project_id: str
    artifact_id: str
    artifact_version: str
    review_role: ReviewRole
    reviewer_identity_reference: str
    review_mode: ReviewMode
    decision: HumanDecision
    reason: str
    required_actions: List[str]
    blocking_gate: str
    risk_level: RiskLevel
    created_at_utc: str
    audit_event_id: str

    def as_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["review_role"]  = self.review_role.value
        d["review_mode"]  = self.review_mode.value
        d["decision"]     = self.decision.value
        d["risk_level"]   = self.risk_level.value
        return d

    def to_jsonl(self) -> str:
        return json.dumps(self.as_dict(), ensure_ascii=False)


# ---------------------------------------------------------------------------
# Routing Matrix
# ---------------------------------------------------------------------------

_ROUTING = Dict[ArtifactID, Tuple[List[ReviewRole], str, RiskLevel, str]]

REVIEW_ROUTING_MATRIX: _ROUTING = {
    ArtifactID.RESEARCH_CHARTER: (
        [ReviewRole.PI_PROJECT_OWNER],
        "objectives, outcomes, feasibility",
        RiskLevel.HIGH, "D-R1",
    ),
    ArtifactID.RESEARCH_QUESTION_AND_PICO: (
        [ReviewRole.PI_PROJECT_OWNER],
        "objectives, outcomes, feasibility",
        RiskLevel.HIGH, "D-R2",
    ),
    ArtifactID.PROTOCOL_DRAFT: (
        [
            ReviewRole.PI_PROJECT_OWNER,
            ReviewRole.METHODS_STATISTICS_REVIEWER,
            ReviewRole.IRB_ETHICS_COMMITTEE,
        ],
        "design, population, bias, IRB/ethics readiness",
        RiskLevel.CRITICAL, "D-R4",
    ),
    ArtifactID.EVIDENCE_PLAN: (
        [ReviewRole.EVIDENCE_CITATION_REVIEWER],
        "evidence status, verification, retraction",
        RiskLevel.HIGH, "D-R8",
    ),
    ArtifactID.METHODS_AND_SAMPLE_SIZE: (
        [ReviewRole.METHODS_STATISTICS_REVIEWER],
        "assumptions, confounding, missing data",
        RiskLevel.CRITICAL, "D-R15",
    ),
    ArtifactID.CRF_DRAFT: (
        [ReviewRole.DATA_GOVERNANCE_QA_REVIEWER],
        "variables, coding, validation, provenance",
        RiskLevel.HIGH, "D-R5",
    ),
    ArtifactID.DATA_DICTIONARY: (
        [ReviewRole.DATA_GOVERNANCE_QA_REVIEWER],
        "variables, coding, validation, provenance",
        RiskLevel.HIGH, "D-R5",
    ),
    ArtifactID.SAP_DRAFT: (
        [ReviewRole.METHODS_STATISTICS_REVIEWER],
        "outcome-analysis consistency",
        RiskLevel.CRITICAL, "D-R6",
    ),
    ArtifactID.TABLE_AND_FIGURE_SHELLS: (
        [ReviewRole.METHODS_STATISTICS_REVIEWER],
        "outcome-analysis consistency",
        RiskLevel.MEDIUM, "D-R7",
    ),
    ArtifactID.SYNTHETIC_ANALYSIS_READINESS: (
        [ReviewRole.METHODS_STATISTICS_REVIEWER],
        "synthetic data readiness, no real data",
        RiskLevel.MEDIUM, "D-R9",
    ),
    ArtifactID.REPORTING_CHECKLIST_DRAFT: (
        [
            ReviewRole.PI_PROJECT_OWNER,
            ReviewRole.EVIDENCE_CITATION_REVIEWER,
            ReviewRole.INDEPENDENT_PEER_REVIEWER,
        ],
        "reporting standard, citations, independent critique",
        RiskLevel.HIGH, "D-R11",
    ),
    ArtifactID.MANUSCRIPT_OUTLINE_DRAFT: (
        [ReviewRole.PI_PROJECT_OWNER, ReviewRole.INDEPENDENT_PEER_REVIEWER],
        "outline completeness, independent critique, draft-only status",
        RiskLevel.MEDIUM, "D-R11",
    ),
    ArtifactID.GOVERNANCE_AND_CAPA_PACK: (
        [ReviewRole.DATA_GOVERNANCE_QA_REVIEWER],
        "traceability, change control, audit",
        RiskLevel.HIGH, "D-R12",
    ),
    ArtifactID.REVIEW_PACK: (
        [ReviewRole.PI_PROJECT_OWNER, ReviewRole.INDEPENDENT_PEER_REVIEWER],
        "unresolved decisions, independent critique, next action",
        RiskLevel.HIGH, "D-R14",
    ),
    ArtifactID.PROJECT_TRACEABILITY_MATRIX: (
        [ReviewRole.DATA_GOVERNANCE_QA_REVIEWER],
        "traceability completeness",
        RiskLevel.MEDIUM, "D-R14",
    ),
    ArtifactID.PROJECT_QA_REPORT: (
        [ReviewRole.PI_PROJECT_OWNER],
        "gate results, outstanding WARN/FAIL",
        RiskLevel.HIGH, "D-R1",
    ),
    ArtifactID.CHANGE_IMPACT_REPORT: (
        [ReviewRole.PI_PROJECT_OWNER],
        "stale artifacts, propagation",
        RiskLevel.MEDIUM, "D-R12",
    ),
    ArtifactID.DECISION_REGISTER: (
        [ReviewRole.PI_PROJECT_OWNER],
        "decision completeness, outstanding items",
        RiskLevel.MEDIUM, "D-R12",
    ),
    ArtifactID.VERSION_REGISTER: (
        [ReviewRole.DATA_GOVERNANCE_QA_REVIEWER],
        "version sequence, no overwrite",
        RiskLevel.LOW, "D-R12",
    ),
}


# ---------------------------------------------------------------------------
# ReviewLedger — append-only
# ---------------------------------------------------------------------------

LEDGER_FILENAME = "review_ledger.jsonl"


class ReviewLedger:
    """Sổ cái review decision — chỉ ghi thêm, không sửa/xóa."""

    def __init__(self, project_dir: pathlib.Path) -> None:
        self._path = project_dir / LEDGER_FILENAME

    def append(self, record: ReviewRecord) -> None:
        """Ghi thêm một record. Không overwrite record cũ."""
        # Guard: SELF_REVIEW không được ghi lại như independent review
        forbidden_modes = {
            "INDEPENDENT_REVIEW_APPROVED", "ETHICS_APPROVED",
            "PI_APPROVED", "FINAL_APPROVED",
        }
        if record.review_mode.value in forbidden_modes:
            raise ForbiddenReviewMode(
                f"ReviewMode '{record.review_mode}' bị cấm trong V4.3.4."
            )
        reviewer_ref = (record.reviewer_identity_reference or "").strip()
        if reviewer_ref in ("", "none", "N/A", "NA", "[REQUIRE_HUMAN_INPUT]"):
            raise MissingReviewActorReference(
                "Cần reviewer_identity_reference dạng mã giả danh, không dùng tên thật/PII."
            )
        pii_payload = {
            "reviewer_identity_reference": record.reviewer_identity_reference,
            "reason": record.reason,
            "required_actions": record.required_actions,
        }
        if contains_pii(json.dumps(pii_payload, ensure_ascii=False)):
            raise PIIInReviewRecord(
                "Review record chứa PII. Hãy dùng mã giả danh và mô tả không định danh."
            )
        # Guard: ACCEPT_DRAFT không thay đổi draft_only semantics
        # (không cần action ở đây — chỉ record việc chấp nhận DRAFT cho stage tiếp theo)
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(record.to_jsonl() + "\n")

    def read_all(self) -> List[ReviewRecord]:
        if not self._path.exists():
            return []
        records = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                records.append(ReviewRecord(
                    review_id=d["review_id"],
                    project_id=d["project_id"],
                    artifact_id=d["artifact_id"],
                    artifact_version=d["artifact_version"],
                    review_role=ReviewRole(d["review_role"]),
                    reviewer_identity_reference=d.get(
                        "reviewer_identity_reference",
                        "LEGACY_REVIEWER_REF_MISSING",
                    ),
                    review_mode=ReviewMode(d["review_mode"]),
                    decision=HumanDecision(d["decision"]),
                    reason=d["reason"],
                    required_actions=d.get("required_actions", []),
                    blocking_gate=d.get("blocking_gate", ""),
                    risk_level=RiskLevel(d.get("risk_level", "MEDIUM")),
                    created_at_utc=d["created_at_utc"],
                    audit_event_id=d["audit_event_id"],
                ))
            except (KeyError, ValueError):
                continue
        return records

    def exists(self) -> bool:
        return self._path.exists()

    def record_count(self) -> int:
        return len(self.read_all())

    @property
    def path(self) -> pathlib.Path:
        return self._path


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def _make_review_id(project_id: str, artifact_id: str) -> str:
    raw = f"{project_id}:{artifact_id}:{uuid.uuid4()}"
    return "RV-" + hashlib.sha256(raw.encode()).hexdigest()[:12].upper()


def _make_audit_event_id(review_id: str) -> str:
    return "AE-" + hashlib.sha256(review_id.encode()).hexdigest()[:10].upper()


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _artifact_version(project_dir: pathlib.Path, artifact_id: ArtifactID) -> str:
    """Lấy version từ VERSION_REGISTER hoặc trả default."""
    reg = project_dir / ARTIFACT_FILENAME[ArtifactID.VERSION_REGISTER]
    if not reg.exists():
        return "0.1.0"
    for line in reg.read_text(encoding="utf-8").splitlines()[1:]:
        if not line.strip():
            continue
        parts = line.split(",")
        if len(parts) >= 3 and parts[0].strip() == artifact_id.value:
            return parts[2].strip()
    return "0.1.0"


def required_roles_for_artifact(artifact_id: ArtifactID) -> List[ReviewRole]:
    """Danh sách role bắt buộc được phép review artifact."""
    roles, _, _, _ = REVIEW_ROUTING_MATRIX.get(
        artifact_id,
        ([ReviewRole.PI_PROJECT_OWNER], "", RiskLevel.MEDIUM, "D-R1"),
    )
    return list(roles)


def _review_snapshot(artifact_id: ArtifactID, records: List[ReviewRecord]) -> dict:
    """Tóm tắt review theo từng role bắt buộc cho một artifact."""
    required_roles = required_roles_for_artifact(artifact_id)
    artifact_records = [r for r in records if r.artifact_id == artifact_id.value]
    latest_by_role: Dict[ReviewRole, ReviewRecord] = {}
    for record in artifact_records:
        if record.review_role not in required_roles:
            continue
        prior = latest_by_role.get(record.review_role)
        if prior is None or record.created_at_utc > prior.created_at_utc:
            latest_by_role[record.review_role] = record

    role_decisions = {
        role.value: latest_by_role[role].decision.value
        for role in required_roles
        if role in latest_by_role
    }
    accepted_roles = [
        role.value for role in required_roles
        if latest_by_role.get(role)
        and latest_by_role[role].decision == HumanDecision.ACCEPT_DRAFT_FOR_NEXT_INTERNAL_STAGE
    ]
    missing_roles = [role.value for role in required_roles if role.value not in accepted_roles]
    blocking_roles = [
        role.value for role in required_roles
        if latest_by_role.get(role)
        and latest_by_role[role].decision in {
            HumanDecision.REQUEST_HUMAN_INPUT,
            HumanDecision.REVISION_REQUIRED,
            HumanDecision.REJECT_DRAFT,
        }
    ]

    if not artifact_records:
        current_status = "DRAFT"
    elif any(
        latest_by_role.get(role)
        and latest_by_role[role].decision == HumanDecision.REJECT_DRAFT
        for role in required_roles
    ):
        current_status = "REJECTED_DRAFT"
    elif any(
        latest_by_role.get(role)
        and latest_by_role[role].decision == HumanDecision.REVISION_REQUIRED
        for role in required_roles
    ):
        current_status = "REVISION_REQUIRED"
    elif any(
        latest_by_role.get(role)
        and latest_by_role[role].decision == HumanDecision.REQUEST_HUMAN_INPUT
        for role in required_roles
    ):
        current_status = "AWAITING_HUMAN_INPUT"
    elif not missing_roles:
        current_status = "ACCEPTED_DRAFT"
    elif accepted_roles:
        current_status = "PARTIAL_REVIEW"
    else:
        current_status = "DRAFT"

    newest = max(artifact_records, key=lambda r: r.created_at_utc) if artifact_records else None
    return {
        "required_roles": [role.value for role in required_roles],
        "accepted_roles": accepted_roles,
        "missing_roles": missing_roles,
        "blocking_roles": blocking_roles,
        "role_decisions": role_decisions,
        "current_status": current_status,
        "complete_required_review": not missing_roles,
        "last_decision": newest.decision.value if newest else None,
    }


def list_review_queue(
    project_dir: pathlib.Path,
    config: ProjectConfig,
) -> List[dict]:
    """Liệt kê artifact cần review — không chứa PII."""
    items = []
    ledger = ReviewLedger(project_dir)
    records = ledger.read_all()

    for art_id, (roles, focus, risk, gate) in REVIEW_ROUTING_MATRIX.items():
        fname = ARTIFACT_FILENAME.get(art_id, "")
        fpath = project_dir / fname
        if not fpath.exists():
            continue
        snapshot = _review_snapshot(art_id, records)

        item = {
            "artifact_id": art_id.value,
            "artifact_file": fname,
            "primary_roles": [r.value for r in roles],
            "required_roles": snapshot["required_roles"],
            "accepted_roles": snapshot["accepted_roles"],
            "missing_roles": snapshot["missing_roles"],
            "blocking_roles": snapshot["blocking_roles"],
            "role_decisions": snapshot["role_decisions"],
            "complete_required_review": snapshot["complete_required_review"],
            "mandatory_focus": focus,
            "risk_level": risk.value,
            "blocking_gate": gate,
            "current_status": snapshot["current_status"],
            "last_decision": snapshot["last_decision"],
            "missing_input": RHI in fpath.read_text(encoding="utf-8"),
            "draft_only": True,
            "human_review_required": True,
        }
        # Xác nhận không có PII trong summary
        assert not contains_pii(str(item)), "PII detected in review queue item"
        items.append(item)
    return items


def record_decision(
    project_dir: pathlib.Path,
    config: ProjectConfig,
    artifact_id_str: str,
    decision: HumanDecision,
    review_role: ReviewRole,
    reason: str,
    reviewer_ref: str,
    required_actions: Optional[List[str]] = None,
    review_mode: ReviewMode = ReviewMode.HUMAN_REVIEW_INDEPENDENCE_NOT_ESTABLISHED,
    automation_caller: bool = False,
) -> ReviewRecord:
    """
    Ghi nhận quyết định review — append-only.
    automation_caller=True sẽ bị từ chối.
    """
    if automation_caller:
        raise AutoReviewForbidden(
            "Automation không được phép tạo review decision. "
            "Chỉ PI/reviewer người thật mới được ghi quyết định."
        )
    # Validate artifact_id
    try:
        art_id = ArtifactID(artifact_id_str)
    except ValueError:
        raise ValueError(f"Artifact ID '{artifact_id_str}' không hợp lệ.")

    routing = REVIEW_ROUTING_MATRIX.get(art_id)
    if routing is None:
        blocking_gate = "D-R1"
        risk_level = RiskLevel.MEDIUM
        routed_roles = [ReviewRole.PI_PROJECT_OWNER]
    else:
        blocking_gate = routing[3]
        risk_level = routing[2]
        routed_roles = routing[0]

    if review_role not in routed_roles:
        allowed = ", ".join(role.value for role in routed_roles)
        raise UnauthorizedReviewRole(
            f"Role {review_role.value} không được phép review {art_id.value}. "
            f"Role bắt buộc: {allowed}."
        )

    version = _artifact_version(project_dir, art_id)
    rid = _make_review_id(config.project_id, artifact_id_str)
    audit_id = _make_audit_event_id(rid)

    record = ReviewRecord(
        review_id=rid,
        project_id=config.project_id,
        artifact_id=artifact_id_str,
        artifact_version=version,
        review_role=review_role,
        reviewer_identity_reference=reviewer_ref,
        review_mode=review_mode,
        decision=decision,
        reason=reason,
        required_actions=required_actions or [],
        blocking_gate=blocking_gate,
        risk_level=risk_level,
        created_at_utc=_utc_now(),
        audit_event_id=audit_id,
    )
    ledger = ReviewLedger(project_dir)
    ledger.append(record)
    return record


def get_review_status(project_dir: pathlib.Path) -> dict:
    """Tổng hợp trạng thái review — không dùng từ 'approved final'."""
    ledger = ReviewLedger(project_dir)
    records = ledger.read_all()

    # Tổng hợp theo artifact (chỉ lấy quyết định mới nhất)
    latest: Dict[str, ReviewRecord] = {}
    for r in records:
        if r.artifact_id not in latest or r.created_at_utc > latest[r.artifact_id].created_at_utc:
            latest[r.artifact_id] = r

    snapshots = {}
    for artifact_id_str in latest:
        try:
            artifact_id = ArtifactID(artifact_id_str)
        except ValueError:
            continue
        snapshots[artifact_id_str] = _review_snapshot(artifact_id, records)

    draft_count = 0
    revision_count = 0
    human_input_count = 0
    accepted_draft_count = 0
    rejected_count = 0
    archived_count = 0
    partial_review_count = 0

    for artifact_id_str, r in latest.items():
        snapshot = snapshots.get(artifact_id_str)
        status = snapshot["current_status"] if snapshot else "DRAFT"
        if status == "AWAITING_HUMAN_INPUT":
            human_input_count += 1
        elif status == "REVISION_REQUIRED":
            revision_count += 1
        elif status == "ACCEPTED_DRAFT":
            accepted_draft_count += 1
        elif status == "REJECTED_DRAFT" or r.decision == HumanDecision.REJECT_DRAFT:
            rejected_count += 1
        elif r.decision == HumanDecision.ARCHIVE_DRAFT:
            archived_count += 1
        elif status == "PARTIAL_REVIEW":
            partial_review_count += 1
        else:
            draft_count += 1

    missing_required = [
        {
            "artifact_id": artifact_id_str,
            "missing_roles": snapshot["missing_roles"],
            "accepted_roles": snapshot["accepted_roles"],
            "current_status": snapshot["current_status"],
        }
        for artifact_id_str, snapshot in sorted(snapshots.items())
        if snapshot["missing_roles"]
    ]

    return {
        "total_review_records": len(records),
        "total_artifacts_reviewed": len(latest),
        "draft_pending_review": draft_count,
        "partial_review": partial_review_count,
        "revision_required": revision_count,
        "human_input_required": human_input_count,
        "accepted_as_draft_internal": accepted_draft_count,
        "complete_required_review_count": accepted_draft_count,
        "artifacts_missing_required_roles": missing_required,
        "review_role_matrix": snapshots,
        "rejected_draft": rejected_count,
        "archived_draft": archived_count,
        # Bắt buộc: mọi artifact vẫn là DRAFT
        "draft_only_status": True,
        "human_review_required": True,
        "final_released_submitted_count": 0,
        "qualification": "NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE",
        "disclaimer": DISCLAIMER,
    }


def build_revision_plan(
    project_dir: pathlib.Path,
    config: ProjectConfig,
) -> dict:
    """
    Tạo revision plan từ REVISION_REQUIRED records.
    Không overwrite artifact version cũ.
    Đánh dấu downstream artifacts là STALE.
    """
    ledger = ReviewLedger(project_dir)
    records = ledger.read_all()

    revision_items = [r for r in records if r.decision == HumanDecision.REVISION_REQUIRED]

    if not revision_items:
        return {
            "project_id": config.project_id,
            "revision_items": [],
            "stale_artifacts": [],
            "downstream_impact": {},
            "summary": "Không có REVISION_REQUIRED record. Không cần revision plan.",
            "draft_only": True,
            "disclaimer": DISCLAIMER,
        }

    stale_set: set = set()
    downstream_map: Dict[str, List[str]] = {}

    for r in revision_items:
        try:
            art_id = ArtifactID(r.artifact_id)
        except ValueError:
            continue
        downstream = get_downstream(art_id)
        downstream_names = [a.value for a in downstream]
        downstream_map[r.artifact_id] = downstream_names
        stale_set.update(downstream_names)

        # Đánh dấu STALE trong VERSION_REGISTER nếu có
        _mark_stale_in_register(project_dir, downstream)

    revision_items_data = []
    for r in revision_items:
        revision_items_data.append({
            "artifact_id": r.artifact_id,
            "artifact_version": r.artifact_version,
            "review_role": r.review_role.value,
            "reason": r.reason,
            "required_actions": r.required_actions,
            "review_id": r.review_id,
            "created_at_utc": r.created_at_utc,
            "instruction": (
                f"Artifact {r.artifact_id} cần được sửa. "
                f"Tạo version mới, KHÔNG overwrite version cũ. "
                f"Sau đó chạy: researchctl project-change-impact --field artifact_revision"
            ),
        })

    return {
        "project_id": config.project_id,
        "revision_items": revision_items_data,
        "stale_artifacts": sorted(stale_set),
        "downstream_impact": downstream_map,
        "summary": (
            f"{len(revision_items)} artifact cần sửa; "
            f"{len(stale_set)} artifact phụ thuộc cần rà soát."
        ),
        "draft_only": True,
        "human_review_required": True,
        "no_overwrite_policy": "Artifact version cũ được bảo toàn. Tạo version mới sau khi PI sửa.",
        "disclaimer": DISCLAIMER,
    }


def _mark_stale_in_register(
    project_dir: pathlib.Path,
    stale_artifact_ids: List[ArtifactID],
) -> None:
    """Ghi chú STALE vào CHANGE_IMPACT_REPORT — không overwrite artifact thật."""
    cir_path = project_dir / ARTIFACT_FILENAME[ArtifactID.CHANGE_IMPACT_REPORT]
    if not cir_path.exists():
        return
    content = cir_path.read_text(encoding="utf-8")
    stale_note = "\n\n## STALE từ Revision Plan\n\n"
    for art_id in stale_artifact_ids:
        stale_note += f"- `{art_id.value}` — STALE_REQUIRES_REVISION (từ revision plan)\n"
    stale_note += f"\n{RHI} PI cần rà soát và cập nhật các artifact trên.\n"
    stale_note += f"\n---\n*{DISCLAIMER}*\n"
    if "STALE từ Revision Plan" not in content:
        with open(cir_path, "a", encoding="utf-8") as f:
            f.write(stale_note)


# ---------------------------------------------------------------------------
# Review Queue items  (cho ReviewQueue trong research_automation)
# ---------------------------------------------------------------------------

def make_review_queue_item(
    project_id: str,
    artifact_id: ArtifactID,
    reason: str,
) -> dict:
    """Tạo dict item để nạp vào ReviewQueue — không auto-approve."""
    roles, focus, risk, gate = REVIEW_ROUTING_MATRIX.get(
        artifact_id,
        ([ReviewRole.PI_PROJECT_OWNER], "", RiskLevel.MEDIUM, "D-R1"),
    )
    return {
        "project_id": project_id,
        "artifact_id": artifact_id.value,
        "review_reason": reason,
        "primary_roles": [r.value for r in roles],
        "mandatory_focus": focus,
        "risk_level": risk.value,
        "blocking_gate": gate,
        "auto_approve": False,
        "draft_only": True,
        "human_review_required": True,
    }
