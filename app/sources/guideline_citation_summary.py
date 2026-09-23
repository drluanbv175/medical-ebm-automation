"""Trích dẫn + tóm tắt DỰ PHÒNG cho guideline KHÔNG đọc được toàn văn — thêm
23/09/2026 theo yêu cầu bác sĩ, ban đầu cho BTS/Thorax (Cloudflare chặn,
`bts_guidelines.py`) và NICE (giấy phép AI trả phí, `pmc_guideline_fulltext.py`
không phủ) — nhưng viết GENERIC nên dùng được cho BẤT KỲ DOI/PMID nào mà mọi
connector toàn văn (GOLD/GINA/BTS/PMC/Wiley TDM/Wiley MCP) đều thất bại.

⚠️ RANH GIỚI PHẢI HIỂU ĐÚNG, KHÔNG ĐƯỢC NHẦM LẪN: module này trả về **ABSTRACT** —
đoạn tóm tắt do CHÍNH tác giả/nhà xuất bản viết và nộp cho Crossref/Europe PMC khi
công bố bài — KHÔNG PHẢI "tôi tự đọc toàn văn rồi tóm tắt lại", và KHÔNG PHẢI toàn
văn. Một abstract thường 150-350 từ, đủ để biết bài nói về CÁI GÌ và KẾT LUẬN
CHUNG, nhưng KHÔNG đủ để trích số liệu/ngưỡng/liều cụ thể — những thứ đó chỉ có
trong toàn văn. Mọi kết quả trả về đều tự mang `ghi_chu` nói rõ ranh giới này,
đúng nguyên tắc "không tự gán mức/không giả vờ đã đọc đủ" của toàn bộ dự án.

Hai tầng, theo thứ tự (không phải thi đua tốc độ — Europe PMC trước vì hồ sơ đủ cả
DOI+PMID+abstract trong MỘT bản ghi, ít phải ghép nguồn hơn):
  1. Europe PMC — tra CHÍNH XÁC theo DOI hoặc PMID (không phải tìm mờ theo từ khóa),
     dùng `EuropePMCClient.search()` đã có sẵn + đã qua kiểm thử.
  2. Crossref — tra TRỰC TIẾP `GET /works/{doi}` (khác hẳn `CrossrefClient.search()`
     hiện có, vốn là tìm mờ theo `query=`) — chỉ dùng khi Europe PMC không có bản
     ghi hoặc có bản ghi nhưng thiếu abstract.

KHÔNG bịa DOI/PMID — người gọi phải tự có định danh trước (từ Crossref title lane,
PubMed, hoặc bác sĩ cung cấp)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote

from app.sources.base import RawRecord
from app.sources.europepmc import EuropePMCClient
from app.sources.guideline_lanes import sach_van_ban
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

_CROSSREF_WORKS = "https://api.crossref.org/works/"

_GHI_CHU_CO_TOM_TAT = (
    "Đây là TÓM TẮT (abstract) do CHÍNH tác giả/nhà xuất bản viết, KHÔNG PHẢI toàn "
    "văn — không có số liệu/ngưỡng/liều cụ thể, chỉ có nội dung tổng quát và kết "
    "luận chung. Cần bác sĩ kiểm chứng; muốn chi tiết đầy đủ phải tự đọc toàn văn."
)
_GHI_CHU_KHONG_CO_TOM_TAT = (
    "Có trích dẫn thật (đã xác minh qua Europe PMC/Crossref) nhưng KHÔNG có abstract "
    "công khai trong dữ liệu hai nguồn này — không thể tóm tắt nội dung, chỉ có "
    "thông tin định danh (tác giả/tạp chí/năm). Cần bác sĩ tự đọc toàn văn."
)


@dataclass
class KetQuaTrichDanTomTat:
    """Kết quả trích dẫn + tóm tắt dự phòng. `thanh_cong=True` chỉ nghĩa là ĐÃ XÁC
    MINH bài có thật (qua Europe PMC/Crossref) — KHÔNG đảm bảo có `tom_tat`; kiểm
    `tom_tat is not None` riêng trước khi dùng."""

    thanh_cong: bool
    doi: Optional[str] = None
    pmid: Optional[str] = None
    tieu_de: Optional[str] = None
    tac_gia: Optional[str] = None
    tap_chi_hoac_to_chuc: Optional[str] = None
    nam: Optional[str] = None
    trich_dan: Optional[str] = None
    tom_tat: Optional[str] = None
    nguon_tom_tat: Optional[str] = None  # "europepmc" | "crossref" | None
    ghi_chu: str = ""


def _dinh_dang_trich_dan(ban_ghi: RawRecord) -> str:
    """Trích dẫn kiểu Vancouver RÚT GỌN — chỉ ghép trường THẬT SỰ có, không bịa
    thêm volume/issue/trang (hai nguồn ở đây không luôn cung cấp đủ)."""
    phan: list[str] = []
    if ban_ghi.authors:
        phan.append(ban_ghi.authors.rstrip(".") + ".")
    if ban_ghi.title:
        phan.append(ban_ghi.title.rstrip(".") + ".")
    if ban_ghi.journal_or_organization:
        phan.append(ban_ghi.journal_or_organization.rstrip(".") + ".")
    if ban_ghi.publication_date:
        phan.append(f"{ban_ghi.publication_date}.")
    dinh_danh = []
    if ban_ghi.doi:
        dinh_danh.append(f"doi:{ban_ghi.doi}")
    if ban_ghi.pmid:
        dinh_danh.append(f"PMID:{ban_ghi.pmid}")
    if dinh_danh:
        phan.append(" ".join(dinh_danh))
    return " ".join(phan) if phan else "[thiếu metadata để ghép trích dẫn]"


def _tra_europepmc(doi: Optional[str], pmid: Optional[str]) -> Optional[RawRecord]:
    if pmid:
        truy_van = f"EXT_ID:{pmid} AND SRC:MED"
    elif doi:
        truy_van = f'DOI:"{doi}"'
    else:
        return None
    try:
        ket_qua = EuropePMCClient().search(truy_van, max_results=1)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[guideline_citation_summary] Europe PMC lỗi (doi=%s pmid=%s): %s",
                        doi, pmid, exc)
        return None
    return ket_qua[0] if ket_qua else None


def _tra_crossref_truc_tiep(doi: str) -> Optional[RawRecord]:
    """`GET /works/{doi}` — tra CHÍNH XÁC một DOI đã biết, KHÁC `CrossrefClient.
    search()` (tìm mờ theo `query=`, có thể lệch bài khi tiêu đề trùng lặp)."""
    try:
        data = HttpClient().get_json(_CROSSREF_WORKS + quote(doi, safe=""))
    except Exception as exc:  # noqa: BLE001
        logger.warning("[guideline_citation_summary] Crossref /works/%s lỗi: %s", doi, exc)
        return None
    it = (data or {}).get("message")
    if not isinstance(it, dict):
        return None
    title = (it.get("title") or [""])[0]
    authors = ", ".join(
        f"{a.get('family', '')} {a.get('given', '')}".strip()
        for a in it.get("author", []) or []
    ).strip()
    issued = (it.get("issued", {}) or {}).get("date-parts", [[None]])[0]
    year = str(issued[0]) if issued and issued[0] else None
    journal = (it.get("container-title") or [None])[0]
    abstract = it.get("abstract")
    return RawRecord(
        source="crossref", title=title, authors=authors or None,
        journal_or_organization=journal, publication_date=year,
        doi=it.get("DOI") or doi, abstract=abstract,
    )


def lay_trich_dan_tom_tat(
    doi: Optional[str] = None, pmid: Optional[str] = None
) -> KetQuaTrichDanTomTat:
    """Trả trích dẫn + tóm tắt (nếu có abstract) cho MỘT bài đã biết DOI/PMID —
    dùng khi connector toàn văn (GOLD/GINA/BTS/PMC/Wiley) đã thử và thất bại. Cần
    ÍT NHẤT một trong hai định danh; không tự tìm/đoán DOI/PMID."""
    doi = (doi or "").strip() or None
    pmid = (pmid or "").strip() or None
    if not doi and not pmid:
        return KetQuaTrichDanTomTat(
            thanh_cong=False,
            ghi_chu="Cần ít nhất DOI hoặc PMID đã biết — module này không tự tìm/đoán định danh.",
        )

    ban_ghi = _tra_europepmc(doi, pmid)
    nguon_tom_tat: Optional[str] = "europepmc" if ban_ghi and ban_ghi.abstract else None

    if doi and (ban_ghi is None or not ban_ghi.abstract):
        cr = _tra_crossref_truc_tiep(doi)
        if cr:
            if ban_ghi is None:
                ban_ghi = cr
                nguon_tom_tat = "crossref" if cr.abstract else None
            elif not ban_ghi.abstract and cr.abstract:
                ban_ghi.abstract = cr.abstract
                nguon_tom_tat = "crossref"

    if ban_ghi is None:
        return KetQuaTrichDanTomTat(
            thanh_cong=False, doi=doi, pmid=pmid,
            ghi_chu=(
                "Không tra được qua CẢ Europe PMC lẫn Crossref — DOI/PMID có thể sai, "
                "hoặc lỗi mạng tạm thời. Không bịa trích dẫn."
            ),
        )

    tom_tat = sach_van_ban(ban_ghi.abstract) if ban_ghi.abstract else None
    return KetQuaTrichDanTomTat(
        thanh_cong=True,
        doi=ban_ghi.doi or doi,
        pmid=ban_ghi.pmid or pmid,
        tieu_de=ban_ghi.title or None,
        tac_gia=ban_ghi.authors,
        tap_chi_hoac_to_chuc=ban_ghi.journal_or_organization,
        nam=ban_ghi.publication_date,
        trich_dan=_dinh_dang_trich_dan(ban_ghi),
        tom_tat=tom_tat or None,
        nguon_tom_tat=nguon_tom_tat if tom_tat else None,
        ghi_chu=_GHI_CHU_CO_TOM_TAT if tom_tat else _GHI_CHU_KHONG_CO_TOM_TAT,
    )
