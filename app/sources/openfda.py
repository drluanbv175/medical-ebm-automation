"""Connector openFDA – cảnh báo an toàn thuốc & tín hiệu FAERS.

NGUYÊN TẮC QUAN TRỌNG (an toàn thuốc):
- FAERS là báo cáo tự phát, CHỈ dùng để phát hiện tín hiệu / mô tả báo cáo.
- KHÔNG suy luận quan hệ nhân quả từ FAERS.
- Cảnh báo chính thức FDA/EMA/MHRA/WHO có trọng số cao hơn dữ liệu báo cáo tự phát.
"""
from __future__ import annotations

from typing import List, Optional

from app.sources._fixtures import MOCK_DRUG_SAFETY, mock_records_for
from app.sources.base import RawRecord, SourceClient
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
EVENT = "https://api.fda.gov/drug/event.json"


def _escape_lucene_phrase(text: str) -> str:
    """Thoát dấu `\\` và `"` trước khi nhét vào một cụm trích dẫn Lucene.

    openFDA (nền Elasticsearch) dùng cú pháp truy vấn Lucene: `field:"cụm từ"`
    là khớp NGUYÊN CỤM. Bên trong cụm trích dẫn, chỉ gạch chéo ngược và `"`
    có ý nghĩa cú pháp (theo chuẩn Lucene) — một dấu `"` chưa thoát sẽ ĐÓNG
    cụm trích dẫn SỚM, phần còn lại của `text` rơi ra ngoài và bị Lucene diễn giải
    như CÚ PHÁP TRUY VẤN THÊM (có thể gồm toán tử `AND`/`OR`, ký tự đại diện,
    hoặc bộ lọc trường khác `field:value`) thay vì dữ liệu văn bản thuần —
    đúng lớp lỗi "query injection" qua chuỗi định dạng không thoát ký tự.
    """
    return text.replace("\\", "\\\\").replace('"', '\\"')


class OpenFDAClient(SourceClient):
    name = "openfda"
    endpoint = EVENT

    def __init__(self) -> None:
        super().__init__()
        self.http = HttpClient()

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        if self.use_mock:
            # Pool an toàn thuốc dùng chung; trả tín hiệu cho mọi truy vấn thuốc (demo).
            recs = mock_records_for(self.name, "", "An toàn thuốc",
                                    max_results, pool=MOCK_DRUG_SAFETY)
            for r in recs:
                r.ingest_query = query
            return recs
        try:
            # SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #75) — trước bản
            # vá, `query` được nhét THẲNG vào cụm trích dẫn Lucene, không thoát
            # dấu `"`. Một tên thuốc/chuỗi truy vấn chứa `"` sẽ đóng cụm trích
            # dẫn sớm, phần còn lại rơi ra ngoài và bị openFDA diễn giải như cú
            # pháp truy vấn thêm — xem `_escape_lucene_phrase()` để biết cơ chế.
            query_an_toan = _escape_lucene_phrase(query)
            params = {"search": f'patient.drug.medicinalproduct:"{query_an_toan}"',
                      "count": "patient.reaction.reactionmeddrapt.exact", "limit": max_results}
            data = self.http.get_json(EVENT, params=params)
            self.save_raw(query, data)
            out: List[RawRecord] = []
            for row in data.get("results", []):
                reaction = row.get("term", "")
                count = row.get("count", 0)
                out.append(RawRecord(
                    source=self.name, source_type="drug_safety",
                    title=f"FAERS signal: {query} – {reaction} ({count} reports)",
                    journal_or_organization="openFDA FAERS",
                    document_type="spontaneous report signal",
                    study_type="pharmacovigilance_signal",
                    clinical_area="An toàn thuốc",
                    safety_signal=(f"{count} báo cáo phản ứng '{reaction}'. "
                                   "FAERS chỉ là tín hiệu, KHÔNG kết luận nhân quả."),
                    url="https://open.fda.gov/apis/drug/event/",
                    ingest_query=query, api_endpoint=EVENT,
                ))
            return out
        except Exception as exc:  # pragma: no cover
            logger.warning("[openfda] lỗi gọi thật (live) — BỎ QUA, KHÔNG bịa mock: %s", exc)
            return []
