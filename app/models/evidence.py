"""Model bản ghi bằng chứng (evidence item) – schema chuẩn hóa chung.

Đây là bảng trung tâm của pipeline EBM. Mỗi bản ghi truy vết được về nguồn gốc
qua `source`, `url`, `doi`, `pmid`... và mang đầy đủ điểm scoring + lý do actionable.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Truy vết nguồn
    source: Mapped[str] = mapped_column(String(64), index=True)            # pubmed, crossref...
    source_type: Mapped[str] = mapped_column(String(32), default="article")  # article|guideline|trial|drug_safety
    title: Mapped[str] = mapped_column(Text)
    authors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    journal_or_organization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    publication_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    update_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # Định danh chuẩn
    doi: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    pmid: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)
    pmcid: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)
    nct_id: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    study_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    clinical_area: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)

    keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    mesh_terms: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    guideline_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # PICO + tín hiệu lâm sàng
    population: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    intervention: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comparator: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcomes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    safety_signal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    practice_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Scoring
    evidence_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    practice_change_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reliability_tier: Mapped[Optional[str]] = mapped_column(String(4), index=True, nullable=True)  # A|B|C|D
    # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 10) — cột từng khai
    # String(16), nhưng `app/scoring/operational_level.py::operational_
    # evidence_level()` thực tế trả "High (operational)"/"Moderate
    # (operational)"/"Low (operational)" (17-22 ký tự) ở NHÁNH PHỔ BIẾN NHẤT
    # (mọi bản ghi không có official_grade — tức không phải guideline nhập
    # tay), và nhánh "Theo nguồn: <official_grade>" có thể dài tới 44 ký tự
    # (official_grade tự nó đã là String(32)). SQLite bỏ qua giới hạn VARCHAR
    # nên lỗi im lặng trên máy hiện tại, nhưng docstring đầu file
    # `app/database.py` tự khai ý định "nâng cấp PostgreSQL dễ dàng" — trên
    # Postgres, VARCHAR(16) được THI HÀNH THẬT, mọi lần ghi bản ghi không có
    # official_grade (đa số) sẽ vỡ `DataError: value too long`. Đổi sang
    # Text (không giới hạn) — cùng kiểu đã dùng cho các trường mô tả khác
    # trong model này (reason_for_exclusion, safety_signal...).
    # High|Moderate|Low (+ hậu tố operational/theo nguồn)
    operational_evidence_level: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # GRADE chính thức nếu có
    official_grade: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # Phân loại hành động
    is_actionable: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    actionable_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason_for_exclusion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    classification: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)
    # classification: actionable | need_full_text | watch_only | excluded

    # Tóm tắt lâm sàng (clinical synthesis) – lưu dạng JSON các trường mẫu
    synthesis: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Truy vết raw payload + dedup
    raw_payload_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ingest_query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    api_endpoint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_primary_record: Mapped[bool] = mapped_column(Boolean, default=True)
    dedup_key: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    # Truy vết chế độ nguồn: True nếu bản ghi đến từ dữ liệu MOCK/demo (KHÔNG dùng lâm sàng).
    # Ngăn dữ liệu minh họa lẫn vào khuyến cáo thật khi DB từng chạy mock rồi chạy live.
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Theo dõi "mới" theo lần chạy: run_id khi bản ghi LẦN ĐẦU xuất hiện và lần gần nhất.
    # Đây là cơ sở để xác định "cái gì mới tuần này".
    first_seen_run_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    last_run_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<EvidenceItem {self.id} {self.source} {self.title[:40]!r}>"


class DuplicateLink(Base):
    """Liên kết bản ghi trùng nhau – KHÔNG xóa, chỉ trỏ duplicate -> primary."""

    __tablename__ = "duplicate_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    primary_id: Mapped[int] = mapped_column(Integer, index=True)
    duplicate_id: Mapped[int] = mapped_column(Integer, index=True)
    match_reason: Mapped[str] = mapped_column(String(64))  # doi|pmid|pmcid|nct|title_similarity
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
