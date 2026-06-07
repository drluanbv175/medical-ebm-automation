"""Connector PubMed / NCBI E-utilities.

Thật: esearch -> efetch (XML). Ở MVP, parse XML tối giản; nếu lỗi/không có email
hoặc USE_MOCK_SOURCES=true thì fallback mock. Lọc ưu tiên SR/MA/RCT/guideline qua
publication type filter trong query.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import List, Optional

from app.config import settings
from app.sources._fixtures import mock_records_for
from app.sources.base import RawRecord, SourceClient
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Bộ lọc ưu tiên các thiết kế bằng chứng mạnh.
PUBTYPE_FILTER = (
    '("systematic review"[Publication Type] OR "meta-analysis"[Publication Type] '
    'OR "randomized controlled trial"[Publication Type] OR "guideline"[Publication Type] '
    'OR "practice guideline"[Publication Type])'
)


class PubMedClient(SourceClient):
    name = "pubmed"
    endpoint = ESEARCH

    def __init__(self) -> None:
        super().__init__()
        self.http = HttpClient()

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        if self.use_mock or not settings.ncbi_email:
            logger.info("[pubmed] dùng mock (use_mock=%s, có email=%s)",
                        self.use_mock, bool(settings.ncbi_email))
            return mock_records_for(self.name, query, clinical_area, max_results)
        try:
            return self._live_search(query, clinical_area, max_results, since_date)
        except Exception as exc:  # pragma: no cover - lỗi mạng thực tế
            logger.warning("[pubmed] lỗi gọi thật (live) — BỎ QUA nguồn này, KHÔNG bịa mock: %s", exc)
            return []

    # -- Live ------------------------------------------------------------
    def _live_search(self, query: str, clinical_area: Optional[str],
                     max_results: int, since_date: Optional[str] = None) -> List[RawRecord]:
        term = f"({query}) AND {PUBTYPE_FILTER}"
        params = {
            "db": "pubmed", "term": term, "retmax": max_results,
            "retmode": "json", "email": settings.ncbi_email, "sort": "date",
        }
        # Lọc theo ngày xuất bản: chỉ bài MỚI kể từ since_date.
        if since_date:
            params["datetype"] = "pdat"
            params["mindate"] = since_date.replace("-", "/")
            params["maxdate"] = "3000/01/01"
        if settings.ncbi_api_key:
            params["api_key"] = settings.ncbi_api_key
        data = self.http.get_json(ESEARCH, params=params)
        ids = data.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        fetch_params = {
            "db": "pubmed", "id": ",".join(ids), "retmode": "xml",
            "email": settings.ncbi_email,
        }
        if settings.ncbi_api_key:
            fetch_params["api_key"] = settings.ncbi_api_key
        xml_text = self.http.get_text(EFETCH, params=fetch_params)
        self.save_raw(query, xml_text)
        return self._parse_efetch(xml_text, clinical_area, query)

    def _parse_efetch(self, xml_text: str, clinical_area: Optional[str],
                      query: str) -> List[RawRecord]:
        records: List[RawRecord] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            logger.warning("[pubmed] parse XML lỗi: %s", exc)
            return records
        for art in root.findall(".//PubmedArticle"):
            pmid = art.findtext(".//PMID")
            title = art.findtext(".//ArticleTitle") or ""
            abstract = " ".join(t.text or "" for t in art.findall(".//AbstractText"))
            journal = art.findtext(".//Journal/Title")
            year = art.findtext(".//PubDate/Year")
            pubtypes = [pt.text for pt in art.findall(".//PublicationType") if pt.text]
            mesh = [m.text for m in art.findall(".//MeshHeading/DescriptorName") if m.text]
            doi = None
            for el in art.findall(".//ArticleId"):
                if el.get("IdType") == "doi":
                    doi = el.text
            authors = ", ".join(
                f"{a.findtext('LastName') or ''} {a.findtext('Initials') or ''}".strip()
                for a in art.findall(".//Author")[:5]
            )
            records.append(RawRecord(
                source=self.name, source_type="article", title=title,
                authors=authors or None, journal_or_organization=journal,
                publication_date=year, doi=doi, pmid=pmid, abstract=abstract or None,
                document_type=pubtypes[0] if pubtypes else None,
                study_type=self._infer_study_type(pubtypes),
                clinical_area=clinical_area, mesh_terms=mesh,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                ingest_query=query, api_endpoint=EFETCH,
            ))
        return records

    @staticmethod
    def _infer_study_type(pubtypes: List[str]) -> Optional[str]:
        joined = " ".join(pubtypes).lower()
        if "meta-analysis" in joined or "systematic review" in joined:
            return "systematic_review"
        if "guideline" in joined:
            return "guideline"
        if "randomized" in joined:
            return "rct"
        return None
