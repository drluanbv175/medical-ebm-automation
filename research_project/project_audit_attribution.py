"""
project_audit_attribution — R1.1.2 Tamper-Evident Local Audit Ledger Simulation.

Triển khai:
  - Synthetic audit event model (18 fields = 17 R1.0 fields + sequence_number)
  - Append-only JSONL với SHA-256 hash chain
  - Tamper detection: modified content · missing hash link · sequence discontinuity ·
    deleted middle record · duplicate event_id · out-of-order sequence
  - Monotonic sequence_number per ledger instance
  - Ledger root hash (hash of concatenated event hashes)
  - Checkpoint record
  - Marker bắt buộc: is_synthetic=True, production_valid=False

PHÂN LOẠI ĐÚNG: tamper-evident local audit ledger simulation.
KHÔNG PHẢI: WORM storage · immutable storage · regulatory-compliant retention
             · production audit storage.

PROD-AUD-01 (NOT IMPLEMENTED): Production requires external WORM-capable retention,
  retention policy, legal hold, off-system backup, access-controlled archive,
  and independent restore verification. Deferred to R1.3.

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

# Production WORM dependency marker — NOT IMPLEMENTED offline
PROD_AUD_01_WORM_DEPENDENCY = "NOT_IMPLEMENTED"

# Local ledger classification — must never be called WORM
LOCAL_LEDGER_CLASSIFICATION = "TAMPER_EVIDENT_LOCAL_SIMULATION_NOT_WORM"


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
    18-field synthetic audit event (17 R1.0 fields + sequence_number).

    is_synthetic=True, production_valid=False bắt buộc.
    Không chứa PII, không chứa credential thật.
    sequence_number: monotonic counter assigned by ledger (1-based).
    """
    event_id: str
    synthetic_actor_id: str
    actor_role_at_event_time: str
    action_type: str
    object_id: str
    object_version: str
    timestamp_utc: str
    reason: str
    # Monotonic sequence for tamper detection
    sequence_number: int = 0
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
            "sequence_number": self.sequence_number,
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
            "local_ledger_classification": LOCAL_LEDGER_CLASSIFICATION,
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
    Kiểm tra tính toàn vẹn của chuỗi hash chain (enhanced R1.1.2).

    Phát hiện:
      - modified event content (hash mismatch)
      - missing previous_event_hash link (chain break)
      - sequence_number discontinuity (gaps between consecutive seq nums)
      - deleted middle record (same as sequence discontinuity)
      - duplicate event_id
      - out-of-order event (seq_number[i] <= seq_number[i-1])

    Returns: (ok, errors)
      ok=True nếu không có lỗi nào.
      errors là danh sách mô tả vi phạm tìm thấy.

    Giới hạn bắt buộc phải ghi nhận:
      Phát hiện được tamper trong JSONL file đang nắm giữ.
      KHÔNG ngăn được replace-then-rehash toàn bộ file trên filesystem.
      Production cần WORM/off-system backup (PROD-AUD-01, NOT IMPLEMENTED).
    """
    errors: List[str] = []
    prev_hash: Optional[str] = None
    prev_seq: Optional[int] = None
    seen_event_ids: dict = {}

    for i, ev in enumerate(events):
        # Vá 2026-09-06 (audit vòng 40, phát hiện #3): create_checkpoint()
        # append một dict KHÁC SCHEMA (không có event_id/audit_event_hash/
        # previous_event_hash/sequence_number của SyntheticAuditEvent) vào
        # CÙNG file JSONL. Đưa checkpoint vào vòng lặp kiểm event như một
        # event thật sinh ra 2 lỗi tamper GIẢ (hash rỗng không khớp, chain
        # break) CHO CHÍNH checkpoint, rồi còn làm prev_hash/prev_seq bị
        # checkpoint "xoá" (None/rỗng) nên sự kiện THẬT ngay sau checkpoint
        # cũng bị báo sai "chain break"/"sequence discontinuity" dù chưa hề
        # bị sửa. Checkpoint không phải một mắt xích của chuỗi hash sự kiện
        # nên bị bỏ qua hoàn toàn ở đây; prev_hash/prev_seq giữ nguyên từ sự
        # kiện THẬT gần nhất.
        if ev.get("checkpoint_type") == "LEDGER_CHECKPOINT":
            continue

        event_id = ev.get("event_id", f"<idx={i}>")
        stored_hash = ev.get("audit_event_hash", "")
        stored_prev = ev.get("previous_event_hash")
        seq_num = ev.get("sequence_number")

        # 1. Hash integrity — modified event content
        expected_hash = compute_event_hash(ev)
        if stored_hash != expected_hash:
            errors.append(
                f"[{event_id}] audit_event_hash không khớp (modified content): "
                f"stored='{stored_hash[:16]}...' expected='{expected_hash[:16]}...'"
            )

        # 2. Hash chain link — missing/broken previous_event_hash
        expected_prev = prev_hash if prev_hash is not None else _GENESIS_HASH
        if stored_prev != expected_prev:
            errors.append(
                f"[{event_id}] previous_event_hash chain break: "
                f"stored='{str(stored_prev)[:16]}' expected='{str(expected_prev)[:16]}'"
            )

        # 3. Duplicate event_id
        if event_id in seen_event_ids:
            errors.append(
                f"[{event_id}] duplicate event_id: "
                f"first seen at index={seen_event_ids[event_id]}, duplicate at index={i}"
            )
        else:
            seen_event_ids[event_id] = i

        # 4. Sequence number checks (if present)
        if seq_num is not None:
            if prev_seq is None:
                # First event: sequence_number should be 1
                if seq_num != 1:
                    errors.append(
                        f"[{event_id}] sequence_number phải bắt đầu từ 1: got {seq_num}"
                    )
            else:
                # Out-of-order event
                if seq_num <= prev_seq:
                    errors.append(
                        f"[{event_id}] out-of-order sequence: "
                        f"seq={seq_num} <= prev_seq={prev_seq}"
                    )
                # Sequence discontinuity / deleted middle record
                elif seq_num != prev_seq + 1:
                    errors.append(
                        f"[{event_id}] sequence discontinuity (possible deleted middle record): "
                        f"prev_seq={prev_seq}, current_seq={seq_num}, expected={prev_seq + 1}"
                    )
            prev_seq = seq_num

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

        # Lấy hash của event THẬT cuối cùng + sequence number tiếp theo.
        # Vá 2026-09-06 (audit vòng 40, phát hiện #3): trước đây dùng thẳng
        # self._read_all()[-1] — DÒNG JSONL CUỐI CÙNG bất kể là event hay
        # checkpoint (create_checkpoint() ghi vào CÙNG file JSONL). Nếu dòng
        # cuối là checkpoint (không có khoá "audit_event_hash") thì
        # prev_hash âm thầm rơi về GENESIS thay vì hash của event thật liền
        # trước, và sequence_number đếm CẢ checkpoint vào — chuỗi hash/
        # sequence bị đứt thật sự trong dữ liệu lưu (không chỉ báo sai ở
        # verify_hash_chain()). Nay chỉ đếm/nối chuỗi theo các dòng THẬT là
        # event (bỏ qua mọi checkpoint).
        all_lines = self._read_all()
        prior_events = [
            e for e in all_lines if e.get("checkpoint_type") != "LEDGER_CHECKPOINT"
        ]
        prev_hash: Optional[str]
        if prior_events:
            prev_hash = prior_events[-1].get("audit_event_hash", _GENESIS_HASH)
        else:
            prev_hash = _GENESIS_HASH
        next_seq = len(prior_events) + 1  # 1-based monotonic sequence (chỉ event thật)

        event = SyntheticAuditEvent(
            event_id=event_id,
            synthetic_actor_id=synthetic_actor_id,
            actor_role_at_event_time=actor_role_at_event_time,
            action_type=action_type,
            object_id=object_id,
            object_version=object_version,
            timestamp_utc=ts,
            reason=reason,
            sequence_number=next_seq,
            delegation_reference_if_any=delegation_reference_if_any,
            before_state_hash_if_applicable=before_state_hash_if_applicable,
            after_state_hash_if_applicable=after_state_hash_if_applicable,
            previous_event_hash=prev_hash,
        )

        # Tính hash sau khi tất cả các field (kể cả sequence_number) đã được đặt
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

    def ledger_root_hash(self) -> str:
        """
        Tính root hash của toàn bộ ledger = SHA-256(concat of RECOMPUTED event hashes).

        Recompute (không dùng stored audit_event_hash) để phát hiện cả:
          - content modification (recomputed hash thay đổi)
          - hash field modification (stored hash thay đổi, nếu có)
        Không phải WORM — replace-then-rehash toàn bộ file vẫn có thể bypass.
        Production cần WORM/off-system backup (PROD-AUD-01, NOT IMPLEMENTED).
        """
        events = self._read_all()
        concatenated = "".join(compute_event_hash(ev) for ev in events)
        return hashlib.sha256(concatenated.encode("ascii")).hexdigest()

    def create_checkpoint(self, checkpoint_reason: str = "PERIODIC") -> dict:
        """
        Tạo một checkpoint record ghi nhận root hash và sequence number hiện tại.

        Checkpoint không phải event audit — không có synthetic_actor_id.
        Không phải WORM checkpoint — chỉ là point-in-time snapshot cho local verification.
        """
        events = self._read_all()
        root = self.ledger_root_hash()
        cp = {
            "checkpoint_type": "LEDGER_CHECKPOINT",
            "checkpoint_sequence_reference": len(events),
            "ledger_root_hash": root,
            "event_count": len(events),
            "checkpoint_reason": checkpoint_reason,
            "timestamp_utc": _utc_now(),
            "local_ledger_classification": LOCAL_LEDGER_CLASSIFICATION,
            "production_worm_dependency": PROD_AUD_01_WORM_DEPENDENCY,
        }
        self._append(cp)
        return cp

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
