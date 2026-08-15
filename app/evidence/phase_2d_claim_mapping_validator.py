"""Validator claim-to-source mapping Phase 2D.

CẢNH BÁO: đây KHÔNG PHẢI cơ chế retraction-check đang được dùng thật trong pipeline
G0-G9. retraction_monitor.detect_retraction() chỉ đọc field 'retracted'/'withdrawn'
đã có sẵn trong metadata truyền vào — KHÔNG tự tra cứu gì. Cơ chế THẬT (tự tra cứu
PubMed E-utilities sống) nằm ở app/sources/pubmed.py::PubMedClient.check_retraction_status(),
dùng bởi tools/check_citation_retraction.py + cổng A12 trong tools/run_g10_assemble.py.
Module này là 1 trong 5 nhánh mồ côi đã ghi nhận trong CLAUDE.md — không xoá vì có thể
còn dùng nội bộ/thử nghiệm, nhưng KHÔNG dùng làm cơ chế retraction-check chính thức.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Mapping

REQUIRED_CLAIM_SOURCE_COLUMNS = [
    "claim_id",
    "claim_text_draft",
    "population",
    "clinical_question",
    "source_id",
    "source_type",
    "organization",
    "title",
    "version",
    "publication_date",
    "pmid",
    "doi",
    "source_url",
    "claim_location",
    "certainty_original",
    "verification_status",
    "verification_method",
    "verified_by",
    "verified_at",
    "freshness_status",
    "retraction_status",
    "approval_status",
    "notes",
]


@dataclass(frozen=True)
class ClaimMappingValidation:
    claim_id: str
    release_ready: bool
    can_be_verified: bool
    issues: List[str] = field(default_factory=list)


def validate_claim_to_source_mapping(mapping: Mapping[str, object]) -> ClaimMappingValidation:
    issues: List[str] = []
    for column in REQUIRED_CLAIM_SOURCE_COLUMNS:
        if column not in mapping:
            issues.append(f"missing_column:{column}")

    claim_id = str(mapping.get("claim_id") or "")
    claim_location = str(mapping.get("claim_location") or "")
    verification_method = str(mapping.get("verification_method") or "")
    verification_status = str(mapping.get("verification_status") or "")
    freshness_status = str(mapping.get("freshness_status") or "")
    retraction_status = str(mapping.get("retraction_status") or "")
    source_type = str(mapping.get("source_type") or "").lower()
    verified_by = str(mapping.get("verified_by") or "")

    if not claim_location:
        issues.append("claim_location_required")
    if not verification_method:
        issues.append("verification_method_required")
    if verification_status == "VERIFIED" and not verified_by:
        issues.append("verified_by_required")
    if source_type == "pdf" and "page" not in claim_location.lower():
        issues.append("pdf_claim_page_mapping_required")
    if freshness_status in {"STALE", "UNKNOWN", "needs_live_verification", ""}:
        issues.append(f"freshness_blocks_release:{freshness_status or 'missing'}")
    if retraction_status in {"RETRACTED", "CORRECTED_WITH_IMPACT", "unknown_or_affected", ""}:
        issues.append(f"retraction_blocks_release:{retraction_status or 'missing'}")

    can_be_verified = not any(
        issue
        for issue in issues
        if issue.endswith("_required") or issue.startswith("missing_column") or issue.startswith("pdf_claim")
    )
    release_ready = (
        can_be_verified
        and verification_status == "VERIFIED"
        and freshness_status == "current"
        and retraction_status == "not_retracted"
        and str(mapping.get("approval_status") or "") in {"approved", "physician_exception"}
    )
    return ClaimMappingValidation(
        claim_id=claim_id,
        release_ready=release_ready,
        can_be_verified=can_be_verified,
        issues=issues,
    )
