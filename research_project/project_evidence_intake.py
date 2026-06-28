"""
project_evidence_intake — Quản lý bằng chứng offline cho đề tài (V4.3.3).

evidence_manifest.csv tại projects/<project_id>/evidence/evidence_manifest.csv.
4 trạng thái: VERIFIED_BY_HUMAN, MANUAL_REVIEW_REQUIRED, RETRACTED, REJECTED.
KHÔNG tự trích DOI/PMID, KHÔNG auto-citation. OFFLINE · KHÔNG PII / API.
"""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import io
import pathlib
from datetime import datetime, timezone
from typing import List, Optional

from .project_config import (
    EvidenceStatus,
    REQUIRE_HUMAN_INPUT_MARKER,
    contains_pii,
    contains_real_data,
)

MANIFEST_FILENAME = "evidence_manifest.csv"
_MANIFEST_HEADER = [
    "evidence_id", "source_description", "provided_pmid_or_doi", "status",
    "added_at", "added_by_pseudonym", "notes",
]


class EvidenceIntakeError(Exception):
    pass


class RetractedEvidenceError(EvidenceIntakeError):
    pass


class PIIInEvidenceError(EvidenceIntakeError):
    pass


@dataclasses.dataclass
class EvidenceItem:
    evidence_id: str
    source_description: str
    provided_pmid_or_doi: str   # do human cung cấp, KHÔNG tự suy luận
    status: EvidenceStatus
    added_at: str
    added_by_pseudonym: str
    notes: str

    def as_row(self) -> List[str]:
        return [
            self.evidence_id,
            self.source_description,
            self.provided_pmid_or_doi,
            self.status.value,
            self.added_at,
            self.added_by_pseudonym,
            self.notes,
        ]


@dataclasses.dataclass
class EvidenceIntakeResult:
    decision: str           # "ADDED" | "BLOCKED" | "FLAGGED_REVIEW"
    evidence_id: Optional[str]
    reason: str


class EvidenceIntake:
    """
    Quản lý evidence_manifest.csv cho một project.
    Chỉ thêm bằng chứng qua add_evidence(); KHÔNG tự xác minh DOI/PMID.
    """

    def __init__(self, evidence_dir: pathlib.Path) -> None:
        self._dir = pathlib.Path(evidence_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._manifest_path = self._dir / MANIFEST_FILENAME
        if not self._manifest_path.exists():
            self._write_manifest([])

    # ------------------------------------------------------------------
    # Thêm bằng chứng
    # ------------------------------------------------------------------

    def add_evidence(
        self,
        source_description: str,
        provided_pmid_or_doi: str,
        status: EvidenceStatus,
        added_by_pseudonym: str,
        notes: str = "",
    ) -> EvidenceIntakeResult:
        """
        Thêm một mục bằng chứng vào manifest.
        - PII trong source_description → BLOCK
        - Dữ liệu thật trong notes → BLOCK
        - Status RETRACTED → không cho thêm nếu đã có, ghi log
        - Status REJECTED → ghi và trả FLAGGED_REVIEW
        """
        # Kiểm tra PII
        full_text = f"{source_description} {notes} {provided_pmid_or_doi}"
        if contains_pii(full_text):
            return EvidenceIntakeResult(
                decision="BLOCKED",
                evidence_id=None,
                reason="PII detected in evidence fields — không được nhập thông tin định danh.",
            )

        # Kiểm tra dữ liệu thật
        if contains_real_data(full_text):
            return EvidenceIntakeResult(
                decision="BLOCKED",
                evidence_id=None,
                reason="Real-data marker detected — chỉ nhập bằng chứng synthetic/tham chiếu.",
            )

        # Không cho thêm mục bị rút (RETRACTED) mới — nên cập nhật status thay thế
        if status == EvidenceStatus.RETRACTED:
            return EvidenceIntakeResult(
                decision="BLOCKED",
                evidence_id=None,
                reason="RETRACTED evidence không được thêm mới. Dùng update_status() để cập nhật.",
            )

        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        eid = _make_evidence_id(source_description, provided_pmid_or_doi, ts)

        item = EvidenceItem(
            evidence_id=eid,
            source_description=source_description,
            provided_pmid_or_doi=provided_pmid_or_doi or REQUIRE_HUMAN_INPUT_MARKER,
            status=status,
            added_at=ts,
            added_by_pseudonym=added_by_pseudonym or "SYNTH-USER",
            notes=notes or "",
        )

        items = self.load_all()
        # Kiểm tra trùng
        for existing in items:
            if (
                existing.source_description == source_description
                and existing.provided_pmid_or_doi == provided_pmid_or_doi
            ):
                return EvidenceIntakeResult(
                    decision="BLOCKED",
                    evidence_id=existing.evidence_id,
                    reason="Bằng chứng đã tồn tại trong manifest.",
                )

        items.append(item)
        self._write_manifest(items)

        decision = (
            "FLAGGED_REVIEW"
            if status in (EvidenceStatus.MANUAL_REVIEW_REQUIRED, EvidenceStatus.REJECTED)
            else "ADDED"
        )
        return EvidenceIntakeResult(decision=decision, evidence_id=eid, reason="OK")

    # ------------------------------------------------------------------
    # Cập nhật status
    # ------------------------------------------------------------------

    def update_status(
        self, evidence_id: str, new_status: EvidenceStatus, updated_by: str = "SYNTH"
    ) -> bool:
        """Cập nhật status của một mục (vd đánh dấu RETRACTED). Trả True nếu tìm thấy."""
        items = self.load_all()
        found = False
        for item in items:
            if item.evidence_id == evidence_id:
                item.status = new_status
                item.notes = f"{item.notes} | status_updated_by={updated_by}"
                found = True
                break
        if found:
            self._write_manifest(items)
        return found

    # ------------------------------------------------------------------
    # Đọc
    # ------------------------------------------------------------------

    def load_all(self) -> List[EvidenceItem]:
        if not self._manifest_path.exists():
            return []
        raw = self._manifest_path.read_bytes().decode("utf-8")
        reader = csv.DictReader(io.StringIO(raw))
        items: List[EvidenceItem] = []
        for row in reader:
            try:
                status = EvidenceStatus(row.get("status", "MANUAL_REVIEW_REQUIRED"))
            except ValueError:
                status = EvidenceStatus.MANUAL_REVIEW_REQUIRED
            items.append(
                EvidenceItem(
                    evidence_id=row.get("evidence_id", ""),
                    source_description=row.get("source_description", ""),
                    provided_pmid_or_doi=row.get("provided_pmid_or_doi", ""),
                    status=status,
                    added_at=row.get("added_at", ""),
                    added_by_pseudonym=row.get("added_by_pseudonym", ""),
                    notes=row.get("notes", ""),
                )
            )
        return items

    def count_by_status(self) -> dict:
        items = self.load_all()
        counts = {s.value: 0 for s in EvidenceStatus}
        for item in items:
            counts[item.status.value] = counts.get(item.status.value, 0) + 1
        return counts

    def has_retracted(self) -> bool:
        return any(i.status == EvidenceStatus.RETRACTED for i in self.load_all())

    def unverified_items(self) -> List[EvidenceItem]:
        return [
            i for i in self.load_all()
            if i.status != EvidenceStatus.VERIFIED_BY_HUMAN
        ]

    # ------------------------------------------------------------------
    # Nội bộ
    # ------------------------------------------------------------------

    def _write_manifest(self, items: List[EvidenceItem]) -> None:
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow(_MANIFEST_HEADER)
        for item in items:
            writer.writerow(item.as_row())
        self._manifest_path.write_bytes(buf.getvalue().encode("utf-8"))


def _make_evidence_id(source: str, pmid_doi: str, ts: str) -> str:
    raw = f"{source}|{pmid_doi}|{ts}"
    return "EV-" + hashlib.sha256(raw.encode()).hexdigest()[:10].upper()


def build_evidence_intake(project_dir: pathlib.Path) -> EvidenceIntake:
    """Factory: trả EvidenceIntake cho project_dir."""
    return EvidenceIntake(project_dir / "evidence")
