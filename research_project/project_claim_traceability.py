"""
project_claim_traceability — Claim Traceability Ledger (V4.3.5).

Mỗi claim trong dossier phải liên kết với ít nhất một Evidence Source đã
được human verified. Claim dùng evidence RETRACTED hoặc UNVERIFIED bị BLOCK.
OFFLINE · KHÔNG PII · KHÔNG API · DRAFT-ONLY.
"""

from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
import pathlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .project_evidence_intake import (
    EvidenceSourceLedger,
    PIIInEvidenceError,
    VerificationState,
    contains_pii,
)

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ClaimType(str, enum.Enum):
    BACKGROUND  = "BACKGROUND"
    METHODS     = "METHODS"
    SAFETY      = "SAFETY"
    GUIDELINE   = "GUIDELINE"
    STATISTICAL = "STATISTICAL"
    REPORTING   = "REPORTING"


class ClaimStatus(str, enum.Enum):
    NOT_READY                            = "NOT_READY"
    REQUIRE_HUMAN_EVIDENCE_INPUT         = "REQUIRE_HUMAN_EVIDENCE_INPUT"
    REQUIRE_HUMAN_REVIEW                 = "REQUIRE_HUMAN_REVIEW"
    SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE = "SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE"
    BLOCKED_RETRACTED_EVIDENCE           = "BLOCKED_RETRACTED_EVIDENCE"
    BLOCKED_UNVERIFIED_EVIDENCE          = "BLOCKED_UNVERIFIED_EVIDENCE"


# Các trạng thái claim bị cấm dứt khoát (không có final/approved)
FORBIDDEN_CLAIM_STATUSES: frozenset = frozenset({
    "FINAL", "APPROVED", "CLINICALLY_VALIDATED", "PUBLISHED",
})

_CLAIM_DISCLAIMER = (
    "DRAFT — REQUIRE HUMAN REVIEW. "
    "Automation cannot create clinical claims. "
    "Reviewer identity authentication is not implemented. "
    "Reviewer independence is not established."
)


# ---------------------------------------------------------------------------
# ClaimRecord dataclass (13 fields)
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ClaimRecord:
    claim_id:               str
    project_id:             str
    artifact_id:            str
    artifact_version:       str
    claim_text:             str
    claim_type:             ClaimType
    claim_status:           ClaimStatus
    linked_source_ids:      List[str]
    evidence_status_summary: Dict[str, str]
    human_review_required:  bool
    blocking_reason:        str
    created_at_utc:         str
    audit_event_id:         str

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["claim_type"] = self.claim_type.value
        d["claim_status"] = self.claim_status.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ClaimRecord":
        d = dict(d)
        d["claim_type"] = ClaimType(d.get("claim_type", "BACKGROUND"))
        d["claim_status"] = ClaimStatus(d.get("claim_status", "NOT_READY"))
        return cls(**d)


# ---------------------------------------------------------------------------
# ClaimTraceabilityLedger — append-only JSONL
# ---------------------------------------------------------------------------

CLAIM_LEDGER_FILENAME = "claim_traceability_ledger.jsonl"


class ClaimTraceabilityLedger:
    """
    Append-only JSONL ledger cho ClaimRecord.
    Không có delete() hay update() — chỉ add().
    """

    def __init__(self, project_dir: pathlib.Path) -> None:
        self._path = pathlib.Path(project_dir) / CLAIM_LEDGER_FILENAME

    def add(self, record: ClaimRecord) -> None:
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def read_all(self) -> List[ClaimRecord]:
        if not self._path.exists():
            return []
        records: List[ClaimRecord] = []
        with self._path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(ClaimRecord.from_dict(json.loads(line)))
                except (json.JSONDecodeError, TypeError, KeyError, ValueError):
                    pass
        return records

    def exists(self) -> bool:
        return self._path.exists()

    @property
    def path(self) -> pathlib.Path:
        return self._path


# ---------------------------------------------------------------------------
# Business logic
# ---------------------------------------------------------------------------

def compute_claim_status(
    linked_source_ids: List[str],
    evidence_ledger: EvidenceSourceLedger,
) -> Tuple[ClaimStatus, str, Dict[str, str]]:
    """
    Tính ClaimStatus từ danh sách source_id liên kết và trạng thái ledger.

    Returns: (status, blocking_reason, summary_dict)
    """
    if not linked_source_ids:
        return (
            ClaimStatus.REQUIRE_HUMAN_EVIDENCE_INPUT,
            "Không có evidence source nào được liên kết với claim này.",
            {},
        )

    sources_by_id = {s.source_id: s for s in evidence_ledger.read_all()}
    summary: Dict[str, str] = {}

    for sid in linked_source_ids:
        source = sources_by_id.get(sid)
        summary[sid] = source.verification_state.value if source else "NOT_FOUND"

    # RETRACTED takes highest priority
    retracted = [
        sid for sid, state in summary.items()
        if state == VerificationState.RETRACTED.value
    ]
    if retracted:
        return (
            ClaimStatus.BLOCKED_RETRACTED_EVIDENCE,
            f"Evidence source bị RETRACTED: {retracted}. "
            "Claim bị block cho đến khi loại bỏ source đã bị rút.",
            summary,
        )

    # UNVERIFIED / REQUIRES_HUMAN_REVIEW / NOT_FOUND
    unverified = [
        sid for sid, state in summary.items()
        if state in (
            VerificationState.UNVERIFIED.value,
            VerificationState.REQUIRES_HUMAN_REVIEW.value,
            "NOT_FOUND",
        )
    ]
    if unverified:
        return (
            ClaimStatus.BLOCKED_UNVERIFIED_EVIDENCE,
            f"Evidence source chưa được human verified: {unverified}. "
            "Claim bị block cho đến khi reviewer xác minh.",
            summary,
        )

    # All linked sources are HUMAN_VERIFIED (and not EXCLUDED)
    return (
        ClaimStatus.SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE,
        "Tất cả evidence source được liên kết đã được human verified.",
        summary,
    )


def _make_claim_id(project_id: str, artifact_id: str, claim_text: str, ts: str) -> str:
    raw = f"{project_id}|{artifact_id}|{claim_text[:40]}|{ts}"
    return "CL-" + hashlib.sha256(raw.encode()).hexdigest()[:10].upper()


def register_claim(
    project_dir: pathlib.Path,
    project_id: str,
    artifact_id: str,
    artifact_version: str,
    claim_text: str,
    claim_type: ClaimType,
    linked_source_ids: List[str],
    automation_caller: bool = False,
) -> ClaimRecord:
    """
    Đăng ký một claim mới vào ClaimTraceabilityLedger.

    - automation_caller=True: vẫn được gọi để đăng ký, nhưng claim_status
      chỉ có thể là NOT_READY / REQUIRE_HUMAN_EVIDENCE_INPUT / BLOCKED_*.
      Automation không thể tạo ra SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE trực tiếp
      — trạng thái này chỉ xuất hiện khi evidence đã được human verify trước đó.
    - PII trong claim_text → PIIInEvidenceError.
    """
    if contains_pii(claim_text):
        raise PIIInEvidenceError(
            "PII detected in claim_text — không ghi thông tin định danh."
        )

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    claim_id = _make_claim_id(project_id, artifact_id, claim_text, ts)
    audit_event_id = "AE-" + hashlib.sha256(
        f"{claim_id}|{ts}".encode()
    ).hexdigest()[:8].upper()

    # Tính trạng thái
    ev_ledger = EvidenceSourceLedger(project_dir)
    status, blocking_reason, summary = compute_claim_status(
        linked_source_ids, ev_ledger
    )

    record = ClaimRecord(
        claim_id=claim_id,
        project_id=project_id,
        artifact_id=artifact_id,
        artifact_version=artifact_version,
        claim_text=claim_text,
        claim_type=claim_type,
        claim_status=status,
        linked_source_ids=list(linked_source_ids),
        evidence_status_summary=summary,
        human_review_required=True,
        blocking_reason=blocking_reason,
        created_at_utc=ts,
        audit_event_id=audit_event_id,
    )

    ledger = ClaimTraceabilityLedger(project_dir)
    ledger.add(record)
    return record


def get_claim_audit(project_dir: pathlib.Path, claim_id: Optional[str] = None) -> List[dict]:
    """
    Trả audit trail của claim(s). Nếu claim_id=None, trả tất cả.
    """
    ledger = ClaimTraceabilityLedger(project_dir)
    records = ledger.read_all()

    if claim_id is not None:
        records = [r for r in records if r.claim_id == claim_id]

    return [
        {
            "claim_id": r.claim_id,
            "artifact_id": r.artifact_id,
            "claim_type": r.claim_type.value,
            "claim_status": r.claim_status.value,
            "linked_source_ids": r.linked_source_ids,
            "blocking_reason": r.blocking_reason,
            "human_review_required": r.human_review_required,
            "created_at_utc": r.created_at_utc,
            "disclaimer": _CLAIM_DISCLAIMER,
        }
        for r in records
    ]
