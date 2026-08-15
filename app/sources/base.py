"""Interface chung cho mọi nguồn dữ liệu + cấu trúc RawRecord.

Mỗi connector triển khai `search()` trả về list[RawRecord]. Khi không có key /
không truy cập được mạng / USE_MOCK_SOURCES=true, connector dùng `mock_search()`
nhưng vẫn giữ NGUYÊN interface thật để dễ chuyển sang gọi thật.
"""
from __future__ import annotations

import abc
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class RawRecord:
    """Bản ghi thô đã được connector trích sơ bộ từ payload nguồn.

    Đây CHƯA phải schema chuẩn hóa cuối cùng; normalization service sẽ map tiếp.
    """

    source: str
    source_type: str = "article"
    title: str = ""
    authors: Optional[str] = None
    journal_or_organization: Optional[str] = None
    publication_date: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    nct_id: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    document_type: Optional[str] = None
    study_type: Optional[str] = None
    clinical_area: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    mesh_terms: List[str] = field(default_factory=list)
    guideline_version: Optional[str] = None
    safety_signal: Optional[str] = None
    official_grade: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)
    ingest_query: Optional[str] = None
    api_endpoint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SourceClient(abc.ABC):
    """Lớp cơ sở cho mọi nguồn."""

    name: str = "base"
    endpoint: str = ""

    def __init__(self) -> None:
        self.use_mock = settings.use_mock_sources

    @abc.abstractmethod
    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        """Gọi nguồn thật. Phải bắt lỗi và fallback mock nếu cần.

        since_date: 'YYYY-MM-DD' – chỉ lấy bài kể từ ngày này (lọc 'mới'); None = không lọc.
        """

    def mock_search(self, query: str, clinical_area: Optional[str] = None,
                    max_results: int = 20) -> List[RawRecord]:
        """Mặc định: không có dữ liệu mock. Connector cụ thể override."""
        return []

    # -- Lưu raw payload (không ghi đè dữ liệu cũ) -------------------------
    def save_raw(self, query: str, payload: Any) -> Path:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        safe_q = "".join(c if c.isalnum() else "_" for c in query)[:40]
        out_dir = settings.raw_dir / self.name
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{ts}_{safe_q}.json"
        try:
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
        except OSError as exc:  # pragma: no cover
            logger.warning("Không lưu được raw payload: %s", exc)
        return path
