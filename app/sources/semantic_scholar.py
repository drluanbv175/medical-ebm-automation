"""Connector Semantic Scholar – citation, influential citations, abstract, metadata."""
from __future__ import annotations

from typing import List, Optional

from app.config import settings
from app.sources.base import RawRecord, SourceClient
from app.sources._fixtures import mock_records_for
from app.sources.classify_meta import infer_study_type
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,abstract,year,venue,externalIds,authors,publicationTypes,citationCount"


class SemanticScholarClient(SourceClient):
    name = "semantic_scholar"
    endpoint = SEARCH

    def __init__(self) -> None:
        super().__init__()
        headers = {}
        if settings.semantic_scholar_api_key:
            headers["x-api-key"] = settings.semantic_scholar_api_key
        self.http = HttpClient(default_headers=headers or None)

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        if self.use_mock:
            return mock_records_for(self.name, query, clinical_area, max_results)
        try:
            params = {"query": query, "limit": max_results, "fields": FIELDS}
            if since_date:
                # S2 lọc theo năm; dùng năm của since_date làm cận dưới (xấp xỉ).
                params["year"] = f"{since_date[:4]}-"
            data = self.http.get_json(SEARCH, params=params)
            self.save_raw(query, data)
            out: List[RawRecord] = []
            for p in data.get("data", []):
                ext = p.get("externalIds") or {}
                ptypes = p.get("publicationTypes") or []
                title = p.get("title") or ""
                venue = p.get("venue")
                # S2 publicationTypes: vd 'Review','JournalArticle','ClinicalTrial'
                dt = " ".join(ptypes) if ptypes else None
                out.append(RawRecord(
                    source=self.name, title=title,
                    authors=", ".join(a.get("name", "") for a in p.get("authors", [])[:5]) or None,
                    journal_or_organization=venue,
                    publication_date=str(p.get("year")) if p.get("year") else None,
                    doi=ext.get("DOI"), pmid=str(ext.get("PubMed")) if ext.get("PubMed") else None,
                    abstract=p.get("abstract"),
                    document_type=ptypes[0] if ptypes else None,
                    study_type=infer_study_type(title, dt, venue),
                    clinical_area=clinical_area,
                    url=f"https://www.semanticscholar.org/paper/{p.get('paperId')}",
                    ingest_query=query, api_endpoint=SEARCH,
                ))
            return out
        except Exception as exc:  # pragma: no cover
            logger.warning("[semantic_scholar] lỗi gọi thật (live) — BỎ QUA, KHÔNG bịa mock: %s", exc)
            return []
