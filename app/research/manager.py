"""Quản lý dự án nghiên cứu + tích hợp tìm tài liệu nền từ pipeline EBM."""
from __future__ import annotations

from typing import Dict, List, Optional

from app.database import session_scope
from app.models import EvidenceItem, ResearchProject
from app.services.fallback_ladder import (
    bo_sung_neu_thieu,
    du_phong_dang_bat,
    goi_nguon_thuong,
    tom_tat_ngan,
)
from app.sources import get_enabled_sources
from app.sources.base import RawRecord
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

STATUS_FIELDS = [
    "data_collection_status", "ethics_status", "protocol_status",
    "questionnaire_status", "spss_status", "analysis_status",
    "report_status", "manuscript_status",
]


def add_project(data: Dict) -> int:
    """Thêm/cập nhật đề tài theo project_id. Trả về id DB."""
    with session_scope() as s:
        existing = s.query(ResearchProject).filter_by(
            project_id=data["project_id"]).first()
        if existing:
            for k, v in data.items():
                if hasattr(existing, k):
                    setattr(existing, k, v)
            s.flush()
            return existing.id
        obj = ResearchProject(**{k: v for k, v in data.items()
                                 if hasattr(ResearchProject, k)})
        s.add(obj)
        s.flush()
        return obj.id


def list_projects() -> List[Dict]:
    with session_scope() as s:
        rows = s.query(ResearchProject).order_by(ResearchProject.updated_at.desc()).all()
        return [_to_dict(r) for r in rows]


def update_project(project_id: str, **fields) -> bool:
    with session_scope() as s:
        obj = s.query(ResearchProject).filter_by(project_id=project_id).first()
        if not obj:
            return False
        for k, v in fields.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        return True


def link_evidence(project_id: str, evidence_ids: List[int]) -> bool:
    with session_scope() as s:
        obj = s.query(ResearchProject).filter_by(project_id=project_id).first()
        if not obj:
            return False
        current = set(obj.linked_evidence_ids or [])
        current.update(evidence_ids)
        obj.linked_evidence_ids = sorted(current)
        return True


def suggest_background_literature(query: str, clinical_area: Optional[str] = None,
                                  max_results: int = 10) -> List[Dict]:
    """Gợi ý tài liệu nền (guideline/SR/MA/RCT) cho một đề tài.

    Ưu tiên các nguồn mạnh đã có trong DB; nếu chưa có, quét nhanh qua connector.
    Trả về danh sách tài liệu kèm link truy vết.

    BẬC THANG DỰ PHÒNG (20/09/2026): Consensus/SerpApi Scholar không nằm trong vòng quét nhanh. Khi được bật (và
    không mock) và chứng cứ đáng tin của truy vấn vẫn còn thiếu SAU vòng quét, mới hỏi thêm và chỉ thêm bài được
    Crossref/PubMed xác minh (mỗi mục có `phat_hien_boi`); lỗi/lý do được ghi vào log (hàm này trả list, không có
    kênh lỗi khác).
    """
    results: List[Dict] = []
    with session_scope() as s:
        q = s.query(EvidenceItem).filter(
            EvidenceItem.reliability_tier.in_(["A", "B"]),
            EvidenceItem.is_primary_record.is_(True),
        )
        if clinical_area:
            q = q.filter(EvidenceItem.clinical_area == clinical_area)
        for r in q.limit(max_results).all():
            results.append({
                "id": r.id, "title": r.title, "type": r.study_type,
                "tier": r.reliability_tier, "doi": r.doi, "pmid": r.pmid,
                "url": r.url, "source": r.source,
            })

    if results:
        return results

    # Fallback: quét nhanh connector (mock/live tùy cấu hình).
    dang_bat = du_phong_dang_bat()
    logs_thuong: Optional[List[dict]] = [] if dang_bat else None
    raw_thuong: List[RawRecord] = []
    for client in get_enabled_sources():
        try:
            recs = goi_nguon_thuong(client, query, clinical_area, max_results, logs_thuong)
            raw_thuong.extend(recs)
            for rec in recs:
                results.append({"title": rec.title, "type": rec.study_type,
                                "doi": rec.doi, "pmid": rec.pmid, "url": rec.url,
                                "source": rec.source})
        except Exception as exc:  # pragma: no cover
            logger.warning("Gợi ý tài liệu lỗi nguồn %s: %s", client.name, exc)
        if len(results) >= max_results:
            break

    if dang_bat:
        # Chỉ hỏi tầng dự phòng khi chứng cứ ĐÁNG TIN còn thiếu (cổng chấm điểm lại từ RawRecord, không tin đếm
        # số lượng thô). Bản ghi thêm là bản ghi của Crossref/PubMed đã xác minh, xếp SAU kết quả thường.
        try:
            xac_minh, tom_tat = bo_sung_neu_thieu(query, clinical_area, raw_thuong, max_results=max_results,
                                                  logs=logs_thuong)
            them = [{"title": rec.title, "type": rec.study_type,
                     "doi": rec.doi, "pmid": rec.pmid, "url": rec.url,
                     "source": rec.source,
                     "phat_hien_boi": (rec.raw or {}).get("phat_hien_boi"),
                     "chua_xac_minh": bool((rec.raw or {}).get("chua_xac_minh"))} for rec in xac_minh]
            if them:
                # chừa chỗ cho bài đã xác minh: chúng là lý do duy nhất để hỏi thêm, không được bị cắt đuôi
                results = results[:max(0, max_results - len(them))] + them
            ghi_chu = tom_tat_ngan(tom_tat)
            if ghi_chu:
                logger.warning("Bậc thang dự phòng (gợi ý tài liệu nền): %s", ghi_chu)
        except Exception as exc:  # noqa: BLE001 — bậc thang không được làm hỏng gợi ý
            logger.warning("Bậc thang dự phòng lỗi ở gợi ý tài liệu nền (%s).", type(exc).__name__)
    return results[:max_results]


def _to_dict(r: ResearchProject) -> Dict:
    return {c.name: getattr(r, c.name) for c in r.__table__.columns}
