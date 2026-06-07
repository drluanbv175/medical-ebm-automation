"""Connector Zotero Web API (optional) – đẩy tài liệu quan trọng vào collection.

Bật bằng ENABLE_ZOTERO=true + ZOTERO_API_KEY + ZOTERO_LIBRARY_ID.
Nếu chưa cấu hình, các hàm trả về cảnh báo nhẹ và không lỗi.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from app.config import settings
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class ZoteroClient:
    name = "zotero"

    def __init__(self) -> None:
        self.enabled = (
            settings.enable_zotero
            and bool(settings.zotero_api_key)
            and bool(settings.zotero_library_id)
        )
        self.base = (
            f"https://api.zotero.org/{settings.zotero_library_type}s/"
            f"{settings.zotero_library_id}"
        )
        headers = {"Zotero-API-Key": settings.zotero_api_key} if settings.zotero_api_key else None
        self.http = HttpClient(default_headers=headers, cache_ttl=0)

    def is_ready(self) -> bool:
        return self.enabled

    def push_items(self, items: List[Dict], collection_key: Optional[str] = None) -> Dict:
        """Đẩy danh sách item (định dạng Zotero) vào thư viện.

        items: list dict theo schema item Zotero (itemType, title, DOI, tags...).
        """
        if not self.enabled:
            logger.info("[zotero] chưa bật/chưa cấu hình – bỏ qua push %d item.", len(items))
            return {"status": "skipped", "reason": "zotero_not_configured", "count": 0}
        try:
            # Zotero POST /items với payload list JSON.
            import requests  # local import để giữ optional
            resp = requests.post(
                f"{self.base}/items",
                headers={"Zotero-API-Key": settings.zotero_api_key,
                         "Content-Type": "application/json"},
                json=items, timeout=settings.http_timeout,
            )
            resp.raise_for_status()
            return {"status": "ok", "count": len(items), "response": resp.json()}
        except Exception as exc:  # pragma: no cover
            logger.warning("[zotero] lỗi push: %s", exc)
            return {"status": "error", "error": str(exc), "count": 0}

    def push_actionable_evidence(self, collection_key: Optional[str] = None) -> Dict:
        """Đẩy các bản ghi actionable/need_full_text (record chính) vào Zotero.

        Gắn tag theo chuyên khoa + reliability tier + phân loại. Trả về kết quả.
        Nếu chưa cấu hình Zotero -> trả status 'skipped' (không lỗi).
        """
        from app.database import session_scope
        from app.models import EvidenceItem

        with session_scope() as s:
            rows = (s.query(EvidenceItem)
                    .filter(EvidenceItem.is_primary_record.is_(True))
                    .filter(EvidenceItem.classification.in_(["actionable", "need_full_text"]))
                    .all())
            items = []
            for r in rows:
                tags = [t for t in (r.clinical_area, f"tier:{r.reliability_tier}",
                                    r.classification, r.study_type) if t]
                items.append(self.to_zotero_item({
                    "title": r.title, "authors": r.authors,
                    "journal_or_organization": r.journal_or_organization,
                    "publication_date": r.publication_date, "doi": r.doi, "url": r.url,
                }, tags=tags))
        if not items:
            return {"status": "empty", "count": 0}
        return self.push_items(items, collection_key=collection_key)

    @staticmethod
    def to_zotero_item(evidence: Dict, tags: Optional[List[str]] = None) -> Dict:
        """Map một evidence dict sang item Zotero tối giản (journalArticle)."""
        return {
            "itemType": "journalArticle",
            "title": evidence.get("title", ""),
            "creators": [{"creatorType": "author", "name": evidence.get("authors", "")}],
            "publicationTitle": evidence.get("journal_or_organization", ""),
            "date": evidence.get("publication_date", ""),
            "DOI": evidence.get("doi", "") or "",
            "url": evidence.get("url", "") or "",
            "tags": [{"tag": t} for t in (tags or [])],
        }
