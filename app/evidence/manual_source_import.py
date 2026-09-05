"""Manual source import có provenance cho Phase 2D."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Mapping

from app.evidence.document_provenance import DocumentProvenance, file_sha256
from app.evidence.source_snapshot import SourceSnapshot, build_source_snapshot, validate_source_snapshot


@dataclass(frozen=True)
class ManualSourceImportResult:
    imported: bool
    status: str
    provenance: DocumentProvenance | None = None
    snapshot: SourceSnapshot | None = None
    issues: List[str] = field(default_factory=list)


def import_official_source(metadata: Mapping[str, object]) -> ManualSourceImportResult:
    """Import nguồn chính thức theo metadata; không tự VERIFIED claim."""
    issues: List[str] = []
    source_file = Path(str(metadata.get("source_file") or ""))
    if not source_file.exists() or not source_file.is_file():
        issues.append("source_file_missing")
        return ManualSourceImportResult(imported=False, status="BLOCKED", issues=issues)

    expected_sha = str(metadata.get("sha256") or "")
    if not expected_sha:
        issues.append("sha256_required")
    actual_sha = file_sha256(source_file)
    # SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #91, vòng 6): so
    # sánh chuỗi thô `!=` nhạy hoa/thường, nhưng `file_sha256()` LUÔN trả hex
    # CHỮ THƯỜNG (`hashlib.sha256(...).hexdigest()`). Công cụ tính hash phổ
    # biến trên Windows (`Get-FileHash -Algorithm SHA256` của PowerShell —
    # nền vận hành chính của repo này theo CLAUDE.md) in hex CHỮ HOA. Một
    # curator dán `--sha256 3A7BD3E2...` (hoa) cho một file có hash thật
    # `3a7bd3e2...` (cùng giá trị, khác chữ hoa/thường) sẽ bị báo
    # `sha256_mismatch` và BLOCKED — một tài liệu nguyên vẹn, đúng hash, bị
    # từ chối chỉ vì khác cách viết hoa/thường. Chuẩn hoá về chữ thường
    # trước khi so sánh.
    if expected_sha and expected_sha.lower() != actual_sha.lower():
        issues.append("sha256_mismatch")

    suffix = source_file.suffix.lower()
    source_kind = "pdf" if suffix == ".pdf" else "html" if suffix in {".html", ".htm"} else "document"
    provenance = DocumentProvenance(
        source_file=str(source_file),
        source_origin_url=str(metadata.get("source_origin_url") or ""),
        organization=str(metadata.get("organization") or ""),
        source_type=str(metadata.get("source_type") or ""),
        title=str(metadata.get("title") or ""),
        version=str(metadata.get("version") or ""),
        publication_date=str(metadata.get("publication_date") or ""),
        imported_by=str(metadata.get("imported_by") or ""),
        import_date=str(metadata.get("import_date") or ""),
        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 12) — lưu `expected_sha`
        # (chuỗi curator tự gõ, có thể HOA/thường tuỳ công cụ — xem ghi chú so sánh
        # case-insensitive ở trên, task #91 vòng 6) thay vì `actual_sha` (giá trị THẬT
        # do chính `file_sha256()` tính) khiến bản ghi `DocumentProvenance` bất biến lưu
        # một chuỗi không CANONICAL: cùng file, hai lần import với cách viết hoa/thường
        # khác nhau của curator sẽ cho ra 2 giá trị `sha256` khác nhau trong provenance dù
        # nội dung file giống hệt nhau — bất kỳ lần đối chiếu lại nào sau này (tính lại
        # hash rồi so `==` với provenance đã lưu) sẽ SAI ngay cả khi file chưa hề đổi.
        # Lưu giá trị CANONICAL (`actual_sha`, luôn chữ thường) — đã xác nhận qua nhánh
        # trên rằng nó khớp `expected_sha` (không phân biệt hoa/thường) khi tới đây.
        sha256=actual_sha,
        page_count_or_html_snapshot=str(metadata.get("page_count_or_html_snapshot") or ""),
        copyright_or_access_note=str(metadata.get("copyright_or_access_note") or ""),
        verification_channel=str(metadata.get("verification_channel") or "manual_source_import"),
        text_extraction_reliable=bool(metadata.get("text_extraction_reliable", False)),
    )
    provenance_validation = provenance.validate()
    issues.extend(provenance_validation.issues)

    snapshot = build_source_snapshot(
        source_file,
        source_origin_url=provenance.source_origin_url,
        source_kind=source_kind,
        page_count_or_html_snapshot=provenance.page_count_or_html_snapshot,
        section_heading=str(metadata.get("section_heading") or ""),
        extraction_reliable=provenance.text_extraction_reliable,
        access_date=provenance.import_date,
    )
    snapshot_validation = validate_source_snapshot(snapshot)
    issues.extend(snapshot_validation.issues)

    return ManualSourceImportResult(
        imported=not issues,
        status="SOURCE_IMPORTED" if not issues else "BLOCKED",
        provenance=provenance,
        snapshot=snapshot,
        issues=sorted(set(issues)),
    )
