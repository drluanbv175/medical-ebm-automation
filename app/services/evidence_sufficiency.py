"""Đánh giá "ĐỦ chứng cứ đáng tin chưa?" cho từng truy vấn — cổng của bậc thang dự phòng.

Dùng bởi `app/services/fallback_ladder.py` để quyết định truy vấn nào mới được phép hỏi các tầng dự phòng
TÍNH PHÍ/có hạn mức (Consensus tầng 1, SerpApi Scholar tầng 2). Module này THUẦN LOGIC: không gọi mạng; chỉ
`khoa_tin_cay_trong_kho()` đọc DB (kho EvidenceItem đã lưu).

ĐỊNH NGHĨA "ĐÁNG TIN" (một bản ghi đã `normalize` + `score_item`, xem `la_tin_cay`):
  • nguồn KHÔNG phải consensus / serpapi_scholar — tầng dự phòng không bao giờ tự bảo chứng cho mình; phát hiện
    của chúng chỉ được tính SAU KHI đã được cơ quan đăng ký (Crossref/PubMed) xác minh và trở thành bản ghi
    của chính cơ quan đó (source = crossref/pubmed);
  • không phải bản mock;
  • có PMID hoặc DOI (không định danh thì không xác minh được);
  • hạng độ tin cậy KHÁC "D" (và đã được chấm — không phải None);
  • điểm chất lượng chứng cứ >= `settings.fallback_min_evidence` (mặc định 60).
KHÔNG đổi trọng số/ngưỡng/luật tier nào: chỉ ĐỌC kết quả của bộ chấm điểm hiện có (`score_item`).

ĐẾM "phân biệt": cùng một bài xuất hiện ở PubMed và Europe PMC chỉ tính MỘT (đồ thị liên thông theo PMID/DOI).

"ĐỦ" = số bài đáng tin phân biệt của LƯỢT NÀY HỢP với bài đáng tin ĐÃ LƯU trong kho cho cùng `ingest_query`
>= `settings.fallback_min_trusted` (mặc định 3). Phải cộng cả kho vì ở chế độ incremental mỗi nguồn chỉ trả bài
MỚI kể từ lần chạy trước — "ít bài mới" tuyệt đối KHÔNG được đọc là "thiếu chứng cứ". Vì vậy
`danh_gia_du_chung_cu(khoa_trong_kho=None)` TỰ ĐỌC KHO (None = "hãy tra kho", còn `set()` = "kho không có gì"):
người gọi quên truyền kho không được làm cổng âm thầm bỏ qua kho. Kho không đọc được thì KHÔNG BIẾT
(`ket_luan_duoc=False`), không bao giờ bị coi là 0.

"CHƯA KẾT LUẬN ĐƯỢC" (`ket_luan_duoc=False`): khi không có nguồn lõi khám phá (pubmed/europepmc/crossref) nào có
dòng log status ok/degraded cho truy vấn này trong lượt chạy — nguồn sập không phải bằng chứng của việc thiếu
chứng cứ, nên KHÔNG BAO GIỜ leo thang (im lặng khác an toàn: trạng thái không biết được báo rõ, không âm thầm
coi là đủ hay thiếu).

GIỚI HẠN ĐÃ BIẾT: `EvidenceItem.ingest_query` trong kho bị `_upsert` GHI ĐÈ bằng truy vấn thấy sau cùng
(pipeline.py) — cùng một bài thấy qua hai truy vấn chồng lấn chỉ còn gắn với truy vấn sau, nên số đếm-từ-kho của
truy vấn trước có thể THẤP hơn thực tế (nghiêng về leo thang thừa, không nghiêng về bỏ sót).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

from app.config import settings
from app.services.normalization import normalize, normalized_title_key
from app.sources.base import RawRecord
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Tầng dự phòng: không bao giờ tự làm thoả cổng của chính mình (tránh vòng tự thoả).
NGUON_DU_PHONG = frozenset({"consensus", "serpapi_scholar"})
# Nguồn lõi khám phá: có dòng log ok/degraded cho truy vấn nghĩa là "đã hỏi được", nên kết luận được.
NGUON_LOI_KHAM_PHA = frozenset({"pubmed", "europepmc", "crossref"})
_TRANG_THAI_HOI_DUOC = frozenset({"ok", "degraded"})


@dataclass(frozen=True)
class KetQuaDuChungCu:
    """Kết quả đánh giá cho MỘT truy vấn.

    du: đủ (so_tin_cay >= nguong). ket_luan_duoc: False = không thể kết luận thiếu (nguồn lõi không trả lời) —
    khi đó KHÔNG được leo thang dù du=False. so_tin_cay: số bài đáng tin PHÂN BIỆT (hợp lượt này + kho).
    tu_luot_nay / tu_kho: số bài đáng tin phân biệt tính RIÊNG từng phía (có thể chồng nhau nên tổng >=
    so_tin_cay). ly_do: câu giải thích tiếng Việt (đi vào nhật ký và diagnostics).
    """

    du: bool
    ket_luan_duoc: bool
    so_tin_cay: int
    nguong: int
    tu_luot_nay: int
    tu_kho: int
    ly_do: str


def _lam_sach_doi(doi: object) -> str:
    d = str(doi or "").strip().lower()
    for tien_to in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/", "doi:"):
        if d.startswith(tien_to):
            d = d[len(tien_to):]
    return d.strip()


def khoa_dinh_danh(item: dict) -> Optional[str]:
    """Khoá định danh của một bản ghi đã chuẩn hoá: "pmid:<n>" | "doi:<doi thường>" | "title:<khoá tiêu đề>".

    Ưu tiên PMID rồi DOI rồi tiêu đề chuẩn hoá (`normalized_title_key`). Không có gì dùng được thì None.
    """
    pmid = str(item.get("pmid") or "").strip()
    if pmid:
        return f"pmid:{pmid}"
    doi = _lam_sach_doi(item.get("doi"))
    if doi:
        return f"doi:{doi}"
    khoa_tieu_de = normalized_title_key(str(item.get("title") or ""))
    if khoa_tieu_de:
        return f"title:{khoa_tieu_de}"
    return None


def _cac_khoa_dinh_danh(item: dict) -> List[str]:
    """MỌI khoá định danh mạnh (pmid, doi) của một bản ghi — để nối cùng một bài đi qua nhiều nguồn."""
    khoa: List[str] = []
    pmid = str(item.get("pmid") or "").strip()
    if pmid:
        khoa.append(f"pmid:{pmid}")
    doi = _lam_sach_doi(item.get("doi"))
    if doi:
        khoa.append(f"doi:{doi}")
    return khoa


def _nguong_mac_dinh() -> int:
    try:
        return int(getattr(settings, "fallback_min_trusted", 3))
    except (TypeError, ValueError):
        return 3


def _min_evidence_mac_dinh(min_evidence: Optional[float]) -> float:
    if min_evidence is not None:
        return float(min_evidence)
    try:
        return float(getattr(settings, "fallback_min_evidence", 60.0))
    except (TypeError, ValueError):
        return 60.0


def la_tin_cay(item: dict, min_evidence: Optional[float] = None) -> bool:
    """Bản ghi (đã normalize VÀ đã chấm điểm bằng `score_item`) có phải bằng chứng đáng tin không?

    Xem quy tắc ở docstring module. `min_evidence=None` -> `settings.fallback_min_evidence`.
    """
    if str(item.get("source") or "").lower() in NGUON_DU_PHONG:
        return False
    if item.get("is_mock"):
        return False
    if not (str(item.get("pmid") or "").strip() or _lam_sach_doi(item.get("doi"))):
        return False
    tier = item.get("reliability_tier")
    if not tier or str(tier).upper() == "D":
        return False
    diem = item.get("evidence_quality_score")
    if diem is None:
        return False
    try:
        return float(diem) >= _min_evidence_mac_dinh(min_evidence)
    except (TypeError, ValueError):
        return False


def _chuan_hoa_va_cham(rec: RawRecord) -> dict:
    """normalize + score_item (KHÔNG có bộ chấm thứ hai). Import muộn để tránh vòng ingestion<->pipeline."""
    from app.services.pipeline import score_item  # noqa: PLC0415

    return score_item(normalize(rec))


class _NoiKhoa:
    """Đồ thị liên thông nhỏ trên các khoá định danh (union-find) để đếm bài PHÂN BIỆT."""

    def __init__(self) -> None:
        self._cha: Dict[str, str] = {}

    def them(self, khoa: str) -> None:
        self._cha.setdefault(khoa, khoa)

    def _goc(self, khoa: str) -> str:
        while self._cha[khoa] != khoa:
            self._cha[khoa] = self._cha[self._cha[khoa]]
            khoa = self._cha[khoa]
        return khoa

    def noi(self, cac_khoa: Iterable[str]) -> None:
        ds = list(cac_khoa)
        for k in ds:
            self.them(k)
        for k in ds[1:]:
            self._cha[self._goc(k)] = self._goc(ds[0])

    def sao_chep(self) -> "_NoiKhoa":
        ban_sao = _NoiKhoa()
        ban_sao._cha = dict(self._cha)
        return ban_sao

    def so_nhom(self) -> int:
        return len({self._goc(k) for k in self._cha})


def _tach_query_log(query_log: object) -> Optional[str]:
    """Bóc chuỗi truy vấn từ trường `query` của SourceLog dạng "[nhóm] truy vấn"; không đúng dạng thì None.

    Tên nhóm không chứa "]" nên cắt ở "] " ĐẦU TIÊN — không nhầm với dấu ngoặc nằm trong truy vấn.
    """
    q = str(query_log or "")
    if not q.startswith("[") or "] " not in q:
        return None
    return q.split("] ", 1)[1]


def _co_nguon_loi_tra_loi(logs: List[dict], query: str) -> bool:
    for lg in logs:
        if str(lg.get("source") or "") not in NGUON_LOI_KHAM_PHA:
            continue
        if str(lg.get("status") or "") not in _TRANG_THAI_HOI_DUOC:
            continue
        if _tach_query_log(lg.get("query")) == query:
            return True
    return False


def danh_gia_du_chung_cu(
    records: List[RawRecord],
    query: str,
    *,
    logs: Optional[List[dict]] = None,
    khoa_trong_kho: Optional[Set[str]] = None,
    nguong: Optional[int] = None,
    min_evidence: Optional[float] = None,
    lien_ket_kho: Optional[Iterable[Iterable[str]]] = None,
) -> KetQuaDuChungCu:
    """Đánh giá độ đủ chứng cứ đáng tin cho MỘT truy vấn.

    records: RawRecord của lượt này (mọi truy vấn cũng được — chỉ lấy bản có `ingest_query == query`).
    logs: SourceLog dict của lượt này (khoá source/query/status; query dạng "[nhóm] truy vấn"). `None` = KHÔNG
      cung cấp -> bỏ qua kiểm nguồn lõi (ket_luan_duoc=True, ly_do ghi rõ); danh sách rỗng `[]` = đã cung cấp
      và không có dòng nào -> ket_luan_duoc=False.
    khoa_trong_kho: khoá định danh (xem `khoa_dinh_danh`) của bài đáng tin ĐÃ LƯU cho cùng truy vấn
      (`khoa_tin_cay_trong_kho`). None = TỰ ĐỌC KHO (không đọc được -> ket_luan_duoc=False, không coi là 0);
      `set()` = kho không có gì (không tra DB).
    nguong: None -> `settings.fallback_min_trusted`. min_evidence: None -> `settings.fallback_min_evidence`.
    lien_ket_kho: (tuỳ chọn) các NHÓM khoá cùng thuộc MỘT bài đã lưu (vd PMID và DOI của cùng hàng) để một bản
      ghi mới chỉ có DOI không bị đếm hai lần với bài đã lưu dưới dạng PMID. Không truyền = chỉ nối theo khoá đơn.
    """
    nguong_dung = _nguong_mac_dinh() if nguong is None else int(nguong)
    loi_doc_kho: Optional[str] = None
    if khoa_trong_kho is None:
        try:
            khoa_trong_kho = khoa_tin_cay_trong_kho(query, min_evidence=min_evidence)
        except Exception as exc:  # noqa: BLE001 — không đọc được kho => KHÔNG BIẾT, không đoán là 0
            loi_doc_kho = type(exc).__name__
            khoa_trong_kho = set()
            logger.warning("Đánh giá đủ chứng cứ: không đọc được kho bài đã lưu (%s) — sẽ báo chưa kết luận.",
                           loi_doc_kho)

    noi_luot_nay = _NoiKhoa()
    for rec in records:
        if rec.ingest_query != query:
            continue
        try:
            item = _chuan_hoa_va_cham(rec)
        except Exception as exc:  # noqa: BLE001 — một bản ghi hỏng không được làm sập cả đánh giá
            logger.warning("Đánh giá đủ chứng cứ: bỏ qua 1 bản ghi không chấm được (%s): %s",
                           getattr(rec, "source", "?"), type(exc).__name__)
            continue
        if not la_tin_cay(item, min_evidence):
            continue
        noi_luot_nay.noi(_cac_khoa_dinh_danh(item))
    tu_luot_nay = noi_luot_nay.so_nhom()

    khoa_kho = {k for k in (khoa_trong_kho or set()) if k}
    tu_kho = len(khoa_kho)

    noi_chung = noi_luot_nay.sao_chep()   # giữ liên kết pmid<->doi của lượt này khi hợp với kho
    for k in khoa_kho:
        noi_chung.them(k)
    for nhom in (lien_ket_kho or []):
        nhom_khoa = [k for k in nhom if k]
        if nhom_khoa and any(k in khoa_kho for k in nhom_khoa):
            noi_chung.noi(nhom_khoa)      # PMID và DOI của CÙNG một bài đã lưu -> một nút
    so_tin_cay = noi_chung.so_nhom()
    du = so_tin_cay >= nguong_dung

    if logs is None:
        ket_luan_duoc = True
        ghi_chu_nguon = " (không có log nguồn để kiểm: bỏ qua bước kiểm nguồn lõi)"
    else:
        ket_luan_duoc = _co_nguon_loi_tra_loi(logs, query)
        ghi_chu_nguon = ""
    if loi_doc_kho is not None:
        ket_luan_duoc = False

    chong = tu_luot_nay + tu_kho - so_tin_cay
    chi_tiet = (f"{so_tin_cay} bài đáng tin phân biệt (lượt này {tu_luot_nay}, kho {tu_kho}"
                f"{f', trùng {chong}' if chong > 0 else ''}), ngưỡng {nguong_dung}")
    if du:
        ly_do = f"đủ: {chi_tiet}{ghi_chu_nguon}"
    elif loi_doc_kho is not None:
        ly_do = (f"chưa kết luận được: {chi_tiet}; không đọc được kho bài đã lưu ({loi_doc_kho}) — không được coi "
                 "kho là rỗng, KHÔNG leo thang")
    elif not ket_luan_duoc:
        ly_do = (f"chưa kết luận được: {chi_tiet}; không nguồn lõi khám phá (pubmed/europepmc/crossref) nào "
                 "trả lời ok/degraded cho truy vấn này trong lượt chạy — sự cố nguồn không phải bằng chứng "
                 "của việc thiếu chứng cứ, KHÔNG leo thang")
    else:
        ly_do = f"thiếu: {chi_tiet}{ghi_chu_nguon}"
    return KetQuaDuChungCu(du=du, ket_luan_duoc=ket_luan_duoc, so_tin_cay=so_tin_cay, nguong=nguong_dung,
                           tu_luot_nay=tu_luot_nay, tu_kho=tu_kho, ly_do=ly_do)


def _doc_hang_tin_cay_trong_kho(
    queries: Iterable[str],
    min_evidence: Optional[float],
    session,
) -> Dict[str, List[Tuple[str, List[str]]]]:
    """Đọc kho MỘT lần: với mỗi `ingest_query` trả list (khoá đơn, mọi khoá mạnh pmid/doi) của bài đáng tin.

    Chỉ tính hàng chính (classification khác "duplicate"), không mock, và qua đúng `la_tin_cay`. Lỗi DB được NÉM
    ra để người gọi báo "chưa kết luận" (không âm thầm coi là 0).
    """
    from sqlalchemy import or_  # noqa: PLC0415

    from app.database import session_scope  # noqa: PLC0415
    from app.models import EvidenceItem  # noqa: PLC0415

    ds = sorted({q for q in queries if q})
    ket_qua: Dict[str, List[Tuple[str, List[str]]]] = {q: [] for q in ds}
    if not ds:
        return ket_qua

    nguong_diem = _min_evidence_mac_dinh(min_evidence)

    def _quet(s) -> None:
        for i in range(0, len(ds), 400):
            lo = ds[i:i + 400]
            hang = (
                s.query(
                    EvidenceItem.ingest_query, EvidenceItem.source, EvidenceItem.pmid, EvidenceItem.doi,
                    EvidenceItem.evidence_quality_score, EvidenceItem.reliability_tier,
                    EvidenceItem.is_mock,
                )
                .filter(
                    EvidenceItem.ingest_query.in_(lo),
                    or_(EvidenceItem.classification.is_(None), EvidenceItem.classification != "duplicate"),
                    or_(EvidenceItem.is_mock.is_(None), EvidenceItem.is_mock.is_(False)),
                    EvidenceItem.reliability_tier.isnot(None),
                    EvidenceItem.reliability_tier != "D",
                    EvidenceItem.evidence_quality_score >= nguong_diem,
                )
                .all()
            )
            for iq, nguon, pmid, doi, diem, tier, mock in hang:
                item = {"source": nguon, "pmid": pmid, "doi": doi, "evidence_quality_score": diem,
                        "reliability_tier": tier, "is_mock": bool(mock)}
                if not la_tin_cay(item, nguong_diem):
                    continue
                khoa = khoa_dinh_danh(item)
                if khoa:
                    ket_qua.setdefault(iq, []).append((khoa, _cac_khoa_dinh_danh(item)))

    if session is not None:
        _quet(session)
    else:
        with session_scope() as s:
            _quet(s)
    return ket_qua


def khoa_tin_cay_trong_kho_nhieu(
    queries: Iterable[str],
    *,
    min_evidence: Optional[float] = None,
    session=None,
) -> Dict[str, Set[str]]:
    """Khoá định danh của bài đáng tin ĐÃ LƯU, gom theo `ingest_query` — MỘT truy vấn DB cho cả lô.

    Truy vấn không có hàng nào -> tập rỗng. Lỗi DB được NÉM ra để người gọi báo "chưa kết luận".
    """
    hang = _doc_hang_tin_cay_trong_kho(queries, min_evidence, session)
    return {q: {khoa for khoa, _tat_ca in ds} for q, ds in hang.items()}


def lien_ket_khoa_trong_kho_nhieu(
    queries: Iterable[str],
    *,
    min_evidence: Optional[float] = None,
    session=None,
) -> Dict[str, List[Tuple[str, ...]]]:
    """Như `khoa_tin_cay_trong_kho_nhieu` nhưng trả NHÓM khoá (PMID và DOI của cùng một hàng) cho mỗi bài đã lưu.

    Dùng để một bản ghi mới chỉ có DOI (vd bản ghi Crossref đã xác minh) không bị đếm là bài KHÁC với bài đã lưu
    dưới dạng PMID (`khoa_dinh_danh` ưu tiên PMID). Cùng một lần đọc DB, cùng bộ lọc.
    """
    hang = _doc_hang_tin_cay_trong_kho(queries, min_evidence, session)
    return {q: [tuple(tat_ca) for _khoa, tat_ca in ds] for q, ds in hang.items()}


def khoa_tin_cay_trong_kho(query: str, *, min_evidence: Optional[float] = None, session=None) -> Set[str]:
    """Khoá định danh của bài đáng tin ĐÃ LƯU trong kho cho đúng `ingest_query == query` (xem bản `_nhieu`)."""
    return khoa_tin_cay_trong_kho_nhieu([query], min_evidence=min_evidence, session=session).get(query, set())


__all__ = [
    "KetQuaDuChungCu", "NGUON_DU_PHONG", "NGUON_LOI_KHAM_PHA", "khoa_dinh_danh", "la_tin_cay",
    "danh_gia_du_chung_cu", "khoa_tin_cay_trong_kho", "khoa_tin_cay_trong_kho_nhieu",
    "lien_ket_khoa_trong_kho_nhieu",
]
