"""Trợ lý xác minh Scite qua endpoint CÔNG KHAI papers/tallies — thêm 20/09/2026, theo yêu cầu
bác sĩ ("tôi cũng đã kết nối Scite, hãy xây cơ chế tương tự Consensus và Scholar").

VAI TRÒ (đọc kỹ trước khi dùng): đây là LỚP XÁC MINH bổ sung, KHÔNG phải nguồn khám phá và KHÔNG
phải một tầng của thang dự phòng (ladder Consensus -> SerpApi Scholar). Lớp này KHÔNG kế thừa
`SourceClient`, không có `search()`, không nằm trong `get_enabled_sources()` hay
`get_fallback_sources()`. Nó chỉ được gọi từ `app/services/fallback_verification.py`, và chỉ cho
những hit MÀ MỘT TẦNG DỰ PHÒNG VỪA TÌM THẤY (đã có DOI xác nhận từ Crossref) — tức nằm trong đúng
đường gated "chỉ khi nguồn tin cậy chưa đủ chứng cứ". Không có lời gọi Scite nào ngoài đường đó.
Hai việc duy nhất: (1) đọc cờ `retracted`/`editorialNotices` của bản ghi bài để cổng rút-bài/thông
báo biên tập của bộ xác minh có thêm một nguồn; (2) ghi lại số trích dẫn ủng hộ/phản bác
(`tallies`) làm THÔNG TIN — tally KHÔNG BAO GIỜ đổi điểm, tier, phân loại hay quyết định giữ/loại.

VÌ SAO KHÔNG DÙNG ENDPOINT SEARCH CỦA SCITE (theo tài liệu docs.scite.ai, đọc 20/09/2026):
  • Search đòi khoá API gói Pro. Khoá Pro tự đăng ký chỉ dành cho ĐÁNH GIÁ (evaluation), và tài liệu
    Scite ghi rõ "commercial or research use of Search requires a separate license agreement" — dùng
    Search trong pipeline nghiên cứu này cần một thoả thuận cấp phép riêng mà bác sĩ chưa có; với
    khoá tự đăng ký, các đoạn trích (snippet) còn bị che (redacted).
  • Kết nối Scite của bác sĩ là kết nối MCP (tín dụng dành cho trợ lý AI: gói Basic 250 tín dụng,
    Pro 2.500 tín dụng), KHÔNG phải một khoá API REST cho engine này; tín dụng MCP và giới hạn REST
    là hai thứ tách biệt. Gói Basic (20 USD/tháng) không có khoá REST.
  • Vì vậy chỉ dùng hai endpoint CÔNG KHAI, không khoá, không tài khoản: GET
    https://api.scite.ai/papers/{doi} và GET https://api.scite.ai/tallies/{doi}. KHÔNG có khoá API
    nào trong module này, KHÔNG BAO GIỜ gửi header Authorization (`__init__` còn chặn cả việc
    `requests` tự thêm Authorization từ ~/.netrc).
  • ĐIỂM MỞ RỘNG: nếu sau này bác sĩ có thoả thuận cấp phép và khoá, một tầng khám phá
    `SciteSearchClient(SourceClient)` nên nằm ở MỘT MODULE RIÊNG (vd `scite_search.py`), tái dùng
    `SciteLoi` và `chuan_hoa_doi` của module này, và được thêm vào thang bằng `get_fallback_sources()`.
    KHÔNG xây tầng đó bây giờ và KHÔNG thêm khoá/Search vào lớp này.

HÌNH DẠNG PHẢN HỒI ĐÃ THẤY (một lượt GET công khai thật cho mỗi endpoint, đúng ví dụ của tài liệu,
DOI 10.1038/nature12373): papers -> {"id", "doi", "type", "title", "abstract", "authors", "keywords",
"year", "shortJournal", "publisher", "issue", "volume", "page", "retracted": false, "memberId",
"issns", "editorialNotices": [], "journalSlug", "journal", "preprintLinks", "publicationLinks",
"normalizedTypes"}; tallies -> {"total", "supporting", "contradicting", "mentioning",
"unclassified", "doi", "citingPublications"} (total = số câu trích dẫn, citingPublications = số bài
trích dẫn khác nhau). Lỗi trả JSON {"detail": ...}: 401 (cần khoá), 403 (thiếu quyền), 404 (không có
DOI), 422 (kiểm tra tham số), 429 (giới hạn tốc độ; kèm Retry-After / RateLimit-*).

CHUẨN HOÁ ĐẦU RA:
  • `lay_bai(doi)` -> {doi, title, year, journal, retracted, editorial_notices} hoặc None nếu 404.
    `retracted` là BA TRẠNG THÁI: True / False / None. None = phản hồi KHÔNG nói rõ (thiếu khoá, null,
    hoặc kiểu lạ) — người gọi KHÔNG được coi None là "không bị rút bài"; im lặng khác an toàn.
    `editorial_notices` là danh sách dict đã lược sạch (giữ nguyên khoá/giá trị gốc, cắt chuỗi dài,
    giới hạn độ sâu); phần tử không phải dict được bọc thành {"text": ...}; phần tử rỗng bị bỏ. Cấu
    trúc thật của phần tử CHƯA xác minh (trong ví dụ của tài liệu danh sách rỗng) nên module KHÔNG tự
    phân loại "rút bài / đính chính": việc đó thuộc bộ xác minh, và phải xử lý thận trọng khi không
    hiểu cấu trúc.
  • `lay_tally(doi)` -> {doi, total, supporting, contradicting, mentioning, unclassified,
    citingPublications} giữ NGUYÊN tên khoá của API; `supporting`/`contradicting` bắt buộc là số
    nguyên >= 0 (thiếu/sai kiểu -> phan_hoi_khong_hop_le), các trường còn lại sai kiểu -> None.
  • DOI trong phản hồi PHẢI khớp DOI đã hỏi (sau khi chuẩn hoá, không phân biệt hoa/thường), nếu
    không -> phan_hoi_khong_hop_le: kết luận rút-bài của bản ghi bài khác không được gán cho hit này.
  • 404 -> trả None (tin "Scite không có DOI này", KHÔNG phải "đã kiểm sạch"; không thử lại cùng giá
    trị). Cũng nên nhớ: 404 không phân biệt được "DOI vắng" với "đường dẫn API đã đổi" (chưa xác
    minh) — `stats["khong_tim_thay"]` bằng đúng số lời gọi là dấu hiệu đáng ngờ.

LỖI CÓ PHÂN LOẠI (`SciteLoi`, là RuntimeError, thuộc tính `loai`): khong_tim_thay | gioi_han_toc_do |
loi_phia_scite | phan_hoi_khong_hop_le | khac. (`khong_tim_thay` nằm trong bộ từ vựng nhưng `lay_*`
trả None cho 404 thay vì ném.) `khac` gồm: DOI không hợp lệ (KHÔNG gọi mạng), cờ
ENABLE_SCITE_VERIFICATION tắt, timeout/mất mạng, và 401/403/4xx bất ngờ. Thông báo KHÔNG chứa URL,
tham số hay header. Người gọi phải coi mọi `SciteLoi` là "Scite CHƯA kiểm được" và ghi
raw["scite"]={"da_kiem": False, "ly_do": ...} — không bao giờ khẳng định một lượt kiểm chưa xảy ra.

TỐC ĐỘ VÀ ĐỘ BỀN: `HttpClient(max_retries=1, cache_ttl=0)` — không cache đĩa (cờ rút bài phải
tươi; cũng không lưu kết quả Scite xuống OneDrive), tối đa MỘT lần thử lại (429/5xx/mất mạng; 429
tôn trọng Retry-After, tối đa 30 giây theo HttpClient, KHÔNG có jitter); giãn cách lịch sự mặc định
0,5 giây giữa hai request tới api.scite.ai (tiêm được qua `khoang_cach_giay`). Cầu dao (circuit
breaker) theo instance: một 429 còn sót sau lần thử lại, hoặc 3 lỗi hạ tầng liên tiếp, thì trong 120
giây các lời gọi kế tiếp bị từ chối NGAY (cùng `loai`, không gửi request) — để lượt xác minh hàng
chục hit không treo hàng giờ khi Scite đang giới hạn tốc độ.

CHƯA XÁC MINH (KHÔNG được coi là đã biết):
  • Điều khoản sử dụng và giới hạn tốc độ của các endpoint CÔNG KHAI papers/tallies cho việc gọi tự
    động/hàng loạt và cho việc lưu kết quả (tài liệu chỉ nói giới hạn theo endpoint/tài khoản, hiện
    qua header RateLimit-* / X-RateLimit-*-Minute; giới hạn của endpoint công khai không được công
    bố). Vì vậy: gọi ít (tối đa 2 request mỗi hit, chỉ hit của tầng dự phòng), giãn cách, một lần
    thử lại, cầu dao, và không lưu cache.
  • Lược đồ chính xác của phần tử `editorialNotices` (rỗng trong ví dụ) và tập giá trị của trường
    `type`; `retracted` có bao giờ là null hay không (vì thế mới có trạng thái None).
  • Điều kiện khoá của các biến thể batch/POST (không dùng).
  • Việc DOI có ký tự đặc biệt (dấu ngoặc, `;`, `<`, `>`) được máy chủ Scite giải mã phần trăm
    đúng như mong đợi hay không: module mã hoá phần trăm mọi ký tự ngoài `A-Za-z0-9_.-~/`, giữ nguyên
    dấu `/` như ví dụ đã thấy của tài liệu (papers/10.1038/nature12373).
  • Hành vi khi Scite chuyển hướng (redirect): `HttpClient` theo chuyển hướng mặc định của requests;
    `rebuild_auth` đã bị vô hiệu để không Authorization nào bị dựng lại, nhưng không ép được đích
    chuyển hướng.
"""
from __future__ import annotations

import re
from datetime import date
from time import monotonic
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import quote

import requests

from app.config import settings
from app.utils.http import HttpClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

__all__ = ["SciteClient", "SciteLoi", "chuan_hoa_doi", "GOC_SCITE"]

GOC_SCITE = "https://api.scite.ai"
_DUONG_BAI = GOC_SCITE + "/papers/"
_DUONG_TALLY = GOC_SCITE + "/tallies/"

_KHOANG_CACH_MAC_DINH = 0.5      # giây giữa hai request tới api.scite.ai (giới hạn công khai chưa được công bố)
_NGUONG_LOI_LIEN_TIEP = 3        # số lỗi hạ tầng liên tiếp thì mở cầu dao
_THOI_GIAN_TAM_DUNG = 120.0      # giây cầu dao mở: từ chối ngay, không gửi request
_TRAN_DOI = 255                  # cột doi String(255) — quá dài coi như không hợp lệ
_TRAN_CHUOI = 500                # cắt chuỗi trong editorialNotices/thông báo lỗi
_TRAN_SO_THONG_BAO = 100
_UA = "medical-ebm-automation/0.1 (scite-public-verification)"   # KHÔNG kèm email vận hành viên

_TIEN_TO_DOI_RE = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.IGNORECASE)
_DOI_RE = re.compile(r"10\.[0-9]{4,9}/\S+")     # [0-9], không dùng \d (khớp cả chữ số Unicode)

_LOAI_HOP_LE = frozenset({"khong_tim_thay", "gioi_han_toc_do", "loi_phia_scite",
                          "phan_hoi_khong_hop_le", "khac"})


class SciteLoi(RuntimeError):
    """Lỗi có phân loại của trợ lý Scite công khai.

    `loai`: khong_tim_thay | gioi_han_toc_do | loi_phia_scite | phan_hoi_khong_hop_le | khac.
    Thông báo KHÔNG BAO GIỜ chứa URL/params/header. Mọi `SciteLoi` nghĩa là "Scite CHƯA kiểm được".
    """

    def __init__(self, thong_bao: str, loai: str = "khac") -> None:
        super().__init__(thong_bao)
        self.loai = loai if loai in _LOAI_HOP_LE else "khac"


# --------------------------------------------------------------------------- tiện ích

def _rut_gon(text: Any, tran: int = 120) -> str:
    """Chuỗi một dòng, đã bỏ ký tự điều khiển/xuống dòng (chống làm giả dòng log), cắt ngắn."""
    return " ".join(str(text).split())[:tran]


def chuan_hoa_doi(doi: Any) -> str:
    """Kiểm tra và chuẩn hoá DOI TRƯỚC KHI dùng làm phần đường dẫn URL; ném `SciteLoi("khac")` nếu sai.

    Bỏ tiền tố "https://doi.org/", "https://dx.doi.org/", "doi:", bỏ khoảng trắng đầu/cuối, chuyển
    chữ thường (DOI không phân biệt hoa/thường; dữ liệu Scite dùng chữ thường). Hợp lệ khi: dạng
    `10.<4-9 chữ số>/<hậu tố>`, hậu tố không rỗng, không có khoảng trắng/ký tự điều khiển/ký tự
    không in được ở giữa, dài <= 255, và KHÔNG có đoạn đường dẫn "." hay ".." (urllib3 sẽ chuẩn hoá
    dot-segment làm URL rời khỏi /papers/ hoặc /tallies/). Ký tự lạ vẫn hợp lệ (DOI thật có thể chứa
    `<`, `>`, `;`, dấu ngoặc, `?`, `#`) vì sẽ được mã hoá phần trăm ở `_url`, không bao giờ thành
    query/fragment.
    """
    ly_do: Optional[str] = None
    s = ""
    if not isinstance(doi, str):
        ly_do = f"DOI phải là chuỗi (nhận {type(doi).__name__})"
    else:
        s = _TIEN_TO_DOI_RE.sub("", doi.strip()).strip().lower()
        if not s:
            ly_do = "DOI rỗng"
        elif len(s) > _TRAN_DOI:
            ly_do = f"DOI dài quá {_TRAN_DOI} ký tự"
        elif not s.isprintable():
            ly_do = "DOI chứa ký tự điều khiển/không in được"
        elif _DOI_RE.fullmatch(s) is None:
            ly_do = "DOI không đúng dạng 10.<4-9 chữ số>/<hậu tố> hoặc có khoảng trắng"
        elif any(doan in (".", "..") for doan in s.split("/")):
            ly_do = "DOI có đoạn đường dẫn '.' hoặc '..'"
    if ly_do is not None:
        raise SciteLoi(f"[scite_public] DOI không hợp lệ — KHÔNG gọi Scite ({ly_do}): "
                       f"{_rut_gon(repr(doi), 80)}", "khac")
    return s


def _url(goc: str, doi_da_chuan_hoa: str) -> str:
    """`goc` + DOI mã hoá phần trăm. Giữ `/` (đúng ví dụ tài liệu), mã hoá MỌI ký tự khác ngoài
    A-Za-z0-9_.-~ (kể cả `?`, `#`, `%`, khoảng trắng, Unicode) nên không thể sinh query/fragment."""
    url = goc + quote(doi_da_chuan_hoa, safe="/")
    if not url.startswith((_DUONG_BAI, _DUONG_TALLY)):   # phòng thủ: không bao giờ rời api.scite.ai
        raise SciteLoi("[scite_public] URL dựng ra không thuộc api.scite.ai — huỷ.", "khac")
    return url


def _so_nguyen(v: Any) -> Optional[int]:
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, str) and v.strip().isascii() and v.strip().isdigit():
        return int(v.strip())
    return None


def _so_khong_am(v: Any) -> Optional[int]:
    n = _so_nguyen(v)
    return n if n is not None and n >= 0 else None


def _nam(v: Any) -> Optional[int]:
    n = _so_nguyen(v)
    return n if n is not None and 1000 <= n <= date.today().year + 2 else None


def _chuoi_hoac_none(v: Any) -> Optional[str]:
    if not isinstance(v, str):
        return None
    s = " ".join(v.split())
    return s or None


def _ba_trang_thai(v: Any) -> Optional[bool]:
    """True / False / None (không rõ). KHÔNG bao giờ suy None thành False."""
    if isinstance(v, bool):
        return v
    if isinstance(v, int) and v in (0, 1):
        return bool(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s == "true":
            return True
        if s == "false":
            return False
    return None


def _lam_sach(obj: Any, do_sau: int = 0) -> Any:
    """Bản sao JSON-an-toàn: giữ khoá/giá trị gốc, cắt chuỗi, giới hạn số phần tử; quá sâu thì
    chuyển thành chuỗi (không bỏ) để chữ như "retraction" ở tầng sâu vẫn còn cho bộ phân loại."""
    if do_sau > 4:
        return _rut_gon(obj, _TRAN_CHUOI)
    if isinstance(obj, dict):
        return {_rut_gon(k, 64): _lam_sach(v, do_sau + 1) for k, v in list(obj.items())[:30]}
    if isinstance(obj, (list, tuple)):
        return [_lam_sach(v, do_sau + 1) for v in list(obj)[:30]]
    if isinstance(obj, str):
        return obj.strip()[:_TRAN_CHUOI]
    if obj is None or isinstance(obj, (bool, int, float)):
        return obj
    return _rut_gon(obj, _TRAN_CHUOI)


def _chuan_hoa_thong_bao(v: Any) -> List[Dict[str, Any]]:
    """`editorialNotices` -> danh sách dict đã lược sạch. Không phải list mà không rỗng -> coi là MỘT
    thông báo (bảo thủ: không nuốt cấu trúc lạ); phần tử rỗng bị bỏ."""
    if v is None:
        return []
    muc = v if isinstance(v, list) else [v]
    out: List[Dict[str, Any]] = []
    for m in muc:
        if m is None or (isinstance(m, (str, dict, list, tuple)) and len(m) == 0):
            continue
        if isinstance(m, str) and not m.strip():
            continue
        if isinstance(m, dict):
            out.append(_lam_sach(m))
        else:
            out.append({"text": _rut_gon(_lam_sach(m), _TRAN_CHUOI)})
        if len(out) >= _TRAN_SO_THONG_BAO:
            break
    return out


def _khop_doi(doi_tra_ve: Any, doi_yeu_cau: str) -> bool:
    if not isinstance(doi_tra_ve, str):
        return False
    return _TIEN_TO_DOI_RE.sub("", doi_tra_ve.strip()).strip().lower() == doi_yeu_cau


def _chuan_hoa_bai(data: Any, doi_yeu_cau: str) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise SciteLoi(f"[scite_public] papers: phản hồi không phải JSON object (kiểu "
                       f"{type(data).__name__}).", "phan_hoi_khong_hop_le")
    if not _khop_doi(data.get("doi"), doi_yeu_cau):
        raise SciteLoi("[scite_public] papers: phản hồi thiếu DOI hoặc DOI khác DOI đã hỏi — không gán "
                       "kết luận của bản ghi khác cho hit này.", "phan_hoi_khong_hop_le")
    return {
        "doi": doi_yeu_cau,
        "title": _chuoi_hoac_none(data.get("title")),
        "year": _nam(data.get("year")),
        "journal": _chuoi_hoac_none(data.get("journal")),
        "retracted": _ba_trang_thai(data.get("retracted")),
        "editorial_notices": _chuan_hoa_thong_bao(data.get("editorialNotices")),
    }


def _chuan_hoa_tally(data: Any, doi_yeu_cau: str) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise SciteLoi(f"[scite_public] tallies: phản hồi không phải JSON object (kiểu "
                       f"{type(data).__name__}).", "phan_hoi_khong_hop_le")
    if not _khop_doi(data.get("doi"), doi_yeu_cau):
        raise SciteLoi("[scite_public] tallies: phản hồi thiếu DOI hoặc DOI khác DOI đã hỏi.",
                       "phan_hoi_khong_hop_le")
    ung_ho = _so_khong_am(data.get("supporting"))
    phan_bac = _so_khong_am(data.get("contradicting"))
    if ung_ho is None or phan_bac is None:
        raise SciteLoi("[scite_public] tallies: 'supporting'/'contradicting' thiếu hoặc không phải số "
                       "nguyên >= 0.", "phan_hoi_khong_hop_le")
    return {
        "doi": doi_yeu_cau,
        "total": _so_khong_am(data.get("total")),
        "supporting": ung_ho,
        "contradicting": phan_bac,
        "mentioning": _so_khong_am(data.get("mentioning")),
        "unclassified": _so_khong_am(data.get("unclassified")),
        "citingPublications": _so_khong_am(data.get("citingPublications")),
    }


def _khong_xac_thuc(request: Any) -> Any:
    """`session.auth` giả: trả nguyên request. Việc chỉ cần `session.auth` khác None là đủ để
    `requests` KHÔNG tự thêm Authorization từ ~/.netrc cho request đầu tiên."""
    return request


def _bo_qua_dung_lai_xac_thuc(prepared_request: Any, response: Any = None) -> None:
    """Thay `Session.rebuild_auth`: khi chuyển hướng, requests có thể dựng lại Authorization từ
    ~/.netrc — ở đây luôn gỡ header đó."""
    try:
        prepared_request.headers.pop("Authorization", None)
    except Exception:  # pragma: no cover
        pass


# --------------------------------------------------------------------------- client

class SciteClient:
    """Trợ lý đọc endpoint công khai papers/tallies của Scite (KHÔNG phải SourceClient, KHÔNG phải tầng).

    Không có khoá API, không header Authorization. Xem docstring module về vai trò, giới hạn và các
    mục chưa xác minh. Mọi lỗi -> `SciteLoi` có `loai`; 404 -> None.
    """

    def __init__(self, *, http: Optional[Any] = None, khoang_cach_giay: Optional[float] = None,
                 dong_ho: Optional[Callable[[], float]] = None) -> None:
        """`http`: thay HttpClient (chỉ để test); `khoang_cach_giay`: giãn cách tối thiểu giữa hai
        request tới api.scite.ai (mặc định 0,5; 0 = không giãn cách); `dong_ho`: đồng hồ đơn điệu
        cho cầu dao (mặc định time.monotonic)."""
        if khoang_cach_giay is not None and (isinstance(khoang_cach_giay, bool)
                                             or not isinstance(khoang_cach_giay, (int, float))
                                             or khoang_cach_giay < 0):
            raise ValueError(f"khoang_cach_giay phải là số >= 0 hoặc None, nhận {khoang_cach_giay!r}")
        if http is None:
            khoang = _KHOANG_CACH_MAC_DINH if khoang_cach_giay is None else float(khoang_cach_giay)
            # max_retries=1: tối đa MỘT lần thử lại. cache_ttl=0: không cache đĩa (cờ rút bài phải tươi,
            # không lưu kết quả Scite xuống OneDrive). User-Agent riêng để KHÔNG gửi email vận hành viên
            # (HttpClient mặc định nhét mailto: vào UA) sang một dịch vụ bên thứ ba không cần nó.
            http = HttpClient(default_headers={"User-Agent": _UA}, cache_ttl=0,
                              min_interval=khoang, max_retries=1)
        self.http = http
        self._chan_xac_thuc(http)
        self._dong_ho: Callable[[], float] = dong_ho or monotonic
        self._tam_dung_den: Optional[float] = None
        self._loai_tam_dung = "khac"
        self._so_loi_lien_tiep = 0
        self.stats: Dict[str, int] = {
            "so_lan_goi_bai": 0, "so_lan_goi_tally": 0, "khong_tim_thay": 0, "gioi_han_toc_do": 0,
            "loi_phia_scite": 0, "phan_hoi_khong_hop_le": 0, "loi_khac": 0, "bo_qua_tam_dung": 0,
        }

    @staticmethod
    def _chan_xac_thuc(http: Any) -> None:
        """Bảo đảm KHÔNG Authorization nào rời máy: gỡ header nếu có, chặn netrc tự thêm ở request đầu
        và ở lần dựng lại sau chuyển hướng. HttpClient của repo không bao giờ đặt Authorization."""
        session = getattr(http, "session", None)
        if session is None:
            return
        try:
            session.headers.pop("Authorization", None)
            session.auth = _khong_xac_thuc
            session.rebuild_auth = _bo_qua_dung_lai_xac_thuc
        except Exception as exc:  # pragma: no cover
            logger.warning("[scite_public] không đặt được chặn Authorization cho session: %s",
                           type(exc).__name__)

    # ------------------------------------------------------------------ API công khai
    def lay_bai(self, doi: str) -> Optional[Dict[str, Any]]:
        """GET /papers/{doi} -> {doi, title, year, journal, retracted, editorial_notices} hoặc None (404).

        `retracted` True/False/None (None = KHÔNG rõ, đừng coi là sạch). Ném `SciteLoi` cho mọi lỗi
        khác (xem docstring module) — người gọi ghi "Scite chưa kiểm được", không bao giờ bịa kết quả.
        """
        return self._truy_van(_DUONG_BAI, chuan_hoa_doi(doi), _chuan_hoa_bai, "bai")

    def lay_tally(self, doi: str) -> Optional[Dict[str, Any]]:
        """GET /tallies/{doi} -> {doi, total, supporting, contradicting, mentioning, unclassified,
        citingPublications} hoặc None (404). Chỉ để GHI NHẬN, không đổi điểm/tier/quyết định."""
        return self._truy_van(_DUONG_TALLY, chuan_hoa_doi(doi), _chuan_hoa_tally, "tally")

    # ------------------------------------------------------------------ lõi
    def _truy_van(self, goc: str, doi: str, chuan_hoa: Callable[[Any, str], Dict[str, Any]],
                  ten: str) -> Optional[Dict[str, Any]]:
        self._kiem_cho_phep()
        self._kiem_tam_dung()
        url = _url(goc, doi)
        self.stats["so_lan_goi_" + ten] += 1

        loi: Optional[SciteLoi] = None
        dem_vao_cau_dao = False
        khong_thay = False
        ket_qua: Optional[Dict[str, Any]] = None
        # Dựng lỗi TRONG khối except nhưng ném ở NGOÀI: __context__ không giữ HTTPError/response.
        try:
            data = self.http.get_json(url)
        except requests.HTTPError as exc:
            loi, dem_vao_cau_dao = self._loi_tu_http(exc, ten)
            khong_thay = loi is None
        except ValueError:
            loi, dem_vao_cau_dao = SciteLoi(
                f"[scite_public] {ten}: phản hồi không phải JSON hợp lệ.", "phan_hoi_khong_hop_le"), True
        except Exception as exc:
            loi, dem_vao_cau_dao = self._loi_tu_ngoai_le(exc, ten), True
        else:
            try:
                ket_qua = chuan_hoa(data, doi)
            except SciteLoi as e:
                loi, dem_vao_cau_dao = e, True

        if khong_thay:
            self.stats["khong_tim_thay"] += 1
            self._ghi_nhan_thanh_cong()      # 404 là phản hồi hợp lệ của máy chủ, không phải sự cố
            logger.debug("[scite_public] %s: 404 (Scite không có DOI %s)", ten, _rut_gon(doi, 80))
            return None
        if loi is not None:
            self.stats[loi.loai if loi.loai != "khac" else "loi_khac"] += 1
            self._ghi_nhan_that_bai(loi, dem_vao_cau_dao)
            logger.warning("[scite_public] %s: Scite CHƯA kiểm được DOI %s (%s): %s", ten,
                           _rut_gon(doi, 80), loi.loai, _rut_gon(loi, 200))
            raise loi
        self._ghi_nhan_thanh_cong()
        return ket_qua

    def _kiem_cho_phep(self) -> None:
        """Cờ ENABLE_SCITE_VERIFICATION (mặc định True nếu setting chưa tồn tại). Tắt thì ném rõ ràng,
        KHÔNG trả None (None nghĩa là 404, sẽ bị hiểu nhầm là "Scite không có DOI này")."""
        if not getattr(settings, "enable_scite_verification", True):
            raise SciteLoi("[scite_public] ENABLE_SCITE_VERIFICATION đang tắt — không gọi Scite.", "khac")

    # ------------------------------------------------------------------ cầu dao
    def _kiem_tam_dung(self) -> None:
        if self._tam_dung_den is None:
            return
        if self._dong_ho() < self._tam_dung_den:
            self.stats["bo_qua_tam_dung"] += 1
            raise SciteLoi(
                f"[scite_public] tạm dừng {int(_THOI_GIAN_TAM_DUNG)} giây sau lỗi hạ tầng liên tiếp/giới "
                "hạn tốc độ của Scite — không gửi request; hit này Scite CHƯA kiểm được.",
                self._loai_tam_dung)
        self._tam_dung_den = None
        self._so_loi_lien_tiep = 0

    def _ghi_nhan_thanh_cong(self) -> None:
        self._so_loi_lien_tiep = 0

    def _ghi_nhan_that_bai(self, loi: SciteLoi, dem: bool) -> None:
        mo_cau_dao = False
        if loi.loai == "gioi_han_toc_do":
            mo_cau_dao = True          # 429 còn sót sau lần thử lại duy nhất: dừng ngay
        elif dem:
            self._so_loi_lien_tiep += 1
            mo_cau_dao = self._so_loi_lien_tiep >= _NGUONG_LOI_LIEN_TIEP
        if mo_cau_dao:
            self._tam_dung_den = self._dong_ho() + _THOI_GIAN_TAM_DUNG
            self._loai_tam_dung = loi.loai
            logger.warning("[scite_public] MỞ cầu dao %d giây (%s) — các lời gọi kế tiếp bị từ chối "
                           "ngay, không gửi request.", int(_THOI_GIAN_TAM_DUNG), loi.loai)

    # ------------------------------------------------------------------ phân loại lỗi
    def _loi_tu_http(self, exc: requests.HTTPError, ten: str) -> Tuple[Optional[SciteLoi], bool]:
        """HTTPError (có status) -> (SciteLoi, có_tính_vào_cầu_dao). 404 -> (None, False) = không tìm thấy.
        Thông báo KHÔNG chứa URL/params."""
        resp = getattr(exc, "response", None)
        status = getattr(resp, "status_code", None)
        if not isinstance(status, int):
            m = re.match(r"\s*(\d{3})\b", str(exc))
            status = int(m.group(1)) if m else None
        if status == 404:
            return None, False
        chi_tiet = ""
        try:
            body = resp.json() if resp is not None else None
            if isinstance(body, dict) and body.get("detail"):
                chi_tiet = _rut_gon(body["detail"], 200)
        except Exception:
            chi_tiet = ""
        ma = f"HTTP {status}" if status else "HTTP (không rõ mã)"
        if status == 429:
            return SciteLoi(f"[scite_public] {ten}: {ma} — vượt giới hạn tốc độ của Scite (đã thử lại tối đa "
                            f"1 lần theo Retry-After). {chi_tiet}".strip(), "gioi_han_toc_do"), True
        if status is not None and status >= 500:
            return SciteLoi(f"[scite_public] {ten}: {ma} — lỗi phía Scite. {chi_tiet}".strip(),
                            "loi_phia_scite"), True
        if status in (401, 403):
            return SciteLoi(f"[scite_public] {ten}: {ma} — endpoint công khai bất ngờ đòi xác thực/quyền; "
                            f"KHÔNG gửi khoá (chính sách Scite có thể đã đổi). {chi_tiet}".strip(), "khac"), True
        # 400/422/4xx khác: lỗi theo giá trị DOI hoặc tham số — không tính vào cầu dao.
        return SciteLoi(f"[scite_public] {ten}: {ma} — Scite từ chối yêu cầu. {chi_tiet}".strip(), "khac"), False

    def _loi_tu_ngoai_le(self, exc: Exception, ten: str) -> SciteLoi:
        """Lỗi KHÔNG có response. HttpClient bọc timeout/mất mạng/JSON hỏng thành RuntimeError chung,
        `__cause__` giữ nguyên nhân gốc: ValueError -> JSON hỏng. Thông báo chỉ nêu TÊN kiểu lỗi."""
        goc = exc.__cause__ if exc.__cause__ is not None else exc
        if isinstance(goc, ValueError):
            return SciteLoi(f"[scite_public] {ten}: phản hồi không phải JSON hợp lệ.", "phan_hoi_khong_hop_le")
        if isinstance(goc, requests.Timeout) or isinstance(exc, requests.Timeout):
            return SciteLoi(f"[scite_public] {ten}: hết thời gian chờ Scite ({type(goc).__name__}).", "khac")
        return SciteLoi(f"[scite_public] {ten}: lỗi mạng/không xác định khi gọi Scite "
                        f"({type(exc).__name__}, nguyên nhân {type(goc).__name__}).", "khac")
