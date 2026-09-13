"""Connector DynaMed / DynaMedex (EBSCO) — thêm 13/09/2026 theo yêu cầu bác sĩ, sau khi
bác sĩ xác nhận đang có tài khoản DynaMed.

KHÁC MỌI NGUỒN KHÁC trong `app/sources/`: DynaMed không dùng API key đơn giản (như
Scopus/NCBI) mà dùng OAuth 2.0 `client_credentials` — client_id/client_secret đổi
lấy một access token có hạn (4 giờ), token đó mới dùng để gọi endpoint tìm kiếm.

⚠️ ĐIỀU KIỆN TIÊN QUYẾT bác sĩ cần biết TRƯỚC khi mong connector này chạy được:
đăng ký ứng dụng khách tại
https://developer.ebsco.com/medical-point-care-apis/dynamed/register-app đòi
"Customer ID" và "Group ID" do **đại diện EBSCO cấp riêng** cho tài khoản — nghĩa
là KHÔNG PHẢI mọi tài khoản DynaMed cá nhân/website (chỉ đăng nhập trình duyệt)
đều tự động có quyền gọi MedsAPI. Cần xác nhận với EBSCO/đơn vị chủ quản xem gói
đang dùng có đi kèm quyền MedsAPI hay không.

Tài liệu dưới đây đã XÁC MINH TRỰC TIẾP (WebFetch developer.ebsco.com/dynamed,
KHÔNG lấy từ trí nhớ) ngày 13/09/2026 — đúng kỷ luật "chỉ dùng nguồn đã xác minh"
của repo này:
  • Lấy access token: POST https://apis.ebsco.com/medsapi-auth/v1/token
      {"grant_type": "client_credentials", "client_id": ..., "client_secret": ...,
       "product": "dynamed" | "dynamedex"}
    -> {"access_token": "..."} , hết hạn sau 4 giờ.
  • Tìm nội dung: POST https://apis.ebsco.com/medsapi-dynamed/v2/content/search
    header Authorization: Bearer <token>
      {"query": "...", "fields": [...], "pageSize": N}
    -> {"items": [{"id", "title", "pubType": {"title": ...}, "slug", "exactMatch",
                   "links": [{"rel": "self", "href": ...}]}]}

GIỚI HẠN ĐÃ BIẾT, ghi rõ để không ai hiểu nhầm phạm vi/độ phủ:
  • DynaMed là nguồn TỔNG HỢP THỨ CẤP tại điểm khám (Condition/Drug Monograph/…),
    KHÔNG phải bài báo gốc — "id" dạng "T916967" không phải PMID/DOI. Connector
    này vì vậy KHÔNG tham gia chuỗi 3 tầng kiểm rút bài của retraction_chain.py,
    giống Scopus/OpenAlex/Crossref/Semantic Scholar.
  • Nội dung DynaMed có bản quyền/giấy phép EBSCO. `fields` CỐ Ý chỉ xin
    "title"+"pubType" (KHÔNG xin "description"/"sections"/"toc" — nội dung đầy đủ)
    để tránh việc toàn văn có bản quyền bị lưu vào cache (`data/raw/dynamed/`,
    `data/raw/_http_cache/`) hoặc lọt vào dashboard/export git-tracked. Kết quả
    trả về chỉ mang tiêu đề + đường link — bác sĩ tự mở DynaMed để đọc toàn văn.
  • `product` mặc định "dynamed"; đổi DYNAMED_PRODUCT=dynamedex nếu tài khoản là
    DynaMedex (thêm dữ liệu thuốc Micromedex) — sai giá trị `product` sẽ bị từ
    chối ở bước lấy token dù client_id/secret đúng.
  • Phạm vi bản đầu: mới nối vào TẦNG NGHIÊN CỨU (`app/sources/`, `run.py
    test-live dynamed`) — CHƯA nối vào tầng giám sát lâm sàng
    (`EBM-Dashboards/tools/surveillance_scan.py`), khác Scopus đã có ở cả hai
    tầng. Nối tầng lâm sàng là bước tiếp theo nếu bác sĩ xác nhận connector này
    chạy được thật với key thật.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.config import settings
from app.sources._fixtures import mock_records_for
from app.sources.base import RawRecord, SourceClient
from app.sources.classify_meta import infer_study_type
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

TOKEN_URL = "https://apis.ebsco.com/medsapi-auth/v1/token"
SEARCH_URL = "https://apis.ebsco.com/medsapi-dynamed/v2/content/search"

# Tài liệu chính thức: "the access token ... will expire in 4 hours". Trừ hao 5
# phút để không dùng sát nút lúc một request đang bay giữa đường.
_TOKEN_TTL_SECONDS = 4 * 3600 - 300


def _lay_url_dynamed(slug: Optional[str], links: Optional[List[dict]]) -> Optional[str]:
    """Ưu tiên URL đọc công khai dựng từ `slug` (vd '/condition/...'); dự phòng
    lấy href của link @rel == 'self' (trỏ vào API, không phải trang đọc, nhưng
    còn hơn không có gì) nếu `slug` vắng mặt."""
    if slug:
        return f"https://www.dynamed.com{slug}"
    for lk in links or []:
        if isinstance(lk, dict) and lk.get("rel") == "self":
            href = lk.get("href")
            if href:
                return href
    return None


class DynaMedClient(SourceClient):
    name = "dynamed"
    endpoint = SEARCH_URL

    def __init__(self) -> None:
        super().__init__()
        self.http = HttpClient(default_headers={"Accept": "application/json"})
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def _lay_token(self) -> str:
        """Lấy access token OAuth2 (client_credentials), tự làm mới khi hết hạn.

        KHÔNG đi qua cache file của HttpClient (`use_cache=False`, mặc định của
        `post_json`) — access_token là bí mật, không được ghi ra đĩa lâu hơn cần
        thiết; cache trong bộ nhớ tiến trình (`self._token`) là đủ."""
        now = time.monotonic()
        if self._token and now < self._token_expires_at:
            return self._token
        payload = {
            "grant_type": "client_credentials",
            "client_id": settings.dynamed_client_id,
            "client_secret": settings.dynamed_client_secret,
            "product": settings.dynamed_product,
        }
        data = self.http.post_json(TOKEN_URL, json_body=payload)
        token = data.get("access_token")
        if not token:
            raise RuntimeError(
                "[dynamed] Phản hồi OAuth2 không có 'access_token' — kiểm lại "
                "DYNAMED_CLIENT_ID/DYNAMED_CLIENT_SECRET/DYNAMED_PRODUCT "
                "('dynamed' hoặc 'dynamedex') trong ~/.ebm-secrets/"
                "medical-ebm-automation.env."
            )
        self._token = token
        self._token_expires_at = now + _TOKEN_TTL_SECONDS
        return token

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        # since_date không dùng: DynaMed là nội dung tổng hợp được CẬP NHẬT liên
        # tục trên CÙNG một article (không phải xuất bản rời rạc theo ngày như
        # bài báo) — API tìm kiếm không có tham số lọc theo ngày.
        if self.use_mock:
            return mock_records_for(self.name, query, clinical_area, max_results)

        if not settings.dynamed_client_id or not settings.dynamed_client_secret:
            # Chặn SỚM, rõ ràng — cùng nguyên tắc fail-closed của ScopusClient:
            # nguồn BẬT mà thiếu điều kiện thật phải NỔ TO, không âm thầm trả rỗng.
            raise RuntimeError(
                "[dynamed] ENABLE_DYNAMED=true nhưng thiếu DYNAMED_CLIENT_ID/"
                "DYNAMED_CLIENT_SECRET — đăng ký app tại https://developer.ebsco.com/"
                "medical-point-care-apis/dynamed/register-app (cần Customer ID + "
                "Group ID do đại diện EBSCO cấp cho tài khoản) rồi thêm 2 giá trị "
                "này vào ~/.ebm-secrets/medical-ebm-automation.env."
            )

        try:
            token = self._lay_token()
            body: Dict[str, Any] = {
                "query": query,
                "fields": ["title", "pubType"],
                "pageSize": min(max_results, 30),
            }
            data = self.http.post_json(
                SEARCH_URL, json_body=body,
                headers={"Authorization": f"Bearer {token}"},
                use_cache=True,  # an toàn: chỉ cache tiêu đề công khai, không cache token
            )
            self.save_raw(query, data)
        except Exception as exc:  # pragma: no cover
            logger.warning("[dynamed] lỗi gọi thật (live) — BỎ QUA, KHÔNG bịa mock: %s", exc)
            return []

        items = data.get("items") or []
        out: List[RawRecord] = []
        organization = "DynaMedex" if settings.dynamed_product == "dynamedex" else "DynaMed"
        for it in items:
            try:
                title = it.get("title") or ""
                pub_type = (it.get("pubType") or {}).get("title")
                out.append(RawRecord(
                    source=self.name, title=title,
                    authors=None,  # DynaMed là nội dung biên tập tập thể, không có tác giả cá nhân
                    journal_or_organization=organization,
                    publication_date=None,  # nội dung được CẬP NHẬT liên tục, không có ngày xuất bản cố định
                    doi=None, pmid=None,
                    abstract=None,  # cố ý KHÔNG xin field nội dung đầy đủ — xem docstring module
                    document_type=pub_type,
                    study_type=infer_study_type(title, pub_type, organization),
                    clinical_area=clinical_area,
                    url=_lay_url_dynamed(it.get("slug"), it.get("links")),
                    ingest_query=query, api_endpoint=SEARCH_URL,
                    raw={"id": it.get("id"), "exactMatch": it.get("exactMatch")},
                ))
            except Exception as exc:  # pragma: no cover
                logger.warning("[dynamed] bỏ qua 1 bản ghi hỏng (query=%r): %s", query, exc)
                continue
        return out
