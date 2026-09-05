"""Snapshot nguồn chính thức cho Phase 2D."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import List

from app.evidence.document_provenance import file_sha256


@dataclass(frozen=True)
class SourceSnapshot:
    source_file: str
    source_origin_url: str
    snapshot_hash: str
    access_date: str
    source_kind: str
    page_count_or_html_snapshot: str
    section_heading: str = ""
    extraction_reliable: bool = False


@dataclass(frozen=True)
class SourceSnapshotValidation:
    valid: bool
    issues: List[str] = field(default_factory=list)


def build_source_snapshot(
    source_file: Path,
    *,
    source_origin_url: str,
    source_kind: str,
    page_count_or_html_snapshot: str,
    section_heading: str = "",
    extraction_reliable: bool = False,
    access_date: str | None = None,
) -> SourceSnapshot:
    # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 13) — `access_date or
    # date.today()...` coi CẢ HAI "không truyền (None)" LẪN "truyền chuỗi rỗng" là
    # "chưa có, tự điền hôm nay" — nhưng manual_source_import.py truyền THẲNG
    # `provenance.import_date`, một str LUÔN có giá trị (rỗng khi metadata thiếu
    # import_date, không phải None). Kết quả: một lượt import BỊ CHẶN vì thiếu
    # import_date (provenance.validate() báo `missing_required_provenance:
    # import_date`) vẫn ghi vào SourceSnapshot.access_date một ngày HÔM NAY bịa ra —
    # trông như ngày truy cập/nhập đã ghi nhận thật, dù chưa ai cung cấp giá trị đó.
    # Chỉ tự điền khi caller THỰC SỰ không truyền gì (None), không phải khi giá trị
    # truyền vào rỗng — cùng nguyên tắc None-vs-falsy đã áp cho nhiều bản vá trong
    # marathon này.
    return SourceSnapshot(
        source_file=str(source_file),
        source_origin_url=source_origin_url,
        snapshot_hash=file_sha256(source_file),
        access_date=access_date if access_date is not None else date.today().isoformat(),
        source_kind=source_kind,
        page_count_or_html_snapshot=str(page_count_or_html_snapshot),
        section_heading=section_heading,
        extraction_reliable=extraction_reliable,
    )


def validate_source_snapshot(snapshot: SourceSnapshot) -> SourceSnapshotValidation:
    issues: List[str] = []
    if not snapshot.snapshot_hash:
        issues.append("snapshot_hash_missing")
    if not snapshot.source_origin_url.startswith(("http://", "https://")):
        issues.append("source_origin_url_missing_or_invalid")
    if snapshot.source_kind == "pdf" and not str(snapshot.page_count_or_html_snapshot).isdigit():
        issues.append("pdf_page_count_required")
    if snapshot.source_kind == "html" and not snapshot.section_heading:
        issues.append("html_section_heading_required")
    return SourceSnapshotValidation(valid=not issues, issues=issues)
