"""Data lock với hash manifest."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping


@dataclass(frozen=True)
class DataLockRecord:
    lock_id: str
    dataset_hash: str
    locked_at: str
    locked_by: str


def lock_dataset(dataset_manifest: Mapping[str, object], locked_by: str) -> DataLockRecord:
    blob = json.dumps(dataset_manifest, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    return DataLockRecord(
        lock_id=f"dlock_{digest[:16]}",
        dataset_hash=digest,
        locked_at=datetime.now(timezone.utc).isoformat(),
        locked_by=locked_by,
    )
