"""Connector Consensus (consensus.app — công cụ tìm kiếm nghiên cứu bằng AI) qua REST API —
thêm 20/09/2026 theo yêu cầu bác sĩ ("Consensus được thiết kế tương tự Scholar": chỉ chạy khi các
nguồn miễn phí chưa đủ chứng cứ đáng tin, rồi phải được xác minh bởi Crossref/PubMed).

Đây là nguồn DỰ PHÒNG KHÁM PHÁ (tầng 1 của thang dự phòng, xem app/services/fallback_ladder.py),
KHÔNG phải nguồn xác minh và KHÔNG tham gia quét toàn bộ nguồn (`get_enabled_sources()` không bao
giờ trả nó; chỉ `get_fallback_sources()` trả nó khi ENABLE_CONSENSUS=true). Mọi bản ghi từ đây chỉ
là "gợi ý cần tra lại": chỉ được giữ lại nếu một sổ đăng ký độc lập (Crossref/PubMed) xác nhận.

API (đọc từ docs.consensus.app ngày 20/09/2026 bằng trình duyệt thật):
  • `GET https://api.consensus.app/v1/search`, khoá ở HEADER `x-api-key` (thiếu/sai -> 401).
    Endpoint cũ `/v1/quick_search` đã bị đánh dấu deprecated (gỡ 07/02/2027): KHÔNG dùng.
  • Tham số dùng ở đây: `query`, `page_size` (<= 20), `medical_mode=true`, `exclude_preprints=true`,
    `year_min`. TUYỆT ĐỐI không dùng `page >= 1` (403 `feature_not_allowed` ở gói Free),
    `include_full_text_chunks` (chỉ gói trả phí) hay bộ lọc `study_types`/tính năng trả phí khác.
  • Phản hồi: `{"results": [...], "page", "is_end", "page_size", "next_page"}`.

GIỚI HẠN ĐÃ BIẾT, ghi rõ để không ai hiểu nhầm độ tin cậy dữ liệu:
  • `takeaway` là câu kết luận do AI của Consensus VIẾT, KHÔNG PHẢI abstract và KHÔNG PHẢI chứng
    cứ: chỉ được giữ ở `raw["takeaway"]`, TUYỆT ĐỐI không nhét vào `abstract` và không dùng để chấm
    điểm (cấp trên phải làm sạch việc đó, ở đây `abstract` chỉ lấy từ trường `abstract` thật).
  • `study_type` của Consensus là nhãn của CHỈ MỤC Consensus, không phải loại công bố trong sổ đăng
    ký: chỉ giữ ở `raw["consensus_study_type"]` làm GỢI Ý (chỉ được phép HẠ, không bao giờ NÂNG
    study_type của pipeline). `RawRecord.study_type` chỉ là "preprint" khi `is_preprint` là True,
    còn lại None — không bao giờ suy từ tiêu đề.
  • Không phải mọi hit là bài báo bình duyệt (ví dụ mẫu của chính tài liệu Consensus là một ý kiến
    khoa học của EFSA): việc giữ/loại do xác minh + chấm điểm của pipeline quyết định, không phải ở đây.
  • `doi`/`abstract` có thể vắng (chưa biết tần suất); DOI chỉ nhận khi đúng cú pháp `10.xxxx/...`,
    không thì None kèm cờ `invalid_doi`/`no_doi` — không bao giờ suy đoán DOI từ tiêu đề.
  • Ngày: `publication_date` = "YYYY" từ `publish_year`, hoặc `publish_date` nếu nó đọc được theo
    ISO (chưa biết `publish_date` có luôn là ISO không, và có điền "-01-01" giả khi chỉ biết năm
    không — bản gốc luôn giữ ở `raw["publish_date_goc"]`).
  • KHÔNG tham gia chuỗi 3 tầng kiểm rút bài (retraction_chain.py): kiểm rút bài thuộc bước xác
    minh (fallback_verification.py), không thuộc connector này.

GÓI VÀ NGÂN SÁCH (số đo từ docs.consensus.app 20/09/2026): gói Free = 30 lượt/tháng, tối đa 20 bài
mỗi request, không có `page >= 1`, không toàn văn, 1 request/giây; Pro/Teams = 500 lượt bao gồm, Deep
= 2000. MỘT lượt được tính cho mỗi 100 bài trả về (làm tròn lên, tối thiểu 1) nên `page_size <= 20`
luôn là 1 lượt. API và MCP DÙNG CHUNG MỘT hạn mức tháng (các lần bác sĩ tự tìm bằng Consensus MCP
cũng trừ vào đó); hạn mức đặt lại vào ngày 1 hằng tháng. Vì vậy connector này có HAI trần cục bộ:
  (a) BỘ ĐẾM THÁNG BỀN VỮNG (`consensus_max_calls_per_month`, mặc định 10/30 để chừa phần còn lại cho
      MCP): file JSON `<data>/raw/_state/consensus_usage.json` (nằm dưới `data/raw/*` nên đã được
      .gitignore; cùng kiểu thư mục nội bộ với `_http_cache`), ghi NGUYÊN TỬ (tệp tạm cùng thư mục +
      fsync + os.replace), an toàn giữa các luồng (khoá tiến trình + luôn đọc lại tệp trước khi sửa) và
      tự sang tháng mới theo lịch UTC. Tệp HỎNG/không đọc được thì coi như ĐÃ CHẠM TRẦN và NÓI TO
      (fail-closed), KHÔNG BAO GIỜ tự đặt lại về 0 — xoá/sửa tay tệp sau khi đối chiếu số lượt thật
      trên trang Consensus nếu muốn dùng lại. Giới hạn: hai TIẾN TRÌNH cùng ghi một lúc có thể thua
      cuộc đua đọc-sửa-ghi (đếm thiếu 1) — chấp nhận được vì trần cục bộ thấp hơn quota thật.
  (b) TRẦN THEO LƯỢT CHẠY (`consensus_max_calls_per_run`, mặc định 5): bộ đếm THEO TIẾN TRÌNH, dùng
      chung mọi instance, tự về 0 khi sang ngày mới (cùng lý do như serpapi_scholar.py).
  Lượt trúng cache cục bộ của HttpClient được HOÀN cả hai trần. Lượt thất bại TRƯỚC KHI Consensus tính
  (4xx trừ 429, lỗi vận chuyển không có response, và phản hồi 200 mà HttpClient không đọc được thành
  JSON — cả hai đều ra `ConsensusLoi("khac")`) được hoàn riêng trần THÁNG. 429 "đã dùng hết lượt
  bao gồm" đặt bộ đếm tháng bằng đúng trần và ĐÁNH DẤU hết quota cho cả tháng dương lịch đó.
  429/5xx và phản hồi 200 hỏng vẫn tính vào bộ đếm (hướng thận trọng: đếm dư an toàn hơn đếm thiếu).

PHÂN LOẠI LỖI (im lặng ≠ an toàn: mọi thất bại đều NÉM `ConsensusLoi`, không trả [] để "ok/0" che
sự cố; `loai` xem lớp bên dưới). Lỗi CHỐT — nguồn bị dừng cho phần còn lại của lượt chạy, không gọi
thêm — gồm `key_sai`, `thanh_toan_qua_han`, `tinh_nang_khong_cho_phep`, `het_quota`, `het_ngan_sach`
(và `thieu_key`: thiếu khoá thì mọi lời gọi đều vô nghĩa; xem `LOAI_CHOT`).
  • Đúng MỘT request HTTP cho mỗi `search()` trên MỌI đường (`HttpClient(max_retries=0)`): mỗi request
    là một lượt tính hạn mức, retry sẽ nhân lượt.
  • Giãn cách >= 1,1 giây giữa hai request (giới hạn 1 request/giây của Consensus): `HttpClient` tự
    ngủ theo `min_interval`, và tầng thang dự phòng cũng ngủ theo `KHOANG_CACH_TOI_THIEU_GIAY`.
  • Phản hồi 200 mà thiếu `results` hoặc `results` sai kiểu, hoặc có hit nhưng không hit nào dùng
    được -> NÉM `phan_hoi_khong_hop_le` (nghi Consensus đổi cấu trúc), không trả [] im lặng.
    `results` là danh sách RỖNG hợp lệ mới là "không có kết quả" (trả [], đếm ở `stats`).

BẢO VỆ KHOÁ: khoá CHỈ đi qua HEADER `x-api-key` (`default_headers` của HttpClient), không bao giờ ở
params/URL nên không lọt vào log của HttpClient. Mọi exception do connector tự tạo KHÔNG chứa
URL/params/khoá; mọi chuỗi từ payload được che thêm bằng chính giá trị khoá; payload trước `save_raw`
và mọi trường đưa vào RawRecord đều bị lược khoá tên `api_key`/`x-api-key`. `User-Agent` được đặt cố
định KHÔNG kèm email vận hành (khác HttpClient mặc định). Lỗi HTTP được DỰNG trong khối except rồi
NÉM ở ngoài nó để `__context__` không giữ `requests.HTTPError`.

CHƯA XÁC MINH (không được ghi là đã xác nhận ở nơi khác):
  • CHƯA gọi API thật lần nào (chưa có lệnh chạy thật được duyệt): cấu trúc phản hồi, chuỗi lỗi, mã
    lỗi và hành vi từng tham số đều dựng từ tài liệu + fixture tự dựng. Sau khi bác sĩ duyệt, chạy MỘT
    lần `python run.py test-live consensus "<từ khoá>"` (tốn đúng 1 lượt) để đối chiếu.
  • Điều khoản về LƯU/CACHE kết quả và ghi nguồn (attribution): chưa đọc/chưa xác minh. Connector này
    dùng cache GET 24 giờ mặc định của HttpClient (data/raw/_http_cache/) và `save_raw` payload đã
    làm sạch; nếu điều khoản cấm lưu thì phải tắt hai thứ đó.
  • Thân lỗi 422/429 (dạng JSON), định dạng header `Retry-After` và việc `publish_date` có luôn ISO
    hay không: phân loại lỗi 429 dựa vào chuỗi trong thân ("used all included searches" so với "Too
    many requests"); thân không nhận ra được thì coi là `gioi_han_toc_do` (KHÔNG chốt, không khoá cả
    tháng vì một thân lạ).
  • `medical_mode`/`exclude_preprints`/`year_min` có nằm trong gói Free hay không (nếu không, sẽ ra
    403 `tinh_nang_khong_cho_phep` — lỗi chốt, thông báo có nhắc).
  • Mốc đặt lại hạn mức tháng theo múi giờ nào (dùng UTC), và việc lượt timeout có bị Consensus tính
    hay không (theo hợp đồng: hoàn lượt cục bộ; trần cục bộ thấp hơn quota thật nên có dư địa).
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

from app.config import khoa_do_proxy_gan, settings
from app.core.policy_engine import contains_pii_text
from app.sources._fixtures import mock_records_for
from app.sources.base import RawRecord, SourceClient
from app.utils.http import HttpClient, _cache_key, _cache_path, _redact, _write_cache
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
SEARCH = "https://api.consensus.app/v1/search"

# Giới hạn 1 request/giây của Consensus -> chừa dư 0,1 giây. Tầng thang dự phòng dùng hằng này
# cho hàm ngủ (ngu_fn) giữa hai lời gọi liên tiếp.
KHOANG_CACH_TOI_THIEU_GIAY = 1.1

# Gói Free: tối đa 20 bài/request và KHÔNG có page >= 1 -> page_size không bao giờ vượt 20.
_TRAN_TRANG = 20

# Lỗi CHỐT: tầng thang dự phòng dừng tầng này cho phần còn lại của lượt chạy.
LOAI_CHOT = frozenset({
    "thieu_key", "key_sai", "thanh_toan_qua_han", "tinh_nang_khong_cho_phep", "het_quota",
    "het_ngan_sach",
})

_NAM_TOI_THIEU = 1500
_TRAN_DOI = 200        # cột doi String(255): quá dài coi như không hợp lệ
_TRAN_TAP_CHI = 255    # cột journal_or_organization String(255)
_TRAN_CHUOI_LOI = 300
_KHOANG_TRANG_RE = re.compile(r"\s+")
_DOI_HOP_LE_RE = re.compile(r"^10\.\d{4,9}/[^\s\"<>#?]+$")
_DOI_TIEN_TO_RE = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.IGNORECASE)
_NGAY_ISO_RE = re.compile(r"^(\d{4})-(\d{2})(?:-(\d{2}))?(?:[T ].*)?$")
_THANG_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")
# Thẻ trường của PubMed vô nghĩa với Consensus (hỏi bằng câu/cụm tự nhiên): gửi đi chỉ tốn 1 lượt.
_CU_PHAP_PUBMED_RE = re.compile(
    r"\[(?:ta|pt|cn|tiab|ti|mh|majr|dp|au|la|sb|tw)\]", re.IGNORECASE)
# Khoá có thể bị lặp lại dạng "x-api-key: xxx"/"x-api-key=xxx" trong một chuỗi lỗi/echo.
_KHOA_HEADER_RE = re.compile(r"(x-api-key['\"]?\s*[:=]\s*['\"]?)[^\s'\",;}]+", re.IGNORECASE)

# Từ khoá phân loại thân lỗi 429 (không phân biệt hoa/thường). Cấu trúc thân CHƯA xác minh nên chỉ
# dựa vào chuỗi mà tài liệu Consensus ghi.
_DAU_HIEU_HET_QUOTA = ("used all", "included searches", "all of your", "quota", "exhaust")
_DAU_HIEU_QUA_NHANH = ("too many requests", "rate limit")


# --------------------------------------------------------------------------- lỗi có phân loại

class ConsensusLoi(RuntimeError):
    """Lỗi có phân loại của connector Consensus.

    `loai`: thieu_key | key_sai (401) | thanh_toan_qua_han (402) | tinh_nang_khong_cho_phep (403) |
    het_quota (429 "đã dùng hết lượt bao gồm") | gioi_han_toc_do (429 "Too many requests") |
    tham_so_sai (422/400, hoặc truy vấn PII/rỗng) | het_ngan_sach (trần cục bộ theo lượt chạy/tháng,
    hoặc bộ đếm tháng hỏng) | phan_hoi_khong_hop_le | khac (5xx, lỗi vận chuyển, mã lạ).
    `chot` = loại này là lỗi CHỐT (xem LOAI_CHOT). `ma_http`: mã HTTP nếu có. `retry_after`: số giây
    từ header Retry-After nếu đọc được (định dạng chưa xác minh). `pham_vi` (chỉ het_ngan_sach/
    het_quota): lan_chay | thang | trang_thai_hong | khong_ghi_duoc | consensus.
    Thông báo KHÔNG BAO GIỜ chứa URL/params/khoá.
    """

    def __init__(self, thong_bao: str, loai: str = "khac", *, ma_http: Optional[int] = None,
                 retry_after: Optional[float] = None, pham_vi: Optional[str] = None) -> None:
        super().__init__(thong_bao)
        self.loai = loai
        self.ma_http = ma_http
        self.retry_after = retry_after
        self.pham_vi = pham_vi

    @property
    def chot(self) -> bool:
        return self.loai in LOAI_CHOT


# --------------------------------------------------------------------------- cấu hình / che khoá

_THIEU = object()


def _lay_khoa() -> str:
    khoa = getattr(settings, "consensus_api_key", "")
    return khoa.strip() if isinstance(khoa, str) else ""


def _khoa_dinh_dang_hop_le(khoa: str) -> bool:
    """Khoá hợp lệ = ASCII, in được, không khoảng trắng bên trong. Ký tự vô hình/ngoài ASCII (zero-width
    U+200B, nháy cong U+2019 — hay dính theo khi copy khoá từ web) làm `requests` ném UnicodeEncodeError
    lúc dựng header; nếu không kiểm trước thì lỗi đó bị báo là «timeout/mất mạng» (sai nguyên nhân) và
    nguồn không bị dừng, mỗi truy vấn kế tiếp lại thử lại vô ích."""
    return bool(khoa) and khoa.isascii() and khoa.isprintable() and not any(c.isspace() for c in khoa)


def _go_khoa_khi_chuyen_huong(prepared_request: Any, response: Any) -> None:
    """`requests` chỉ gỡ header `Authorization` khi đổi host, KHÔNG gỡ header tuỳ biến — nên `x-api-key`
    từng đi theo cả chuyển hướng 302 sang host/`http://` khác (đo thật 20/09/2026). Consensus không có lý do
    chuyển hướng ⇒ gỡ khoá ở MỌI chuyển hướng (thay cho `Session.rebuild_auth`)."""
    prepared_request.headers.pop("x-api-key", None)


def _cau_hinh_tran(ten: str, mac_dinh: int) -> int:
    """Trần số lượt gọi từ settings. Thiếu thuộc tính -> mặc định của hợp đồng; có mà sai kiểu ->
    0 (fail-closed: không bao giờ hiểu cấu hình hỏng thành 'không giới hạn')."""
    v = getattr(settings, ten, _THIEU)
    if v is _THIEU:
        return mac_dinh
    if isinstance(v, bool) or not isinstance(v, int):
        return 0
    return max(v, 0)


def _sach_chuoi(text: Any) -> str:
    """Che `api_key=...` (regex của HttpClient), `x-api-key: ...` và chính GIÁ TRỊ khoá nếu lọt vào."""
    s = _KHOA_HEADER_RE.sub(r"\1***", _redact(str(text)))
    khoa = _lay_khoa()
    if khoa and len(khoa) >= 4:
        s = s.replace(khoa, "***")
    return s


def _la_ten_khoa(key: Any) -> bool:
    return re.sub(r"[^a-z]", "", str(key).lower()) in ("apikey", "xapikey")


def _sach_payload(obj: Any, do_sau: int = 0) -> Any:
    """Bản sao payload đã bỏ mọi khoá tên `api_key`/`x-api-key` và che khoá trong chuỗi.

    Dùng cho save_raw + mọi trường đưa vào RawRecord. Quá sâu (bất thường) thì cắt bỏ."""
    if do_sau > 25:
        return None
    if isinstance(obj, dict):
        return {k: _sach_payload(v, do_sau + 1) for k, v in obj.items() if not _la_ten_khoa(k)}
    if isinstance(obj, list):
        return [_sach_payload(v, do_sau + 1) for v in obj]
    if isinstance(obj, str):
        return _sach_chuoi(obj)
    return obj


# --------------------------------------------------------------------------- tiện ích phân tích

def _chuoi(value: Any, tran: Optional[int] = None) -> Optional[str]:
    """Chuỗi thật đã gộp khoảng trắng, hoặc None (không ép kiểu số/danh sách thành chuỗi)."""
    if not isinstance(value, str):
        return None
    s = _KHOANG_TRANG_RE.sub(" ", value).strip()
    if not s:
        return None
    return s[:tran] if tran else s


def _so_nguyen(value: Any) -> Optional[int]:
    """Số nguyên thật (loại bool) hoặc chuỗi toàn chữ số; ngoài ra None — vắng thì KHÔNG ép thành 0."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _bay_gio() -> datetime:
    return datetime.now(timezone.utc)


def _nam_hop_ly(nam: int) -> bool:
    return _NAM_TOI_THIEU <= nam <= _bay_gio().year + 1


def _nam_tu_since_date(since_date: Optional[str]) -> Optional[int]:
    """'YYYY-MM-DD' (hoặc 'YYYY-MM'/'YYYY') -> năm; sai định dạng -> None kèm cảnh báo."""
    if not since_date:
        return None
    s = str(since_date).strip()
    if re.match(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$", s):
        nam = int(s[:4])
        if _nam_hop_ly(nam):
            return nam
    logger.warning("[consensus] since_date không đúng định dạng YYYY-MM-DD: %r", since_date)
    return None


def _lam_sach_doi(value: Any) -> Tuple[Optional[str], Optional[str]]:
    """(doi đã làm sạch chữ thường | None, lý do) — lý do: None nếu ổn, 'no_doi', 'invalid_doi'.

    Chỉ bỏ khoảng trắng, tiền tố https://doi.org/ hoặc 'doi:' và hạ chữ thường; không sửa gì khác,
    không suy đoán, không dựng từ tiêu đề."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, "no_doi"
    if not isinstance(value, str):
        return None, "invalid_doi"
    doi = _DOI_TIEN_TO_RE.sub("", value.strip()).strip().lower()
    if len(doi) > _TRAN_DOI or not _DOI_HOP_LE_RE.match(doi):
        return None, "invalid_doi"
    return doi, None


def _ngay_iso(value: Any) -> Optional[str]:
    """`publish_date` đọc được theo ISO -> 'YYYY-MM-DD' hoặc 'YYYY-MM'; không thì None."""
    s = _chuoi(value)
    if s is None:
        return None
    m = _NGAY_ISO_RE.match(s)
    if not m:
        return None
    nam, thang, ngay = int(m.group(1)), int(m.group(2)), m.group(3)
    try:
        if ngay is None:
            date(nam, thang, 1)
            return f"{nam:04d}-{thang:02d}"
        date(nam, thang, int(ngay))
        return f"{nam:04d}-{thang:02d}-{int(ngay):02d}"
    except ValueError:
        return None


def _ngay_xuat_ban(publish_year: Any, publish_date: Any) -> Tuple[Optional[str], List[str]]:
    """publication_date: 'YYYY' từ publish_year, hoặc ISO publish_date nếu đọc được và khớp năm.
    Không đoán: cả hai không dùng được -> None + cờ year_unknown."""
    co: List[str] = []
    nam = _so_nguyen(publish_year)
    if nam is not None and not _nam_hop_ly(nam):
        nam = None
    iso = _ngay_iso(publish_date)
    if iso is not None and _nam_hop_ly(int(iso[:4])):
        nam_iso = int(iso[:4])
        if nam is None or nam == nam_iso:
            return iso, co
        co.append("date_year_mismatch")
    if nam is not None:
        return str(nam), co
    co.append("year_unknown")
    return None, co


def _gom_chuoi(obj: Any, do_sau: int = 0) -> List[str]:
    """Gom các chuỗi mô tả lỗi từ thân JSON (cấu trúc 422/429 chưa xác minh nên đọc lỏng)."""
    if do_sau > 3:
        return []
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        out: List[str] = []
        for k in ("error", "detail", "message", "msg", "code", "type", "reason"):
            if k in obj:
                out.extend(_gom_chuoi(obj[k], do_sau + 1))
        return out
    if isinstance(obj, list):
        out = []
        for v in obj[:5]:
            out.extend(_gom_chuoi(v, do_sau + 1))
        return out
    return []


def _chi_tiet_tu_response(resp: Any) -> str:
    """Chuỗi chi tiết lỗi từ thân phản hồi, đã che khoá và cắt ngắn; thân không phải JSON -> ghi rõ."""
    if resp is None:
        return ""
    try:
        body = resp.json()
    except Exception:
        return "(thân phản hồi không phải JSON)"
    chuoi = _gom_chuoi(body)
    return _sach_chuoi(" | ".join(chuoi))[:_TRAN_CHUOI_LOI] if chuoi else ""


def _doc_retry_after(resp: Any) -> Optional[float]:
    """Header Retry-After (định dạng chưa xác minh) -> số giây, hoặc None nếu không đọc được."""
    try:
        gia_tri = resp.headers.get("Retry-After") if resp is not None else None
        return float(gia_tri) if gia_tri is not None else None
    except (TypeError, ValueError, AttributeError):
        return None


def _dem_cache_hit(http: Any) -> Optional[int]:
    v = getattr(http, "cache_hit_count", None)
    return v if isinstance(v, int) else None


# --------------------------------------------------------------------------- bộ đếm tháng bền vững

# Khoá RLock dùng chung cho bộ đếm THEO LƯỢT CHẠY (trong bộ nhớ) và bộ đếm THÁNG (trên đĩa):
# mọi chuỗi đọc-kiểm-sửa-ghi đều nằm trọn trong khoá này.
_KHOA_NGAN_SACH = threading.RLock()
_LAN_CHAY: Dict[str, Any] = {"ngay": None, "da_goi": 0}
_PHIEN_BAN_TRANG_THAI = 1


class _TrangThaiHong(Exception):
    """Nội bộ: tệp bộ đếm tháng hỏng/không đọc được (KHÔNG bao giờ được hiểu là 0)."""


def _duong_dan_trang_thai() -> Path:
    """Tệp bộ đếm tháng. Tính tại thời điểm gọi (không hằng số) để test đổi được settings.data_dir."""
    return settings.raw_dir / "_state" / "consensus_usage.json"


def _thang_hien_tai() -> str:
    return _bay_gio().strftime("%Y-%m")


def _doc_trang_thai() -> Dict[str, Any]:
    """Trạng thái bộ đếm tháng đã kiểm: {thang, da_goi, het_quota_do_consensus}.

    Tệp VẮNG = cài mới -> 0. Tháng trong tệp CŨ hơn tháng hiện tại -> sang tháng mới -> 0 (chưa ghi).
    Tháng trong tệp MỚI hơn tháng hiện tại (đồng hồ lùi/tệp từ máy lệch giờ) thì GIỮ NGUYÊN số đếm,
    không đặt lại. NÉM _TrangThaiHong với mọi thứ khác (JSON hỏng, sai kiểu, số âm, phiên bản lạ,
    lỗi đọc): người gọi phải coi là ĐÃ CHẠM TRẦN."""
    duong_dan = _duong_dan_trang_thai()
    hien_tai = _thang_hien_tai()
    try:
        van_ban = duong_dan.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"thang": hien_tai, "da_goi": 0, "het_quota_do_consensus": False}
    except OSError as exc:
        raise _TrangThaiHong(f"không đọc được tệp ({type(exc).__name__})") from None
    try:
        du_lieu = json.loads(van_ban)
    except ValueError:
        raise _TrangThaiHong("nội dung không phải JSON hợp lệ") from None
    if not isinstance(du_lieu, dict):
        raise _TrangThaiHong("nội dung không phải JSON object")
    phien_ban = du_lieu.get("phien_ban", _PHIEN_BAN_TRANG_THAI)
    if isinstance(phien_ban, bool) or phien_ban != _PHIEN_BAN_TRANG_THAI:
        raise _TrangThaiHong(f"phiên bản định dạng lạ ({phien_ban!r})")
    thang = du_lieu.get("thang")
    da_goi = du_lieu.get("da_goi")
    co_het = du_lieu.get("het_quota_do_consensus", False)
    if not isinstance(thang, str) or not _THANG_RE.match(thang):
        raise _TrangThaiHong("trường 'thang' thiếu hoặc sai định dạng YYYY-MM")
    if isinstance(da_goi, bool) or not isinstance(da_goi, int) or da_goi < 0:
        raise _TrangThaiHong("trường 'da_goi' thiếu hoặc không phải số nguyên >= 0")
    if not isinstance(co_het, bool):
        raise _TrangThaiHong("trường 'het_quota_do_consensus' không phải bool")
    if thang < hien_tai:
        return {"thang": hien_tai, "da_goi": 0, "het_quota_do_consensus": False}
    return {"thang": thang, "da_goi": da_goi, "het_quota_do_consensus": co_het}


def _ghi_nguyen_tu(duong_dan: Path, trang_thai: Dict[str, Any]) -> None:
    """Ghi NGUYÊN TỬ: tệp tạm cùng thư mục -> fsync -> os.replace (an toàn cả Windows/OneDrive: thử
    lại vài lần khi tệp đích đang bị khoá tạm thời). Lỗi thì dọn tệp tạm rồi NÉM OSError."""
    duong_dan.parent.mkdir(parents=True, exist_ok=True)
    noi_dung = dict(trang_thai)
    noi_dung["phien_ban"] = _PHIEN_BAN_TRANG_THAI
    noi_dung["cap_nhat_luc"] = _bay_gio().isoformat()
    fd, ten_tam = tempfile.mkstemp(prefix=".consensus_usage.", suffix=".tmp", dir=str(duong_dan.parent))
    da_thay = False
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(noi_dung, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        for lan in range(4):
            try:
                os.replace(ten_tam, duong_dan)
                da_thay = True
                return
            except PermissionError:
                if lan == 3:
                    raise
                time.sleep(0.05 * (lan + 1))
    finally:
        if not da_thay:
            try:
                os.unlink(ten_tam)
            except OSError:
                pass


def _giu_cho_ngan_sach(tran_thang: int, tran_lan_chay: int) -> None:
    """Giữ chỗ 1 lượt gọi trong CẢ HAI trần; NÉM ConsensusLoi(het_ngan_sach/het_quota) nếu không được.

    Chỉ sửa bộ đếm khi cả hai kiểm tra đã qua và bản ghi đĩa đã ghi xong (ghi lỗi -> không đếm lượt
    chạy, không gọi mạng)."""
    with _KHOA_NGAN_SACH:
        hom_nay = _bay_gio().date()
        if _LAN_CHAY["ngay"] != hom_nay:
            _LAN_CHAY["ngay"] = hom_nay
            _LAN_CHAY["da_goi"] = 0
        if _LAN_CHAY["da_goi"] >= tran_lan_chay:
            raise ConsensusLoi(
                f"[consensus] đã dùng hết ngân sách {tran_lan_chay} lượt gọi Consensus của tiến trình "
                "này (CONSENSUS_MAX_CALLS_PER_RUN) — các truy vấn còn lại BỊ BỎ QUA có chủ đích để "
                "không đốt hạn mức tháng (gói Free 30 lượt, dùng chung với Consensus MCP).",
                "het_ngan_sach", pham_vi="lan_chay")
        duong_dan = _duong_dan_trang_thai()
        try:
            tt = _doc_trang_thai()
        except _TrangThaiHong as exc:
            raise ConsensusLoi(
                f"[consensus] bộ đếm lượt gọi THÁNG bị hỏng/không đọc được ({exc}) — coi như ĐÃ CHẠM "
                "TRẦN (fail-closed), KHÔNG tự đặt lại về 0. Đối chiếu số lượt thật trên trang Consensus "
                f"rồi sửa hoặc xoá tay tệp {duong_dan} nếu muốn dùng lại.",
                "het_ngan_sach", pham_vi="trang_thai_hong") from None
        if tt["het_quota_do_consensus"]:
            raise ConsensusLoi(
                f"[consensus] Consensus đã báo HẾT lượt bao gồm của tháng {tt['thang']} (429) — không "
                "gọi thêm cho đến hết tháng dương lịch (UTC).", "het_quota", pham_vi="consensus")
        if tt["da_goi"] >= tran_thang:
            raise ConsensusLoi(
                f"[consensus] đã dùng {tt['da_goi']}/{tran_thang} lượt của THÁNG {tt['thang']} "
                "(CONSENSUS_MAX_CALLS_PER_MONTH; cố ý chừa phần còn lại của gói Free 30 lượt cho "
                "Consensus MCP) — các truy vấn còn lại BỊ BỎ QUA.", "het_ngan_sach", pham_vi="thang")
        tt["da_goi"] += 1
        try:
            _ghi_nguyen_tu(duong_dan, tt)
        except OSError as exc:
            raise ConsensusLoi(
                f"[consensus] không ghi được bộ đếm lượt gọi tháng ({type(exc).__name__}) — không thể "
                "bảo đảm trần tháng nên KHÔNG gọi (fail-closed).",
                "het_ngan_sach", pham_vi="khong_ghi_duoc") from None
        _LAN_CHAY["da_goi"] += 1


def _hoan_ngan_sach(ca_lan_chay: bool) -> None:
    """Hoàn 1 lượt: luôn hoàn bộ đếm THÁNG; hoàn thêm bộ đếm LƯỢT CHẠY khi `ca_lan_chay` (trúng cache).
    Bộ đếm tháng hỏng/lỗi ghi thì giữ nguyên (không hoàn) — hướng thận trọng."""
    with _KHOA_NGAN_SACH:
        if ca_lan_chay and _LAN_CHAY["da_goi"] > 0:
            _LAN_CHAY["da_goi"] -= 1
        try:
            tt = _doc_trang_thai()
            if tt["da_goi"] > 0:
                tt["da_goi"] -= 1
                _ghi_nguyen_tu(_duong_dan_trang_thai(), tt)
        except (_TrangThaiHong, OSError) as exc:
            logger.warning("[consensus] không hoàn được 1 lượt trong bộ đếm tháng (giữ nguyên số đếm): %s",
                           type(exc).__name__)


def _danh_dau_het_quota(tran_thang: int) -> None:
    """Consensus báo 429 hết lượt bao gồm: đặt bộ đếm tháng = trần và đánh dấu hết quota cả tháng."""
    with _KHOA_NGAN_SACH:
        try:
            tt = _doc_trang_thai()
        except _TrangThaiHong:
            return  # tệp hỏng vốn đã chặn (fail-closed); không ghi đè lên bằng suy đoán
        tt["da_goi"] = max(tt["da_goi"], tran_thang)
        tt["het_quota_do_consensus"] = True
        try:
            _ghi_nguyen_tu(_duong_dan_trang_thai(), tt)
        except OSError as exc:
            logger.warning("[consensus] không ghi được dấu hết quota tháng: %s", type(exc).__name__)


def doc_ngan_sach() -> Dict[str, Any]:
    """Ảnh chụp ngân sách để tầng thang dự phòng/diagnostics báo trước 'còn lượt không'. KHÔNG NÉM,
    KHÔNG sửa gì. `trang_thai_hong` True thì `con_lai_thang` = 0 (fail-closed)."""
    tran_thang = _cau_hinh_tran("consensus_max_calls_per_month", 10)
    tran_run = _cau_hinh_tran("consensus_max_calls_per_run", 5)
    with _KHOA_NGAN_SACH:
        da_run = _LAN_CHAY["da_goi"] if _LAN_CHAY["ngay"] == _bay_gio().date() else 0
        info: Dict[str, Any] = {
            "thang": _thang_hien_tai(), "tran_thang": tran_thang, "tran_lan_chay": tran_run,
            "da_goi_lan_chay": da_run, "con_lai_lan_chay": max(tran_run - da_run, 0),
            "duong_dan": str(_duong_dan_trang_thai()),
        }
        try:
            tt = _doc_trang_thai()
        except _TrangThaiHong:
            info.update(da_goi_thang=None, het_quota_do_consensus=False, trang_thai_hong=True,
                        con_lai_thang=0)
            return info
        con_lai = 0 if tt["het_quota_do_consensus"] else max(tran_thang - tt["da_goi"], 0)
        info.update(da_goi_thang=tt["da_goi"], het_quota_do_consensus=tt["het_quota_do_consensus"],
                    trang_thai_hong=False, con_lai_thang=con_lai)
        return info


# --------------------------------------------------------------------------- client

class ConsensusClient(SourceClient):
    name = "consensus"
    endpoint = SEARCH

    def __init__(self) -> None:
        super().__init__()
        # Khoá đi qua HEADER x-api-key (không params/URL) nên không lọt vào log của HttpClient.
        # User-Agent đặt cố định, KHÔNG kèm email vận hành (HttpClient mặc định sẽ nhét mailto).
        # max_retries=0: MỖI request tới Consensus là một lượt tính hạn mức — hợp đồng là đúng MỘT
        # request cho mỗi search() (retry sẽ nhân lượt, mà bộ đếm chỉ tính 1). min_interval: giới hạn
        # 1 request/giây của Consensus. Lỗi thì NÉM ngay; việc thử lại thuộc về lượt chạy sau.
        headers = {"Accept": "application/json", "User-Agent": "medical-ebm-automation/0.1"}
        khoa = _lay_khoa()
        if khoa:
            headers["x-api-key"] = khoa
        self.http = HttpClient(default_headers=headers, min_interval=KHOANG_CACH_TOI_THIEU_GIAY,
                               max_retries=0)
        session = getattr(self.http, "session", None)
        if session is not None:   # client giả trong test có thể không có session
            session.rebuild_auth = _go_khoa_khi_chuyen_huong
        self._chot_loi: Optional[ConsensusLoi] = None   # lỗi chốt: dừng gọi tiếp trên instance này
        self.stats: Dict[str, int] = {
            "so_lan_goi": 0, "bo_qua_ngan_sach": 0, "khong_co_ket_qua": 0, "bo_qua_thieu_tieu_de": 0,
            "bo_qua_khong_phai_dict": 0, "bo_qua_cu_phap_pubmed": 0, "hit_tra_ve": 0,
        }

    # ------------------------------------------------------------------ search
    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        if self.use_mock:
            return mock_records_for(self.name, query, clinical_area, max_results)

        khoa = _lay_khoa()
        qua_proxy = not khoa and khoa_do_proxy_gan("consensus")
        if not khoa and not qua_proxy:
            # Chặn SỚM, rõ ràng — cùng nguyên tắc fail-closed của scopus.py/serpapi_scholar.py:
            # nguồn BẬT mà thiếu điều kiện thật phải NỔ TO, không âm thầm trả rỗng.
            raise ConsensusLoi(
                "[consensus] ENABLE_CONSENSUS=true nhưng thiếu CONSENSUS_API_KEY — thêm vào "
                "~/.ebm-secrets/medical-ebm-automation.env rồi thử lại.", "thieu_key")
        if not qua_proxy and not _khoa_dinh_dang_hop_le(khoa):
            # Thông điệp CỐ ĐỊNH — tuyệt đối không chèn giá trị khoá. Lỗi CHỐT: cấu hình sai thì mọi lời gọi
            # sau đều vô nghĩa. Nằm TRƯỚC ngân sách nên không tốn lượt nào.
            raise self._chot(ConsensusLoi(
                "[consensus] CONSENSUS_API_KEY chứa ký tự không hợp lệ (khoảng trắng, ký tự vô hình hoặc "
                "ngoài ASCII — hay dính theo khi copy từ web). Nạp lại khoá, không kèm dấu nháy/khoảng "
                "trắng; nguồn dừng cho phần còn lại của lượt chạy.", "key_sai"))
        if self._chot_loi is not None:
            raise ConsensusLoi(
                f"{self._chot_loi.args[0]} [nguồn đã bị dừng cho phần còn lại của lượt chạy, "
                "không gọi thêm]", self._chot_loi.loai, ma_http=self._chot_loi.ma_http,
                pham_vi=self._chot_loi.pham_vi)
        if not isinstance(query, str) or not query.strip():
            raise ConsensusLoi("[consensus] truy vấn rỗng — không gọi Consensus (tốn lượt vô ích).",
                               "tham_so_sai")
        if contains_pii_text(query):
            # Truy vấn đi qua Consensus (bên thứ ba): chặn TRƯỚC khi tốn ngân sách và KHÔNG đưa truy
            # vấn vào thông báo (tránh PII lọt vào log/Source Log). Không đặt _chot_loi: một truy vấn
            # xấu không được khoá cả nguồn.
            raise ConsensusLoi(
                "[consensus] truy vấn có dấu hiệu PII/PHI (email, CCCD/mã bệnh nhân, SĐT, ngày sinh...) "
                "— TỪ CHỐI, không gửi sang Consensus. Chỉ dùng chuỗi chủ đề y văn.", "tham_so_sai")
        if _CU_PHAP_PUBMED_RE.search(query):
            self.stats["bo_qua_cu_phap_pubmed"] += 1
            logger.warning(
                "[consensus] BỎ QUA truy vấn cú pháp PubMed (thẻ [ta]/[pt]/...; không gọi Consensus, "
                "không tốn ngân sách): %r", query[:120])
            return []
        if isinstance(max_results, int) and not isinstance(max_results, bool) and max_results <= 0:
            return []  # xin 0 (hoặc âm) kết quả: không gọi (mỗi request là 1 lượt tính hạn mức)

        try:
            so_bai = max(1, min(int(max_results), _TRAN_TRANG))
        except (TypeError, ValueError):
            so_bai = _TRAN_TRANG
        nam_loc = self._nam_loc(since_date)
        params: Dict[str, Any] = {"query": query.strip(), "page_size": so_bai,
                                  "medical_mode": "true", "exclude_preprints": "true"}
        if nam_loc is not None:
            params["year_min"] = nam_loc

        self._giu_ngan_sach()
        if not qua_proxy:   # qua proxy: KHÔNG đặt header rỗng — proxy tự gắn x-api-key
            self._dong_bo_header(khoa)

        cache_truoc = _dem_cache_hit(self.http)
        loi_http: Optional[ConsensusLoi] = None
        loi_van_chuyen: Optional[ConsensusLoi] = None
        data: Any = None
        try:
            data = self.http.get_json(SEARCH, params=params)
        except requests.HTTPError as exc:
            # Chỉ DỰNG lỗi trong khối except rồi ném ở NGOÀI: `raise ... from None` chỉ đặt
            # __suppress_context__, __context__ vẫn trỏ tới HTTPError (có response/URL).
            loi_http = self._loi_tu_http(exc)
        except Exception as exc:
            # Lỗi vận chuyển KHÔNG có response (timeout/mất mạng/JSON hỏng; HttpClient này không retry vì
            # max_retries=0). KHÁC serpapi_scholar (trả []): ở đây NÉM, để thang dự phòng phân biệt
            # "sự cố" với "không có kết quả" — im lặng không được là an toàn. Lượt này chưa chắc được
            # Consensus tính -> hoàn riêng bộ đếm tháng (theo hợp đồng).
            _hoan_ngan_sach(ca_lan_chay=False)
            logger.warning("[consensus] lỗi vận chuyển khi gọi Consensus: %s: %s",
                           type(exc).__name__, _sach_chuoi(str(exc))[:_TRAN_CHUOI_LOI])
            loi_van_chuyen = ConsensusLoi(
                f"[consensus] lỗi vận chuyển khi gọi Consensus ({type(exc).__name__}: timeout/mất mạng/"
                "phản hồi không đọc được) — không kết luận được 'không có kết quả'; lượt này được hoàn "
                "bộ đếm tháng.", "khac")
        if loi_http is not None:
            raise loi_http
        if loi_van_chuyen is not None:
            raise loi_van_chuyen

        cache_sau = _dem_cache_hit(self.http)
        if cache_truoc is not None and cache_sau is not None and cache_sau > cache_truoc:
            _hoan_ngan_sach(ca_lan_chay=True)  # trúng cache cục bộ: không request nào rời máy
            self.stats["so_lan_goi"] -= 1

        ket_qua, sach = self._kiem_phan_hoi(data, query, params)
        self._che_cache(params, data, sach)
        if not ket_qua:
            return []
        self.stats["hit_tra_ve"] += len(ket_qua)

        boi_canh = {"year_min": nam_loc, "medical_mode": True, "exclude_preprints": True,
                    "page_size": so_bai, "ngay_lay": _bay_gio().date().isoformat()}
        out: List[RawRecord] = []
        for vi_tri, item in enumerate(ket_qua):
            try:
                rec, ly_do_bo = self._anh_xa(item, query, clinical_area, boi_canh, vi_tri)
                if rec is None:
                    if ly_do_bo:
                        self.stats[ly_do_bo] += 1
                    continue
                out.append(rec)
                if len(out) >= so_bai:  # so_bai luôn là int (max_results có thể là kiểu lạ)
                    break
            except Exception as exc:  # pragma: no cover
                logger.warning("[consensus] bỏ qua 1 bản ghi hỏng trong trang kết quả (query=%r): %s",
                               query[:120], _sach_chuoi(str(exc))[:_TRAN_CHUOI_LOI])
                continue
        if not out:
            # Có hit nhưng KHÔNG hit nào dùng được: nghi Consensus đổi schema (đổi tên 'title'...).
            # Trả [] sẽ thành 'ok/0' im lặng dù đã tốn 1 lượt -> NÉM, và gỡ cache để không phát lại
            # phản hồi này 24 giờ.
            self._xoa_cache(params)
            khoa_gap = sorted({_sach_chuoi(k) for it in ket_qua if isinstance(it, dict) for k in it})[:15]
            raise ConsensusLoi(
                f"[consensus] phản hồi 200 có {len(ket_qua)} hit nhưng KHÔNG hit nào dùng được (thiếu "
                f"'title' hoặc không phải object) — nghi Consensus đổi cấu trúc; đã tốn 1 lượt. Khoá gặp "
                f"trong phần tử: {khoa_gap}", "phan_hoi_khong_hop_le")
        return out

    # ------------------------------------------------------------------ tham số
    def _nam_loc(self, since_date: Optional[str]) -> Optional[int]:
        """year_min = năm của since_date; không có (hoặc sai định dạng) thì lùi `lookback` năm nếu > 0."""
        nam = _nam_tu_since_date(since_date)
        if nam is None:
            lui = getattr(settings, "consensus_lookback_years", 10)
            if isinstance(lui, bool) or not isinstance(lui, int) or lui < 0:
                lui = 10
            if lui > 0:
                nam = _bay_gio().year - lui
        if nam is not None:
            nam = min(nam, _bay_gio().year)
        return nam

    def _dong_bo_header(self, khoa: str) -> None:
        """Bảo đảm header x-api-key của session khớp khoá hiện hành (khoá có thể được nạp sau khi dựng
        client). Chỉ chạm session thật; client giả không có session thì bỏ qua."""
        session = getattr(self.http, "session", None)
        if session is None:
            return
        try:
            if session.headers.get("x-api-key") != khoa:
                session.headers["x-api-key"] = khoa
        except Exception:  # pragma: no cover
            pass

    # ------------------------------------------------------------------ ngân sách
    def _giu_ngan_sach(self) -> None:
        """Giữ chỗ 1 lượt gọi trong cả trần tháng (bền vững) lẫn trần theo lượt chạy; hết thì NỔ TO."""
        tran_thang = _cau_hinh_tran("consensus_max_calls_per_month", 10)
        tran_run = _cau_hinh_tran("consensus_max_calls_per_run", 5)
        try:
            _giu_cho_ngan_sach(tran_thang, tran_run)
        except ConsensusLoi as loi:
            self.stats["bo_qua_ngan_sach"] += 1
            logger.warning(loi.args[0])
            raise
        self.stats["so_lan_goi"] += 1

    # ------------------------------------------------------------------ xử lý lỗi
    def _chot(self, loi: ConsensusLoi) -> ConsensusLoi:
        self._chot_loi = loi
        logger.warning("[consensus] LỖI CHỐT (%s) — dừng gọi Consensus cho phần còn lại của lượt chạy.",
                       loi.loai)
        return loi

    def _xoa_cache(self, params: Dict[str, Any]) -> None:
        """Gỡ mục cache GET của phản hồi hỏng (HttpClient cache mọi 200 trong 24 giờ) để không phát lại."""
        try:
            _cache_path(_cache_key("GET", SEARCH, params)).unlink(missing_ok=True)
        except Exception:  # pragma: no cover
            pass

    def _che_cache(self, params: Dict[str, Any], data: Any, sach: Dict[str, Any]) -> None:
        """HttpClient ghi NGUYÊN payload vào cache GET TRƯỚC khi connector kịp che. Nếu bản đã che khác
        bản thô (phản hồi có lặp lại khoá...), ghi đè tệp cache bằng bản đã che. Chỉ ghi đè khi tệp đã
        tồn tại, không tự tạo tệp mới."""
        if sach == data:
            return
        try:
            khoa_cache = _cache_key("GET", SEARCH, params)
            if _cache_path(khoa_cache).exists():
                _write_cache(khoa_cache, {"json": sach, "text": None})
        except Exception as exc:  # pragma: no cover
            logger.warning("[consensus] không che được tệp cache HTTP: %s", type(exc).__name__)

    def _loi_tu_http(self, exc: requests.HTTPError) -> ConsensusLoi:
        """Phân loại HTTPError (đã có status) thành ConsensusLoi; KHÔNG đưa URL/params/khoá vào thông báo.

        Lỗi 4xx (trừ 429) là lỗi xảy ra TRƯỚC khi Consensus tính lượt -> hoàn bộ đếm tháng."""
        resp = getattr(exc, "response", None)
        status = getattr(resp, "status_code", None)
        if not isinstance(status, int):
            m = re.match(r"\s*(\d{3})\b", str(exc))
            status = int(m.group(1)) if m else None
        chi_tiet = _chi_tiet_tu_response(resp)
        low = chi_tiet.lower()
        ma = f"HTTP {status}" if status else "HTTP (không rõ mã)"
        if status is not None and 400 <= status < 500 and status != 429:
            _hoan_ngan_sach(ca_lan_chay=False)

        if status == 401:
            return self._chot(ConsensusLoi(
                f"[consensus] {ma}: Consensus từ chối CONSENSUS_API_KEY (thiếu/sai/đã thu hồi) — sửa "
                f"khoá trong ~/.ebm-secrets/medical-ebm-automation.env. {chi_tiet}".strip(),
                "key_sai", ma_http=status))
        if status == 402:
            return self._chot(ConsensusLoi(
                f"[consensus] {ma}: tài khoản Consensus quá hạn thanh toán — kiểm gói/thanh toán trên "
                f"trang Consensus. {chi_tiet}".strip(), "thanh_toan_qua_han", ma_http=status))
        if status == 403:
            return self._chot(ConsensusLoi(
                f"[consensus] {ma}: tính năng không có trong gói hiện tại (feature_not_allowed) — connector "
                "chỉ dùng page=0, page_size<=20, medical_mode, exclude_preprints, year_min; kiểm xem gói "
                f"Free có cho các tham số đó không (chưa xác minh). {chi_tiet}".strip(),
                "tinh_nang_khong_cho_phep", ma_http=status))
        if status == 429:
            retry_after = _doc_retry_after(resp)
            if any(d in low for d in _DAU_HIEU_HET_QUOTA):
                _danh_dau_het_quota(_cau_hinh_tran("consensus_max_calls_per_month", 10))
                return self._chot(ConsensusLoi(
                    f"[consensus] {ma}: HẾT lượt bao gồm của tháng trên tài khoản Consensus (API và MCP "
                    f"dùng chung hạn mức) — không gọi thêm đến hết tháng. {chi_tiet}".strip(),
                    "het_quota", ma_http=status, pham_vi="consensus"))
            dau_hieu_ro = any(d in low for d in _DAU_HIEU_QUA_NHANH) or retry_after is not None
            if dau_hieu_ro:
                # 429 "Too many requests" bị từ chối TRƯỚC khi tìm, không có bài nào trả về (tài liệu: 1 lượt cho mỗi
                # 100 bài TRẢ VỀ) -> không tốn lượt: hoàn bộ đếm tháng.
                # Thân không nhận ra được thì KHÔNG hoàn (thận trọng).
                _hoan_ngan_sach(ca_lan_chay=False)
            ghi_chu = ("" if dau_hieu_ro
                       else " (thân phản hồi không nhận ra được — coi là giới hạn tốc độ, KHÔNG chốt)")
            return ConsensusLoi(
                f"[consensus] {ma}: vượt giới hạn 1 request/giây của Consensus{ghi_chu}. "
                f"{chi_tiet}".strip(), "gioi_han_toc_do", ma_http=status, retry_after=retry_after)
        if status in (400, 422):
            return ConsensusLoi(
                f"[consensus] {ma}: tham số bị Consensus từ chối (lỗi lập trình/cấu hình, không retry). "
                f"{chi_tiet}".strip(), "tham_so_sai", ma_http=status)
        if status is not None and status >= 500:
            return ConsensusLoi(
                f"[consensus] {ma}: lỗi phía Consensus (chưa rõ có bị tính lượt hay không nên KHÔNG hoàn "
                f"bộ đếm). {chi_tiet}".strip(), "khac", ma_http=status)
        return ConsensusLoi(f"[consensus] {ma}: Consensus trả lỗi không thuộc danh mục đã biết. "
                            f"{chi_tiet}".strip(), "khac", ma_http=status)

    def _kiem_phan_hoi(self, data: Any, query: str,
                       params: Dict[str, Any]) -> Tuple[List[Any], Dict[str, Any]]:
        """Trả (results, payload đã che); ([], ...) chỉ khi `results` là danh sách RỖNG hợp lệ.
        NÉM ConsensusLoi(phan_hoi_khong_hop_le) cho mọi lệch schema."""
        if not isinstance(data, dict):
            self._xoa_cache(params)
            raise ConsensusLoi(
                f"[consensus] phản hồi không phải JSON object (kiểu {type(data).__name__}).",
                "phan_hoi_khong_hop_le")
        sach = _sach_payload(data)
        ket_qua = sach.get("results")
        if isinstance(ket_qua, list):
            self.save_raw(query, sach)
            if not ket_qua:
                self.stats["khong_co_ket_qua"] += 1
            return ket_qua, sach
        # 'results' vắng hoặc sai kiểu: Consensus có thể đã đổi schema — NÉM, không coi là rỗng.
        self._xoa_cache(params)
        self.save_raw(query, sach)
        khoa_top = sorted({_sach_chuoi(k) for k in sach})[:15]
        chi_tiet = _sach_chuoi(" | ".join(_gom_chuoi(sach)))[:_TRAN_CHUOI_LOI]
        raise ConsensusLoi(
            f"[consensus] phản hồi 200 thiếu 'results' hoặc 'results' không phải danh sách (kiểu "
            f"{type(ket_qua).__name__}) — nghi Consensus đổi cấu trúc; đã tốn 1 lượt. Khoá cấp trên: "
            f"{khoa_top}. {chi_tiet}".strip(), "phan_hoi_khong_hop_le")

    # ------------------------------------------------------------------ ánh xạ bản ghi
    def _anh_xa(self, item: Any, query: str, clinical_area: Optional[str], boi_canh: Dict[str, Any],
                vi_tri: int) -> Tuple[Optional[RawRecord], Optional[str]]:
        """results[i] -> RawRecord. Trả (None, khoá_stats) khi bỏ; dữ liệu đã được che khoá."""
        if not isinstance(item, dict):
            return None, "bo_qua_khong_phai_dict"
        item = _sach_payload(item)
        tieu_de = _chuoi(item.get("title"))
        if not tieu_de:
            return None, "bo_qua_thieu_tieu_de"
        co: List[str] = []

        tac_gia_ds: List[str] = []
        ds = item.get("authors")
        if isinstance(ds, list):
            for a in ds:
                ten = _chuoi(a) if isinstance(a, str) else (
                    _chuoi(a.get("name")) if isinstance(a, dict) else None)
                if ten:
                    tac_gia_ds.append(ten)
        elif isinstance(ds, str):
            ten = _chuoi(ds)
            if ten:
                tac_gia_ds.append(ten)
        tac_gia = ", ".join(tac_gia_ds) if tac_gia_ds else None

        doi, ly_do_doi = _lam_sach_doi(item.get("doi"))
        if ly_do_doi:
            co.append(ly_do_doi)

        link_tho = item.get("url")
        url = link_tho.strip() if isinstance(link_tho, str) and link_tho.strip().lower().startswith(
            ("http://", "https://")) else None
        if url is None:
            co.append("no_link")  # không tự dựng URL

        ngay, co_ngay = _ngay_xuat_ban(item.get("publish_year"), item.get("publish_date"))
        co.extend(co_ngay)

        # takeaway là câu kết luận do AI của Consensus viết: KHÔNG phải abstract, KHÔNG phải chứng cứ.
        takeaway = _chuoi(item.get("takeaway"), 2000)
        abstract_tho = item.get("abstract")
        abstract = abstract_tho.strip() if isinstance(abstract_tho, str) and abstract_tho.strip() else None
        if abstract is not None and takeaway is not None and (
                _KHOANG_TRANG_RE.sub(" ", abstract).lower() == takeaway.lower()):
            abstract = None  # chống việc takeaway bị lặp vào trường abstract
            co.append("abstract_equals_takeaway")
        if abstract is None:
            co.append("no_abstract")

        la_preprint = item.get("is_preprint") if isinstance(item.get("is_preprint"), bool) else None
        if la_preprint:
            co.append("preprint")

        quartile = _so_nguyen(item.get("sjr_best_quartile"))
        raw: Dict[str, Any] = {
            "nguon_phat_hien": self.name,
            "vi_tri": vi_tri,
            "takeaway": takeaway,
            "consensus_study_type": _chuoi(item.get("study_type"), 100),
            "citation_count": _so_nguyen(item.get("citation_count")),
            "sjr_best_quartile": quartile if quartile in (1, 2, 3, 4) else None,
            "sample_size": _so_nguyen(item.get("sample_size")),
            "is_preprint": la_preprint,
            "publisher_name": _chuoi(item.get("publisher_name"), 255),
            "publish_date_goc": _chuoi(item.get("publish_date"), 64),
            "bo_loc_truy_van": {k: v for k, v in boi_canh.items() if k != "ngay_lay"},
            "ngay_lay": boi_canh.get("ngay_lay"),
            "api_endpoint": SEARCH,
            "co": co,
            "luu_y": ("Kết quả khám phá từ Consensus: takeaway là câu do AI của Consensus viết, KHÔNG "
                      "phải abstract/chứng cứ; study_type của Consensus chỉ là gợi ý (chỉ được hạ, "
                      "không nâng); chưa xác minh bằng sổ đăng ký; chưa kiểm rút bài."),
        }
        if ly_do_doi == "invalid_doi":
            raw["doi_goc"] = _chuoi(item.get("doi"), 300)

        rec = RawRecord(
            source=self.name, title=tieu_de,
            authors=tac_gia,
            journal_or_organization=_chuoi(item.get("journal_name"), _TRAN_TAP_CHI),
            publication_date=ngay,
            doi=doi,
            url=url,
            abstract=abstract,
            # study_type CHỈ 'preprint' (tín hiệu an toàn, hạ điểm); KHÔNG suy từ tiêu đề hay từ nhãn
            # study_type của Consensus — xem docstring module.
            study_type="preprint" if la_preprint else None,
            clinical_area=clinical_area,
            ingest_query=query, api_endpoint=SEARCH,
            raw=raw,
        )
        return rec, None
