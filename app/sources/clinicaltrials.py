"""Connector ClinicalTrials.gov API v2 – theo dõi RCT mới/đang tuyển/hoàn tất."""
from __future__ import annotations

from typing import List, Optional

from app.sources.base import RawRecord, SourceClient
from app.sources._fixtures import mock_records_for
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
STUDIES = "https://clinicaltrials.gov/api/v2/studies"


class ClinicalTrialsClient(SourceClient):
    name = "clinicaltrials"
    endpoint = STUDIES

    def __init__(self) -> None:
        super().__init__()
        self.http = HttpClient()

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        if self.use_mock:
            # Chỉ trả các bản ghi có NCT trong pool mock.
            recs = mock_records_for(self.name, query, clinical_area, max_results)
            return [r for r in recs if r.nct_id]
        try:
            params = {"query.term": query, "pageSize": max_results, "format": "json"}
            if since_date:
                # Lọc theo ngày cập nhật gần nhất của hồ sơ thử nghiệm.
                params["filter.advanced"] = f"AREA[LastUpdatePostDate]RANGE[{since_date},MAX]"
            data = self.http.get_json(STUDIES, params=params)
            self.save_raw(query, data)
            out: List[RawRecord] = []
            for st in data.get("studies", []):
                ps = st.get("protocolSection", {})
                ident = ps.get("identificationModule", {})
                status = ps.get("statusModule", {})
                nct = ident.get("nctId")
                out.append(RawRecord(
                    source=self.name, source_type="trial",
                    title=ident.get("officialTitle") or ident.get("briefTitle", ""),
                    journal_or_organization="ClinicalTrials.gov",
                    publication_date=status.get("startDateStruct", {}).get("date"),
                    nct_id=nct, document_type="clinical trial registration",
                    study_type="rct", clinical_area=clinical_area,
                    abstract=ps.get("descriptionModule", {}).get("briefSummary"),
                    url=f"https://clinicaltrials.gov/study/{nct}" if nct else None,
                    ingest_query=query, api_endpoint=STUDIES,
                ))
            return out
        except Exception as exc:  # pragma: no cover
            logger.warning("[clinicaltrials] lỗi gọi thật (live) — BỎ QUA, KHÔNG bịa mock: %s", exc)
            return []
