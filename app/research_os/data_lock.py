"""Data lock với hash manifest (G6).

Quy tắc: không bao giờ sửa dữ liệu gốc sau khi khoá.
verify_dataset_hash() dùng để kiểm tra tính toàn vẹn sau khoá.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping


@dataclass(frozen=True)
class DataLockRecord:
    """Bản ghi khoá dữ liệu bất biến."""
    lock_id: str
    dataset_hash: str
    locked_at: str
    locked_by: str


def _compute_hash(dataset_manifest: Mapping[str, object]) -> str:
    """Tính SHA-256 của manifest (JSON chuẩn hoá)."""
    blob = json.dumps(dataset_manifest, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def lock_dataset(dataset_manifest: Mapping[str, object], locked_by: str) -> DataLockRecord:
    """Khoá dataset — trả DataLockRecord với hash SHA-256."""
    if not locked_by or not locked_by.strip():
        raise ValueError("locked_by không được để trống")
    digest = _compute_hash(dataset_manifest)
    return DataLockRecord(
        lock_id=f"dlock_{digest[:16]}",
        dataset_hash=digest,
        locked_at=datetime.now(timezone.utc).isoformat(),
        locked_by=locked_by.strip(),
    )


def verify_dataset_hash(
    dataset_manifest: Mapping[str, object],
    lock_record: DataLockRecord,
) -> bool:
    """Kiểm tra dataset có khớp hash trong lock_record không.

    Trả True nếu toàn vẹn, False nếu dữ liệu đã bị sửa sau khi khoá.
    """
    return _compute_hash(dataset_manifest) == lock_record.dataset_hash
