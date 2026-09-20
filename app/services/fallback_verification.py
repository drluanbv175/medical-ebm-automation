"""Xác minh ĐỘC LẬP phát hiện của tầng dự phòng (Consensus / SerpApi Scholar) bằng cơ quan đăng ký.

Nguyên tắc: phát hiện của tầng dự phòng chỉ là GỢI Ý. Nó chỉ được GIỮ khi Crossref hoặc PubMed — cơ quan đăng ký
độc lập — xác nhận đó là một bài có thật; bản ghi trả về chính là bản ghi CỦA CƠ QUAN ĐĂNG KÝ (source = crossref
hoặc pubmed), gắn `raw["phat_hien_boi"]` (tầng nào tìm ra) và `raw["xac_minh"]` (bằng chứng xác minh). Mọi thứ
khác bị bỏ và được ĐẾM (không bao giờ đoán). Hàm `xac_minh_ban_ghi` không phụ thuộc nguồn phát hiện.

QUY TẮC (STRICT, fail-closed) — chỉ giữ khi:
  (a) hit có DOI và bản ghi Crossref CỦA DOI ĐÓ tồn tại và tiêu đề khớp sau chuẩn hoá (độ giống >= 0,9); hoặc
  (b) không có DOI (và không có PMID): có ĐÚNG MỘT ứng viên Crossref `query.bibliographic` rõ ràng tốt nhất với
      độ giống tiêu đề >= 0,9 VÀ (khi biết năm của hit) |lệch năm| <= 1 VÀ (khi biết tác giả) họ của tác giả
      đầu tiên xuất hiện trong danh sách tác giả Crossref; hoặc
  (c) không có DOI nhưng có PMID: PubMed xác nhận PMID đó tồn tại.
Các trường hợp khác — không khớp, mơ hồ, tiêu đề gần trùng nhau, tiêu đề là thông báo đính chính/rút bài, lỗi
mạng — KHÔNG được giữ: "khong_khop"/"mo_ho" khác "loi_xac_minh" (lỗi mạng/parse KHÔNG BAO GIỜ thành khớp).
Tối đa 2 lời gọi cơ quan đăng ký cho mỗi hit (1 tra cứu + 1 kiểm rút bài; riêng nguyên thủy kiểm rút bài có sẵn
của Crossref còn đọc thêm tiêu đề thông báo khi PHÁT HIỆN rút bài — hiếm).

CỔNG RÚT BÀI / THÔNG BÁO BIÊN TẬP cho mọi hit kết thúc bằng một DOI đã xác nhận: từ chối ("bi_rut_bai") khi nguyên
thủy kiểm rút bài của Crossref (`CrossrefRetraction`) HOẶC bản ghi PUBLIC `api.scite.ai/papers/<doi>` báo đã rút
(retracted=True, hoặc mục editorialNotices có type/title nhắc retract/withdraw). Cấu trúc thông báo không phân
loại được thì giữ và gắn cờ raw["co"] += "thong_bao_bien_tap_chua_phan_loai" (thận trọng); đính chính /
expression-of-concern thì giữ và gắn "co_thong_bao_bien_tap".

SCITE chỉ là lớp XÁC MINH THÊM, KHÔNG phải tầng khám phá (Search của Scite cần khoá Pro và giấy phép riêng cho
dùng thương mại/nghiên cứu — xem app/sources/scite_public.py). Chỉ dùng endpoint công khai papers/tallies (không
khoá, không Authorization). Tally chỉ được GHI vào raw["scite"] (kèm cờ "nhieu_trich_dan_phan_bac" khi phản bác >= 3
và > ủng hộ) — không bao giờ đổi điểm/tier/phân loại/lọc và không bao giờ quyết định giữ hay bỏ. Scite không
liên lạc được (timeout/404/429/5xx/JSON hỏng) thì bản ghi được xét chỉ bằng các kiểm tra còn lại và
raw["scite"] = {"da_kiem": False, "ly_do": ...}: mã KHÔNG BAO GIỜ khẳng định một lần kiểm Scite chưa xảy ra.
ĐIỂM MỞ RỘNG: nếu sau này bác sĩ có giấy phép + khoá Scite Search, có thể thêm một tầng khám phá mới vào
`get_fallback_sources()`; bản ghi của nó vẫn đi qua đúng hàm xác minh này. Hiện KHÔNG xây tầng đó.

`study_type` của bản ghi đăng ký KHÔNG BAO GIỜ suy từ tiêu đề: chỉ từ `type`/`subtype`/tên tạp chí của cơ quan
đăng ký. Nhãn `study_type` của Consensus (raw["consensus_study_type"]) chỉ có thể HẠ BẬC bản ghi, không bao giờ
nâng. `takeaway` của Consensus không phải abstract và không phải bằng chứng — chỉ ở raw["phat_hien"].

GIAO DIỆN CLIENT (tiêm được để test): xem `CrossrefXacMinh` (lay_theo_doi / tim_theo_thu_muc / kiem_rut_bai),
`pubmed_client` cần `check_citations(pmids)` (ưu tiên) hoặc `fetch_metadata(pmids)`, `scite_client` cần
`lay_bai(doi)` và `lay_tally(doi)` (trả None khi 404; ném lỗi có thuộc tính `loai` khi lỗi khác).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from app.config import settings
from app.services.normalization import normalized_title_key
from app.sources.base import RawRecord
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

KET_QUA_XAC_MINH_DUOC = "xac_minh_duoc"
KET_QUA_KHONG_KHOP = "khong_khop"
KET_QUA_MO_HO = "mo_ho"
KET_QUA_LOI = "loi_xac_minh"
KET_QUA_RUT_BAI = "bi_rut_bai"

NGUONG_GIONG_TIEU_DE = 0.9
_WORKS = "https://api.crossref.org/works"
_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

_DOI_HOP_LE_RE = re.compile(r"^10\.\d{4,9}/\S+$")
_NAM_RE = re.compile(r"(?<!\d)(1[5-9]\d{2}|20\d{2})(?!\d)")
# Tiêu đề của chính một THÔNG BÁO biên tập (không phải bài nghiên cứu): đính chính, đính chính nhà xuất bản, rút
# bài, expression of concern, thu hồi. Neo ở ĐẦU tiêu đề hoặc sau tiền tố quen thuộc để không bắt nhầm bài nghiên
# cứu có chữ "correction" ở giữa ("Bias correction methods for ...").
_TIEU_DE_THONG_BAO_RE = re.compile(
    r"^\s*(?:\[?(?:publisher|author)\s+)?"
    r"(?:erratum|errata|corrigendum|corrigenda|correction|retraction|retracted|withdrawal|withdrawn|"
    r"expression\s+of\s+concern|editorial\s+expression\s+of\s+concern|notice\s+of\s+retraction|"
    r"addendum|publisher\s+correction|author\s+correction)\b",
    re.IGNORECASE)
_TU_KHOA_RUT = ("retract", "withdraw", "withdrew", "removal")
_TU_KHOA_DINH_CHINH = ("correct", "erratum", "errata", "corrigend", "concern", "addend", "clarification")
_KHOA_LOAI_THONG_BAO = ("type", "title", "status", "label", "name", "description", "category", "kind",
                        "noticetype", "notice_type", "subtype")

# Nhãn study_type của Consensus -> nhãn nội bộ CHỈ để HẠ BẬC (xem `_ap_dung_ha_bac_consensus`).
_NHAN_CONSENSUS_SANG_NOI_BO = {
    "case report": "case_series", "case study": "case_series",
    "commentary or perspective": "editorial",
    "literature review": "narrative_review",
    "non-rct in vitro": "animal_invitro", "bench experiment": "animal_invitro",
    "cohort study": "cohort", "case-control study": "cohort", "cross-sectional study": "cohort",
    "longitudinal / panel data study": "cohort", "non-rct observational study": "cohort",
    "non-randomized experimental study": "cohort", "non-rct experimental": "cohort",
}
_THIET_KE_LOAI_TRU_MAC_DINH = frozenset({"preprint", "animal_invitro", "editorial", "narrative_review",
                                         "expert_opinion"})


@dataclass(frozen=True)
class KetQuaXacMinh:
    """Kết quả xác minh một hit. `ban_ghi` CHỈ có khi ket_qua == "xac_minh_duoc" (bản ghi của cơ quan đăng ký).

    ket_qua: "xac_minh_duoc" | "khong_khop" | "mo_ho" | "loi_xac_minh" | "bi_rut_bai".
    ly_do: giải thích tiếng Việt cho nhật ký (không tham gia so sánh bằng).
    """

    ban_ghi: Optional[RawRecord]
    ket_qua: str
    ly_do: str = field(default="", compare=False)


# ============================================================================ tiện ích chuẩn hoá

def _lam_sach_doi(doi: object) -> Optional[str]:
    d = str(doi or "").strip().lower()
    for tien_to in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/", "doi:"):
        if d.startswith(tien_to):
            d = d[len(tien_to):]
    d = d.strip().rstrip(".,;)")
    return d if _DOI_HOP_LE_RE.match(d) else None


def _lam_sach_pmid(pmid: object) -> Optional[str]:
    p = str(pmid or "").strip()
    return p if re.fullmatch(r"[1-9]\d{0,8}", p) else None


def _nam_tu_chuoi(x: object) -> Optional[int]:
    m = _NAM_RE.search(str(x or ""))
    return int(m.group(1)) if m else None


def _bo_dau(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


# ── Token PHÂN BIỆT giữa hai bài có tiêu đề gần giống nhau (thêm 20/09/2026) ────────────────────────────────
# Tỷ lệ ký tự >= 0,9 KHÔNG đủ để kết luận "cùng một bài": "…52-week results" và "…26-week results", "…Part II" và
# "…Part I", "…in adults…" và "…in children…" đều vượt ngưỡng nhưng là bài KHÁC. Sau tỷ lệ ký tự phải đối chiếu thêm
# (a) tập các CHUỖI CHỮ SỐ trong tiêu đề (kể cả số La Mã đứng sau "part/type/phase…": "Type II" == "type 2") và
# (b) tập NHÓM QUẦN THỂ (người lớn, trẻ em, người cao tuổi, nữ, nam, thai kỳ…). Khác nhau => coi là bài khác.
_LA_MA = {"i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5", "vi": "6", "vii": "7", "viii": "8", "ix": "9",
          "x": "10"}
_TU_DANH_SO = frozenset({"part", "type", "phase", "stage", "grade", "class", "study", "trial", "volume", "vol",
                         "chapter", "section", "group", "level", "cohort", "cycle", "step", "trimester"})
_NHOM_QUAN_THE = {
    "adult": ("adult", "adults"),
    "child": ("child", "children", "childhood", "pediatric", "paediatric", "pediatrics", "paediatrics", "kid",
              "kids", "schoolchildren"),
    "adolescent": ("adolescent", "adolescents", "teen", "teens", "teenager", "teenagers", "youth"),
    "infant": ("infant", "infants", "neonate", "neonates", "neonatal", "newborn", "newborns", "preterm",
               "premature"),
    "elderly": ("elderly", "older", "aged", "geriatric", "senior", "seniors", "frail"),
    "female": ("women", "woman", "female", "females", "girls", "girl"),
    "male": ("men", "man", "male", "males", "boys", "boy"),
    "pregnancy": ("pregnant", "pregnancy", "gestational", "maternal", "antenatal", "postpartum", "perinatal"),
}
_TU_QUAN_THE = {tu: nhom for nhom, ds in _NHOM_QUAN_THE.items() for tu in ds}


def _dac_trung_phan_biet(khoa: str) -> Tuple[Set[str], Set[str]]:
    """Từ chuỗi đã chuẩn hoá (chữ thường, chỉ a-z0-9 và khoảng trắng) trả (tập chuỗi chữ số, tập nhóm quần thể)."""
    so: Set[str] = set(re.findall(r"\d+", khoa))
    qt: Set[str] = set()
    toks = khoa.split()
    for i, t in enumerate(toks):
        if t in _LA_MA and i > 0 and toks[i - 1] in _TU_DANH_SO:
            so.add(_LA_MA[t])
        elif t in _TU_QUAN_THE:
            qt.add(_TU_QUAN_THE[t])
    return so, qt


def _khac_dac_trung(ka: str, kb: str, hit_bi_cat: bool) -> bool:
    """Hai tiêu đề (đã chuẩn hoá) khác nhau ở token phân biệt? Hit bị cắt bằng "…" chỉ đòi token của hit là TẬP CON."""
    so_a, qt_a = _dac_trung_phan_biet(ka)
    so_b, qt_b = _dac_trung_phan_biet(kb)
    if hit_bi_cat:
        return not (so_a <= so_b and qt_a <= qt_b)
    return so_a != so_b or qt_a != qt_b


def _khoa_ho(text: str) -> str:
    """Chữ thường, bỏ dấu, chỉ giữ chữ cái — để so họ tác giả."""
    return re.sub(r"[^a-z]", "", _bo_dau(str(text or "")).lower())


def _ho_tac_gia_dau_cua_hit(tac_gia: object) -> Set[str]:
    """Các từ (đã chuẩn hoá) trong đoạn tác giả ĐẦU của chuỗi tác giả — họ nằm trong đó dù viết "Ho Ten" hay
    "Ten Ho"/"Ho, Ten". Chuỗi không có tác giả thì trả tập rỗng (= tác giả chưa biết)."""
    s = str(tac_gia or "").strip()
    if not s:
        return set()
    doan_dau = re.split(r"[;,]| and | & ", s, maxsplit=1)[0]
    tu = {_khoa_ho(t) for t in re.split(r"[\s.\-]+", doan_dau)}
    return {t for t in tu if len(t) >= 2}


def _ho_tac_gia_crossref(msg: dict) -> Set[str]:
    ho: Set[str] = set()
    for a in (msg.get("author") or []):
        if isinstance(a, dict):
            k = _khoa_ho(a.get("family") or a.get("name") or "")
            if k:
                ho.add(k)
    return ho


def _tieu_de_crossref(msg: dict) -> List[str]:
    """Các biến thể tiêu đề của bản ghi Crossref: tiêu đề, và tiêu đề + phụ đề."""
    tieu = msg.get("title")
    tieu = tieu[0] if isinstance(tieu, list) and tieu else (tieu if isinstance(tieu, str) else "")
    tieu = str(tieu or "").strip()
    if not tieu:
        return []
    phu = msg.get("subtitle")
    phu = phu[0] if isinstance(phu, list) and phu else (phu if isinstance(phu, str) else "")
    phu = str(phu or "").strip()
    return [tieu, f"{tieu} {phu}"] if phu else [tieu]


def _nam_crossref(msg: dict) -> Optional[int]:
    for khoa in ("issued", "published-print", "published-online", "published"):
        v = msg.get(khoa)
        if isinstance(v, dict):
            try:
                y = v.get("date-parts", [[None]])[0][0]
                if y:
                    return int(y)
            except (IndexError, TypeError, ValueError):
                continue
    return None


def _do_giong_tieu_de(tieu_de_hit: str, tieu_de_dang_ky: str, hit_bi_cat: bool = False) -> float:
    """Độ giống 0..1 sau chuẩn hoá (chữ thường, bỏ ký tự thừa). Hit bị cắt bằng "…" (Scholar hay cắt) chỉ được
    coi là khớp khi nó là TIỀN TỐ của tiêu đề đăng ký và đủ dài (>= 30 ký tự chuẩn hoá) — tránh khớp nhầm."""
    # _bo_dau (NFKD, bỏ dấu phụ) TRƯỚC khi chuẩn hoá: cùng một tiêu đề ở dạng NFC/NFD, có/không dấu phụ, gạch nối
    # không ngắt... phải cho cùng một khoá (normalized_title_key chỉ giữ a-z0-9 nên nếu không bỏ dấu, chữ có dấu bị xoá
    # ở dạng NFC nhưng còn lại chữ gốc ở dạng NFD -> hai khoá lệch nhau).
    ka = normalized_title_key(_bo_dau(str(tieu_de_hit or "")))
    kb = normalized_title_key(_bo_dau(str(tieu_de_dang_ky or "")))
    if not ka or not kb:
        return 0.0
    if ka == kb:
        return 1.0
    if hit_bi_cat and len(ka) >= 30 and kb.startswith(ka):
        ty_le = 1.0
    else:
        ty_le = SequenceMatcher(None, ka, kb).ratio()
    if ty_le >= NGUONG_GIONG_TIEU_DE and _khac_dac_trung(ka, kb, hit_bi_cat):
        return min(ty_le, 0.5)   # giống về ký tự nhưng khác số/quần thể: bài KHÁC, không được vượt ngưỡng
    return ty_le


def _la_tieu_de_thong_bao(tieu_de: str) -> bool:
    return bool(_TIEU_DE_THONG_BAO_RE.match(tieu_de or ""))


# Nhà xuất bản gắn "RETRACTED:"/"WITHDRAWN:" vào TIÊU ĐỀ CỦA CHÍNH BÀI bị rút — khác thông báo rút bài (có DOI riêng,
# tiêu đề "Retraction Note: ..."). Đo thật 20/09/2026: DOI gốc của Wakefield (Lancet 1998) có tiêu đề "RETRACTED: ...",
# bị `_la_tieu_de_thong_bao` xếp thành "không khớp" — vẫn bị loại (an toàn) nhưng sai nhãn: đáng phải đếm là BỊ RÚT.
_TIEU_DE_BAI_BI_RUT_RE = re.compile(r"^\s*\[?\s*(?:retracted|withdrawn)\s*[:\]\-\u2013\u2014]\s*", re.IGNORECASE)


def _la_tieu_de_bai_bi_rut(tieu_de: str) -> bool:
    return bool(_TIEU_DE_BAI_BI_RUT_RE.match(tieu_de or ""))


def _bo_tien_to_bi_rut(tieu_de: str) -> str:
    return _TIEU_DE_BAI_BI_RUT_RE.sub("", tieu_de or "", count=1).strip()


def _hit_bi_cat(rec: RawRecord) -> bool:
    co = (rec.raw or {}).get("co") if isinstance(rec.raw, dict) else None
    return isinstance(co, list) and "title_truncated" in co


def _ngay_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _them_co(raw: dict, co: str) -> None:
    ds = raw.setdefault("co", [])
    if co not in ds:
        ds.append(co)


def _sach_phat_hien(raw_hit: Any) -> dict:
    """Bản sao nông của raw của hit để lưu vết: bỏ khoá nhạy cảm, cắt chuỗi dài, bỏ cấu trúc lồng quá lớn."""
    if not isinstance(raw_hit, dict):
        return {}
    ra: dict = {}
    for k, v in raw_hit.items():
        ten = str(k).lower()
        if any(x in ten for x in ("key", "token", "secret", "password", "authorization")):
            continue
        if isinstance(v, str):
            ra[k] = v[:2000]
        elif isinstance(v, (int, float, bool)) or v is None:
            ra[k] = v
        elif isinstance(v, list) and len(v) <= 20 and all(isinstance(x, (str, int, float, bool)) for x in v):
            ra[k] = [x[:300] if isinstance(x, str) else x for x in v]
    return ra


# ============================================================================ bản ghi đăng ký

def _study_type_dang_ky(msg: dict, hit: RawRecord) -> Optional[str]:
    """study_type từ tín hiệu CỦA CƠ QUAN ĐĂNG KÝ (type/subtype/tên tạp chí) — KHÔNG dùng tiêu đề."""
    from app.sources.classify_meta import infer_study_type  # noqa: PLC0415

    tap_chi = (msg.get("container-title") or [None])[0] if isinstance(msg.get("container-title"), list) else None
    st = infer_study_type("", msg.get("type"), tap_chi)
    if str(msg.get("subtype") or "").lower() == "preprint":
        st = "preprint"
    if hit.study_type == "preprint":
        st = "preprint"
    return st


def _ap_dung_ha_bac_consensus(study_type: Optional[str], hit: RawRecord) -> Tuple[Optional[str], Optional[str]]:
    """Nhãn study_type của Consensus CHỈ được HẠ BẬC. Trả (study_type mới, mô tả thay đổi hoặc None).

    Có study_type nội bộ: chỉ đổi khi nhãn Consensus (quy về nhãn nội bộ) có điểm thiết kế THẤP hơn. Chưa có
    (None): chỉ gắn khi nhãn thuộc nhóm bị loại (hạng D) — gắn nhãn yếu khác sẽ NÂNG điểm nền từ 0 lên 15-55.
    """
    raw = hit.raw if isinstance(hit.raw, dict) else {}
    nhan = str(raw.get("consensus_study_type") or "").strip().lower()
    if not nhan:
        return study_type, None
    noi_bo = "animal_invitro" if nhan.startswith("animal") else _NHAN_CONSENSUS_SANG_NOI_BO.get(nhan)
    if not noi_bo:
        return study_type, None
    try:
        from app.scoring.evidence_quality import DESIGN_BASE  # noqa: PLC0415
        from app.scoring.reliability import EXCLUDED_DESIGNS  # noqa: PLC0415
    except ImportError:  # pragma: no cover
        DESIGN_BASE, EXCLUDED_DESIGNS = {}, _THIET_KE_LOAI_TRU_MAC_DINH
    if study_type is None:
        if noi_bo in EXCLUDED_DESIGNS:
            return noi_bo, f"consensus:{nhan}->{noi_bo} (None->loại)"
        return study_type, None
    if DESIGN_BASE.get(noi_bo, 0) < DESIGN_BASE.get(study_type, 0):
        return noi_bo, f"consensus:{nhan}->{noi_bo} (hạ từ {study_type})"
    return study_type, None


def _dung_ban_ghi_crossref(msg: dict, hit: RawRecord, phuong_phap: str, do_giong: float,
                           chi_tiet: dict) -> RawRecord:
    doi = str(msg.get("DOI") or "").strip().lower()
    tieu_de_ds = _tieu_de_crossref(msg)
    tap_chi = (msg.get("container-title") or [None])[0] if isinstance(msg.get("container-title"), list) else None
    tac_gia = ", ".join(
        f"{a.get('family', '')} {a.get('given', '')}".strip()
        for a in (msg.get("author") or [])[:5] if isinstance(a, dict)) or None
    nam = _nam_crossref(msg)
    study_type = _study_type_dang_ky(msg, hit)
    study_type, ha_bac = _ap_dung_ha_bac_consensus(study_type, hit)
    abstract = msg.get("abstract") if isinstance(msg.get("abstract"), str) and msg.get("abstract").strip() else None
    raw = {
        "phat_hien_boi": hit.source,
        "phat_hien": _sach_phat_hien(hit.raw),
        "xac_minh": {"phuong_phap": phuong_phap, "nguon_xac_minh": "crossref", "do_giong": round(do_giong, 4),
                     "doi_khop": doi or None, "pmid_khop": None, "ngay": _ngay_iso(), **chi_tiet},
        "co": [],
    }
    if ha_bac:
        raw["xac_minh"]["ha_bac_study_type"] = ha_bac
        _them_co(raw, "study_type_ha_bac_theo_consensus")
    return RawRecord(
        source="crossref", title=tieu_de_ds[0] if tieu_de_ds else hit.title,
        authors=tac_gia, journal_or_organization=tap_chi,
        publication_date=str(nam) if nam else None, doi=doi or None,
        abstract=abstract, document_type=msg.get("type") if isinstance(msg.get("type"), str) else None,
        study_type=study_type, clinical_area=hit.clinical_area,
        url=f"https://doi.org/{doi}" if doi else None,
        ingest_query=hit.ingest_query, api_endpoint=_WORKS, raw=raw,
    )


def _dung_ban_ghi_pubmed(pmid: str, meta: dict, hit: RawRecord, do_giong: Optional[float],
                         chi_tiet: dict) -> RawRecord:
    doi = _lam_sach_doi(meta.get("doi"))
    nam = _nam_tu_chuoi(meta.get("year"))
    study_type: Optional[str] = "preprint" if hit.study_type == "preprint" else None
    study_type, ha_bac = _ap_dung_ha_bac_consensus(study_type, hit)
    raw = {
        "phat_hien_boi": hit.source,
        "phat_hien": _sach_phat_hien(hit.raw),
        "xac_minh": {"phuong_phap": "pmid", "nguon_xac_minh": "pubmed",
                     "do_giong": None if do_giong is None else round(do_giong, 4),
                     "doi_khop": doi, "pmid_khop": pmid, "ngay": _ngay_iso(), **chi_tiet},
        "co": [],
    }
    if ha_bac:
        raw["xac_minh"]["ha_bac_study_type"] = ha_bac
        _them_co(raw, "study_type_ha_bac_theo_consensus")
    return RawRecord(
        source="pubmed", title=str(meta.get("title") or hit.title or "").strip(),
        authors=meta.get("authors"), journal_or_organization=meta.get("journal"),
        publication_date=str(nam) if nam else None, doi=doi, pmid=pmid,
        abstract=None, study_type=study_type, clinical_area=hit.clinical_area,
        url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        ingest_query=hit.ingest_query, api_endpoint=_EFETCH, raw=raw,
    )


# ============================================================================ client mặc định

class CrossrefXacMinh:
    """Cầu nối Crossref cho việc xác minh (tiêm được / thay bằng fake khi test).

    Giao diện: `lay_theo_doi(doi)` -> dict bản ghi hoặc None khi 404 (ném lỗi khác);
    `tim_theo_thu_muc(tieu_de, so_ket_qua=5)` -> list bản ghi ứng viên (query.bibliographic);
    `kiem_rut_bai(doi, thong_diep=None)` -> dict trạng thái của nguyên thủy `CrossrefRetraction` có sẵn
    (ok | retracted | expression_of_concern | unresolved | unknown_fetch_error). Nếu đã có bản ghi Crossref của
    DOI (`thong_diep`) thì dùng lại, KHÔNG gọi mạng lần nữa cho bản ghi chính.

    Tất cả GET đều `use_cache=False`: kết quả nuôi cổng rút bài, cache 24 giờ có thể che một đợt rút bài mới
    (cùng lý do các nơi kiểm rút bài khác tắt cache).
    """

    def __init__(self, *, http=None, mailto: Optional[str] = None, lop_rut_bai=None) -> None:
        if http is None:
            from app.utils.http import HttpClient  # noqa: PLC0415
            http = HttpClient()
        self.http = http
        self.mailto = settings.openalex_email if mailto is None else mailto
        self._lop_rut_bai = lop_rut_bai

    def _tham_so(self, them: Optional[dict] = None) -> dict:
        p = dict(them or {})
        if self.mailto:
            p["mailto"] = self.mailto
        return p

    def lay_theo_doi(self, doi: str) -> Optional[dict]:
        from urllib.parse import quote  # noqa: PLC0415

        import requests  # noqa: PLC0415

        try:
            data = self.http.get_json(f"{_WORKS}/{quote(doi, safe='')}", params=self._tham_so(), use_cache=False)
        except requests.HTTPError as exc:
            resp = getattr(exc, "response", None)
            if getattr(resp, "status_code", None) == 404:
                return None
            raise
        msg = data.get("message") if isinstance(data, dict) else None
        if not isinstance(msg, dict):
            raise ValueError("Crossref trả phản hồi không có 'message' dạng dict")
        return msg

    def tim_theo_thu_muc(self, tieu_de: str, so_ket_qua: int = 5) -> List[dict]:
        data = self.http.get_json(
            _WORKS, params=self._tham_so({"query.bibliographic": tieu_de[:300], "rows": so_ket_qua}),
            use_cache=False)
        msg = data.get("message") if isinstance(data, dict) else None
        items = msg.get("items") if isinstance(msg, dict) else None
        if not isinstance(items, list):
            raise ValueError("Crossref trả phản hồi tìm kiếm không có 'message.items' dạng list")
        return [it for it in items if isinstance(it, dict)]

    def kiem_rut_bai(self, doi: str, thong_diep: Optional[dict] = None) -> dict:
        from app.sources.crossref_retraction import CrossrefRetraction  # noqa: PLC0415

        lop = self._lop_rut_bai or CrossrefRetraction
        bo_kiem = lop(mailto=self.mailto or "")
        if thong_diep is not None:
            goc_lay = bo_kiem._lay

            def _lay_co_nho(d: str):
                return thong_diep if d == doi else goc_lay(d)

            bo_kiem._lay = _lay_co_nho   # dùng lại bản ghi đã tải; thông báo rút bài (nếu có) vẫn tải thật
        ra = bo_kiem.check([doi])
        return ra.get(doi) or {"status": "unknown_fetch_error", "reason": "nguyên thủy kiểm rút bài không trả kết quả"}


# ============================================================================ Scite

def _van_ban_thong_bao(muc: Any) -> str:
    """Gộp các trường loại/tiêu đề của một mục editorialNotices thành một chuỗi thường để dò từ khoá."""
    if isinstance(muc, str):
        return muc.lower()
    if isinstance(muc, dict):
        phan = [str(v) for k, v in muc.items() if str(k).lower() in _KHOA_LOAI_THONG_BAO and isinstance(v, (str, int))]
        if not phan:
            phan = [str(v) for v in muc.values() if isinstance(v, str)]
        return " ".join(phan).lower()
    return str(muc).lower() if muc is not None else ""


def _phan_loai_thong_bao(cac_muc: Any) -> str:
    """"rut" | "dinh_chinh" | "chua_phan_loai" | "khong_co" cho danh sách editorialNotices của Scite."""
    if not isinstance(cac_muc, list) or not cac_muc:
        return "khong_co"
    co_dinh_chinh = False
    co_khong_ro = False
    for muc in cac_muc:
        van_ban = _van_ban_thong_bao(muc)
        if any(t in van_ban for t in _TU_KHOA_RUT):
            return "rut"
        if any(t in van_ban for t in _TU_KHOA_DINH_CHINH):
            co_dinh_chinh = True
        else:
            co_khong_ro = True
    if co_khong_ro:
        return "chua_phan_loai"
    return "dinh_chinh" if co_dinh_chinh else "khong_co"


def _lop_scite(doi: str, scite_client: Any, raw: dict) -> Optional[str]:
    """Chạy lớp Scite cho DOI đã xác nhận. Ghi raw["scite"] / raw["co"]. Trả lý do từ chối nếu Scite báo đã rút.

    KHÔNG BAO GIỜ khẳng định một lần kiểm chưa xảy ra: mọi lỗi -> raw["scite"] = {"da_kiem": False, "ly_do": ...}.
    Tally chỉ được ghi lại, không quyết định giữ/bỏ."""
    ngay = _ngay_iso()
    if not getattr(settings, "enable_scite_verification", True):
        raw["scite"] = {"da_kiem": False, "ly_do": "tat_trong_cau_hinh", "nguon": "api.scite.ai", "ngay": ngay}
        return None
    if scite_client is None:
        raw["scite"] = {"da_kiem": False, "ly_do": "khong_co_client_scite", "nguon": "api.scite.ai", "ngay": ngay}
        return None
    try:
        bai = scite_client.lay_bai(doi)
    except Exception as exc:  # noqa: BLE001
        raw["scite"] = {"da_kiem": False, "ly_do": f"papers:{getattr(exc, 'loai', None) or type(exc).__name__}",
                        "nguon": "api.scite.ai", "ngay": ngay}
        return None
    if bai is None:
        raw["scite"] = {"da_kiem": False, "ly_do": "scite_khong_co_doi_nay(404)", "nguon": "api.scite.ai",
                        "ngay": ngay}
        return None
    if not isinstance(bai, dict):
        raw["scite"] = {"da_kiem": False, "ly_do": "papers:phan_hoi_khong_hop_le", "nguon": "api.scite.ai",
                        "ngay": ngay}
        return None

    thong_bao = bai.get("editorial_notices")
    if thong_bao is None:
        thong_bao = bai.get("editorialNotices")
    phan_loai = _phan_loai_thong_bao(thong_bao)
    scite: Dict[str, Any] = {"da_kiem": True, "nguon": "api.scite.ai", "ngay": ngay, "tally": None,
                             "thong_bao_bien_tap": phan_loai, "retracted": bai.get("retracted")}
    if bai.get("retracted") is None:
        # Scite trả bản ghi nhưng KHÔNG rõ retracted (chưa xác minh có bao giờ null không): nói rõ là "không rõ",
        # không được đọc thành "sạch".
        scite["retracted_khong_ro"] = True
    raw["scite"] = scite
    if bai.get("retracted") is True or phan_loai == "rut":
        return "Scite báo đã rút (retracted=True hoặc thông báo biên tập nhắc retract/withdraw)"
    if phan_loai == "dinh_chinh":
        _them_co(raw, "co_thong_bao_bien_tap")
    elif phan_loai == "chua_phan_loai":
        _them_co(raw, "thong_bao_bien_tap_chua_phan_loai")

    try:
        tally = scite_client.lay_tally(doi)
    except Exception as exc:  # noqa: BLE001
        scite["ly_do_tally"] = f"tally:{getattr(exc, 'loai', None) or type(exc).__name__}"
        return None
    if not isinstance(tally, dict):
        scite["ly_do_tally"] = "scite_khong_co_tally" if tally is None else "tally:phan_hoi_khong_hop_le"
        return None
    gon = {k: tally.get(k) for k in ("total", "supporting", "contradicting", "mentioning", "unclassified",
                                     "citingPublications", "citing_publications")
           if isinstance(tally.get(k), int) and not isinstance(tally.get(k), bool)}
    scite["tally"] = gon
    ung_ho, phan_bac = gon.get("supporting"), gon.get("contradicting")
    if isinstance(ung_ho, int) and isinstance(phan_bac, int) and phan_bac >= 3 and phan_bac > ung_ho:
        _them_co(raw, "nhieu_trich_dan_phan_bac")
    return None


class BaoVeScite:
    """Bọc client Scite: sau `so_loi_toi_da` lần lỗi LIÊN TIẾP thì tạm ngưng gọi (Scite đang sập/giới hạn tốc độ)
    và mọi lần gọi tiếp theo ném lỗi loại "tam_ngung" — bản ghi được ghi rõ da_kiem=False thay vì đập dịch vụ."""

    def __init__(self, client: Any, so_loi_toi_da: int = 3) -> None:
        self._client = client
        self._toi_da = so_loi_toi_da
        self.loi_lien_tiep = 0

    @property
    def tam_ngung(self) -> bool:
        return self.loi_lien_tiep >= self._toi_da

    def _goi(self, ten: str, doi: str):
        if self.tam_ngung:
            e = RuntimeError("Scite tạm ngưng sau nhiều lỗi liên tiếp trong lượt chạy này")
            e.loai = "tam_ngung"  # type: ignore[attr-defined]
            raise e
        try:
            ket_qua = getattr(self._client, ten)(doi)
        except Exception:
            self.loi_lien_tiep += 1
            raise
        self.loi_lien_tiep = 0
        return ket_qua

    def lay_bai(self, doi: str):
        return self._goi("lay_bai", doi)

    def lay_tally(self, doi: str):
        return self._goi("lay_tally", doi)


def _tao_scite_mac_dinh() -> Tuple[Optional[Any], Optional[str]]:
    """Dựng SciteClient theo kiểu nạp chịu lỗi của registry: thiếu module => không kiểm Scite (có lý do)."""
    try:
        from app import sources as _nguon  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001  # pragma: no cover
        return None, f"khong_nap_duoc_app_sources:{type(exc).__name__}"
    lop = getattr(_nguon, "SciteClient", None)
    if lop is None:
        return None, "chua_co_module_scite_public"
    try:
        return lop(), None
    except Exception as exc:  # noqa: BLE001
        return None, f"khong_dung_duoc_scite:{type(exc).__name__}"


# ============================================================================ xác minh một hit

@dataclass
class _KetQuaTho:
    ket_qua: str
    ly_do: str
    ban_ghi: Optional[RawRecord] = None
    msg: Optional[dict] = None          # bản ghi Crossref đã tải (để cổng rút bài dùng lại)
    doi: Optional[str] = None
    retracted_pubmed: bool = False
    da_kiem_rut_bai_pubmed: bool = False


def _theo_doi(rec: RawRecord, doi: str, crossref_client: Any) -> _KetQuaTho:
    try:
        msg = crossref_client.lay_theo_doi(doi)
    except Exception as exc:  # noqa: BLE001 — lỗi mạng/parse KHÔNG BAO GIỜ thành khớp
        return _KetQuaTho(KET_QUA_LOI, f"lỗi tra Crossref theo DOI: {type(exc).__name__}")
    if msg is None:
        return _KetQuaTho(KET_QUA_KHONG_KHOP, "Crossref không có bản ghi cho DOI này")
    if msg.get("update-to"):
        return _KetQuaTho(KET_QUA_KHONG_KHOP,
                          "bản ghi Crossref là một thông báo cập nhật (update-to), không phải bài gốc")
    ds_tieu_de = _tieu_de_crossref(msg)
    if not ds_tieu_de:
        return _KetQuaTho(KET_QUA_MO_HO, "bản ghi Crossref không có tiêu đề để đối chiếu")
    if _la_tieu_de_bai_bi_rut(ds_tieu_de[0]):
        # Chỉ kết luận "bị rút" khi hit CÙNG BÀI với bản ghi bị đánh dấu (tiêu đề sau khi bỏ tiền tố khớp);
        # khác bài thì đây là DOI gắn nhầm — vẫn "không khớp" như mọi trường hợp DOI/tiêu đề lệch.
        giong_rut = _do_giong_tieu_de(rec.title, _bo_tien_to_bi_rut(ds_tieu_de[0]), _hit_bi_cat(rec))
        if giong_rut >= NGUONG_GIONG_TIEU_DE:
            return _KetQuaTho(KET_QUA_RUT_BAI,
                              "Crossref ghi tiêu đề bài với tiền tố RETRACTED/WITHDRAWN — bài đã bị rút")
        return _KetQuaTho(KET_QUA_KHONG_KHOP,
                          f"tiêu đề không khớp bản ghi Crossref của DOI (độ giống {giong_rut:.2f})")
    if _la_tieu_de_thong_bao(ds_tieu_de[0]):
        return _KetQuaTho(KET_QUA_KHONG_KHOP, "bản ghi Crossref là thông báo đính chính/rút bài (theo tiêu đề)")
    giong = max(_do_giong_tieu_de(rec.title, t, _hit_bi_cat(rec)) for t in ds_tieu_de)
    if giong < NGUONG_GIONG_TIEU_DE:
        return _KetQuaTho(KET_QUA_KHONG_KHOP, f"tiêu đề không khớp bản ghi Crossref của DOI (độ giống {giong:.2f})")
    doi_dk = str(msg.get("DOI") or doi).strip().lower()
    ban_ghi = _dung_ban_ghi_crossref(msg, rec, "doi", giong, {})
    return _KetQuaTho(KET_QUA_XAC_MINH_DUOC, f"DOI + tiêu đề khớp Crossref (độ giống {giong:.2f})",
                      ban_ghi=ban_ghi, msg=msg, doi=doi_dk)


def _theo_thu_muc(rec: RawRecord, crossref_client: Any) -> _KetQuaTho:
    try:
        ung_vien = crossref_client.tim_theo_thu_muc(rec.title)
    except Exception as exc:  # noqa: BLE001
        return _KetQuaTho(KET_QUA_LOI, f"lỗi tìm Crossref theo tiêu đề: {type(exc).__name__}")
    bi_cat = _hit_bi_cat(rec)
    cham: List[Tuple[float, dict]] = []
    tot_rut = 0.0
    for ms in ung_vien:
        if not isinstance(ms, dict) or not ms.get("DOI") or ms.get("update-to"):
            continue
        ds = _tieu_de_crossref(ms)
        if ds and _la_tieu_de_bai_bi_rut(ds[0]):
            tot_rut = max(tot_rut, max(_do_giong_tieu_de(rec.title, _bo_tien_to_bi_rut(t), bi_cat) for t in ds))
            continue
        if not ds or _la_tieu_de_thong_bao(ds[0]):
            continue
        cham.append((max(_do_giong_tieu_de(rec.title, t, bi_cat) for t in ds), ms))
    cham.sort(key=lambda x: x[0], reverse=True)
    if tot_rut >= NGUONG_GIONG_TIEU_DE and tot_rut >= (cham[0][0] if cham else 0.0):
        return _KetQuaTho(KET_QUA_RUT_BAI,
                          "ứng viên Crossref giống nhất mang tiền tố RETRACTED/WITHDRAWN — bài đã bị rút")
    if not cham:
        return _KetQuaTho(KET_QUA_KHONG_KHOP, "không có ứng viên Crossref dùng được")
    tot_nhat, ms = cham[0]
    if tot_nhat < NGUONG_GIONG_TIEU_DE:
        return _KetQuaTho(KET_QUA_KHONG_KHOP, f"ứng viên tốt nhất chỉ giống {tot_nhat:.2f} (< {NGUONG_GIONG_TIEU_DE})")
    doi_tot = str(ms.get("DOI")).strip().lower()
    for diem, khac in cham[1:]:
        if str(khac.get("DOI")).strip().lower() == doi_tot:
            continue
        if diem >= NGUONG_GIONG_TIEU_DE or diem >= tot_nhat - 0.05:
            return _KetQuaTho(KET_QUA_MO_HO, "có nhiều ứng viên Crossref gần bằng nhau/tiêu đề gần trùng (mơ hồ)")

    chi_tiet: dict = {}
    nam_hit = _nam_tu_chuoi(rec.publication_date)
    if nam_hit is not None:
        nam_cr = _nam_crossref(ms)
        if nam_cr is None:
            return _KetQuaTho(KET_QUA_MO_HO, "biết năm của hit nhưng ứng viên Crossref không có năm để đối chiếu")
        if abs(nam_hit - nam_cr) > 1:
            return _KetQuaTho(KET_QUA_KHONG_KHOP, f"lệch năm quá 1 (hit {nam_hit}, Crossref {nam_cr})")
        chi_tiet["nam_hit"], chi_tiet["nam_crossref"] = nam_hit, nam_cr
    ho_hit = _ho_tac_gia_dau_cua_hit(rec.authors)
    if ho_hit:
        ho_cr = _ho_tac_gia_crossref(ms)
        if not ho_cr:
            return _KetQuaTho(KET_QUA_MO_HO,
                              "biết tác giả của hit nhưng ứng viên Crossref không có tác giả để đối chiếu")
        if not (ho_hit & ho_cr):
            return _KetQuaTho(KET_QUA_KHONG_KHOP, "họ tác giả đầu của hit không có trong tác giả Crossref")
        chi_tiet["tac_gia_dau_khop"] = True
    ban_ghi = _dung_ban_ghi_crossref(ms, rec, "tieu_de_thu_muc", tot_nhat, chi_tiet)
    return _KetQuaTho(KET_QUA_XAC_MINH_DUOC, f"ứng viên Crossref duy nhất rõ ràng (độ giống {tot_nhat:.2f})",
                      ban_ghi=ban_ghi, msg=ms, doi=doi_tot)


def _theo_pmid(rec: RawRecord, pmid: str, pubmed_client: Any) -> _KetQuaTho:
    meta: Optional[dict] = None
    retraction: Optional[dict] = None
    try:
        ham_gop = getattr(pubmed_client, "check_citations", None)
        if callable(ham_gop):
            kq = ham_gop([pmid])
            meta = (kq.get("metadata") or {}).get(pmid)
            retraction = (kq.get("retraction") or {}).get(pmid)
        else:
            meta = pubmed_client.fetch_metadata([pmid]).get(pmid)
    except Exception as exc:  # noqa: BLE001
        return _KetQuaTho(KET_QUA_LOI, f"lỗi tra PubMed theo PMID: {type(exc).__name__}")
    if not isinstance(meta, dict):
        return _KetQuaTho(KET_QUA_LOI, "PubMed không trả thông tin cho PMID (phản hồi không hợp lệ)")
    trang_thai = str(meta.get("status") or "")
    if trang_thai == "unresolved":
        return _KetQuaTho(KET_QUA_KHONG_KHOP, "PubMed không có bản ghi cho PMID này")
    if trang_thai != "resolved":
        return _KetQuaTho(KET_QUA_LOI, f"không tra được PubMed (trạng thái {trang_thai or 'không rõ'})")
    tieu_pubmed = str(meta.get("title") or "")
    giong: Optional[float] = _do_giong_tieu_de(rec.title, tieu_pubmed, _hit_bi_cat(rec)) if tieu_pubmed else None
    chi_tiet: dict = {}
    ban_ghi = _dung_ban_ghi_pubmed(pmid, meta, rec, giong, chi_tiet)
    if giong is not None and giong < NGUONG_GIONG_TIEU_DE:
        # Chỉ ghi nhận, KHÔNG quyết định: quy tắc (c) chỉ đòi PMID tồn tại; độ lệch được để lại cho người xem.
        _them_co(ban_ghi.raw, "tieu_de_hit_lech_so_voi_pmid")
    ket = _KetQuaTho(KET_QUA_XAC_MINH_DUOC, "PMID tồn tại trên PubMed", ban_ghi=ban_ghi,
                     doi=_lam_sach_doi(meta.get("doi")))
    if isinstance(retraction, dict):
        ket.da_kiem_rut_bai_pubmed = str(retraction.get("status") or "") in {"ok", "retracted",
                                                                          "expression_of_concern"}
        ket.retracted_pubmed = str(retraction.get("status") or "") == "retracted"
        if str(retraction.get("status") or "") == "expression_of_concern":
            _them_co(ban_ghi.raw, "co_thong_bao_bien_tap")
    return ket


def _xac_minh(rec: RawRecord, crossref_client: Any, pubmed_client: Any, scite_client: Any) -> KetQuaXacMinh:
    tieu_de = str(rec.title or "").strip()
    if not tieu_de:
        return KetQuaXacMinh(None, KET_QUA_MO_HO, "hit không có tiêu đề")
    if _la_tieu_de_thong_bao(tieu_de):
        return KetQuaXacMinh(None, KET_QUA_KHONG_KHOP,
                             "tiêu đề của hit là thông báo đính chính/rút bài, không phải bài gốc")

    doi = _lam_sach_doi(rec.doi)
    pmid = _lam_sach_pmid(rec.pmid)
    if crossref_client is None and (doi or not pmid):
        crossref_client = CrossrefXacMinh()
    if doi:
        tho = _theo_doi(rec, doi, crossref_client)
    elif pmid:
        if pubmed_client is None:
            from app.sources.pubmed import PubMedClient  # noqa: PLC0415
            pubmed_client = PubMedClient()
        tho = _theo_pmid(rec, pmid, pubmed_client)
    else:
        tho = _theo_thu_muc(rec, crossref_client)

    if tho.ket_qua != KET_QUA_XAC_MINH_DUOC or tho.ban_ghi is None:
        return KetQuaXacMinh(None, tho.ket_qua, tho.ly_do)
    ban_ghi = tho.ban_ghi
    raw = ban_ghi.raw

    if tho.retracted_pubmed:
        return KetQuaXacMinh(None, KET_QUA_RUT_BAI, "PubMed báo bài đã bị rút (Retracted Publication/RetractionIn)")

    # ---- CỔNG RÚT BÀI / THÔNG BÁO BIÊN TẬP: mọi hit kết thúc bằng một DOI đã xác nhận ----
    doi_xn = tho.doi
    if doi_xn:
        if crossref_client is None:
            crossref_client = CrossrefXacMinh()
        try:
            rb = crossref_client.kiem_rut_bai(doi_xn, thong_diep=tho.msg)
        except Exception as exc:  # noqa: BLE001
            return KetQuaXacMinh(None, KET_QUA_LOI, f"không kiểm được rút bài qua Crossref: {type(exc).__name__}")
        trang_thai = str((rb or {}).get("status") or "")
        if trang_thai == "retracted":
            return KetQuaXacMinh(None, KET_QUA_RUT_BAI, "Crossref báo bài đã bị rút (updated-by retraction)")
        if trang_thai == "expression_of_concern":
            _them_co(raw, "co_thong_bao_bien_tap")
        elif trang_thai == "unresolved":
            _them_co(raw, "doi_khong_co_trong_crossref")
        elif trang_thai != "ok":
            return KetQuaXacMinh(None, KET_QUA_LOI,
                                 f"không kiểm được rút bài qua Crossref (trạng thái {trang_thai or 'không rõ'})")
        raw["xac_minh"]["kiem_rut_bai_crossref"] = trang_thai

        ly_do_scite = _lop_scite(doi_xn, scite_client, raw)
        if ly_do_scite:
            return KetQuaXacMinh(None, KET_QUA_RUT_BAI, ly_do_scite)
    else:
        # Không có DOI => Scite (theo DOI) và Crossref không kiểm được. Nếu PubMed cũng không cho biết trạng
        # thái rút bài thì nói rõ là CHƯA kiểm — không im lặng.
        if not tho.da_kiem_rut_bai_pubmed:
            _them_co(raw, "chua_kiem_rut_bai")
        raw["scite"] = {"da_kiem": False, "ly_do": "khong_co_doi", "nguon": "api.scite.ai", "ngay": _ngay_iso()}
    return KetQuaXacMinh(ban_ghi, KET_QUA_XAC_MINH_DUOC, tho.ly_do)


def xac_minh_ban_ghi(rec: RawRecord, *, crossref_client=None, pubmed_client=None,
                     scite_client=None) -> KetQuaXacMinh:
    """Xác minh MỘT hit của tầng dự phòng bằng Crossref/PubMed (xem docstring module). Không bao giờ ném lỗi.

    scite_client=None -> dựng SciteClient theo kiểu nạp chịu lỗi (thiếu module = không kiểm Scite, có ghi lý do).
    Trả `KetQuaXacMinh(ban_ghi, ket_qua)`; `ban_ghi` là bản ghi CỦA CƠ QUAN ĐĂNG KÝ khi ket_qua == "xac_minh_duoc".
    """
    try:
        if scite_client is None and getattr(settings, "enable_scite_verification", True):
            scite_client, ly_do_thieu = _tao_scite_mac_dinh()
        else:
            ly_do_thieu = None
        ket = _xac_minh(rec, crossref_client, pubmed_client, scite_client)
        if ket.ban_ghi is not None and ly_do_thieu:
            scite = ket.ban_ghi.raw.get("scite")
            if isinstance(scite, dict) and not scite.get("da_kiem") and scite.get("ly_do") == "khong_co_client_scite":
                scite["ly_do"] = ly_do_thieu
        return ket
    except Exception as exc:  # noqa: BLE001 — chốt chặn cuối: không bao giờ ném ra ngoài, không bao giờ thành khớp
        logger.warning("Xác minh hit lỗi bất ngờ (%s): %s", type(exc).__name__, str(exc)[:200])
        return KetQuaXacMinh(None, KET_QUA_LOI, f"lỗi bất ngờ: {type(exc).__name__}")


def tao_bo_xac_minh(*, crossref_client=None, pubmed_client=None,
                    scite_client=None) -> Callable[[RawRecord], KetQuaXacMinh]:
    """Dựng hàm xác minh dùng lại client cho cả lượt chạy (không dựng lại mỗi hit) + bọc Scite bằng `BaoVeScite`."""
    cr = crossref_client
    pm = pubmed_client
    sc = scite_client
    trang_thai: Dict[str, Any] = {"ly_do_thieu_scite": None}

    def _xac_minh_dung_lai(rec: RawRecord) -> KetQuaXacMinh:
        nonlocal cr, sc
        if cr is None:
            try:
                cr = CrossrefXacMinh()
            except Exception as exc:  # noqa: BLE001
                return KetQuaXacMinh(None, KET_QUA_LOI, f"không dựng được client Crossref: {type(exc).__name__}")
        if sc is None and getattr(settings, "enable_scite_verification", True):
            client, ly_do = _tao_scite_mac_dinh()
            trang_thai["ly_do_thieu_scite"] = ly_do
            sc = BaoVeScite(client) if client is not None else None
        return xac_minh_ban_ghi(rec, crossref_client=cr, pubmed_client=pm, scite_client=sc)

    return _xac_minh_dung_lai


__all__ = [
    "KetQuaXacMinh", "xac_minh_ban_ghi", "tao_bo_xac_minh", "CrossrefXacMinh", "BaoVeScite",
    "KET_QUA_XAC_MINH_DUOC", "KET_QUA_KHONG_KHOP", "KET_QUA_MO_HO", "KET_QUA_LOI", "KET_QUA_RUT_BAI",
    "NGUONG_GIONG_TIEU_DE",
]
