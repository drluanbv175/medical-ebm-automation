"""
project_audit_attribution — R1.1 Offline Audit Attribution Simulation.

Triển khai:
  - Synthetic audit event model (17 fields theo R1.0 schema)
  - Append-only JSONL với hash chain
  - Tamper detection
  - Marker bắt buộc: is_synthetic=True, production_valid=False

OFFLINE · SYNTHETIC ONLY · KHÔNG API / PII / network.

Câu chữ bắt buộc:
  Simulated audit attribution only.
  Not a production audit trail.
  Not an authenticated event record.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

_AUDIT_DISCLAIMER = (
    "Simulated audit attribution only. "
    "Not a production audit trail. "
    "Not an authenticated event record."
)

_GENESIS_HASH = "GENESIS"

_INTEGRITY_METHOD = "SHA256_HASH_CHAIN_SYNTHETIC"


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AuditActionType(str, Enum):
    """Các action type có thể ghi nhận trong synthetic audit trail."""
    # Research workflow
    PROJECT_CREATED = "PROJECT_CREATED"
    ARTIFACT_EDITED = "ARTIFACT_EDITED"
    ARTIFACT_LOCKED = "ARTIFACT_LOCKED"
    ARTIFACT_UNLOCKED = "ARTIFACT_UNLOCKED"
    REVIEW_ATTESTATION_RECORDED = "REVIEW_ATTESTATION_RECORDED"
    EVIDENCE_ATTESTATION_RECORDED = "EVIDENCE_ATTESTATION_RECORDED"
    CLAIM_REGISTERED = "CLAIM_REGISTERED"
    CLAIM_RETRACTED = "CLAIM_RETRACTED"
    REVISION_REQUESTED = "REVISION_REQUESTED"
    EXPORT_REQUESTED = "EXPORT_REQUESTED"
    # Identity/delegation (synthetic)
    ROLE_ASSIGNED = "ROLE_ASSIGNED"
    ROLE_REVOKED = "ROLE_REVOKED"
    DELEGATION_PROPOSED = "DELEGATION_PROPOSED"
    DELEGATION_ACTIVATED = "DELEGATION_ACTIVATED"
    DELEGATION_REVOKED = "DELEGATION_REVOKED"
    DELEGATION_REJECTED = "DELEGATION_REJECTED"
    # Audit-meta
    AUDIT_VERIFICATION_RUN = "AUDIT_VERIFICATION_RUN"
    RBAC_DECISION_BLOCK = "RBAC_DECISION_BLOCK"
    RBAC_DECISION_ALLOW = "RBAC_DECISION_ALLOW"
    # Access
    AUDIT_LOG_VIEWED = "AUDIT_LOG_VIEWED"
    EVIDENCE_LEDGER_VIEWED = "EVIDENCE_LEDGER_VIEWED"
    SYSTEM_CONFIG_VIEWED = "SYSTEM_CONFIG_VIEWED"
    SYSTEM_CONFIG_MODIFIED = "SYSTEM_CONFIG_MODIFIED"
    DATA_LOCKED = "DATA_LOCKED"
    DATA_UNLOCKED = "DATA_UNLOCKED"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class SyntheticAuditEvent:
    """
    17-field synthetic audit event theo R1.0 schema.

    is_synthetic=True, production_valid=False bắt buộc.
    Không chứa PII, không chứa credential thật.
    """
    event_id: str
    synthetic_actor_id: str
    actor_role_at_event_time: str
    action_type: str
    object_id: str
    object_version: str
    timestamp_utc: str
    reason: str
    # Optional fields
    delegation_reference_if_any: Optional[str] = None
    before_state_hash_if_applicable: Optional[str] = None
    after_state_hash_if_applicable: Optional[str] = None
    # Immutable markers
    authentication_context: str = "SIMULATED_NOT_AUTHENTICATED"
    integrity_protection_method: str = _INTEGRITY_METHOD
    is_synthetic: bool = True
    production_valid: bool = False
    # Hash chain
    audit_event_hash: str = ""
    previous_event_hash: Optional[str] = None
    disclaimer: str = _AUDIT_DISCLAIMER

    def __post_init__(self) -> None:
        if self.is_synthetic is not True:
            raise ValueError("is_synthetic phải là True.")
        if self.production_valid is not False:
            raise ValueError("production_valid phải là False.")

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "synthetic_actor_id": self.synthetic_actor_id,
            "actor_role_at_event_time": self.actor_role_at_event_time,
            "delegation_reference_if_any": self.delegation_reference_if_any,
            "authentication_context": self.authentication_context,
            "action_type": self.action_type,
            "object_id": self.object_id,
            "object_version": self.object_version,
            "before_state_hash_if_applicable": self.before_state_hash_if_applicable,
            "after_state_hash_if_applicable": self.after_state_hash_if_applicable,
            "timestamp_utc": self.timestamp_utc,
            "reason": self.reason,
            "integrity_protection_method": self.integrity_protection_method,
            "is_synthetic": self.is_synthetic,
            "production_valid": self.production_valid,
            "audit_event_hash": self.audit_event_hash,
            "previous_event_hash": self.previous_event_hash,
            "disclaimer": self.disclaimer,
        }


# ---------------------------------------------------------------------------
# Hash chain
# ---------------------------------------------------------------------------

def compute_event_hash(event_dict: dict) -> str:
    """
    SHA-256 của JSON(event minus audit_event_hash field).

    Deterministic: sort_keys=True, ensure_ascii=True.
    """
    d = {k: v for k, v in event_dict.items() if k != "audit_event_hash"}
    payload = json.dumps(d, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def verify_hash_chain(events: List[dict]) -> tuple[bool, List[str]]:
    """
    Kiểm tra tính toàn vẹn của chuỗi hash chain.

    Returns: (ok, errors)
      ok=True nếu không có lỗi nào.
      errors là danh sách mô tả vi phạm tìm thấy.
    """
    errors: List[str] = []
    prev_hash: Optional[str] = None

    for i, ev in enumerate(events):
        event_id = ev.get("event_id", f"<idx={i}>")
        stored_hash = ev.get("audit_event_hash", "")
        stored_prev = ev.get("previous_event_hash")

        # 1. Recompute hash
        expected_hash = compute_event_hash(ev)
        if stored_hash != expected_hash:
            errors.append(
                f"[{event_id}] audit_event_hash không khớp: "
                f"stored='{stored_hash[:16]}...' expected='{expected_hash[:16]}...'"
            )

        # 2. Check previous_event_hash link
        expected_prev = prev_hash if prev_hash is not None else _GENESIS_HASH
        if stored_prev != expected_prev:
            errors.append(
                f"[{event_id}] previous_event_hash không khớp với hash của event trước: "
                f"stored='{str(stored_prev)[:16]}' expected='{str(expected_prev)[:16]}'"
            )

        prev_hash = stored_hash

    return (len(errors) == 0, errors)


# ---------------------------------------------------------------------------
# Append-only ledger
# ---------------------------------------------------------------------------

class AuditAttributionLedger:
    """
    Append-only JSONL ledger với SHA-256 hash chain.

    Không có DELETE, không có UPDATE.
    Không gọi network, không lưu credential thật.
    """

    def __init__(self, ledger_path: pathlib.Path) -> None:
        self._path = ledger_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("", encoding="utf-8")

    # ------------------------------------------------------------------
    # Write (append-only)
    # ------------------------------------------------------------------

    def record(
        self,
        synthetic_actor_id: str,
        actor_role_at_event_time: str,
        action_type: str,
        object_id: str,
        reason: str,
        object_version: str = "1",
        delegation_reference_if_any: Optional[str] = None,
        before_state_hash_if_applicable: Optional[str] = None,
        after_state_hash_if_applicable: Optional[str] = None,
    ) -> SyntheticAuditEvent:
        """Append một audit event mới vào ledger."""
        ts = _utc_now()
        event_id = f"AUD-{uuid.uuid4().hex[:12].upper()}"

        # Lấy hash của event cuối trong ledger (nếu có)
        all_events = self._read_all()
        prev_hash: Optional[str]
        if all_events:
            prev_hash = all_events[-1].get("audit_event_hash", _GENESIS_HASH)
        else:
            prev_hash = _GENESIS_HASH

        event = SyntheticAuditEvent(
            event_id=event_id,
            synthetic_actor_id=synthetic_actor_id,
            actor_role_at_event_time=actor_role_at_event_time,
            action_type=action_type,
            object_id=object_id,
            object_version=object_version,
            timestamp_utc=ts,
            reason=reason,
            delegation_reference_if_any=delegation_reference_if_any,
            before_state_hash_if_applicable=before_state_hash_if_applicable,
            after_state_hash_if_applicable=after_state_hash_if_applicable,
            previous_event_hash=prev_hash,
        )

        # Tính hash sau khi previous_event_hash đã được đặt
        d = event.to_dict()
        event.audit_event_hash = compute_event_hash(d)
        d["audit_event_hash"] = event.audit_event_hash

        self._append(d)
        return event

    # ------------------------------------------------------------------
    # Read & Verify
    # ------------------------------------------------------------------

    def read_all(self) -> List[dict]:
        """Trả toàn bộ events từ ledger (không xóa, không sửa)."""
        return self._read_all()

    def verify(self) -> tuple[bool, List[str]]:
        """Kiểm tra toàn vẹn hash chain của ledger."""
        events = self._read_all()
        return verify_hash_chain(events)

    def event_count(self) -> int:
        return len(self._read_all())

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _append(self, data: dict) -> None:
        """Append 1 JSONL line — không đè, không xóa."""
        line = json.dumps(data, sort_keys=True, ensure_ascii=False) + "\n"
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line)

    def _read_all(self) -> List[dict]:
        lines = self._path.read_text(encoding="utf-8").splitlines()
        result = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    result.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
