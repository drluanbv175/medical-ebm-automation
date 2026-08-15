"""
R2.0 Synthetic EDC Lifecycle — Đóng băng, khóa, xuất, audit, sao lưu/phục hồi.

Chỉ dùng trong harness kiểm thử offline tổng hợp.
KHÔNG xử lý dữ liệu nghiên cứu thật hoặc PII.
KHÔNG xuất file thật ra ngoài hệ thống.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

from research_project.synthetic_edc_core import DISCLAIMER_EDC, SYNTHETIC_EDC_CLASSIFICATION

# ── Trạng thái bản ghi ─────────────────────────────────────────────────────

class RecordStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    QUERIED = "QUERIED"
    CORRECTED = "CORRECTED"
    FROZEN = "FROZEN"
    LOCKED = "LOCKED"


# ── Bản ghi tổng hợp ───────────────────────────────────────────────────────

@dataclass
class SyntheticRecord:
    """
    Một bản ghi dữ liệu nghiên cứu tổng hợp trong harness EDC.
    Không chứa PII thật; tất cả dữ liệu là tổng hợp.
    """

    record_id: str
    subject_id: str
    crf_version_id: str
    data: Dict[str, Any]
    status: RecordStatus = RecordStatus.DRAFT
    created_at_utc: str = "2026-06-28T00:00:00Z"
    last_modified_utc: str = "2026-06-28T00:00:00Z"
    actor_id: str = "synthetic_actor"
    attribution_mode: str = "SYNTHETIC"
    disclaimer: str = DISCLAIMER_EDC

    def __post_init__(self) -> None:
        if not self.record_id:
            raise ValueError("record_id must be non-empty")
        if not self.subject_id:
            raise ValueError("subject_id must be non-empty")
        if not self.crf_version_id:
            raise ValueError("crf_version_id must be non-empty")


# ── Audit và provenance ────────────────────────────────────────────────────

@dataclass
class AuditEntry:
    """Mục nhật ký audit cho một sự kiện trong vòng đời EDC."""

    entry_id: str
    event_type: str
    record_id: str
    actor_id: str
    timestamp_utc: str
    detail: str
    attribution_mode: str = "SYNTHETIC"
    classification: str = SYNTHETIC_EDC_CLASSIFICATION
    disclaimer: str = DISCLAIMER_EDC

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "event_type": self.event_type,
            "record_id": self.record_id,
            "actor_id": self.actor_id,
            "timestamp_utc": self.timestamp_utc,
            "detail": self.detail,
            "attribution_mode": self.attribution_mode,
            "classification": self.classification,
            "disclaimer": self.disclaimer,
        }


class EDCAuditLog:
    """Nhật ký audit EDC — ghi tất cả sự kiện vòng đời."""

    def __init__(self) -> None:
        self._entries: List[AuditEntry] = []

    def log(self, event_type: str, record_id: str, actor_id: str,
            timestamp_utc: str, detail: str) -> AuditEntry:
        entry = AuditEntry(
            entry_id=str(uuid.uuid4()),
            event_type=event_type,
            record_id=record_id,
            actor_id=actor_id,
            timestamp_utc=timestamp_utc,
            detail=detail,
        )
        self._entries.append(entry)
        return entry

    def entries_for_record(self, record_id: str) -> List[AuditEntry]:
        return [e for e in self._entries if e.record_id == record_id]

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def all_entries(self) -> List[AuditEntry]:
        return list(self._entries)


# ── Đóng băng dữ liệu ─────────────────────────────────────────────────────

class DataFreezeManager:
    """
    Mô phỏng đóng băng dữ liệu (data freeze).
    Sau khi đóng băng: bản ghi chuyển sang FROZEN — không thể sửa thêm trường.
    """

    def __init__(self, audit_log: EDCAuditLog) -> None:
        self._frozen_records: set = set()
        self._audit = audit_log

    def freeze(self, record: SyntheticRecord, actor_id: str, timestamp_utc: str,
               reason: str) -> None:
        """Đóng băng bản ghi."""
        if record.status == RecordStatus.LOCKED:
            raise PermissionError(f"Record {record.record_id} is LOCKED — cannot freeze")
        if record.record_id in self._frozen_records:
            raise ValueError(f"Record {record.record_id} already frozen")
        record.status = RecordStatus.FROZEN
        self._frozen_records.add(record.record_id)
        self._audit.log("DATA_FREEZE", record.record_id, actor_id, timestamp_utc,
                        f"Reason: {reason}")

    def unfreeze(self, record: SyntheticRecord, actor_id: str, timestamp_utc: str,
                 reason: str) -> None:
        """Hủy đóng băng bản ghi (chỉ khi chưa khóa)."""
        if record.status == RecordStatus.LOCKED:
            raise PermissionError(f"Record {record.record_id} is LOCKED — cannot unfreeze")
        if record.record_id not in self._frozen_records:
            raise ValueError(f"Record {record.record_id} is not frozen")
        record.status = RecordStatus.ACTIVE
        self._frozen_records.discard(record.record_id)
        self._audit.log("DATA_UNFREEZE", record.record_id, actor_id, timestamp_utc,
                        f"Reason: {reason}")

    def is_frozen(self, record_id: str) -> bool:
        return record_id in self._frozen_records


# ── Khóa dữ liệu ──────────────────────────────────────────────────────────

class DataLockManager:
    """
    Mô phỏng khóa dữ liệu (data lock).
    Sau khi khóa: bản ghi không thể sửa hay hủy đóng băng.
    """

    def __init__(self, audit_log: EDCAuditLog) -> None:
        self._locked_records: set = set()
        self._audit = audit_log

    def lock(self, record: SyntheticRecord, actor_id: str, timestamp_utc: str,
             authority: str) -> None:
        """Khóa bản ghi — yêu cầu authority rõ ràng."""
        if not authority:
            raise ValueError("authority reference must be non-empty to lock a record")
        if record.record_id in self._locked_records:
            raise ValueError(f"Record {record.record_id} already locked")
        record.status = RecordStatus.LOCKED
        self._locked_records.add(record.record_id)
        self._audit.log("DATA_LOCK", record.record_id, actor_id, timestamp_utc,
                        f"Authority: {authority}")

    def is_locked(self, record_id: str) -> bool:
        return record_id in self._locked_records

    def attempt_modify_locked(self, record_id: str) -> None:
        """Ném PermissionError nếu cố sửa bản ghi đã khóa."""
        if record_id in self._locked_records:
            raise PermissionError(f"Record {record_id} is LOCKED — modification forbidden")


# ── Export Manifest ────────────────────────────────────────────────────────

@dataclass
class ExportManifest:
    """Phiếu xuất dữ liệu — mô tả nội dung và checksum của một lô xuất."""

    manifest_id: str
    export_timestamp_utc: str
    actor_id: str
    record_ids: List[str]
    record_count: int
    content_hash: str
    classification: str = SYNTHETIC_EDC_CLASSIFICATION
    is_synthetic: bool = True
    disclaimer: str = DISCLAIMER_EDC

    def __post_init__(self) -> None:
        if self.record_count != len(self.record_ids):
            raise ValueError("record_count must match len(record_ids)")


class ExportManager:
    """Tạo export manifest từ danh sách bản ghi đã khóa."""

    def __init__(self, audit_log: EDCAuditLog) -> None:
        self._audit = audit_log

    def create_manifest(
        self,
        records: List[SyntheticRecord],
        actor_id: str,
        timestamp_utc: str,
    ) -> ExportManifest:
        """Tạo manifest cho một lô xuất; chỉ cho phép LOCKED records."""
        non_locked = [r for r in records if r.status != RecordStatus.LOCKED]
        if non_locked:
            ids = [r.record_id for r in non_locked]
            raise PermissionError(f"Cannot export non-locked records: {ids}")

        record_ids = [r.record_id for r in records]
        content = json.dumps(
            [{"record_id": r.record_id, "data": r.data} for r in records],
            sort_keys=True
        )
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        manifest = ExportManifest(
            manifest_id=str(uuid.uuid4()),
            export_timestamp_utc=timestamp_utc,
            actor_id=actor_id,
            record_ids=record_ids,
            record_count=len(records),
            content_hash=content_hash,
        )
        self._audit.log("DATA_EXPORT", "BATCH", actor_id, timestamp_utc,
                        f"manifest_id={manifest.manifest_id} records={len(records)}")
        return manifest


# ── Backup và phục hồi tổng hợp ────────────────────────────────────────────

@dataclass
class BackupReceipt:
    """Biên lai sao lưu tổng hợp."""

    backup_id: str
    timestamp_utc: str
    record_count: int
    content_hash: str
    is_synthetic: bool = True
    disclaimer: str = DISCLAIMER_EDC


class SyntheticBackupManager:
    """
    Mô phỏng sao lưu và phục hồi dữ liệu EDC trong bộ nhớ.
    KHÔNG ghi ra disk thật hay cloud storage.
    """

    NOT_IMPLEMENTED = (
        "SyntheticBackupManager is an offline simulation only. "
        "Real backup requires external off-system storage."
    )

    def __init__(self) -> None:
        self._backups: Dict[str, dict] = {}

    def backup(self, records: List[SyntheticRecord], timestamp_utc: str) -> BackupReceipt:
        """Sao lưu danh sách bản ghi vào bộ nhớ tạm."""
        snapshot = {r.record_id: dict(r.data) for r in records}
        content = json.dumps(snapshot, sort_keys=True)
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        backup_id = str(uuid.uuid4())
        self._backups[backup_id] = snapshot
        return BackupReceipt(
            backup_id=backup_id,
            timestamp_utc=timestamp_utc,
            record_count=len(records),
            content_hash=content_hash,
        )

    def restore(self, backup_id: str) -> Dict[str, dict]:
        """Phục hồi bản ghi từ backup_id; trả dict record_id → data."""
        if backup_id not in self._backups:
            raise KeyError(f"backup_id not found: {backup_id}")
        return dict(self._backups[backup_id])

    def verify(self, backup_id: str, expected_hash: str) -> bool:
        """Kiểm tra hash nội dung backup so với expected."""
        if backup_id not in self._backups:
            return False
        snapshot = self._backups[backup_id]
        content = json.dumps(snapshot, sort_keys=True)
        actual_hash = hashlib.sha256(content.encode()).hexdigest()
        return actual_hash == expected_hash

    def backup_count(self) -> int:
        return len(self._backups)
