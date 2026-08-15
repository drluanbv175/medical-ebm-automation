"""Provenance cho tài liệu nguồn chính thức Phase 2D."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

REQUIRED_PROVENANCE_FIELDS = {
    "source_file",
    "source_origin_url",
    "organization",
    "source_type",
    "title",
    "version",
    "publication_date",
    "imported_by",
    "import_date",
    "sha256",
    "page_count_or_html_snapshot",
    "copyright_or_access_note",
}


@dataclass(frozen=True)
class ProvenanceValidationResult:
    valid: bool
    issues: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DocumentProvenance:
    source_file: str
    source_origin_url: str
    organization: str
    source_type: str
    title: str
    version: str
    publication_date: str
    imported_by: str
    import_date: str
    sha256: str
    page_count_or_html_snapshot: str
    copyright_or_access_note: str
    verification_channel: str = "manual_source_import"
    text_extraction_reliable: bool = False

    def validate(self) -> ProvenanceValidationResult:
        issues: List[str] = []
        values = self.__dict__
        for field_name in sorted(REQUIRED_PROVENANCE_FIELDS):
            if not values.get(field_name):
                issues.append(f"missing_required_provenance:{field_name}")
        suffix = Path(self.source_file).suffix.lower()
        if suffix == ".pdf":
            if not str(self.page_count_or_html_snapshot).isdigit():
                issues.append("pdf_page_count_required")
            if not self.text_extraction_reliable:
                issues.append("pdf_text_extraction_not_reliable_for_decision")
        if suffix in {".html", ".htm"}:
            if not self.source_origin_url.startswith(("http://", "https://")):
                issues.append("html_origin_url_required")
            if not self.page_count_or_html_snapshot:
                issues.append("html_snapshot_hash_or_section_required")
        if self.verification_channel not in {"manual_source_import", "live_adapter_verification"}:
            issues.append("verification_channel_not_allowed")
        return ProvenanceValidationResult(valid=not issues, issues=issues)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
