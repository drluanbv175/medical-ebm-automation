"""
project_delegation_registry — R1.1 Offline Delegation Lifecycle.

Triển khai:
  - Delegation record model (không dùng SSO/e-signature thật)
  - Append-only JSONL registry
  - Lifecycle: PROPOSED → ACTIVE → EXPIRED/REVOKED/REJECTED
  - Guard: không cho phép self-delegation, không gán forbidden actions

OFFLINE · SYNTHETIC ONLY · KHÔNG API / PII / network.

Câu chữ bắt buộc:
  Manual attestation reference only.
  Not an authenticated delegation mechanism.
  Not an electronic signature or legal authorization.
"""

from __future__ import annotations

import json
import pathlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from research_project.project_rbac_simulation import FORBIDDEN_ACTIONS_ALL_ROLES


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

_DELEGATION_DISCLAIMER = (
    "Manual attestation reference only. "
    "Not an authenticated delegation mechanism. "
    "Not an electronic signature or legal authorization."
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DelegationStatus(str, Enum):
    """Vòng đời của một delegation record."""
    PROPOSED = "PROPOSED"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    REJECTED = "REJECTED"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class DelegationRecord:
    """
    Một delegation record trong append-only registry.

    Không chứa e-signature, không kết nối SSO, không có approval thật.
    """
    delegation_id: str
    principal_synthetic_actor_id: str    # người ủy quyền (thường là PI)
    delegatee_synthetic_actor_id: str    # người nhận ủy quyền
    delegated_role: str
    permitted_actions: List[str]
    effective_from_utc: str
    effective_until_utc: str
    reason: str
    status: str = DelegationStatus.PROPOSED.value
    created_at_utc: str = ""
    revoked_at_utc: Optional[str] = None
    revocation_reason: Optional[str] = None
    disclaimer: str = _DELEGATION_DISCLAIMER

    def __post_init__(self) -> None:
        if not self.created_at_utc:
            self.created_at_utc = _utc_now()
        _validate_delegation(self)

    def is_active(self, now_utc: Optional[datetime] = None) -> bool:
        """Trả True nếu delegation đang ở trạng thái ACTIVE và chưa hết hạn."""
        if self.status != DelegationStatus.ACTIVE.value:
            return False
        now = now_utc or datetime.now(timezone.utc)
        start = datetime.fromisoformat(self.effective_from_utc)
        end = datetime.fromisoformat(self.effective_until_utc)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return start <= now <= end

    def compute_status(self, now_utc: Optional[datetime] = None) -> str:
        """Tính status hiệu lực tại thời điểm now_utc."""
        if self.status in (DelegationStatus.REVOKED.value, DelegationStatus.REJECTED.value):
            return self.status
        if self.status == DelegationStatus.PROPOSED.value:
            return DelegationStatus.PROPOSED.value
        # ACTIVE → có thể EXPIRED
        now = now_utc or datetime.now(timezone.utc)
        end = datetime.fromisoformat(self.effective_until_utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if now > end:
            return DelegationStatus.EXPIRED.value
        return DelegationStatus.ACTIVE.value

    def to_dict(self) -> dict:
        return {
            "delegation_id": self.delegation_id,
            "principal_synthetic_actor_id": self.principal_synthetic_actor_id,
            "delegatee_synthetic_actor_id": self.delegatee_synthetic_actor_id,
            "delegated_role": self.delegated_role,
            "permitted_actions": self.permitted_actions,
            "effective_from_utc": self.effective_from_utc,
            "effective_until_utc": self.effective_until_utc,
            "reason": self.reason,
            "status": self.status,
            "created_at_utc": self.created_at_utc,
            "revoked_at_utc": self.revoked_at_utc,
            "revocation_reason": self.revocation_reason,
            "disclaimer": self.disclaimer,
        }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class DelegationError(ValueError):
    """Raised khi delegation record vi phạm policy."""


def _validate_delegation(record: DelegationRecord) -> None:
    """Block self-delegation và forbidden-action delegation."""
    if record.principal_synthetic_actor_id == record.delegatee_synthetic_actor_id:
        raise DelegationError(
            f"Self-delegation không được phép: "
            f"principal_id='{record.principal_synthetic_actor_id}' == delegatee_id."
        )
    forbidden_in_delegation = [
        a for a in record.permitted_actions
        if a in FORBIDDEN_ACTIONS_ALL_ROLES
    ]
    if forbidden_in_delegation:
        raise DelegationError(
            f"Delegation không thể gán forbidden actions: {forbidden_in_delegation}. "
            + _DELEGATION_DISCLAIMER
        )
    if not record.permitted_actions:
        raise DelegationError("Delegation phải có ít nhất 1 permitted_action.")
    # Validate date window
    try:
        start = datetime.fromisoformat(record.effective_from_utc)
        end = datetime.fromisoformat(record.effective_until_utc)
    except ValueError as exc:
        raise DelegationError(f"Date parse error: {exc}") from exc
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    if end <= start:
        raise DelegationError(
            f"effective_until_utc ({record.effective_until_utc}) phải sau "
            f"effective_from_utc ({record.effective_from_utc})."
        )


# ---------------------------------------------------------------------------
# Append-only registry
# ---------------------------------------------------------------------------

class DelegationRegistry:
    """
    Append-only JSONL registry của delegation records.

    Không có DELETE, không có UPDATE trực tiếp; revoke tạo thêm 1 record.
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

    def propose(
        self,
        principal_id: str,
        delegatee_id: str,
        delegated_role: str,
        permitted_actions: List[str],
        effective_from_utc: str,
        effective_until_utc: str,
        reason: str,
    ) -> DelegationRecord:
        """Tạo delegation ở trạng thái PROPOSED."""
        record = DelegationRecord(
            delegation_id=f"DEL-{uuid.uuid4().hex[:12].upper()}",
            principal_synthetic_actor_id=principal_id,
            delegatee_synthetic_actor_id=delegatee_id,
            delegated_role=delegated_role,
            permitted_actions=permitted_actions,
            effective_from_utc=effective_from_utc,
            effective_until_utc=effective_until_utc,
            reason=reason,
            status=DelegationStatus.PROPOSED.value,
        )
        self._append(record.to_dict())
        return record

    def activate(self, delegation_id: str) -> DelegationRecord:
        """Kích hoạt một PROPOSED delegation → ACTIVE."""
        record = self._get_latest_state(delegation_id)
        if record is None:
            raise DelegationError(f"delegation_id '{delegation_id}' không tìm thấy.")
        if record.status != DelegationStatus.PROPOSED.value:
            raise DelegationError(
                f"Chỉ PROPOSED delegation mới có thể activate; "
                f"current_status='{record.status}'."
            )
        updated = {**record.to_dict(), "status": DelegationStatus.ACTIVE.value}
        self._append(updated)
        return DelegationRecord(**{k: v for k, v in updated.items() if k != "disclaimer"})

    def revoke(self, delegation_id: str, revocation_reason: str) -> DelegationRecord:
        """Thu hồi một ACTIVE delegation → REVOKED."""
        record = self._get_latest_state(delegation_id)
        if record is None:
            raise DelegationError(f"delegation_id '{delegation_id}' không tìm thấy.")
        live_status = record.compute_status()
        if live_status not in (DelegationStatus.ACTIVE.value, DelegationStatus.PROPOSED.value):
            raise DelegationError(
                f"Không thể revoke delegation có status='{live_status}'."
            )
        ts = _utc_now()
        updated = {
            **record.to_dict(),
            "status": DelegationStatus.REVOKED.value,
            "revoked_at_utc": ts,
            "revocation_reason": revocation_reason,
        }
        self._append(updated)
        return DelegationRecord(**{k: v for k, v in updated.items() if k != "disclaimer"})

    def reject(self, delegation_id: str, reason: str) -> DelegationRecord:
        """Từ chối một PROPOSED delegation → REJECTED."""
        record = self._get_latest_state(delegation_id)
        if record is None:
            raise DelegationError(f"delegation_id '{delegation_id}' không tìm thấy.")
        if record.status != DelegationStatus.PROPOSED.value:
            raise DelegationError(
                f"Chỉ PROPOSED delegation mới có thể reject; "
                f"current_status='{record.status}'."
            )
        updated = {
            **record.to_dict(),
            "status": DelegationStatus.REJECTED.value,
            "revocation_reason": reason,
        }
        self._append(updated)
        return DelegationRecord(**{k: v for k, v in updated.items() if k != "disclaimer"})

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_status(
        self, delegation_id: str, now_utc: Optional[datetime] = None
    ) -> Optional[str]:
        """Trả status hiệu lực tại thời điểm now_utc, hoặc None nếu không tìm thấy."""
        record = self._get_latest_state(delegation_id)
        if record is None:
            return None
        return record.compute_status(now_utc)

    def list_active(self, now_utc: Optional[datetime] = None) -> List[DelegationRecord]:
        """Trả danh sách delegation đang ACTIVE tại thời điểm now_utc."""
        seen: dict[str, DelegationRecord] = {}
        for entry in self._read_all():
            did = entry.get("delegation_id", "")
            if did:
                # Reconstruct, skip disclaimer field
                r = _record_from_dict(entry)
                seen[did] = r
        return [r for r in seen.values() if r.compute_status(now_utc) == DelegationStatus.ACTIVE.value]

    def all_records(self) -> List[DelegationRecord]:
        """Trả toàn bộ JSONL entries (snapshot cuối của mỗi delegation_id)."""
        seen: dict[str, DelegationRecord] = {}
        for entry in self._read_all():
            did = entry.get("delegation_id", "")
            if did:
                seen[did] = _record_from_dict(entry)
        return list(seen.values())

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _append(self, data: dict) -> None:
        """Append 1 JSONL line — không đè, không xóa."""
        line = json.dumps(data, ensure_ascii=False) + "\n"
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

    def _get_latest_state(self, delegation_id: str) -> Optional[DelegationRecord]:
        """Trả state cuối cùng của một delegation_id trong ledger."""
        latest: Optional[dict] = None
        for entry in self._read_all():
            if entry.get("delegation_id") == delegation_id:
                latest = entry
        if latest is None:
            return None
        return _record_from_dict(latest)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _record_from_dict(d: dict) -> DelegationRecord:
    """Tạo DelegationRecord từ dict (bỏ trường disclaimer để tránh lỗi __init__)."""
    clean = {k: v for k, v in d.items() if k != "disclaimer"}
    return DelegationRecord(**clean)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
