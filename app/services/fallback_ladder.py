"""BẬC THANG DỰ PHÒNG: Consensus (tầng 1) rồi SerpApi Google Scholar (tầng 2) — chỉ khi chứng cứ đáng tin còn thiếu.

Yêu cầu của bác sĩ: hai nguồn này KHÔNG được tham gia quét song song như nguồn thường; chỉ chạy SAU KHI các nguồn
miễn phí đã trả lời, và chỉ cho (nhóm, truy vấn) mà chứng cứ ĐÁNG TIN chưa đủ (xem evidence_sufficiency.py). Thứ tự
tầng lấy từ `settings.fallback_order`, CHỈ tầng đang bật mới chạy. Sau mỗi tầng: phát hiện được XÁC MINH bởi
Crossref/PubMed (fallback_verification.py) được hợp vào, độ đủ của mọi truy vấn vừa đụng tới được ĐÁNH GIÁ LẠI, và
chỉ truy vấn VẪN CÒN thiếu mới xuống tầng kế.

BỐN TRẠNG THÁI, không gộp (quyet_dinh của mỗi truy vấn):
  du — đủ bài đáng tin (lượt này + kho);
  thieu — chưa đủ và KẾT LUẬN ĐƯỢC -> ứng viên leo thang;
  chua_ket_luan — không nguồn lõi nào trả lời cho truy vấn này (hoặc không đọc được kho, hoặc truy vấn có dấu hiệu
    PII) -> KHÔNG BAO GIỜ leo thang, nhưng được báo rõ;
  bo_qua_cu_phap_pubmed — truy vấn theo TẠP CHÍ/tổ chức viết bằng thẻ trường PubMed ([ta]/[pt]/[cn]...), vô nghĩa với
    Scholar/Consensus -> không áp dụng.
Ứng viên xếp TỆ NHẤT TRƯỚC (ít bài đáng tin nhất, rồi theo thứ tự nhóm/truy vấn) để ngân sách hạn chế của từng tầng
rơi vào chỗ thiếu nhất, không rơi vào 8 truy vấn đầu danh mục.

AN TOÀN VẬN HÀNH:
  • Mỗi lần `search()` = đúng MỘT request HTTP (các connector tự bảo đảm); bậc thang dừng một tầng ở LỖI CHỐT đầu
    tiên (nhận biết bằng thuộc tính `loai` của exception — KHÔNG import lớp lỗi của connector) rồi báo các truy vấn
    còn lại là bị bỏ qua trong tóm tắt. Lỗi thường liên tiếp 3 lần cũng dừng tầng (tránh đập vào dịch vụ đang sập).
  • Giữ >= 1,1 giây giữa hai request Consensus qua `ngu_fn` (tiêm được).
  • Không hàm nào ở đây ném ra ngoài `ingest_all`: lỗi tầng dự phòng được GHI LOG + TÓM TẮT, lượt chạy tiếp tục.
    (Ngoại lệ có chủ ý: cấu hình sai — FALLBACK_ORDER chứa tên lạ / tầng đang bật mà không nạp được — do
    `get_fallback_sources()` nổ TO trước khi có bất kỳ lời gọi mạng nào.)
  • Không bí mật nào vào log/diagnostics/SourceLog/exception: chỉ ghi tên tầng, loại lỗi (`loai`), bộ đếm.
  • Sức khoẻ nguồn CHÍNH (summarize_source_health) tính từ log nguồn chính; kết quả dự phòng chỉ nằm ở
    diagnostics["fallback"] và các dòng SourceLog riêng của tầng dự phòng.
"""
from __future__ import annotations

import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from app.config import CLINICAL_AREAS, settings
from app.services.evidence_sufficiency import (
    KetQuaDuChungCu,
    danh_gia_du_chung_cu,
    lien_ket_khoa_trong_kho_nhieu,
)
from app.services.fallback_verification import (
    KET_QUA_KHONG_KHOP,
    KET_QUA_LOI,
    KET_QUA_MO_HO,
    KET_QUA_RUT_BAI,
    KET_QUA_XAC_MINH_DUOC,
    KetQuaXacMinh,
    tao_bo_xac_minh,
)
from app.sources.base import RawRecord
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Lỗi CHỐT: dừng cả tầng cho phần còn lại của lượt chạy (nhận biết bằng exc.loai — duck typing).
LOI_CHOT = frozenset({"thieu_key", "key_sai", "thanh_toan_qua_han", "tinh_nang_khong_cho_phep", "het_quota",
                      "het_ngan_sach", "cam_truy_cap"})
# Lỗi chốt mang nghĩa "hết hạn mức" (tính vào bo_qua_ngan_sach); các chốt khác tính vào bo_qua_do_loi_chot.
_LOI_HET_HAN_MUC = frozenset({"het_ngan_sach", "het_quota"})
# Connector từ chối TRƯỚC khi gửi request: không phải "lời gọi thật" -> không ghi SourceLog, không tính da_goi.
_LOI_TRUOC_HTTP = frozenset({"het_ngan_sach", "thieu_key"})
# Khoảng cách tối thiểu (giây) giữa hai request cùng một tầng (Consensus Free: 1 request/giây).
KHOANG_CACH_GIUA_HAI_LAN = {"consensus": 1.1}
_SO_LOI_THUONG_LIEN_TIEP_TOI_DA = 3
# Thời điểm (time.monotonic) của lần gọi THẬT gần nhất của từng tầng, tính THEO TIẾN TRÌNH: giới hạn 1 request/giây
# của gói Free áp cho cả tài khoản, nên hai lượt bổ sung liên tiếp (dossier/manager) cũng phải cách nhau >= 1,1 giây.
_LAN_GOI_CUOI: Dict[str, float] = {}
_KHOA_LAN_GOI_CUOI = threading.Lock()
_KHOA_LOG_HOP_LE = ("source", "api_endpoint", "query", "record_count", "status", "error_message", "mode")

# Thẻ trường PubMed vô nghĩa với Google Scholar/Consensus. Là TẬP CON MỞ RỘNG của regex trong
# serpapi_scholar.py (thêm ti/tw/au/ad/jour/pdat/sb/mesh/all/la): bậc thang không tốn lượt trả phí cho truy vấn
# mà connector hoặc dịch vụ chắc chắn không hiểu.
_CU_PHAP_PUBMED_RE = re.compile(
    r"\[(?:ta|pt|cn|tiab|mh|majr|dp|ti|tw|au|ad|jour|pdat|sb|mesh|all|la)\]", re.IGNORECASE)


# ============================================================================ phân loại truy vấn

def _co_pii(query: str) -> bool:
    try:
        from app.core.policy_engine import contains_pii_text  # noqa: PLC0415
        return bool(contains_pii_text(query))
    except Exception as exc:  # noqa: BLE001  # pragma: no cover
        logger.warning("Không kiểm được PII cho truy vấn dự phòng (%s) — connector vẫn tự kiểm.", type(exc).__name__)
        return False


def du_phong_dang_bat() -> bool:
    """Có tầng dự phòng nào được bật VÀ không ở chế độ mock không? (cổng chung cho ingest/dossier/manager)."""
    return bool((settings.enable_consensus or settings.enable_serpapi_scholar) and not settings.use_mock_sources)


def _cho_giua_hai_lan(ten: str, khoang_cach: float, ngu_fn: Callable[[float], Any]) -> None:
    """Ngủ (qua ngu_fn tiêm được) đủ để lần gọi kế cách lần gọi thật gần nhất của tầng `ten` >= khoang_cach giây."""
    with _KHOA_LAN_GOI_CUOI:
        truoc = _LAN_GOI_CUOI.get(ten)
    if truoc is None:
        return
    troi_qua = time.monotonic() - truoc
    cho = khoang_cach if troi_qua < 0 else khoang_cach - troi_qua   # đồng hồ đi lùi -> chờ đủ, không đoán
    if cho > 0:
        try:
            ngu_fn(cho)
        except Exception as exc:  # noqa: BLE001  # pragma: no cover
            logger.warning("ngu_fn lỗi (%s) — tiếp tục.", type(exc).__name__)


def _ghi_lan_goi(ten: str) -> None:
    with _KHOA_LAN_GOI_CUOI:
        _LAN_GOI_CUOI[ten] = time.monotonic()


def _dang_o_che_do_mock(logs: Optional[List[dict]]) -> bool:
    """Lượt chạy đang ở chế độ mock? Cổng CHUNG cho mọi điểm vào, kể cả khi người gọi tự tiêm tầng.

    Hai dấu hiệu: cờ `use_mock_sources`, hoặc một nguồn CHÍNH đã trả dòng log mode/status "mock" (vd PubMed rơi về mock
    khi thiếu NCBI_EMAIL — lượt đó sắp FAIL, không được đốt hạn mức trả phí cho một lượt dữ liệu giả)."""
    if getattr(settings, "use_mock_sources", False):
        return True
    return any(str((lg or {}).get("status")) == "mock" for lg in (logs or []))


def _tom_tat_rong(active: bool = False, ten_tang: Optional[List[str]] = None) -> dict:
    tang = {ten: _tang_rong() for ten in (ten_tang or [])}
    return {
        "active": active, "so_truy_van": 0, "du": 0, "thieu": 0, "chua_ket_luan": 0, "bo_qua_cu_phap_pubmed": 0,
        "du_sau_du_phong": 0, "van_thieu": 0,
        "tang": tang,
        "scite": {"da_kiem": 0, "khong_kiem_duoc": 0, "co_thong_bao_bien_tap": 0, "nhieu_trich_dan_phan_bac": 0},
        "quyet_dinh": [],
    }


def _tang_rong() -> dict:
    return {"da_goi": 0, "tim_thay": 0, "xac_minh_duoc": 0, "bi_loai_chua_xac_minh": 0, "bi_loai_rut_bai": 0,
            "loi_xac_minh": 0, "bo_qua_ngan_sach": 0, "bo_qua_do_loi_chot": 0, "trung_da_co": 0,
            "giu_chua_xac_minh": 0, "so_loi": 0, "loi_cuoi": None, "loi_chot": None}


def _khoa_kho_mac_dinh(queries: List[str], min_evidence: Optional[float]) -> Callable[[str], Set[str]]:
    """Đọc kho MỘT lần cho cả lô truy vấn (một IN thay vì 53 truy vấn lẻ); lỗi DB được nhớ và ném lại.

    Hàm trả về là `_lay(query) -> Set[khoá đơn]` và có thêm thuộc tính `_lay.lien_ket(query) -> List[nhóm khoá]`
    (PMID và DOI của cùng một bài đã lưu) để đếm không nhân đôi một bài vừa nằm trong kho vừa được tầng dự phòng
    tìm lại.
    """
    trang_thai: Dict[str, Any] = {"cache": None, "loi": None}

    def _nap() -> Dict[str, List[Tuple[str, ...]]]:
        if trang_thai["loi"] is not None:
            raise trang_thai["loi"]
        if trang_thai["cache"] is None:
            try:
                trang_thai["cache"] = lien_ket_khoa_trong_kho_nhieu(queries, min_evidence=min_evidence)
            except Exception as exc:  # noqa: BLE001
                trang_thai["loi"] = exc
                raise
        return trang_thai["cache"]

    def _lay(query: str) -> Set[str]:
        return {nhom[0] for nhom in _nap().get(query, []) if nhom}

    def _lien_ket(query: str) -> List[Tuple[str, ...]]:
        return list(_nap().get(query, []))

    _lay.lien_ket = _lien_ket  # type: ignore[attr-defined]
    return _lay


def _ds_truy_van(areas: List[str]) -> List[Tuple[str, str]]:
    """(nhóm, truy vấn) theo thứ tự danh mục, KHỬ TRÙNG theo chuỗi truy vấn (giữ lần đầu)."""
    da_co: Set[str] = set()
    ra: List[Tuple[str, str]] = []
    for area in areas:
        for query in CLINICAL_AREAS.get(area, []):
            if query in da_co:
                logger.debug("Truy vấn trùng chuỗi ở nhóm %r — bỏ lần lặp (dedupe theo chuỗi truy vấn).", area)
                continue
            da_co.add(query)
            ra.append((area, query))
    return ra


def _quyet_dinh_mot_truy_van(area: str, query: str, records: List[RawRecord], logs: Optional[List[dict]],
                             khoa_kho_fn: Callable[[str], Set[str]], nguong: Optional[int],
                             min_evidence: Optional[float],
                             ) -> Tuple[dict, Optional[Set[str]], List[Tuple[str, ...]]]:
    """Phân loại một (nhóm, truy vấn). Trả (quyết định, khoá kho đã đọc hoặc None nếu không đọc được, nhóm liên kết)."""
    co_pii = _co_pii(query)
    cu_phap = bool(_CU_PHAP_PUBMED_RE.search(query))
    kho: Optional[Set[str]] = None
    lien_ket: List[Tuple[str, ...]] = []
    loi_kho: Optional[str] = None
    try:
        kho = set(khoa_kho_fn(query) or set())
        ham_lien_ket = getattr(khoa_kho_fn, "lien_ket", None)
        if callable(ham_lien_ket):
            lien_ket = list(ham_lien_ket(query) or [])
    except Exception as exc:  # noqa: BLE001 — không đọc được kho => KHÔNG biết, không đoán
        loi_kho = type(exc).__name__
        kho = None
        logger.warning("Không đọc được kho bài đáng tin cho truy vấn dự phòng (%s) — coi là chưa kết luận.", loi_kho)

    kq: KetQuaDuChungCu = danh_gia_du_chung_cu(
        records, query, logs=logs, khoa_trong_kho=kho if kho is not None else set(),
        nguong=nguong, min_evidence=min_evidence, lien_ket_kho=lien_ket)
    qd: dict = {"area": area, "query": query, "so_tin_cay": kq.so_tin_cay, "nguong": kq.nguong,
                "tu_luot_nay": kq.tu_luot_nay, "tu_kho": kq.tu_kho, "ly_do": kq.ly_do, "tang_da_thu": []}
    if co_pii:
        qd.update(quyet_dinh="chua_ket_luan", co_pii=True,
                  ly_do="truy vấn có dấu hiệu PII/PHI — không bao giờ gửi ra dịch vụ bên ngoài (chưa kết luận)")
    elif cu_phap:
        qd.update(quyet_dinh="bo_qua_cu_phap_pubmed",
                  ly_do=f"truy vấn theo thẻ trường PubMed, không áp dụng cho Consensus/Scholar ({kq.ly_do})")
    elif kq.du:
        qd["quyet_dinh"] = "du"
    elif loi_kho is not None:
        qd.update(quyet_dinh="chua_ket_luan",
                  ly_do=f"chưa kết luận được: không đọc được kho bài đã lưu ({loi_kho}); {kq.ly_do}")
    elif not kq.ket_luan_duoc:
        qd["quyet_dinh"] = "chua_ket_luan"
    else:
        qd["quyet_dinh"] = "thieu"
    qd["ket_qua"] = "van_thieu" if qd["quyet_dinh"] == "thieu" else qd["quyet_dinh"]
    return qd, kho, lien_ket


def chon_truy_van_can_bo_sung(all_records: List[RawRecord], all_logs: List[dict], areas: List[str], *,
                              khoa_kho_fn: Optional[Callable[[str], Set[str]]] = None,
                              ) -> Tuple[List[dict], List[dict]]:
    """Chọn truy vấn cần hỏi tầng dự phòng. Trả (ứng viên xếp TỆ NHẤT TRƯỚC, quyết định cho MỌI truy vấn).

    Mỗi quyết định: area, query, quyet_dinh (du | thieu | chua_ket_luan | bo_qua_cu_phap_pubmed), so_tin_cay,
    nguong, ly_do (+ tu_luot_nay, tu_kho, tang_da_thu, ket_qua). Ứng viên = các quyết định "thieu", xếp theo
    (so_tin_cay tăng dần, rồi thứ tự nhóm/truy vấn). `khoa_kho_fn(query) -> set khoá` mặc định đọc kho DB.
    """
    ds = _ds_truy_van(list(areas))
    kho_fn = khoa_kho_fn or _khoa_kho_mac_dinh([q for _a, q in ds], None)
    theo_truy_van: Dict[str, List[RawRecord]] = {}
    for r in all_records:
        if r.ingest_query is not None:
            theo_truy_van.setdefault(r.ingest_query, []).append(r)
    quyet_dinh: List[dict] = []
    for area, query in ds:
        qd, _kho, _lien = _quyet_dinh_mot_truy_van(area, query, theo_truy_van.get(query, []), all_logs, kho_fn,
                                                   None, None)
        quyet_dinh.append(qd)
    thu_tu = {id(q): i for i, q in enumerate(quyet_dinh)}
    ung_vien = sorted((q for q in quyet_dinh if q["quyet_dinh"] == "thieu"),
                      key=lambda q: (q["so_tin_cay"], thu_tu[id(q)]))
    return ung_vien, quyet_dinh


def goi_nguon_thuong(client: Any, query: str, area: Optional[str], max_results: int,
                     logs: Optional[List[dict]] = None) -> List[RawRecord]:
    """Gọi MỘT nguồn thường cho vòng quét của dossier/manager và (khi cổng dự phòng bật) ghi lại dòng log.

    `logs=None` -> đúng `client.search(...)` như trước (ném lỗi lên người gọi, hành vi không đổi). Có `logs` ->
    đi qua `ingestion._fetch` để có status ok/degraded/error/mock theo telemetry HTTP (nguồn nuốt lỗi mạng và trả
    [] vẫn bị bắt), dòng log được append vào `logs` — cổng dùng chúng để phân biệt "không có kết quả" với "nguồn
    sập" (chưa kết luận). Không bao giờ ném lỗi khi có `logs` (lỗi nằm trong dòng log).
    """
    if logs is None:
        return client.search(query, clinical_area=area, max_results=max_results)
    ban_ghi, log = _fetch_mac_dinh(client, query, area or "", max_results, None)
    logs.append(log)
    return ban_ghi


def tom_tat_ngan(tom_tat: dict) -> str:
    """Một dòng tiếng Việt mô tả kết quả bậc thang (cho hồ sơ/giao diện); rỗng nếu không có gì đáng báo."""
    if not tom_tat or not tom_tat.get("active"):
        return ""
    phan: List[str] = []
    for ten, t in (tom_tat.get("tang") or {}).items():
        if t.get("loi_chot"):
            phan.append(f"{ten}: DỪNG do lỗi {t['loi_chot']}")
        elif t.get("so_loi"):
            phan.append(f"{ten}: lỗi {t['loi_cuoi']} ({t['so_loi']} lần)")
        elif t.get("da_goi"):
            phan.append(f"{ten}: đã gọi {t['da_goi']}, xác minh được {t['xac_minh_duoc']}, "
                        f"loại chưa xác minh {t['bi_loai_chua_xac_minh']}, loại rút bài {t['bi_loai_rut_bai']}")
    if tom_tat.get("loi_noi_bo"):
        phan.append(f"lỗi nội bộ {tom_tat['loi_noi_bo']}")
    if tom_tat.get("chua_ket_luan"):
        phan.append("chưa kết luận được độ đủ chứng cứ (nguồn lõi không trả lời / PII / kho không đọc được)")
    return "; ".join(phan)


# ============================================================================ lõi bậc thang

class _BocClient:
    """Bọc client tầng dự phòng để BẮT `loai` của exception mà `_fetch` nuốt thành status "error".

    Chỉ chuyển tiếp thuộc tính (name/endpoint/use_mock/http...) và ghi nhớ `loai` — không lưu nội dung lỗi (tránh
    lọt bí mật). Chốt lỗi được nhận biết bằng duck typing, KHÔNG import lớp lỗi của connector."""

    def __init__(self, client: Any) -> None:
        self._client = client
        self.loai_cuoi: Optional[str] = None

    def __getattr__(self, ten: str) -> Any:
        return getattr(self._client, ten)

    def search(self, *args: Any, **kwargs: Any) -> List[RawRecord]:
        self.loai_cuoi = None
        try:
            return self._client.search(*args, **kwargs)
        except Exception as exc:
            self.loai_cuoi = str(getattr(exc, "loai", None) or "khac")
            raise


def _fetch_mac_dinh(client: Any, query: str, area: str, max_results: int,
                    since_date: Optional[str]) -> Tuple[List[RawRecord], dict]:
    from app.services.ingestion import _fetch  # noqa: PLC0415 — import muộn: ingestion import module này

    return _fetch(client, query, area, max_results, since_date)


def _log_sach(log: dict) -> dict:
    """Chỉ giữ ĐÚNG 7 khoá của SourceLog (khoá thừa làm SourceLog(**lg) ném TypeError)."""
    return {k: log.get(k) for k in _KHOA_LOG_HOP_LE}


def _khoa_manh(rec: RawRecord) -> List[str]:
    khoa: List[str] = []
    pmid = str(rec.pmid or "").strip()
    if pmid:
        khoa.append(f"pmid:{pmid}")
    doi = str(rec.doi or "").strip().lower()
    for tien_to in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/", "doi:"):
        if doi.startswith(tien_to):
            doi = doi[len(tien_to):]
    if doi:
        khoa.append(f"doi:{doi.strip()}")
    return khoa


def _ghi_scite(tom_tat: dict, ban_ghi: RawRecord) -> None:
    scite = (ban_ghi.raw or {}).get("scite") if isinstance(ban_ghi.raw, dict) else None
    co = (ban_ghi.raw or {}).get("co") if isinstance(ban_ghi.raw, dict) else None
    co = co if isinstance(co, list) else []
    if isinstance(scite, dict):
        if scite.get("da_kiem") is True:
            tom_tat["scite"]["da_kiem"] += 1
        else:
            tom_tat["scite"]["khong_kiem_duoc"] += 1
    if "co_thong_bao_bien_tap" in co:
        tom_tat["scite"]["co_thong_bao_bien_tap"] += 1
    if "nhieu_trich_dan_phan_bac" in co:
        tom_tat["scite"]["nhieu_trich_dan_phan_bac"] += 1


def _chay_bac_thang(
    ung_vien: List[dict],
    records_goc: List[RawRecord],
    clients: List[Any],
    tom_tat: dict,
    extra_records: List[RawRecord],
    extra_logs: List[dict],
    *,
    max_results: int,
    since_date: Optional[str],
    xac_minh_fn: Callable[[RawRecord], KetQuaXacMinh],
    fetch_fn: Callable[..., Tuple[List[RawRecord], dict]],
    ngu_fn: Callable[[float], Any],
    danh_gia_lai: Callable[[dict, List[RawRecord]], KetQuaDuChungCu],
    khoa_da_luu: Optional[Callable[[str], Set[str]]] = None,
) -> None:
    """Chạy các tầng theo thứ tự trên danh sách ứng viên; tích luỹ vào extra_records/extra_logs/tom_tat.

    khoa_da_luu(query) -> mọi khoá mạnh (pmid:/doi:) của bài đáng tin ĐÃ LƯU cho truy vấn đó: hit trùng bài đã lưu
    bị bỏ trước khi tốn lời gọi xác minh và không được đếm thêm lần nữa (tránh "đủ giả" nhờ đếm đôi một bài).
    """
    giu_chua_xm = bool(getattr(settings, "fallback_keep_unverified", False))
    dang_thieu: List[dict] = list(ung_vien)
    da_thay: Set[str] = set()
    for r in records_goc:
        da_thay.update(_khoa_manh(r))
    dang_lam_viec: List[RawRecord] = list(records_goc)
    da_goi_truoc: Set[str] = set()

    for client in clients:
        if not dang_thieu:
            break
        ten = str(getattr(client, "name", type(client).__name__))
        tang = tom_tat["tang"].setdefault(ten, _tang_rong())
        if getattr(client, "use_mock", False):
            tang["loi_chot"] = "mock"
            logger.warning("Tầng dự phòng %s đang ở chế độ mock — BỎ QUA, không gọi.", ten)
            continue
        boc = _BocClient(client)
        khoang_cach = KHOANG_CACH_GIUA_HAI_LAN.get(ten, 0.0)
        chot: Optional[str] = None
        loi_lien_tiep = 0
        da_dung_toi: List[dict] = []

        for cand in sorted(dang_thieu, key=lambda q: (q.get("so_tin_cay_sau", q["so_tin_cay"]),
                                                      q.get("_thu_tu", 0))):
            if chot is not None:
                if chot in _LOI_HET_HAN_MUC:
                    tang["bo_qua_ngan_sach"] += 1
                else:
                    tang["bo_qua_do_loi_chot"] += 1
                cand.setdefault("tang_bi_bo_qua", {})[ten] = chot
                continue

            if khoang_cach > 0:
                _cho_giua_hai_lan(ten, khoang_cach, ngu_fn)
            try:
                records, log = fetch_fn(boc, cand["query"], cand["area"], max_results, since_date)
            except Exception as exc:  # noqa: BLE001 — fetch_fn tiêm có thể ném; không được làm sập bậc thang
                records = []
                log = {"source": ten, "api_endpoint": getattr(client, "endpoint", ""),
                       "query": f"[{cand['area']}] {cand['query']}", "record_count": 0, "status": "error",
                       "error_message": type(exc).__name__, "mode": "live"}
                boc.loai_cuoi = str(getattr(exc, "loai", None) or "khac")
            loai = boc.loai_cuoi
            da_goi_truoc.add(ten)
            if loai not in _LOI_TRUOC_HTTP:
                _ghi_lan_goi(ten)   # chỉ request THẬT mới đặt nhịp
            log = _log_sach(log)

            if str(log.get("status")) == "mock":
                chot = tang["loi_chot"] = "mock"
                logger.error("Tầng dự phòng %s trả bản ghi/log MOCK ở chế độ live — bỏ hết và DỪNG tầng.", ten)
                cand.setdefault("tang_bi_bo_qua", {})[ten] = "mock"
                continue

            truoc_http = loai in _LOI_TRUOC_HTTP
            # MỌI lần thử đều để lại dấu vết (kể cả khi connector từ chối trước khi gửi: hết ngân sách, thiếu khoá) —
            # "im lặng khác an toàn"; nhưng chỉ request THẬT mới tính vào da_goi.
            extra_logs.append(log)
            if not truoc_http:
                tang["da_goi"] += 1
                da_dung_toi.append(cand)
                if ten not in cand["tang_da_thu"]:
                    cand["tang_da_thu"].append(ten)

            if str(log.get("status")) == "error":
                tang["so_loi"] += 1
                tang["loi_cuoi"] = loai or "khac"

            if loai in LOI_CHOT:
                chot = tang["loi_chot"] = loai
                logger.warning("Tầng dự phòng %s gặp lỗi CHỐT %r — dừng tầng cho phần còn lại của lượt chạy.",
                               ten, loai)
                if truoc_http:
                    # chính truy vấn này cũng không được gọi thật: tính là bị bỏ qua
                    if loai in _LOI_HET_HAN_MUC:
                        tang["bo_qua_ngan_sach"] += 1
                    else:
                        tang["bo_qua_do_loi_chot"] += 1
                    cand.setdefault("tang_bi_bo_qua", {})[ten] = loai
                continue
            if str(log.get("status")) == "error":
                loi_lien_tiep += 1
                if loi_lien_tiep >= _SO_LOI_THUONG_LIEN_TIEP_TOI_DA:
                    chot = tang["loi_chot"] = f"loi_lien_tiep:{loai or 'khac'}"
                    logger.warning("Tầng dự phòng %s lỗi liên tiếp %d lần — dừng tầng.", ten, loi_lien_tiep)
                continue
            loi_lien_tiep = 0

            tang["tim_thay"] += len(records)
            khoa_luu: Set[str] = set()
            if khoa_da_luu is not None:
                try:
                    khoa_luu = set(khoa_da_luu(cand["query"]) or set())
                except Exception as exc:  # noqa: BLE001 — chỉ để tiết kiệm lời gọi xác minh; đếm vẫn đúng nhờ lien_ket
                    logger.debug("Không đọc được khoá kho để lọc trùng (%s).", type(exc).__name__)
            for rec in records:
                if rec.ingest_query is None:
                    rec.ingest_query = cand["query"]
                if rec.clinical_area is None:
                    rec.clinical_area = cand["area"]
                khoa = _khoa_manh(rec)
                if khoa and any(k in da_thay or k in khoa_luu for k in khoa):
                    tang["trung_da_co"] += 1
                    continue
                try:
                    kq = xac_minh_fn(rec)
                except Exception as exc:  # noqa: BLE001
                    kq = KetQuaXacMinh(None, KET_QUA_LOI, f"lỗi bất ngờ khi xác minh: {type(exc).__name__}")
                if kq.ket_qua == KET_QUA_XAC_MINH_DUOC and kq.ban_ghi is not None:
                    br = kq.ban_ghi
                    if br.ingest_query is None:
                        br.ingest_query = cand["query"]
                    if br.clinical_area is None:
                        br.clinical_area = cand["area"]
                    tang["xac_minh_duoc"] += 1
                    extra_records.append(br)
                    dang_lam_viec.append(br)
                    da_thay.update(_khoa_manh(br))
                    da_thay.update(khoa)
                    _ghi_scite(tom_tat, br)
                    continue
                if kq.ket_qua == KET_QUA_RUT_BAI:
                    tang["bi_loai_rut_bai"] += 1
                    logger.warning("Loại phát hiện của %s: bài bị rút/thông báo rút bài (%s).", ten, kq.ly_do)
                    continue
                if kq.ket_qua == KET_QUA_LOI:
                    tang["loi_xac_minh"] += 1
                elif kq.ket_qua in (KET_QUA_KHONG_KHOP, KET_QUA_MO_HO):
                    tang["bi_loai_chua_xac_minh"] += 1
                else:  # vocab lạ từ hàm tiêm: coi là lỗi xác minh (fail-closed), không bao giờ là khớp
                    tang["loi_xac_minh"] += 1
                if giu_chua_xm:
                    rec.raw = dict(rec.raw or {})
                    rec.raw["chua_xac_minh"] = True
                    extra_records.append(rec)
                    dang_lam_viec.append(rec)
                    tang["giu_chua_xac_minh"] += 1

        # Đánh giá LẠI mọi truy vấn vừa đụng tới sau khi hợp phát hiện đã xác minh của tầng này.
        for cand in da_dung_toi:
            if cand not in dang_thieu:
                continue
            try:
                kq_moi = danh_gia_lai(cand, dang_lam_viec)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Đánh giá lại sau tầng %s lỗi (%s) — giữ nguyên trạng thái thiếu.", ten,
                               type(exc).__name__)
                continue
            cand["so_tin_cay_sau"] = kq_moi.so_tin_cay
            if kq_moi.du:
                cand["ket_qua"] = f"du_sau_{ten}"
                cand["ly_do"] = f"{cand['ly_do']} -> sau tầng {ten}: {kq_moi.ly_do}"
                dang_thieu.remove(cand)

    for cand in dang_thieu:
        cand["ket_qua"] = "van_thieu"


def _hoan_tat_tom_tat(tom_tat: dict, quyet_dinh: List[dict]) -> None:
    for q in quyet_dinh:
        q.pop("_thu_tu", None)
    tom_tat["so_truy_van"] = len(quyet_dinh)
    for khoa in ("du", "thieu", "chua_ket_luan", "bo_qua_cu_phap_pubmed"):
        tom_tat[khoa] = sum(1 for q in quyet_dinh if q["quyet_dinh"] == khoa)
    tom_tat["du_sau_du_phong"] = sum(1 for q in quyet_dinh if str(q.get("ket_qua", "")).startswith("du_sau_"))
    tom_tat["van_thieu"] = sum(1 for q in quyet_dinh if q.get("ket_qua") == "van_thieu")
    tom_tat["quyet_dinh"] = quyet_dinh


def _log_tom_tat(tom_tat: dict, boi_canh: str) -> None:
    tang = {k: (v["da_goi"], v["xac_minh_duoc"], v["loi_chot"]) for k, v in tom_tat["tang"].items()}
    logger.info(
        "Bậc thang dự phòng (%s): %d truy vấn — đủ %d, thiếu %d, chưa kết luận %d, bỏ qua cú pháp PubMed %d; "
        "đủ nhờ dự phòng %d, vẫn thiếu %d; tầng (đã gọi, xác minh được, lỗi chốt)=%s",
        boi_canh, tom_tat["so_truy_van"], tom_tat["du"], tom_tat["thieu"], tom_tat["chua_ket_luan"],
        tom_tat["bo_qua_cu_phap_pubmed"], tom_tat["du_sau_du_phong"], tom_tat["van_thieu"], tang)


def chay_du_phong_ingest(
    all_records: List[RawRecord],
    all_logs: List[dict],
    areas: List[str],
    max_results_per_query: int,
    since_date: Optional[str],
    *,
    clients: Optional[List[Any]] = None,
    khoa_kho_fn: Optional[Callable[[str], Set[str]]] = None,
    xac_minh_fn: Optional[Callable[[RawRecord], KetQuaXacMinh]] = None,
    fetch_fn: Optional[Callable[..., Tuple[List[RawRecord], dict]]] = None,
    ngu_fn: Optional[Callable[[float], Any]] = None,
) -> Tuple[List[RawRecord], List[dict], dict]:
    """Chạy bậc thang dự phòng cho lượt ingest. Trả (bản ghi đã xác minh, dòng SourceLog thêm, tóm tắt).

    all_records/all_logs: kết quả của MỌI nguồn chính trong lượt này (chưa gồm dự phòng). `clients`: các tầng đang
    bật theo thứ tự (mặc định `get_fallback_sources()` — cấu hình sai nổ to). `fetch_fn(client, query, area,
    max_results, since_date) -> (records, log)` mặc định là `ingestion._fetch`. `ngu_fn` = hàm ngủ (mặc định
    time.sleep) để giữ >= 1,1 giây giữa hai request Consensus. Không ném lỗi thời gian chạy: lỗi được ghi log và
    tóm tắt, phần đã tích luỹ (bản ghi xác minh + dòng log của lời gọi thật) vẫn được trả về.
    """
    if _dang_o_che_do_mock(all_logs):
        return [], [], _tom_tat_rong(active=False)
    if clients is None:
        from app.sources import get_fallback_sources  # noqa: PLC0415
        clients = get_fallback_sources()
    tom_tat = _tom_tat_rong(active=bool(clients), ten_tang=[str(getattr(c, "name", type(c).__name__))
                                                            for c in clients])
    extra_records: List[RawRecord] = []
    extra_logs: List[dict] = []
    if not clients:
        return extra_records, extra_logs, tom_tat

    try:
        ds = _ds_truy_van(list(areas))
        ds_query = [q for _a, q in ds]
        kho_fn = khoa_kho_fn or _khoa_kho_mac_dinh(ds_query, None)
        theo_truy_van: Dict[str, List[RawRecord]] = {}
        for r in all_records:
            if r.ingest_query is not None:
                theo_truy_van.setdefault(r.ingest_query, []).append(r)

        quyet_dinh: List[dict] = []
        kho_da_doc: Dict[str, Optional[Set[str]]] = {}
        lien_ket_da_doc: Dict[str, List[Tuple[str, ...]]] = {}
        for i, (area, query) in enumerate(ds):
            qd, kho, lien_ket = _quyet_dinh_mot_truy_van(area, query, theo_truy_van.get(query, []), all_logs,
                                                        kho_fn, None, None)
            qd["_thu_tu"] = i
            kho_da_doc[query] = kho
            lien_ket_da_doc[query] = lien_ket
            quyet_dinh.append(qd)
        ung_vien = [q for q in quyet_dinh if q["quyet_dinh"] == "thieu"]

        def _danh_gia_lai(cand: dict, dang_lam_viec: List[RawRecord]) -> KetQuaDuChungCu:
            return danh_gia_du_chung_cu(dang_lam_viec, cand["query"], logs=all_logs,
                                        khoa_trong_kho=kho_da_doc.get(cand["query"]) or set(),
                                        lien_ket_kho=lien_ket_da_doc.get(cand["query"]))

        def _khoa_da_luu(query: str) -> Set[str]:
            khoa: Set[str] = set()
            for nhom in lien_ket_da_doc.get(query, []):
                khoa.update(nhom)
            return khoa

        if ung_vien:
            _chay_bac_thang(
                ung_vien, all_records, list(clients), tom_tat, extra_records, extra_logs,
                max_results=max_results_per_query, since_date=since_date,
                xac_minh_fn=xac_minh_fn or tao_bo_xac_minh(),
                fetch_fn=fetch_fn or _fetch_mac_dinh, ngu_fn=ngu_fn or time.sleep,
                danh_gia_lai=_danh_gia_lai, khoa_da_luu=_khoa_da_luu)
        _hoan_tat_tom_tat(tom_tat, quyet_dinh)
        _log_tom_tat(tom_tat, "ingest")
    except Exception as exc:  # noqa: BLE001 — KHÔNG ném ra ngoài ingest_all
        logger.error("Bậc thang dự phòng gặp lỗi bất ngờ (%s) — lượt chạy tiếp tục với phần đã tích luỹ.",
                     type(exc).__name__)
        tom_tat["loi_noi_bo"] = type(exc).__name__
    return extra_records, extra_logs, tom_tat


def bo_sung_neu_thieu(
    query: str,
    area: Optional[str],
    records: List[RawRecord],
    *,
    since_date: Optional[str] = None,
    max_results: int = 10,
    clients: Optional[List[Any]] = None,
    khoa_kho_fn: Optional[Callable[[str], Set[str]]] = None,
    xac_minh_fn: Optional[Callable[[RawRecord], KetQuaXacMinh]] = None,
    ngu_fn: Optional[Callable[[float], Any]] = None,
    logs: Optional[List[dict]] = None,
    fetch_fn: Optional[Callable[..., Tuple[List[RawRecord], dict]]] = None,
) -> Tuple[List[RawRecord], dict]:
    """Biến thể MỘT truy vấn theo yêu cầu (dossier/manager): trả (bản ghi đã xác minh, tóm tắt).

    `records`: RawRecord mà vòng nguồn thường vừa trả cho `query` (cùng `ingest_query`). `khoa_kho_fn` mặc định
    KHÔNG tính kho (truy vấn tự do của đề tài không có lịch sử ingest_query). `logs` (tuỳ chọn, ngoài chữ ký cố
    định): dòng log nguồn theo dạng SourceLog để nhận ra "chưa kết luận"; không có `logs` thì bỏ qua bước kiểm
    nguồn lõi — người gọi (dossier/manager) luôn truyền. Không ném lỗi thời gian chạy.
    """
    if _dang_o_che_do_mock(logs):
        return [], _tom_tat_rong(active=False)
    if clients is None:
        from app.sources import get_fallback_sources  # noqa: PLC0415
        clients = get_fallback_sources()
    area_txt = area or ""
    tom_tat = _tom_tat_rong(active=bool(clients), ten_tang=[str(getattr(c, "name", type(c).__name__))
                                                            for c in clients])
    extra_records: List[RawRecord] = []
    extra_logs: List[dict] = []
    if not clients:
        return extra_records, tom_tat
    try:
        kho_fn = khoa_kho_fn or (lambda _q: set())
        qd, kho, lien_ket = _quyet_dinh_mot_truy_van(area_txt, query, records, logs, kho_fn, None, None)
        qd["_thu_tu"] = 0
        if qd["quyet_dinh"] == "thieu":
            def _danh_gia_lai(cand: dict, dang_lam_viec: List[RawRecord]) -> KetQuaDuChungCu:
                return danh_gia_du_chung_cu(dang_lam_viec, cand["query"], logs=logs, khoa_trong_kho=kho or set(),
                                            lien_ket_kho=lien_ket)

            khoa_luu_tat_ca: Set[str] = set()
            for nhom in lien_ket:
                khoa_luu_tat_ca.update(nhom)

            _chay_bac_thang(
                [qd], records, list(clients), tom_tat, extra_records, extra_logs,
                max_results=max_results, since_date=since_date,
                xac_minh_fn=xac_minh_fn or tao_bo_xac_minh(),
                fetch_fn=fetch_fn or _fetch_mac_dinh, ngu_fn=ngu_fn or time.sleep,
                danh_gia_lai=_danh_gia_lai, khoa_da_luu=lambda _q: khoa_luu_tat_ca)
        _hoan_tat_tom_tat(tom_tat, [qd])
        _log_tom_tat(tom_tat, "theo yêu cầu")
    except Exception as exc:  # noqa: BLE001
        logger.error("Bổ sung dự phòng theo yêu cầu gặp lỗi bất ngờ (%s).", type(exc).__name__)
        tom_tat["loi_noi_bo"] = type(exc).__name__
    return extra_records, tom_tat


__all__ = [
    "LOI_CHOT", "KHOANG_CACH_GIUA_HAI_LAN", "chon_truy_van_can_bo_sung", "chay_du_phong_ingest",
    "bo_sung_neu_thieu", "du_phong_dang_bat", "goi_nguon_thuong", "tom_tat_ngan",
]
