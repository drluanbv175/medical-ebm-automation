"""Connector OpenAlex – metadata học thuật mở, citation count, topic, source."""
from __future__ import annotations

from typing import List, Optional

from app.config import settings
from app.sources._fixtures import mock_records_for
from app.sources.base import RawRecord, SourceClient
from app.sources.classify_meta import infer_study_type
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
WORKS = "https://api.openalex.org/works"


class OpenAlexClient(SourceClient):
    name = "openalex"
    endpoint = WORKS

    def __init__(self) -> None:
        super().__init__()
        self.http = HttpClient()

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        if self.use_mock:
            return mock_records_for(self.name, query, clinical_area, max_results)
        try:
            params = {"search": query, "per-page": max_results}
            if since_date:
                params["filter"] = f"from_publication_date:{since_date}"
            if settings.openalex_email:
                params["mailto"] = settings.openalex_email
            data = self.http.get_json(WORKS, params=params)
            self.save_raw(query, data)
        except Exception as exc:  # pragma: no cover
            logger.warning("[openalex] lỗi gọi thật (live) — BỎ QUA, KHÔNG bịa mock: %s", exc)
            return []

        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #89, vòng 6) — cùng
        # họ lỗi đã vá ở europepmc.py (task #83): tách vòng lặp phân tích khỏi
        # try/except của lệnh gọi mạng. Đã tái hiện thực nghiệm: OpenAlex có
        # thể trả `"concepts": null` cho một work (khoá có mặt, giá trị None,
        # không rơi vào default của .get()) — `None[:5]` ném TypeError, và bản
        # gốc để lỗi đó bay ra khối except NGOÀI, xoá sạch mọi work khác đã
        # phân tích thành công trong CÙNG trang.
        out: List[RawRecord] = []
        for w in data.get("results", []):
            try:
                doi = (w.get("doi") or "").replace("https://doi.org/", "") or None
                title = w.get("title") or ""
                journal = ((w.get("primary_location") or {}).get("source") or {}
                           ).get("display_name") if w.get("primary_location") else None
                # OpenAlex có cờ riêng cho preprint (type_crossref / is preprint)
                src_tag = "preprint" if (w.get("type") == "preprint"
                                         or (w.get("primary_location") or {}).get("version")
                                         == "submittedVersion") else None
                out.append(RawRecord(
                    source=self.name, title=title,
                    journal_or_organization=journal,
                    publication_date=w.get("publication_date"),
                    doi=doi, document_type=w.get("type"),
                    study_type=infer_study_type(title, w.get("type"), journal, src_tag),
                    clinical_area=clinical_area, url=w.get("id"),
                    keywords=[c.get("display_name") for c in (w.get("concepts") or [])[:5]],
                    ingest_query=query, api_endpoint=WORKS,
                ))
            except Exception as exc:  # pragma: no cover
                logger.warning("[openalex] bỏ qua 1 bản ghi hỏng trong trang kết quả (query=%r): %s", query, exc)
                continue
        return out
