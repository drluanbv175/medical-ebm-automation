"""Connector ClinicalTrials.gov API v2 – theo dõi RCT mới/đang tuyển/hoàn tất."""
from __future__ import annotations

from typing import List, Optional

from app.sources._fixtures import MOCK_EVIDENCE, mock_records_for
from app.sources.base import RawRecord, SourceClient
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
            # SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #89, vòng 6):
            # bản gốc gọi `mock_records_for(..., max_results)` trên TOÀN BỘ
            # `MOCK_EVIDENCE` rồi mới lọc `r.nct_id` — nhưng
            # `mock_records_for()` CẮT ở đúng `max_results` bản ghi khớp
            # TRƯỚC KHI hàm này kịp lọc theo NCT. Nếu `max_results` bản ghi
            # khớp ĐẦU TIÊN (theo thứ tự trong pool) không có NCT, một thử
            # nghiệm THẬT SỰ khớp truy vấn nhưng nằm SAU vị trí cắt không
            # bao giờ được thấy — `search(..., max_results=1)` có thể trả 0
            # bản ghi dù pool có thử nghiệm khớp. Sửa: lọc pool theo NCT
            # TRƯỚC khi truyền vào `mock_records_for()`, để phép cắt xảy ra
            # trên đúng tập ứng viên (chỉ bản ghi có NCT).
            pool_co_nct = [item for item in MOCK_EVIDENCE if item.get("nct_id")]
            return mock_records_for(self.name, query, clinical_area, max_results, pool=pool_co_nct)
        try:
            params = {"query.term": query, "pageSize": max_results, "format": "json"}
            if since_date:
                # Lọc theo ngày cập nhật gần nhất của hồ sơ thử nghiệm.
                params["filter.advanced"] = f"AREA[LastUpdatePostDate]RANGE[{since_date},MAX]"
            data = self.http.get_json(STUDIES, params=params)
            self.save_raw(query, data)
        except Exception as exc:  # pragma: no cover
            logger.warning("[clinicaltrials] lỗi gọi thật (live) — BỎ QUA, KHÔNG bịa mock: %s", exc)
            return []

        # SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #89, vòng 6) — cùng
        # họ lỗi đã vá ở europepmc.py (task #83): tách vòng lặp phân tích khỏi
        # try/except của lệnh gọi mạng. Đã tái hiện thực nghiệm: một study có
        # `protocolSection: null` (khoá có mặt, giá trị None) làm
        # `st.get("protocolSection", {})` trả về `None` (default không áp
        # dụng vì khoá đã tồn tại), rồi `.get("identificationModule", ...)`
        # ném AttributeError — bản gốc để lỗi đó bay ra khối except NGOÀI,
        # xoá sạch mọi study khác đã phân tích thành công trong CÙNG trang.
        out: List[RawRecord] = []
        for st in data.get("studies", []):
            try:
                ps = st.get("protocolSection") or {}
                ident = ps.get("identificationModule") or {}
                status = ps.get("statusModule") or {}
                nct = ident.get("nctId")
                out.append(RawRecord(
                    source=self.name, source_type="trial",
                    title=ident.get("officialTitle") or ident.get("briefTitle", ""),
                    journal_or_organization="ClinicalTrials.gov",
                    publication_date=(status.get("startDateStruct") or {}).get("date"),
                    nct_id=nct, document_type="clinical trial registration",
                    study_type="rct", clinical_area=clinical_area,
                    abstract=(ps.get("descriptionModule") or {}).get("briefSummary"),
                    url=f"https://clinicaltrials.gov/study/{nct}" if nct else None,
                    ingest_query=query, api_endpoint=STUDIES,
                ))
            except Exception as exc:  # pragma: no cover
                logger.warning("[clinicaltrials] bỏ qua 1 bản ghi hỏng trong trang kết quả (query=%r): %s", query, exc)
                continue
        return out
