"""Bước 2: Normalization – chuyển RawRecord về dict schema chuẩn hóa chung."""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

from app.services.filtering import ly_do_rut_bai
from app.sources.base import RawRecord
from app.utils.text import clean_text


def _clean_date(v):
    """Ép `publication_date` về chuỗi (hoặc None) cho MỌI nguồn (29/09/2026).

    `RawRecord.publication_date` khai `Optional[str]` nhưng không có gì cưỡng chế lúc chạy: CORE trả
    `yearPublished` là SỐ NGUYÊN khi thiếu `publishedDate` ⇒ `deduplication._same_version` cắt `[:4]`
    trên int và làm sập cả lượt quét (đo thật trên Cloud 29/09). Chặn ở đây vì mọi nguồn đều đi qua.
    """
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return str(int(v))
    s = str(v).strip()
    return s or None


def _chuoi_hoac_none(v):
    """Ép một trường VĂN BẢN của RawRecord về chuỗi (hoặc None) cho MỌI nguồn (29/09/2026).

    Cùng họ lỗi `publication_date` số nguyên của CORE: dataclass khai `Optional[str]` nhưng không cưỡng
    chế lúc chạy, trong khi bước sau gọi `.lower()`/`.strip()`/cắt chuỗi (vd `deduplication._key_for`
    gọi `.lower()` trên `journal_or_organization`). JSON nguồn hay trả DANH SÁCH (Crossref
    `container-title`), số (phiên bản), hoặc dict. Danh sách ⇒ nối bằng «; »; dict ⇒ None (không đoán
    khoá nào là giá trị); số ⇒ `str()`; rỗng ⇒ None.
    """
    if v is None or isinstance(v, (bool, dict)):
        return None
    if isinstance(v, (list, tuple)):
        phan = [p for p in (_chuoi_hoac_none(x) for x in v) if p]
        return "; ".join(phan) or None
    s = str(v).strip()
    return s or None


def _danh_sach_chuoi(v):
    """Ép trường DANH SÁCH (`keywords`, `mesh_terms`) về list[str] không phần tử rỗng/None."""
    if v is None or isinstance(v, (bool, dict)):
        return []
    if isinstance(v, str):
        return [v.strip()] if v.strip() else []
    if isinstance(v, (list, tuple, set)):
        return [s for s in (_chuoi_hoac_none(x) for x in v) if s]
    s = _chuoi_hoac_none(v)
    return [s] if s else []


def _clean_doi(doi):
    if not doi:
        return None
    doi = str(doi).strip().lower()
    doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
    return doi or None


def _clean_id(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def normalize(record: RawRecord) -> Dict:
    """Map RawRecord -> dict khớp các cột EvidenceItem (chưa có scoring).

    Tín hiệu rút bài (vá 26/09/2026, synthesis #4): `raw` KHÔNG được giữ lại sau bước này, nên
    cờ raw["rut_bai"] do nguồn gắn (PubMed/Europe PMC, khớp đúng token) phải được chép NGAY ở
    đây. 'retracted' ⇒ `reason_for_exclusion` (cột đã lưu DB ⇒ reliability_tier D ⇒ không
    «đáng tin», bridge EBM_MASTER tự loại) + khoá tạm `_rut_bai`/`_ly_do_rut_bai` cho classify.
    'eoc' ⇒ chỉ `_rut_bai` (classify chặn actionable). Vắng cờ KHÔNG có nghĩa «chưa bị rút»."""
    raw = getattr(record, "raw", None) or {}
    item = _normalize_co_ban(record, raw)
    rut_bai = raw.get("rut_bai")
    if rut_bai == "retracted":
        ly_do = ly_do_rut_bai(str(raw.get("rut_bai_nguon") or record.source or ""),
                              raw.get("rut_bai_thong_bao"))
        item["_rut_bai"] = "retracted"
        item["_ly_do_rut_bai"] = ly_do
        item["reason_for_exclusion"] = ly_do
    elif rut_bai == "eoc":
        item["_rut_bai"] = "eoc"
    return item


def lan_co_rut_bai_trong_nhom(items: List[Dict], links: List[Tuple[int, int, str]]) -> int:
    """Một thành viên của nhóm trùng bị rút ⇒ bản CHÍNH cũng bị loại (vd bản Europe PMC/Crossref
    không mang cờ, bản PubMed trùng mang «Retracted Publication»). EoC lan tương tự nếu bản chính
    chưa có tín hiệu nào. Không vứt bản ghi. Trả số bản chính được gắn cờ. (vá 26/09/2026, #4)"""
    so = 0
    for vi_tri_chinh, vi_tri_trung, _ly_do in links:
        chinh, trung = items[vi_tri_chinh], items[vi_tri_trung]
        if trung.get("_rut_bai") == "retracted" and chinh.get("_rut_bai") != "retracted":
            ly_do = (trung.get("_ly_do_rut_bai") or ly_do_rut_bai(str(trung.get("source") or "")))
            ly_do = f"{ly_do} [qua bản trùng nguồn {trung.get('source')}]"
            chinh["_rut_bai"] = "retracted"
            chinh["_ly_do_rut_bai"] = ly_do
            chinh["reason_for_exclusion"] = ly_do
            so += 1
        elif trung.get("_rut_bai") == "eoc" and not chinh.get("_rut_bai"):
            chinh["_rut_bai"] = "eoc"
            so += 1
    return so


def _normalize_co_ban(record: RawRecord, raw: Dict) -> Dict:
    c = _chuoi_hoac_none
    return {
        "source": record.source,
        "source_type": c(record.source_type) or "article",
        "title": clean_text(c(record.title), structured=False) or "",
        "authors": c(record.authors),
        "journal_or_organization": c(record.journal_or_organization),
        "publication_date": _clean_date(record.publication_date),
        "update_date": None,
        "doi": _clean_doi(c(record.doi)),
        "pmid": _clean_id(c(record.pmid)),
        "pmcid": _clean_id(c(record.pmcid)),
        "nct_id": _clean_id(c(record.nct_id)),
        "url": c(record.url),
        "abstract": clean_text(c(record.abstract), structured=True),
        "document_type": c(record.document_type),
        "study_type": c(record.study_type),
        "clinical_area": c(record.clinical_area),
        "keywords": _danh_sach_chuoi(record.keywords),
        "mesh_terms": _danh_sach_chuoi(record.mesh_terms),
        "guideline_version": c(record.guideline_version),
        "safety_signal": clean_text(c(record.safety_signal), structured=False),
        "official_grade": c(record.official_grade),
        "ingest_query": record.ingest_query,
        "api_endpoint": record.api_endpoint,
        # Truy vết mock: cờ raw["_mock"] (do _fixtures gắn) -> cột is_mock.
        "is_mock": bool(raw.get("_mock", False)),
    }


def normalized_title_key(title: str) -> str:
    """Chuẩn hóa tiêu đề cho so khớp trùng (lowercase, bỏ ký tự thừa)."""
    t = (title or "").lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t
