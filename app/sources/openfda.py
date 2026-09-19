"""Connector openFDA – cảnh báo an toàn thuốc & tín hiệu FAERS.

NGUYÊN TẮC QUAN TRỌNG (an toàn thuốc):
- FAERS là báo cáo tự phát, CHỈ dùng để phát hiện tín hiệu / mô tả báo cáo.
- KHÔNG suy luận quan hệ nhân quả từ FAERS.
- Cảnh báo chính thức FDA/EMA/MHRA/WHO có trọng số cao hơn dữ liệu báo cáo tự phát.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from app.config import settings
from app.sources._fixtures import MOCK_DRUG_SAFETY, mock_records_for
from app.sources.base import RawRecord, SourceClient
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
EVENT = "https://api.fda.gov/drug/event.json"

# openFDA (sau api.data.gov) trả 401/403 (`API_KEY_INVALID`/`API_KEY_DISABLED`/…) khi khoá SAI.
_MA_KHOA_BI_TU_CHOI = (401, 403)

# Kết quả của lần gọi CÓ KHOÁ gần nhất: "chap_nhan" · "bi_tu_choi" · None (chưa có lần nào). Để
# `run.py test-live openfda` báo được khoá có THẬT SỰ được FDA chấp nhận hay không — chỉ "đã nạp
# khoá" thì chưa chứng minh gì (khoá gõ nhầm vẫn được nạp).
trang_thai_khoa: Optional[str] = None


def get_json_openfda(http: HttpClient, url: str, params: Dict[str, Any]) -> Any:
    """GET api.fda.gov, gắn `api_key` nếu `OPENFDA_API_KEY` được đặt — DÙNG CHUNG cho mọi nơi
    gọi openFDA (connector FAERS, tra nhãn thuốc, live adapter) để không nơi nào quên khoá.

    Vì sao có nhánh lùi: openFDA chạy được KHÔNG khoá, nên khoá chỉ nên làm hệ TỐT HƠN, không
    bao giờ tệ hơn. Khoá gõ nhầm (dán thừa dấu nháy, xuống dòng…) bị trả 403 — mà
    `OpenFDAClient.search()` nuốt mọi lỗi và trả `[]`, tức luồng giám sát đang chạy tốt
    KHÔNG khoá sẽ chuyển thành «không có tín hiệu nào» một cách im lặng (đúng lớp lỗi BH27/BH08:
    «không kiểm được» bị đọc thành «sạch»). Nên khi khoá bị từ chối: cảnh báo RÕ tên biến cần
    kiểm rồi thử lại một lần KHÔNG khoá — dữ liệu trả về vẫn là dữ liệu THẬT của FDA, chỉ chịu
    trần lượt gọi thấp hơn. Mã lỗi khác (404 «không khớp», 5xx, timeout) đi thẳng lên cho nơi
    gọi xử lý như cũ.
    """
    global trang_thai_khoa
    khoa = settings.openfda_api_key
    if not khoa:
        return http.get_json(url, params=params)
    try:
        kq = http.get_json(url, params={**params, "api_key": khoa})
        trang_thai_khoa = "chap_nhan"
        return kq
    except requests.HTTPError as exc:
        ma = exc.response.status_code if exc.response is not None else None
        if ma in _MA_KHOA_BI_TU_CHOI:
            trang_thai_khoa = "bi_tu_choi"
            logger.warning(
                "[openfda] OPENFDA_API_KEY bị từ chối (HTTP %s) — kiểm lại khoá trong "
                "~/.ebm-secrets/medical-ebm-automation.env (dán thừa ký tự?). Tạm thử lại "
                "KHÔNG khoá; dữ liệu vẫn thật nhưng chịu trần lượt gọi thấp hơn.", ma)
            return http.get_json(url, params=params)
        raise


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
            data = get_json_openfda(self.http, EVENT, params)
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
