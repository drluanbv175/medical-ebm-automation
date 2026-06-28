"""
project_evidence_intake — Quản lý bằng chứng offline cho đề tài (V4.3.3/V4.3.5).

evidence_manifest.csv tại projects/<project_id>/evidence/evidence_manifest.csv.
4 trạng thái legacy: VERIFIED_BY_HUMAN, MANUAL_REVIEW_REQUIRED, RETRACTED, REJECTED.

V4.3.5: Evidence Source Ledger (evidence_source_ledger.jsonl) với đầy đủ
  traceability fields, RetrievalMode, VerificationState, claim-use policy.
KHÔNG tự trích DOI/PMID, KHÔNG auto-citation. OFFLINE · KHÔNG PII / API.
"""

from __future__ import annotations

import csv
import dataclasses
import enum
import hashlib
import io
import json
import pathlib
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

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


# ===========================================================================
# V4.3.5 — Evidence Source Ledger (JSONL, append-only)
# ===========================================================================

class RetrievalMode(str, enum.Enum):
    HUMAN_PROVIDED_ONLY = "HUMAN_PROVIDED_ONLY"
    # Forbidden values — exist as enum members so code can reference them,
    # but EvidenceSourceLedger.add() raises ForbiddenRetrievalMode for these.
    AUTO_RETRIEVED  = "AUTO_RETRIEVED"
    MODEL_GENERATED = "MODEL_GENERATED"
    WEB_SCRAPED     = "WEB_SCRAPED"
    API_FETCHED     = "API_FETCHED"


FORBIDDEN_RETRIEVAL_MODES: frozenset = frozenset({
    "AUTO_RETRIEVED", "MODEL_GENERATED", "WEB_SCRAPED", "API_FETCHED",
})


class VerificationState(str, enum.Enum):
    UNVERIFIED             = "UNVERIFIED"
    HUMAN_VERIFIED         = "HUMAN_VERIFIED"
    REQUIRES_HUMAN_REVIEW  = "REQUIRES_HUMAN_REVIEW"
    RETRACTED              = "RETRACTED"
    EXCLUDED               = "EXCLUDED"


class ForbiddenRetrievalMode(ValueError):
    """Raised khi retrieval_mode nằm trong danh sách cấm."""


class AutoVerificationForbidden(RuntimeError):
    """Raised khi automation cố gán verification_state=HUMAN_VERIFIED."""


@dataclasses.dataclass
class EvidenceSource:
    """
    Evidence Source với đầy đủ traceability fields (V4.3.5).
    retrieval_mode luôn phải là HUMAN_PROVIDED_ONLY.
    """
    source_id:                str
    project_id:               str
    source_type:              str
    title:                    str
    authors_or_organization:  str
    publication_year:         str
    journal_or_publisher:     str
    doi:                      str
    pmid:                     str
    url:                      str
    human_provided_reference: str
    retrieval_mode:           RetrievalMode
    verification_state:       VerificationState
    verification_reason:      str
    reviewer_reference:       str
    review_mode:              str
    retraction_status:        str
    claim_use_allowed:        bool
    created_at_utc:           str
    audit_event_id:           str

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["retrieval_mode"] = self.retrieval_mode.value
        d["verification_state"] = self.verification_state.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "EvidenceSource":
        d = dict(d)
        d["retrieval_mode"] = RetrievalMode(d.get("retrieval_mode", "HUMAN_PROVIDED_ONLY"))
        d["verification_state"] = VerificationState(d.get("verification_state", "UNVERIFIED"))
        return cls(**d)


EVIDENCE_SOURCE_LEDGER_FILENAME = "evidence_source_ledger.jsonl"


class EvidenceSourceLedger:
    """
    Append-only JSONL ledger lưu EvidenceSource.
    Không có delete() hay update() — chỉ append().
    """

    def __init__(self, project_dir: pathlib.Path) -> None:
        self._path = pathlib.Path(project_dir) / EVIDENCE_SOURCE_LEDGER_FILENAME

    def add(self, source: EvidenceSource) -> None:
        if source.retrieval_mode.value in FORBIDDEN_RETRIEVAL_MODES:
            raise ForbiddenRetrievalMode(
                f"retrieval_mode='{source.retrieval_mode.value}' bị cấm. "
                "Chỉ HUMAN_PROVIDED_ONLY được phép. Không tự động thu thập."
            )
        if source.retrieval_mode != RetrievalMode.HUMAN_PROVIDED_ONLY:
            raise ForbiddenRetrievalMode(
                "retrieval_mode phải là HUMAN_PROVIDED_ONLY."
            )
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(source.to_dict(), ensure_ascii=False) + "\n")

    def read_all(self) -> List[EvidenceSource]:
        if not self._path.exists():
            return []
        sources: List[EvidenceSource] = []
        with self._path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    sources.append(EvidenceSource.from_dict(json.loads(line)))
                except (json.JSONDecodeError, TypeError, KeyError, ValueError):
                    pass
        return sources

    def exists(self) -> bool:
        return self._path.exists()

    @property
    def path(self) -> pathlib.Path:
        return self._path


def _make_source_id(project_id: str, title: str, ts: str) -> str:
    raw = f"{project_id}|{title}|{ts}"
    return "ES-" + hashlib.sha256(raw.encode()).hexdigest()[:10].upper()


_EVIDENCE_REVIEW_NOTE = (
    "Evidence verification is manually attested. "
    "Reviewer identity authentication is not implemented. "
    "Reviewer independence is not established."
)


def add_evidence_source(
    project_dir: pathlib.Path,
    project_id: str,
    source_type: str,
    title: str,
    authors_or_organization: str,
    publication_year: str,
    journal_or_publisher: str,
    doi: str,
    pmid: str,
    url: str,
    human_provided_reference: str,
    verification_state: VerificationState,
    verification_reason: str,
    reviewer_reference: str,
    review_mode: str = "HUMAN_REVIEW_INDEPENDENCE_NOT_ESTABLISHED",
    retraction_status: str = "NOT_RETRACTED",
    automation_caller: bool = False,
) -> EvidenceSource:
    """
    Thêm EvidenceSource vào ledger.
    - automation_caller=True + HUMAN_VERIFIED → AutoVerificationForbidden
    - PII trong bất kỳ field → PIIInEvidenceError
    - retrieval_mode luôn là HUMAN_PROVIDED_ONLY
    """
    if automation_caller and verification_state == VerificationState.HUMAN_VERIFIED:
        raise AutoVerificationForbidden(
            "Automation không thể đặt verification_state=HUMAN_VERIFIED. "
            "Chỉ PI/reviewer qua CLI mới được xác minh evidence."
        )
    full_text = (
        f"{title} {authors_or_organization} "
        f"{verification_reason} {human_provided_reference}"
    )
    if contains_pii(full_text):
        raise PIIInEvidenceError(
            "PII detected in evidence source fields — không được nhập thông tin định danh."
        )

    _RHI = REQUIRE_HUMAN_INPUT_MARKER
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    source_id = _make_source_id(project_id, title, ts)
    audit_event_id = "AE-" + hashlib.sha256(
        f"{source_id}|{ts}".encode()
    ).hexdigest()[:8].upper()

    claim_use_allowed = (
        verification_state == VerificationState.HUMAN_VERIFIED
        and retraction_status in ("NOT_RETRACTED", "")
    )

    source = EvidenceSource(
        source_id=source_id,
        project_id=project_id,
        source_type=source_type or "UNSPECIFIED",
        title=title or _RHI,
        authors_or_organization=authors_or_organization or _RHI,
        publication_year=publication_year or _RHI,
        journal_or_publisher=journal_or_publisher or _RHI,
        doi=doi or _RHI,
        pmid=pmid or _RHI,
        url=url or "",
        human_provided_reference=human_provided_reference or _RHI,
        retrieval_mode=RetrievalMode.HUMAN_PROVIDED_ONLY,
        verification_state=verification_state,
        verification_reason=verification_reason or "",
        reviewer_reference=reviewer_reference or "EVIDENCE_CITATION_REVIEWER",
        review_mode=review_mode,
        retraction_status=retraction_status or "NOT_RETRACTED",
        claim_use_allowed=claim_use_allowed,
        created_at_utc=ts,
        audit_event_id=audit_event_id,
    )

    ledger = EvidenceSourceLedger(project_dir)
    ledger.add(source)
    return source


def get_evidence_review_queue(project_dir: pathlib.Path) -> List[dict]:
    """Trả danh sách evidence source cần reviewer xem xét."""
    ledger = EvidenceSourceLedger(project_dir)
    queue: List[dict] = []
    for s in ledger.read_all():
        if s.verification_state in (
            VerificationState.UNVERIFIED,
            VerificationState.REQUIRES_HUMAN_REVIEW,
        ):
            snippet = s.title[:60] + "…" if len(s.title) > 60 else s.title
            queue.append({
                "source_id": s.source_id,
                "title": snippet,
                "verification_state": s.verification_state.value,
                "reviewer_reference": s.reviewer_reference,
                "claim_use_allowed": s.claim_use_allowed,
                "note": _EVIDENCE_REVIEW_NOTE,
            })
    return queue
