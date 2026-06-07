"""Connector Europe PMC REST API – bổ sung metadata, full text/open access."""
from __future__ import annotations

from typing import List, Optional

from app.sources._fixtures import mock_records_for
from app.sources.base import RawRecord, SourceClient
from app.sources.classify_meta import infer_study_type
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def _infer_study_type(pubtype: str, journal: str, raw: dict) -> "str | None":
    """Suy study_type từ pubType + tạp chí + cờ nguồn (PPR=preprint) của Europe PMC."""
    title = raw.get("title") or ""
    return infer_study_type(f"{title} {pubtype}", pubtype, journal,
                            source_tag=raw.get("source"))


class EuropePMCClient(SourceClient):
    name = "europepmc"
    endpoint = SEARCH

    def __init__(self) -> None:
        super().__init__()
        self.http = HttpClient()

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        if self.use_mock:
            return mock_records_for(self.name, query, clinical_area, max_results)
        try:
            q = query
            if since_date:
                # Lọc bài có ngày xuất bản đầu tiên >= since_date.
                q = f"({query}) AND (FIRST_PDATE:[{since_date} TO 3000-01-01])"
            params = {"query": q, "format": "json", "pageSize": max_results,
                      "resultType": "core"}
            data = self.http.get_json(SEARCH, params=params)
            self.save_raw(query, data)
            out: List[RawRecord] = []
            for r in data.get("resultList", {}).get("result", []):
                pubtype = r.get("pubType") or ""
                journal = r.get("journalTitle") or ""
                out.append(RawRecord(
                    source=self.name, title=r.get("title", ""),
                    authors=r.get("authorString"),
                    journal_or_organization=journal,
                    publication_date=r.get("firstPublicationDate"),
                    doi=r.get("doi"), pmid=r.get("pmid"), pmcid=r.get("pmcid"),
                    abstract=r.get("abstractText"),
                    document_type=pubtype,
                    study_type=_infer_study_type(pubtype, journal, r),
                    clinical_area=clinical_area,
                    url=f"https://europepmc.org/article/{r.get('source')}/{r.get('id')}",
                    ingest_query=query, api_endpoint=SEARCH,
                ))
            return out
        except Exception as exc:  # pragma: no cover
            logger.warning("[europepmc] lỗi gọi thật (live) — BỎ QUA, KHÔNG bịa mock: %s", exc)
            return []
