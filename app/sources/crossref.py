"""Connector Crossref REST API – chuẩn hóa DOI, metadata thư mục, publication type."""
from __future__ import annotations

from typing import List, Optional

from app.config import settings
from app.sources._fixtures import mock_records_for
from app.sources.base import RawRecord, SourceClient
from app.sources.classify_meta import infer_study_type
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
WORKS = "https://api.crossref.org/works"


class CrossrefClient(SourceClient):
    name = "crossref"
    endpoint = WORKS

    def __init__(self) -> None:
        super().__init__()
        self.http = HttpClient()

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        if self.use_mock:
            return mock_records_for(self.name, query, clinical_area, max_results)
        try:
            params = {"query": query, "rows": max_results,
                      "select": "DOI,title,author,container-title,issued,type,abstract"}
            if since_date:
                params["filter"] = f"from-pub-date:{since_date}"
            if settings.openalex_email:  # mailto polite pool
                params["mailto"] = settings.openalex_email
            data = self.http.get_json(WORKS, params=params)
            self.save_raw(query, data)
        except Exception as exc:  # pragma: no cover
            logger.warning("[crossref] lỗi gọi thật (live) — BỎ QUA, KHÔNG bịa mock: %s", exc)
            return []

        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #89, vòng 6) — cùng
        # họ lỗi đã vá ở europepmc.py (task #83): vòng lặp phân tích bản ghi
        # trước đây nằm CHUNG try/except với lệnh gọi mạng, nên MỘT bản ghi có
        # cấu trúc bất thường (vd Crossref trả "author": None cho bản ghi thiếu
        # metadata tác giả — có thật trên dữ liệu sống) làm bay AttributeError,
        # bị khối except NGOÀI bắt và XOÁ SẠCH mọi bản ghi đã phân tích thành
        # công trước đó trong CÙNG trang. Tách riêng: lỗi một bản ghi chỉ bỏ
        # qua đúng bản ghi đó.
        out: List[RawRecord] = []
        for it in data.get("message", {}).get("items", []):
            try:
                title = (it.get("title") or [""])[0]
                authors = ", ".join(
                    f"{a.get('family', '')} {a.get('given', '')}".strip()
                    for a in it.get("author", [])[:5]
                )
                issued = it.get("issued", {}).get("date-parts", [[None]])[0]
                year = str(issued[0]) if issued and issued[0] else None
                journal = (it.get("container-title") or [None])[0]
                out.append(RawRecord(
                    source=self.name, title=title, authors=authors or None,
                    journal_or_organization=journal,
                    publication_date=year, doi=it.get("DOI"),
                    abstract=it.get("abstract"), document_type=it.get("type"),
                    study_type=infer_study_type(title, it.get("type"), journal),
                    clinical_area=clinical_area,
                    url=f"https://doi.org/{it.get('DOI')}" if it.get("DOI") else None,
                    ingest_query=query, api_endpoint=WORKS,
                ))
            except Exception as exc:  # pragma: no cover
                logger.warning("[crossref] bỏ qua 1 bản ghi hỏng trong trang kết quả (query=%r): %s", query, exc)
                continue
        return out
