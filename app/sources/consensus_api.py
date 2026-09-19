"""Connector Consensus API (consensus.app) — thêm 19/09/2026 theo yêu cầu bác sĩ, để bổ sung
chứng cứ cho hệ nghiên cứu y khoa / cập nhật guideline / trích dẫn thực hành lâm sàng ngoài
PubMed/Europe PMC/Crossref/OpenAlex/Semantic Scholar/Scopus hiện có.

KHÔNG nhầm với: (a) nhãn thiết kế `design:'Consensus'` = ĐỒNG THUẬN CHUYÊN GIA trong cổng
`verify_dashboard` (không liên quan gì tới nguồn này); (b) kênh MCP của claude.ai
(`mcp__plugin_bio-research_consensus__search`, skill `tong-thuat-chung-cu`, lệnh
`/tra-consensus`) — đó là kênh riêng cho phiên Claude, KHÔNG chia sẻ mã với connector này,
nhưng CHIA SẺ CHUNG hạn mức lượt gọi hằng tháng của tài khoản Consensus.

Thông số đã tra từ tài liệu chính thức của Consensus NLP (README Consensus-NLP/consensus-api,
docs.consensus.app/llms-full.txt) ngày 19/09/2026; chưa gọi thật trước khi viết file này:
  • `GET https://api.consensus.app/v1/search`, xác thực bằng header `x-api-key`. Endpoint cũ
    `/v1/quick_search` đã deprecated (dự kiến gỡ 2027-02-07) — KHÔNG dùng.
  • Gói Free: 30 lượt/tháng (1 lượt = mỗi 100 bài trả về, làm tròn lên ⇒ xin 5 hay 20 bài đều 1 lượt),
    tối đa 20 bài/yêu cầu, không phân trang, không có `study_type`/`takeaway`/toàn văn. 1 yêu cầu/giây.
    Vượt hạn mức → 429. Tài liệu còn ghi «Enterprise includes `doi`» ⇒ CHƯA CHẮC gói Free có trả `doi`
    (xem «BẢN GHI PHẢI CÓ DOI» bên dưới).
  • KẾT QUẢ KHÔNG CÓ PMID — chỉ (có thể có) DOI và url trang Consensus. Bản ghi chỉ được kiểm rút bài
    qua đường DOI (Crossref `updated-by`, BH33), KHÔNG tham gia chuỗi 3 tầng PMID của
    `retraction_chain.py` (giống Scopus/OpenAlex/Crossref/Semantic Scholar).

VAI TRÒ (doctrine `_CONNECTOR-CHUNG-CU.md`): Consensus là kênh KHÁM PHÁ. Bản ghi vào kho như một
ứng viên; mọi khẳng định muốn TRÍCH phải truy ngược DOI gốc và qua `kiem-chung-trich-dan` /
`verify_dashboard --online`. Connector này không nâng, không gán mức chứng cứ nào: `study_type` để
None (chỉ suy «preprint» khi API báo), nên bản ghi rơi vào watch_only/Tier C thay vì lên actionable
chỉ nhờ từ khoá «guideline» trong tiêu đề. Nhãn `raw["vai_tro"]` chỉ để tra cứu thủ công —
`normalize()` KHÔNG mang `raw` sang EvidenceItem nên không có mã nào tiêu thụ nó.

BẢN GHI PHẢI CÓ DOI: không DOI thì không dedupe được với PubMed, không kiểm được rút bài, không truy
ngược được ⇒ bản ghi bị BỎ (đếm trong chẩn đoán). Phản hồi có bản ghi mà KHÔNG bản nào có DOI ⇒ nổ to
(gói hiện tại có thể không trả `doi`), không đọc thành «không có gì mới».

QUYẾT ĐỊNH LƯU TRỮ của bác sĩ (19/09/2026): điều khoản của Consensus về lưu cache/lưu trữ kết quả
API KHÔNG tìm thấy (điều khoản consensus.app không nhắc API) ⇒ chọn phương án thận trọng:
  1. KHÔNG ghi payload thô ra đĩa: không gọi `save_raw`, và `HttpClient(cache_ttl=0)` + `use_cache=False`
     (cache HTTP mặc định của repo GHI JSON đầy đủ xuống `data/raw/_http_cache/`).
  2. Chỉ giữ tiêu đề · tác giả · tạp chí · năm · DOI · url · số trích dẫn · tứ phân vị SJR. TUYỆT ĐỐI
     không sao chép `abstract` / `takeaway` (do AI của Consensus sinh) / `full_text_chunks` vào
     `RawRecord` (và vì vậy không vào DB).
  3. Cache CHỈ trong bộ nhớ tiến trình (TTL 6 giờ, khóa theo truy vấn+năm) để không tốn lượt hai lần
     cho cùng một truy vấn (kể cả hai luồng đồng thời — single-flight). Khóa cache KHÔNG chứa khóa API.

HẠN MỨC NỘI BỘ (fail-closed, «cầu chì phía client» — hạn mức thật do 429 của Consensus): gói Free chỉ
30 lượt/tháng, dùng chung với MCP. Sổ đếm bền theo THÁNG UTC, mặc định `~/.ebm-state/consensus_quota.json`
(NGOÀI cây repo/OneDrive để mọi worktree cùng máy dùng chung một bộ đếm và không bị `git add -A`;
đổi bằng `CONSENSUS_QUOTA_PATH`) + trần `CONSENSUS_MONTHLY_CALL_CAP` (mặc định 20). Sổ chỉ chia sẻ
trong phạm vi MỘT MÁY — hai máy dùng chung một tài khoản thì chia trần (vd 10 + 10). Ghi nguyên tử qua
file tạm DUY NHẤT + khoá file liên tiến trình (fcntl trên macOS/Linux, msvcrt trên Windows — nhánh
Windows CHƯA chạy thật). Đếm theo từng YÊU CẦU THẬT: `HttpClient` tự retry (429/5xx 1 lần, lỗi kết nối tới
4 lần) nên phần retry được cộng thêm SAU khi gọi. Chạm trần / sổ hỏng / trần ≤ 0 ⇒ RuntimeError
(Source Log = error), KHÔNG im lặng trả `[]` (họ lỗi BH27/BH08).

QUÉT ĐỊNH KỲ: mặc định connector chỉ phục vụ theo YÊU CẦU (dossier/tài liệu nền đề tài, `test-live`) —
`chi_theo_yeu_cau=True` khiến `ingest_all` bỏ qua nó. Lý do: một lượt quét pipeline có ~53 truy vấn sẽ
ăn hết trần 20 lượt trong 20 truy vấn ĐẦU (chỉ vài chuyên khoa đầu danh sách từng có dữ liệu, các
chuyên khoa sau KHÔNG BAO GIỜ được chạm tới) và cạn phần hạn mức dành cho MCP. Gói trả phí: đặt
`CONSENSUS_TRONG_QUET_DINH_KY=true`.
"""
from __future__ import annotations

import contextlib
import json
import os
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import requests

from app.config import settings
from app.sources._fixtures import mock_records_for
from app.sources.base import RawRecord, SourceClient
from app.sources.classify_meta import infer_study_type
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
SEARCH = "https://api.consensus.app/v1/search"

# Trần số bài/yêu cầu của gói Free. LUÔN xin trần này (1 lượt = 100 bài nên xin 5 hay 20 đều 1 lượt)
# rồi cắt ở phía trả về ⇒ cùng một truy vấn với `max_results` khác nhau dùng chung một lượt + cache.
_PAGE_SIZE_TRAN = 20
# 1 yêu cầu/giây trên mọi gói tự phục vụ; chừa dư 0,1s.
_KHOANG_CACH_GIAY = 1.1
_TTL_BO_NHO_GIAY = 6 * 3600
# Mã lỗi phải NỔ TO (khoá sai/hết hạn/không thuộc gói/tham số sai/hết hạn mức) — khác 5xx/timeout
# chỉ ghi cảnh báo và trả rỗng (health của HttpClient vẫn ghi nhận lỗi, ingestion đánh dấu error).
_MA_LOI_NO_TO = (400, 401, 402, 403, 422, 429)
_HEADER_KHOA = "x-api-key"

_dong_ho = time.monotonic
_khoa_bo_nho = threading.Lock()
_BO_NHO: Dict[Tuple[str, Optional[int]], Tuple[float, List[Dict[str, Any]]]] = {}
_khoa_quota = threading.Lock()
_khoa_ds_khoa = threading.Lock()
_KHOA_THEO_TRUY_VAN: Dict[Tuple[str, Optional[int]], threading.Lock] = {}


# ---------------------------------------------------------------------------
# Khoá API: kiểm định dạng TRƯỚC khi dùng
# ---------------------------------------------------------------------------
def _khoa_hop_le(khoa: str) -> bool:
    """Khoá hợp lệ = ASCII, in được, không khoảng trắng. Ký tự lạ (zero-width U+200B, nháy cong U+2019
    dính theo khi copy từ web) làm `http.client` ném UnicodeEncodeError — vốn KHÔNG phải RequestException
    nên lọt qua bộ đếm lỗi của HttpClient và từng bị đọc thành «ok, 0 bản ghi» dù đã trừ lượt."""
    return bool(khoa) and khoa.isascii() and khoa.isprintable() and not any(c.isspace() for c in khoa)


# ---------------------------------------------------------------------------
# Sổ đếm hạn mức tháng (bền, fail-closed, an toàn liên tiến trình)
# ---------------------------------------------------------------------------
def _duong_quota() -> Path:
    rieng = (settings.consensus_quota_path or "").strip()
    if rieng:
        return Path(rieng).expanduser()
    return Path.home() / ".ebm-state" / "consensus_quota.json"


def _thang_hien_tai() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


@contextlib.contextmanager
def _khoa_tien_trinh(path: Path) -> Iterator[None]:
    """Khoá file liên TIẾN TRÌNH quanh chu trình đọc-kiểm-ghi (khoá luồng không đủ khi pipeline nền và
    `run.py test-live` chạy song song). Không lấy được khoá ⇒ RuntimeError (fail-closed)."""
    lock_path = path.with_suffix(".lock")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(lock_path, "a+b")
    except OSError as exc:
        raise RuntimeError(f"[consensus] không mở được file khoá hạn mức {lock_path}: {exc}") from exc
    try:
        if sys.platform == "win32":  # pragma: no cover — chưa chạy thật trên Windows
            import msvcrt
            fh.seek(0)
            while True:
                try:
                    msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
                    break
                except OSError:
                    time.sleep(0.05)
            try:
                yield
            finally:
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    finally:
        fh.close()


def _doc_so_dem() -> int:
    """Số lượt đã giữ chỗ trong THÁNG HIỆN TẠI (UTC). File chưa có ⇒ 0; sang tháng mới ⇒ 0.

    File có mà không đọc được / sai cấu trúc ⇒ RuntimeError (không đoán là 0: đoán thấp có thể
    làm vượt hạn mức, mà gói trả phí thì vượt hạn mức là tốn tiền thật).
    """
    path = _duong_quota()
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        thang, so = data["thang"], data["so_lan"]
        if not isinstance(thang, str) or isinstance(so, bool) or not isinstance(so, int) or so < 0:
            raise ValueError("sai kiểu dữ liệu")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError(
            f"[consensus] sổ đếm hạn mức {path} không đọc được ({exc}) — không đoán số lượt đã dùng. "
            "Kiểm tra số lượt thật trong API & MCP Dashboard của Consensus rồi XOÁ file này để đặt lại."
        ) from exc
    return so if thang == _thang_hien_tai() else 0


def _ghi_so_dem(path: Path, so: int) -> None:
    """Ghi nguyên tử qua file tạm DUY NHẤT (tên cố định từng làm hai tiến trình đè file của nhau)."""
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".cq-", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"thang": _thang_hien_tai(), "so_lan": so}))
        os.replace(tmp, path)
    except OSError as exc:
        if tmp:
            with contextlib.suppress(OSError):
                os.unlink(tmp)
        # Không ghi được sổ đếm ⇒ không chứng minh được mình còn trong hạn mức ⇒ dừng.
        raise RuntimeError(f"[consensus] không ghi được sổ đếm hạn mức {path}: {exc}") from exc


def so_lan_goi_thang_nay() -> int:
    """Số lượt gọi (đã giữ chỗ) trong tháng UTC hiện tại — cho `run.py test-live consensus`."""
    with _khoa_quota:
        return _doc_so_dem()


def _giu_cho_luot_goi() -> int:
    """Giữ chỗ MỘT lượt TRƯỚC khi gọi mạng; chạm trần nội bộ ⇒ RuntimeError. Trả số lượt sau khi tăng.

    Đếm thừa (kể cả khi yêu cầu sau đó lỗi mạng) là chủ ý: đếm thiếu mới nguy hiểm.
    """
    tran = int(settings.consensus_monthly_call_cap)
    path = _duong_quota()
    with _khoa_quota, _khoa_tien_trinh(path):
        da_dung = _doc_so_dem()
        # Trần ≤ 0 cũng bị chặn ở đây vì da_dung ≥ 0 ≥ tran (không cần vế riêng).
        if da_dung >= tran:
            raise RuntimeError(
                f"[consensus] đã dùng {da_dung}/{max(tran, 0)} lượt gọi trong tháng {_thang_hien_tai()} "
                "(trần nội bộ CONSENSUS_MONTHLY_CALL_CAP; gói Free của Consensus chỉ 30 lượt/tháng và "
                "dùng CHUNG với kênh MCP). Nguồn này bị bỏ qua tới đầu tháng sau, hoặc nâng trần nếu "
                "bạn đã có gói cao hơn."
            )
        _ghi_so_dem(path, da_dung + 1)
        return da_dung + 1


def _cong_them_luot(so: int) -> None:
    """Cộng thêm `so` lượt cho các yêu cầu THẬT do HttpClient tự retry (không kiểm trần — chúng đã
    được gửi đi rồi; chỉ ghi nhận cho đúng). Lỗi ghi sổ ở bước này chỉ cảnh báo, không che kết quả gọi."""
    if so <= 0:
        return
    path = _duong_quota()
    try:
        with _khoa_quota, _khoa_tien_trinh(path):
            _ghi_so_dem(path, _doc_so_dem() + so)
    except RuntimeError as exc:
        logger.warning("[consensus] không cộng được %d lượt retry vào sổ đếm: %s", so, exc)


# ---------------------------------------------------------------------------
# Cache chỉ trong bộ nhớ (không chạm đĩa) + single-flight
# ---------------------------------------------------------------------------
def xoa_bo_nho() -> None:
    """Xoá cache bộ nhớ (dùng cho test)."""
    with _khoa_bo_nho:
        _BO_NHO.clear()
    with _khoa_ds_khoa:
        _KHOA_THEO_TRUY_VAN.clear()


def _khoa_cua(khoa: Tuple[str, Optional[int]]) -> threading.Lock:
    """Mỗi truy vấn một khoá: hai luồng cùng truy vấn cùng lúc chỉ tốn MỘT lượt (single-flight)."""
    with _khoa_ds_khoa:
        return _KHOA_THEO_TRUY_VAN.setdefault(khoa, threading.Lock())


def _doc_bo_nho(khoa: Tuple[str, Optional[int]]) -> Optional[List[Dict[str, Any]]]:
    with _khoa_bo_nho:
        muc = _BO_NHO.get(khoa)
        if muc is None:
            return None
        han, rows = muc
        if _dong_ho() > han:
            _BO_NHO.pop(khoa, None)
            return None
        return [dict(r) for r in rows]


def _ghi_bo_nho(khoa: Tuple[str, Optional[int]], rows: List[Dict[str, Any]]) -> None:
    with _khoa_bo_nho:
        _BO_NHO[khoa] = (_dong_ho() + _TTL_BO_NHO_GIAY, [dict(r) for r in rows])


# ---------------------------------------------------------------------------
# Phân tích phản hồi — CHỈ giữ trường tối thiểu, ép kiểu chặt
# ---------------------------------------------------------------------------
def _chuoi(v: Any) -> Optional[str]:
    return (v.strip() or None) if isinstance(v, str) else None


def _doi_sach(doi: Any) -> Optional[str]:
    """Chỉ nhận chuỗi trông như DOI (bắt đầu «10.»). Bóc tiền tố URL và «doi:»."""
    s = _chuoi(doi)
    if not s:
        return None
    for tien_to in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/",
                    "http://dx.doi.org/", "doi:"):
        if s.lower().startswith(tien_to):
            s = s[len(tien_to):].strip()
            break
    return s if s.startswith("10.") else None


def _so_nguyen(v: Any) -> Optional[int]:
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def _nam(v: Any) -> Optional[str]:
    if isinstance(v, bool):
        return None
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if isinstance(v, str) and v.strip().isdigit():
        v = int(v.strip())
    return str(v) if isinstance(v, int) and 1000 <= v <= 3000 else None


def _url(v: Any) -> Optional[str]:
    s = _chuoi(v)
    return s if s and s.lower().startswith(("http://", "https://")) else None


def _mot_dong(item: Any) -> Optional[Dict[str, Any]]:
    """Rút gọn một bài về đúng các trường được phép giữ. Không tiêu đề ⇒ bỏ."""
    if not isinstance(item, dict):
        return None
    title = _chuoi(item.get("title"))
    if not title:
        return None
    authors = item.get("authors")
    if isinstance(authors, list):
        authors = ", ".join(a.strip() for a in authors if isinstance(a, str) and a.strip()) or None
    else:
        authors = _chuoi(authors)
    return {
        "title": title,
        "authors": authors,
        "journal": _chuoi(item.get("journal_name")),
        "year": _nam(item.get("publish_year")),
        "doi": _doi_sach(item.get("doi")),
        "url": _url(item.get("url")),
        "citation_count": _so_nguyen(item.get("citation_count")),
        "sjr_quartile": _so_nguyen(item.get("sjr_best_quartile")),
        "is_preprint": item.get("is_preprint") is True,   # chuỗi "false" KHÔNG được thành True
    }


def _rut_gon(data: Any) -> Tuple[List[Dict[str, Any]], int]:
    """Lấy `results[]` và rút gọn; trả (các dòng dùng được, số dòng bị loại vì sai định dạng).

    Phản hồi không có mảng `results`, hoặc có dòng mà KHÔNG dòng nào dùng được ⇒ NỔ TO (API đổi cấu
    trúc?), không đọc thành «0 kết quả»."""
    ket_qua = data.get("results") if isinstance(data, dict) else None
    if not isinstance(ket_qua, list):
        raise RuntimeError(
            "[consensus] phản hồi không có mảng `results` — API có thể đã đổi cấu trúc; "
            "không coi đây là «0 kết quả»."
        )
    rows: List[Dict[str, Any]] = []
    for item in ket_qua:
        try:
            r = _mot_dong(item)
        except Exception as exc:  # một dòng hỏng không được huỷ cả lô
            logger.warning("[consensus] bỏ qua 1 dòng kết quả hỏng: %s", exc)
            r = None
        if r:
            rows.append(r)
    if ket_qua and not rows:
        raise RuntimeError(
            f"[consensus] phản hồi có {len(ket_qua)} dòng nhưng KHÔNG dòng nào dùng được (thiếu `title`?) — "
            "schema có thể đã đổi; không coi đây là «0 kết quả»."
        )
    return rows, len(ket_qua) - len(rows)


def _chan_doan(data: Any) -> Dict[str, Any]:
    """Chỉ TÊN trường và số đếm — không giá trị — để `test-live` cho biết gói Free thật sự trả gì."""
    if not isinstance(data, dict):
        return {}
    ds = data.get("results")
    dau = ds[0] if isinstance(ds, list) and ds and isinstance(ds[0], dict) else {}
    return {
        "truong_goc": sorted(data.keys()),
        "tong_ban_ghi": len(ds) if isinstance(ds, list) else None,
        "truong_ban_ghi_dau": sorted(dau.keys()),
        "so_ban_ghi_co_doi": sum(1 for i in ds if isinstance(i, dict) and i.get("doi"))
        if isinstance(ds, list) else None,
    }


def _nam_tu_since(since_date: Optional[str]) -> Optional[int]:
    if not since_date:
        return None
    try:
        return int(since_date[:4])
    except ValueError:
        logger.warning("[consensus] since_date không đúng định dạng YYYY-MM-DD: %r", since_date)
        return None


def _go_khoa_khi_chuyen_huong(prepared_request: Any, response: Any) -> None:
    """`requests` chỉ gỡ header `Authorization` khi đổi host, KHÔNG gỡ header tuỳ biến — nên khoá
    `x-api-key` từng đi theo cả chuyển hướng sang host/http:// khác. Consensus không có lý do chuyển
    hướng ⇒ gỡ khoá ở MỌI chuyển hướng (thay `Session.rebuild_auth`)."""
    prepared_request.headers.pop(_HEADER_KHOA, None)


class ConsensusClient(SourceClient):
    name = "consensus"
    endpoint = SEARCH

    def __init__(self) -> None:
        super().__init__()
        headers = {"Accept": "application/json"}
        khoa = (settings.consensus_api_key or "").strip()
        # Chỉ nạp khoá ĐÃ hợp lệ vào header: khoá dị dạng làm `requests` ném InvalidHeader với thông báo
        # chứa NGUYÊN VĂN giá trị khoá (lộ vào log) — search() sẽ nổ to bằng thông điệp cố định thay vào đó.
        if _khoa_hop_le(khoa):
            headers[_HEADER_KHOA] = khoa  # header, KHÔNG bao giờ đi trong URL/query
        self.http = HttpClient(default_headers=headers, cache_ttl=0, min_interval=_KHOANG_CACH_GIAY)
        self.http.session.rebuild_auth = _go_khoa_khi_chuyen_huong
        # Đếm từng yêu cầu THẬT (HttpClient.request_count chỉ đếm mỗi lần get_json, không đếm retry).
        self._tls = threading.local()
        goc = self.http.session.request

        def _dem_va_gui(*args: Any, **kwargs: Any) -> Any:
            self._tls.so_lan_gui = getattr(self._tls, "so_lan_gui", 0) + 1
            return goc(*args, **kwargs)

        self.http.session.request = _dem_va_gui
        # Chỉ tên trường/số đếm của lần gọi thật gần nhất (xem `_chan_doan`).
        self.chan_doan: Dict[str, Any] = {}

    @property
    def chi_theo_yeu_cau(self) -> bool:
        """True ⇒ `ingest_all` (quét định kỳ) bỏ qua nguồn này; dossier/tài liệu nền vẫn dùng."""
        return not settings.consensus_trong_quet_dinh_ky

    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        if self.use_mock:
            return mock_records_for(self.name, query, clinical_area, max_results)

        khoa = (settings.consensus_api_key or "").strip()
        if not khoa:
            # Chặn SỚM, rõ ràng (cùng nguyên tắc Scopus): nguồn BẬT mà thiếu điều kiện thật
            # phải NỔ TO, không âm thầm trả rỗng.
            raise RuntimeError(
                "[consensus] ENABLE_CONSENSUS=true nhưng thiếu CONSENSUS_API_KEY — "
                "thêm vào ~/.ebm-secrets/medical-ebm-automation.env rồi thử lại."
            )
        if not _khoa_hop_le(khoa):
            # Thông điệp CỐ ĐỊNH — tuyệt đối không chèn giá trị khoá.
            raise RuntimeError(
                "[consensus] CONSENSUS_API_KEY chứa ký tự không hợp lệ (khoảng trắng, ký tự vô hình hoặc "
                "ngoài ASCII — hay dính theo khi copy từ web). Dán lại khoá, không kèm dấu nháy/khoảng trắng."
            )

        nam = _nam_tu_since(since_date)
        khoa_nho = (query.strip().lower(), nam)
        with _khoa_cua(khoa_nho):
            rows = _doc_bo_nho(khoa_nho)
            if rows is None:
                rows = self._goi_that(query, nam)
                if rows is None:
                    return []            # lỗi tạm thời: KHÔNG cache «rỗng» (sẽ bị đọc là «không có kết quả»)
                _ghi_bo_nho(khoa_nho, rows)

        out: List[RawRecord] = []
        for r in rows[:max(1, int(max_results))]:
            doi = r["doi"]
            out.append(RawRecord(
                source=self.name, title=r["title"], authors=r["authors"],
                journal_or_organization=r["journal"], publication_date=r["year"],
                doi=doi, pmid=None,
                url=r["url"] or f"https://doi.org/{doi}",
                abstract=None,  # cố ý: xem đoạn QUYẾT ĐỊNH LƯU TRỮ ở đầu file
                # Không suy loại thiết kế từ tiêu đề (từ «guideline» trong tiêu đề từng đẩy bản ghi lên
                # Tier A/actionable): chỉ ghi nhận «preprint» khi API báo.
                study_type=(infer_study_type(r["title"], None, r["journal"], "PPR")
                            if r["is_preprint"] else None),
                clinical_area=clinical_area,
                ingest_query=query, api_endpoint=SEARCH,
                raw={
                    "vai_tro": "kham_pha_can_xac_minh_doi",
                    "citation_count": r["citation_count"],
                    "sjr_quartile": r["sjr_quartile"],
                },
            ))
        return out

    def _goi_that(self, query: str, nam: Optional[int]) -> Optional[List[Dict[str, Any]]]:
        """MỘT lần gọi thật (đã giữ chỗ lượt): trả các dòng CÓ DOI, đã rút gọn; None = lỗi tạm thời
        (5xx/kết nối — đã cảnh báo, HttpClient đã ghi failure_count) ⇒ người gọi KHÔNG được cache."""
        _giu_cho_luot_goi()  # nổ TO khi chạm trần — cố ý nằm NGOÀI các khối try bên dưới
        # Boolean phải là chuỗi thường "true"/"false" (đã xác nhận với API thật ở PR ToolUniverse #568).
        params: Dict[str, Any] = {
            "query": query,
            "page_size": _PAGE_SIZE_TRAN,
            "medical_mode": "true",
            "exclude_preprints": "true",
        }
        if nam is not None:
            params["year_min"] = nam  # theo NĂM, không có ngày/tháng — bao gồm cả năm này
        self._tls.so_lan_gui = 0
        try:
            data = self.http.get_json(SEARCH, params=params, use_cache=False)
        except requests.HTTPError as exc:
            ma = exc.response.status_code if exc.response is not None else None
            if ma in _MA_LOI_NO_TO:
                raise RuntimeError(_giai_thich_loi(ma)) from exc
            logger.warning("[consensus] lỗi gọi thật (live) HTTP %s — BỎ QUA, KHÔNG bịa mock: %s", ma, exc)
            return None
        except RuntimeError as exc:
            # HttpClient đã ghi nhận lỗi cuối cùng (failure_count) nên ingestion đánh dấu `error`.
            logger.warning("[consensus] lỗi gọi thật (live) — BỎ QUA, KHÔNG bịa mock: %s", exc)
            return None
        finally:
            # Yêu cầu THẬT = 1 + số lần HttpClient tự retry; 1 lượt đã giữ chỗ ở trên.
            _cong_them_luot(getattr(self._tls, "so_lan_gui", 0) - 1)

        rows, so_hong = _rut_gon(data)
        co_doi = [r for r in rows if r["doi"]]
        self.chan_doan = _chan_doan(data)
        self.chan_doan["so_ban_ghi_bo_vi_thieu_doi"] = len(rows) - len(co_doi)
        self.chan_doan["so_dong_bo_vi_sai_dinh_dang"] = so_hong
        if rows and not co_doi:
            raise RuntimeError(
                "[consensus] phản hồi có bản ghi nhưng KHÔNG bản nào có DOI — không truy ngược/dedupe/kiểm "
                "rút bài được nên bị bỏ hết (gói hiện tại có thể không trả `doi`; tài liệu ghi «Enterprise "
                f"includes doi»). Trường có trong phản hồi: {self.chan_doan.get('truong_ban_ghi_dau')}."
            )
        return co_doi


def _giai_thich_loi(ma: Optional[int]) -> str:
    y_nghia = {
        400: "yêu cầu bị từ chối — có thể tham số (medical_mode/exclude_preprints/year_min…) không được API "
             "chấp nhận; chạy `python run.py test-live consensus \"<từ khoá>\"` để xem lỗi thật",
        401: "khoá CONSENSUS_API_KEY thiếu/sai/đã thu hồi (hoặc yêu cầu bị chuyển hướng — khoá không được "
             "gửi theo chuyển hướng)",
        402: "tài khoản Consensus quá hạn thanh toán",
        403: "tính năng không thuộc gói hiện tại (feature_not_allowed)",
        422: "tham số không hợp lệ với API",
        429: "vượt tốc độ (1 yêu cầu/giây) hoặc HẾT HẠN MỨC THÁNG của Consensus (dùng chung với MCP)",
    }.get(ma, "lỗi không rõ")
    return f"[consensus] HTTP {ma}: {y_nghia}."
