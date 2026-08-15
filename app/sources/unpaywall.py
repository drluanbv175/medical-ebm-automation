"""Connector Unpaywall – kiểm tra bản full-text open access hợp pháp theo DOI.

Đây là connector tra cứu theo DOI (không phải search keyword), dùng để bổ sung
liên kết OA cho bản ghi đã có. Trả về URL OA nếu có.
"""
from __future__ import annotations

from typing import List, Optional

from app.config import settings
from app.sources.base import RawRecord, SourceClient
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
BASE = "https://api.unpaywall.org/v2"


class UnpaywallClient(SourceClient):
    name = "unpaywall"
    endpoint = BASE

    def __init__(self) -> None:
        super().__init__()
        self.http = HttpClient()

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        # Unpaywall không hỗ trợ search keyword; trả rỗng để pipeline bỏ qua.
        return []

    def oa_url_for_doi(self, doi: str) -> Optional[str]:
        """Trả về URL open access tốt nhất cho DOI (hoặc None)."""
        if self.use_mock or not settings.unpaywall_email or not doi:
            return None
        try:
            data = self.http.get_json(f"{BASE}/{doi}",
                                      params={"email": settings.unpaywall_email})
            loc = data.get("best_oa_location") or {}
            return loc.get("url")
        except Exception as exc:  # pragma: no cover
            logger.warning("[unpaywall] lỗi tra DOI %s: %s", doi, exc)
            return None
