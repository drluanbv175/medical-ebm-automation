"""
project_change_control — Change Control Engine với dependency graph (V4.3.3).

Khi field thay đổi: tạo ProjectChangeRecord bất biến, bump version,
đánh STALE_REQUIRES_REVISION cho artifact downstream, tạo ReviewQueue item.
Audit trail KHÔNG bao giờ bị sửa/xoá. OFFLINE · KHÔNG PII / API.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .project_config import (
    ArtifactID, ArtifactStatus, ARTIFACT_FILENAME, ProjectChangeRecord,
    contains_pii, scrub_pii,
)
from .project_artifact_graph import mark_stale, get_downstream


# ---------------------------------------------------------------------------
# Field → Artifact ảnh hưởng (đầu vào trực tiếp)
# ---------------------------------------------------------------------------

_FIELD_TO_ARTIFACTS: Dict[str, List[ArtifactID]] = {
    "title": [ArtifactID.RESEARCH_CHARTER, ArtifactID.RESEARCH_QUESTION_AND_PICO],
    "study_type": [ArtifactID.RESEARCH_CHARTER, ArtifactID.PROTOCOL_DRAFT,
                   ArtifactID.METHODS_AND_SAMPLE_SIZE, ArtifactID.CRF_DRAFT,
                   ArtifactID.SAP_DRAFT, ArtifactID.REPORTING_CHECKLIST_DRAFT],
    "primary_objectives": [ArtifactID.RESEARCH_QUESTION_AND_PICO,
                            ArtifactID.PROTOCOL_DRAFT, ArtifactID.SAP_DRAFT],
    "secondary_objectives": [ArtifactID.RESEARCH_QUESTION_AND_PICO,
                              ArtifactID.PROTOCOL_DRAFT, ArtifactID.SAP_DRAFT],
    "primary_outcomes": [ArtifactID.RESEARCH_QUESTION_AND_PICO,
                         ArtifactID.METHODS_AND_SAMPLE_SIZE, ArtifactID.SAP_DRAFT,
                         ArtifactID.TABLE_AND_FIGURE_SHELLS, ArtifactID.CRF_DRAFT],
    "secondary_outcomes": [ArtifactID.RESEARCH_QUESTION_AND_PICO,
                            ArtifactID.SAP_DRAFT, ArtifactID.CRF_DRAFT],
    "population_description_synthetic": [ArtifactID.PROTOCOL_DRAFT,
                                         ArtifactID.METHODS_AND_SAMPLE_SIZE],
    "research_constraints": [ArtifactID.RESEARCH_CHARTER, ArtifactID.GOVERNANCE_AND_CAPA_PACK],
}


def _artifacts_affected_by_field(field: str) -> List[ArtifactID]:
    """Trả danh sách artifact trực tiếp bị ảnh hưởng khi field thay đổi."""
    return list(_FIELD_TO_ARTIFACTS.get(field, [ArtifactID.RESEARCH_CHARTER]))


# ---------------------------------------------------------------------------
# Version helper
# ---------------------------------------------------------------------------

def bump_version(version: str) -> str:
    """0.1.0 → 0.2.0 → ... → 0.9.0 → 1.0.0."""
    try:
        parts = [int(x) for x in version.split(".")]
        parts[1] += 1
        if parts[1] >= 10:
            parts[0] += 1
            parts[1] = 0
        return ".".join(str(p) for p in parts)
    except (ValueError, IndexError):
        return "0.2.0"


# ---------------------------------------------------------------------------
# Audit trail (append-only, chỉ đọc sau khi ghi)
# ---------------------------------------------------------------------------

class ImmutableAuditLog:
    """Audit log append-only. KHÔNG cho sửa hay xoá bản ghi."""

    def __init__(self, log_path: pathlib.Path) -> None:
        self._path = log_path
        if not self._path.exists():
            self._path.write_bytes(b"")

    def append(self, record: ProjectChangeRecord) -> None:
        entry = json.dumps(record.as_dict(), ensure_ascii=False) + "\n"
        with self._path.open("ab") as fh:
            fh.write(entry.encode("utf-8"))

    def read_all(self) -> List[ProjectChangeRecord]:
        if not self._path.exists():
            return []
        records: List[ProjectChangeRecord] = []
        for line in self._path.read_bytes().decode("utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                records.append(ProjectChangeRecord(**d))
            except (json.JSONDecodeError, TypeError):
                continue
        return records

    def record_count(self) -> int:
        return len(self.read_all())


# ---------------------------------------------------------------------------
# Change Control Engine
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ChangeControlResult:
    record_id: str
    new_version: str
    stale_artifacts: List[str]
    review_items_created: int
    blocked: bool
    block_reason: str


class ChangeControlEngine:
    """
    Engine xử lý thay đổi field trong ProjectConfig.
    - Tạo bản ghi bất biến trong audit_log.jsonl
    - Bump version trong .project_config.json
    - Đánh STALE cho mọi artifact downstream
    - Cập nhật CHANGE_IMPACT_REPORT và DECISION_REGISTER
    """

    def __init__(self, project_dir: pathlib.Path) -> None:
        self._dir = pathlib.Path(project_dir)
        self._audit_log = ImmutableAuditLog(self._dir / "audit_log.jsonl")
        self._statuses: Dict[str, ArtifactStatus] = {}

    def record_change(
        self,
        project_id: str,
        changed_field: str,
        old_value: str,
        new_value: str,
        current_version: str,
    ) -> ChangeControlResult:
        """
        Ghi nhận thay đổi field. Trả ChangeControlResult.
        BLOCK nếu PII trong new_value.
        """
        # PII guard — scrub trước khi ghi audit
        if contains_pii(new_value) or contains_pii(old_value):
            return ChangeControlResult(
                record_id="BLOCKED",
                new_version=current_version,
                stale_artifacts=[],
                review_items_created=0,
                blocked=True,
                block_reason="PII detected in changed field — thay đổi bị huỷ.",
            )

        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        record_id = _make_record_id(project_id, changed_field, ts)

        # Xác định artifact bị ảnh hưởng trực tiếp
        direct_affected = _artifacts_affected_by_field(changed_field)

        # Tính toàn bộ downstream (qua dependency graph)
        all_stale: set = set()
        for art in direct_affected:
            all_stale.update(get_downstream(art))
            all_stale.add(art)

        stale_names = sorted([a.value for a in all_stale])

        # Bump version
        new_version = bump_version(current_version)

        # Mô tả impact
        impact = (
            f"Field '{changed_field}' thay đổi từ '{_truncate(old_value)}' "
            f"→ '{_truncate(new_value)}'. "
            f"Affected artifacts: {len(stale_names)} cần revision."
        )

        record = ProjectChangeRecord(
            record_id=record_id,
            project_id=project_id,
            changed_field=changed_field,
            old_value=old_value,
            new_value=new_value,
            timestamp=ts,
            affected_artifacts=stale_names,
            impact_description=impact,
        )

        # Ghi audit (append-only, bất biến)
        self._audit_log.append(record)

        # Cập nhật statuses trong memory
        for art_name in stale_names:
            self._statuses[art_name] = ArtifactStatus.STALE_REQUIRES_REVISION

        # Cập nhật CHANGE_IMPACT_REPORT trên disk
        self._update_change_impact_report(record, new_version)

        # Cập nhật DECISION_REGISTER
        self._update_decision_register(record)

        return ChangeControlResult(
            record_id=record_id,
            new_version=new_version,
            stale_artifacts=stale_names,
            review_items_created=len(stale_names),
            blocked=False,
            block_reason="",
        )

    def get_stale_artifacts(self) -> List[str]:
        return [k for k, v in self._statuses.items()
                if v == ArtifactStatus.STALE_REQUIRES_REVISION]

    def audit_log(self) -> ImmutableAuditLog:
        return self._audit_log

    def load_statuses_from_disk(self, statuses_dict: Dict[str, ArtifactStatus]) -> None:
        """Nạp trạng thái artifact từ ngoài vào engine."""
        self._statuses.update(statuses_dict)

    # ------------------------------------------------------------------
    # Cập nhật artifact CHANGE_IMPACT_REPORT
    # ------------------------------------------------------------------

    def _update_change_impact_report(
        self, record: ProjectChangeRecord, new_version: str
    ) -> None:
        report_path = self._dir / ARTIFACT_FILENAME[ArtifactID.CHANGE_IMPACT_REPORT]
        existing = ""
        if report_path.exists():
            existing = report_path.read_bytes().decode("utf-8")
        else:
            existing = (
                "# CHANGE IMPACT REPORT (DRAFT)\n\n"
                "> DRAFT — Cần PI kiểm chứng. Bản tự động.\n\n"
                "| Record ID | Timestamp | Field | Version | Artifacts bị STALE |\n"
                "|-----------|-----------|-------|---------|--------------------|\n"
            )

        new_row = (
            f"| {record.record_id[:16]} | {record.timestamp[:19]} | "
            f"{record.changed_field} | {new_version} | "
            f"{len(record.affected_artifacts)} artifacts |\n"
        )
        report_path.write_bytes((existing + new_row).encode("utf-8"))

    def _update_decision_register(self, record: ProjectChangeRecord) -> None:
        dr_path = self._dir / ARTIFACT_FILENAME[ArtifactID.DECISION_REGISTER]
        existing = ""
        if dr_path.exists():
            existing = dr_path.read_bytes().decode("utf-8")
        else:
            existing = (
                "# DECISION REGISTER (DRAFT)\n\n"
                "> DRAFT — Cần PI kiểm chứng. Bản tự động.\n\n"
                "| Record ID | Timestamp | Field Changed | Old → New | Impact |\n"
                "|-----------|-----------|---------------|-----------|--------|\n"
            )

        new_row = (
            f"| {record.record_id[:16]} | {record.timestamp[:19]} | "
            f"{record.changed_field} | "
            f"{_truncate(record.old_value, 30)} → {_truncate(record.new_value, 30)} | "
            f"{_truncate(record.impact_description, 60)} |\n"
        )
        dr_path.write_bytes((existing + new_row).encode("utf-8"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_record_id(project_id: str, field: str, ts: str) -> str:
    raw = f"{project_id}|{field}|{ts}"
    return "CHG-" + hashlib.sha256(raw.encode()).hexdigest()[:12].upper()


def _truncate(text: str, max_len: int = 50) -> str:
    text = str(text)
    return text if len(text) <= max_len else text[:max_len - 3] + "..."
