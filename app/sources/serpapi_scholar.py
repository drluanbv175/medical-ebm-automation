"""Connector Google Scholar qua SerpApi — thêm 20/09/2026 theo yêu cầu bác sĩ
("tích hợp Google Scholar API qua SerpApi"), để mở rộng độ phủ KHÁM PHÁ chứng cứ
ngoài PubMed/Europe PMC/Crossref/OpenAlex/Semantic Scholar/Scopus hiện có.

Đây là nguồn KHÁM PHÁ (discovery), KHÔNG phải nguồn xác minh: Google Scholar không
có API chính thức, SerpApi là dịch vụ thương mại bóc kết quả tìm kiếm của Scholar
thành JSON. Mọi bản ghi từ đây chỉ là "gợi ý cần tra lại", không bao giờ là bằng
chứng đã xác minh.

KHÁC các nguồn miễn phí: mỗi lần gọi là MỘT search TÍNH PHÍ (gói Free 250 search/tháng,
50 search/giờ — số đo từ trang giá SerpApi 20/09/2026, chưa xác nhận bằng gọi thật).
Vì vậy: `enable_serpapi_scholar` mặc định TẮT (app/config.py), `search()` chặn SỚM bằng
lỗi rõ ràng nếu bật cờ mà thiếu SERPAPI_API_KEY, và có NGÂN SÁCH số lần gọi mỗi lượt
chạy (`serpapi_max_calls_per_run`, mặc định 8) — hết ngân sách thì NỔ TO chứ không
trả rỗng im lặng.

GIỚI HẠN ĐÃ BIẾT, ghi rõ để không ai hiểu nhầm độ tin cậy dữ liệu:
  • KHÔNG có abstract. `snippet` của Scholar chỉ là đoạn trích ngắn (thường bắt đầu/kết
    thúc bằng dấu "…") — được giữ trong `raw["snippet"]`, TUYỆT ĐỐI không nhét vào
    `abstract` (sẽ làm chấm điểm/báo cáo tưởng là tóm tắt thật).
  • KHÔNG có DOI/PMID/năm dạng trường riêng. `doi`/`pmid`/`pmcid` CHỈ được trích khi
    `link` thật sự là URL doi.org / trang PubMed / PMC / Europe PMC hoặc URL nhà xuất
    bản chứa nguyên văn "…/doi/10.xxxx/…" (regex neo chặt), sau đó BỎ phần URL dính vào
    DOI (dấu phiên bản "vN" của bioRxiv/medRxiv, mã bài toàn chữ số của Silverchair/OUP,
    đuôi "/tables/1", "/fulltext.html"…); không khớp thì để None —
    không bao giờ suy đoán, không tra ngược từ tiêu đề. Năm chỉ lấy từ chuỗi
    `publication_info.summary` theo quy tắc đã thử offline (xem `_tach_summary`); không
    chắc thì `publication_date=None` kèm cờ "year_unknown" trong `raw["co"]`, tuyệt
    đối không đoán tháng/ngày (Scholar chỉ có độ mịn NĂM; `since_date` được dịch sang
    `as_ylo` = năm, nên mỗi lượt vẫn trả các kết quả chồng lấp; bài có năm < năm since_date
    chỉ bị gắn cờ "before_since_year", không bị loại).
  • `study_type` LUÔN là None trừ khi có tín hiệu preprint (medRxiv/bioRxiv/SSRN/arXiv
    trong tên nơi đăng/tên miền/URL). Lý do đã chứng minh offline: bản ghi chỉ có tiêu
    đề mà bị suy `study_type` từ tiêu đề ("systematic review", "recommendations"…) sẽ
    được chấm eq=85–90, tier A, actionable dù không abstract, không định danh — rồi đi
    thẳng vào cảnh báo email/EBM_MASTER. Tiêu đề KHÔNG bao giờ được đưa vào suy luận
    study_type ở connector này.
  • `journal_or_organization` chỉ là TÊN NƠI ĐĂNG đã tách sạch từ `summary` (không dán
    nguyên chuỗi có tên tác giả — sẽ khớp nhầm bí danh tổ chức như GOLD/ASH ở
    authority.py); tên tác giả để riêng ở `authors`. Chuỗi thừa (tên miền/nhà xuất bản)
    nằm ở `raw["nha_xuat_ban_hoac_mien"]`.
  • Số trích dẫn (`cited_by.total`) là con số của Google Scholar, không chuẩn hoá/khử
    trùng; vắng thì None (không ép thành 0).
  • KHÔNG tham gia chuỗi 3 tầng kiểm rút bài (retraction_chain.py) — bản ghi Scholar
    luôn ở trạng thái "chưa kiểm rút bài", giống Scopus/OpenAlex/Crossref/Semantic Scholar.
  • Tiêu đề Scholar hay bị cắt bằng "…" → cờ "title_truncated"; dedup so tiêu đề với
    PubMed sẽ KHÔNG gộp được các bản ghi này (dedup không đụng dữ liệu lượt trước).
  • Chuỗi truy vấn đi qua SerpApi tới Google và bị SerpApi lưu 31 ngày (ToS/Privacy) —
    KHÔNG BAO GIỜ đưa PHI/PII bệnh nhân vào `query`, chỉ dùng chuỗi chủ đề y văn. Connector
    tự chặn: truy vấn khớp `contains_pii_text` (email, CCCD/mã bệnh nhân, SĐT, ngày sinh…)
    bị TỪ CHỐI (`tham_so_sai`) trước khi tốn ngân sách, thông báo không nhắc lại truy vấn.
  • Truy vấn mang thẻ trường PubMed ([ta]/[pt]/[cn]/[tiab]/[mh]/[majr]/[dp]) bị BỎ QUA (trả []
    kèm cảnh báo + `stats["bo_qua_cu_phap_pubmed"]`, không gọi HTTP, không tốn ngân sách): Source
    Log sẽ hiện ok/0 cho các truy vấn đó, số thật nằm ở `client.stats` và dòng log.
  • `max_results <= 0` trả [] ngay, không gọi SerpApi.
  • CHƯA xác nhận chạy thật (chưa có SERPAPI_API_KEY lúc viết): cấu trúc phản hồi, chuỗi
    lỗi, ý nghĩa `as_ylo` "bao gồm năm đó" đều dựng từ tài liệu SerpApi + tóm tắt nghiên
    cứu, chưa đối chiếu bằng `python run.py test-live serpapi_scholar "<từ khoá>"`.

PHÂN LOẠI LỖI (im lặng ≠ an toàn — ingestion coi exception là status "error" trong
Source Log và circuit-breaker dừng nguồn sau 3 lỗi liên tiếp; còn trả [] thì là "ok/0"):
  • Tín hiệu "không có kết quả" HỢP LỆ duy nhất → trả []: phản hồi HTTP 200, body có
    `error` = "Google hasn't returned any results for this query." (so khớp chuẩn hoá
    dấu nháy/hoa-thường), `search_metadata.status` khác "Error", và KHÔNG có
    `organic_results`. (Nếu vẫn có organic_results thì ưu tiên dữ liệu + cảnh báo.)
  • Mọi `error` khác trong body, hoặc status "Error"/"Queued"/"Processing" ở chế độ đồng
    bộ, hoặc HTTP 4xx/5xx có kèm response → NÉM `SerpApiLoi` (là RuntimeError) có phân
    loại: key sai (401) và hết quota ("run out of searches", 429) là lỗi CHỐT — nguồn bị
    dừng cho phần còn lại của lượt chạy, không gọi thêm (tránh đốt tiền/spam lỗi).
  • 200/Success nhưng không có `error` lẫn `organic_results` → "empty_unconfirmed": cảnh
    báo rõ + trả [] (không coi là "không có kết quả" đã xác nhận; ghi ở `self.stats`).
  • LỆCH SCHEMA (nghi SerpApi đổi cấu trúc) → NÉM `phan_hoi_khong_hop_le`, không trả [] im lặng:
    `organic_results` hiện diện nhưng KHÔNG phải danh sách, hoặc là danh sách không rỗng mà
    KHÔNG phần tử nào dùng được (thiếu `title`/không phải object). Trang lẫn phần tử tốt/xấu
    vẫn trả phần tốt.
  • Lỗi tầng vận chuyển KHÔNG có response (timeout/mất mạng/JSON hỏng) → cảnh báo + trả []
    theo quyết định D1 (không bao giờ bịa mock); telemetry của HttpClient (failure_count) vẫn
    khiến ingestion ghi Source Log = "error".
  • KHÔNG BAO GIỜ retry ở tầng HTTP: `HttpClient(max_retries=0)` — đúng MỘT request cho mỗi
    `search()` trên MỌI đường (thành công, 401/429/5xx, timeout, JSON hỏng), vì mỗi request là
    một search tính phí và bộ đếm ngân sách chỉ tính một lượt cho mỗi `search()`.

BẢO VỆ KHOÁ: `api_key` chỉ đi qua `params` của `self.http.get_json` (không header — tài
liệu SerpApi chỉ ghi query param), nên `HttpClient._redact` che nó trong log/exception/
telemetry. Mọi exception do connector này tự tạo KHÔNG chứa URL/params; chuỗi từ payload
được che thêm bằng chính giá trị khoá; payload trước khi `save_raw` và mọi trường đưa vào
RawRecord đều bị lược bỏ khoá `api_key` + che `api_key=…`. Cache GET của HttpClient
(data/raw/_http_cache/) ghi NGUYÊN payload TRƯỚC khi connector thấy: nếu bản đã che khác bản
thô (phản hồi có lặp lại khoá) thì `_che_cache` ghi đè tệp cache bằng bản đã che (vẫn giữ lợi
ích cache 24 giờ). Tài liệu SerpApi không cho thấy phản hồi tìm kiếm lặp lại khoá, nhưng chưa
kiểm bằng gọi thật. Lỗi HTTP được DỰNG trong khối except rồi NÉM ở ngoài nó để `__context__`
không giữ requests.HTTPError có `response.url` chứa khoá (biến cục bộ `khoa`/`params` trong
frame traceback vẫn còn — nằm ngoài phạm vi che của connector).

NGÂN SÁCH: bộ đếm THEO TIẾN TRÌNH, dùng chung mọi instance (ingestion dựng instance mới mỗi
lượt, research/manager.py và research/dossier.py tạo instance riêng — bộ đếm theo instance sẽ
để mỗi đường tự tiêu đủ trần). Để scheduler/dashboard chạy dài không bị khoá vĩnh viễn sau
lượt đầu, bộ đếm tự về 0 khi NGÀY (giờ máy) đổi; với run.py/cron (một tiến trình = một lượt)
nó đúng bằng "mỗi lượt chạy". Lượt trúng cache cục bộ của HttpClient (24 giờ) không tốn
search nên được hoàn lại ngân sách. Lỗi CHỐT (key sai / hết quota) thì theo INSTANCE.
"""
from __future__ import annotations

import re
import threading
from datetime import date
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote, urlparse

import requests

from app.config import settings
from app.core.policy_engine import contains_pii_text
from app.sources._fixtures import mock_records_for
from app.sources.base import RawRecord, SourceClient
from app.sources.classify_meta import infer_study_type
from app.utils.http import HttpClient, _cache_key, _cache_path, _redact, _write_cache
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
SEARCH = "https://serpapi.com/search.json"

_TRAN_NUM = 20          # SerpApi Google Scholar: num tối đa 20/lần gọi (mặc định 10)
_NAM_TOI_THIEU = 1500   # ngưỡng hợp lý cho năm xuất bản trích từ chuỗi summary
_TRAN_DOI = 200         # cột doi String(255) — cắt an toàn, quá dài coi như không hợp lệ

# Chuỗi "không có kết quả" HỢP LỆ (đã chuẩn hoá: chữ thường, dấu nháy thẳng, bỏ dấu chấm cuối).
_KHONG_KET_QUA = "google hasn't returned any results for this query"

_TACH_PHAN_RE = re.compile(r"\s+-\s+")
_NAM_CUOI_RE = re.compile(r"(?:^|[\s,(])(1[5-9]\d{2}|20\d{2})\s*$")
_MIEN_RE = re.compile(r"^(?:[\w-]+\.)+[a-z]{2,}$", re.IGNORECASE)
_THE_DAU_TIEU_DE_RE = re.compile(
    r"^(?:\[(?:PDF|HTML|BOOK|B|CITATION|C|DOC|DOCX|PPT)\]\s*)+", re.IGNORECASE)
_KHOANG_TRANG_RE = re.compile(r"\s+")
# Thẻ trường của PubMed ([ta], [pt], [cn]...) vô nghĩa với Google Scholar: gửi đi chỉ tốn 1 search
# tính phí mà kết quả không tin được. CLINICAL_AREAS có 8 truy vấn dạng này.
_CU_PHAP_PUBMED_RE = re.compile(r"\[(?:ta|pt|cn|tiab|mh|majr|dp)\]", re.IGNORECASE)

# DOI: CHỈ trích khi URL thật sự mang nguyên văn chuỗi 10.xxxx/... ở vị trí có neo.
_DOI_HOST = frozenset({"doi.org", "dx.doi.org", "www.doi.org"})
_DOI_DAU_RE = re.compile(r"^(10\.\d{4,9}/\S+)$")
_DOI_DUONG_DAN_RE = re.compile(
    r"(?:^|/)(?:doi(?:/(?:abs|full|pdf|epdf|pdfdirect|book|ref|citedby))?"
    r"|article|articles|chapter|content(?:/pdf)?)/(10\.\d{4,9}/\S+)",
    re.IGNORECASE)
# Đuôi CHỈ dành cho link doi.org (đường dẫn chính là DOI nên chỉ cắt đuôi hiển thị quen thuộc).
_DOI_DUOI_DOI_ORG_RE = re.compile(
    r"(?:/(?:abstract|full|pdf|epdf|pdfdirect|fulltext|references|citedby|summary|figures?))$"
    r"|(?:\.(?:pdf|full|abstract))$",
    re.IGNORECASE)
# Đuôi của URL NHÀ XUẤT BẢN: sau DOI thường còn '/tables/1', '/figures/2', '/fulltext.html',
# '.full-text'... Chỉ cắt khi đuôi khớp một dạng đã biết (không cắt mọi thứ sau dấu '/').
_DOI_DUOI_RE = re.compile(
    r"(?:/(?:abstract|full|full-text|fulltext|pdf|epdf|pdfdirect|references|citedby|summary|"
    r"metrics|figures?|tables?|supplementary[\w-]*)"
    r"(?:/.*|\.(?:html?|pdf|xml|full(?:-text)?|abstract))?$)"
    r"|(?:\.(?:pdf|full|abstract|full-text|fulltext)$)",
    re.IGNORECASE)
# bioRxiv/medRxiv (tiền tố 10.1101): 'vN' trong URL là dấu PHIÊN BẢN, không thuộc DOI.
_DOI_PHIEN_BAN_RE = re.compile(r"^(10\.1101/\S+?)v\d+(?:[./].*)?$", re.IGNORECASE)
_DOI_HOP_LE_RE = re.compile(r"^10\.\d{4,9}/[^\s\"<>#?]+$")

# PMID/PMCID: chỉ từ URL PubMed / PMC / Europe PMC đúng dạng chuẩn.
_HOST_PUBMED = "pubmed.ncbi.nlm.nih.gov"
_HOST_NCBI = frozenset({"www.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov"})
_HOST_PMC = frozenset({"pmc.ncbi.nlm.nih.gov", "www.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov", "europepmc.org"})
_PMID_PUBMED_RE = re.compile(r"^/([1-9]\d{0,8})/?$")
_PMID_NCBI_CU_RE = re.compile(r"^/pubmed/([1-9]\d{0,8})/?$", re.IGNORECASE)
_PMID_EUROPEPMC_RE = re.compile(r"^/(?:abstract|article)/med/([1-9]\d{0,8})/?$", re.IGNORECASE)
_PMCID_RE = re.compile(r"(?:^|/)(PMC[1-9]\d{0,9})(?:/|$)", re.IGNORECASE)


# Ngân sách lượt gọi THEO TIẾN TRÌNH (mọi instance dùng chung), tự về 0 khi sang ngày mới.
_KHOA_NGAN_SACH = threading.Lock()
_NGAN_SACH: Dict[str, Any] = {"ngay": None, "da_goi": 0}


def _giu_cho_ngan_sach(tran: int) -> bool:
    """Giữ chỗ 1 lượt gọi trong ngân sách tiến trình; False nếu đã chạm trần."""
    with _KHOA_NGAN_SACH:
        hom_nay = date.today()
        if _NGAN_SACH["ngay"] != hom_nay:
            _NGAN_SACH["ngay"] = hom_nay
            _NGAN_SACH["da_goi"] = 0
        if _NGAN_SACH["da_goi"] >= tran:
            return False
        _NGAN_SACH["da_goi"] += 1
        return True


def _hoan_ngan_sach() -> None:
    with _KHOA_NGAN_SACH:
        if _NGAN_SACH["da_goi"] > 0:
            _NGAN_SACH["da_goi"] -= 1


class SerpApiLoi(RuntimeError):
    """Lỗi có phân loại của connector SerpApi.

    `loai`: thieu_key | key_sai | het_quota | het_ngan_sach | cam_truy_cap | gioi_han_toc_do |
    tham_so_sai | loi_phia_serpapi | phan_hoi_khong_hop_le | khac. Thông báo KHÔNG BAO GIỜ chứa
    URL/params/khoá.
    """

    def __init__(self, thong_bao: str, loai: str = "khac") -> None:
        super().__init__(thong_bao)
        self.loai = loai


# --------------------------------------------------------------------------- tiện ích che khoá

def _sach_chuoi(text: Any) -> str:
    """Che `api_key=...` (regex của HttpClient) và chính GIÁ TRỊ khoá nếu nó lọt vào chuỗi."""
    s = _redact(str(text))
    khoa = settings.serpapi_api_key
    if khoa and len(khoa) >= 4:
        s = s.replace(khoa, "***")
    return s


def _la_ten_khoa(key: Any) -> bool:
    return re.sub(r"[^a-z]", "", str(key).lower()) == "apikey"


def _sach_payload(obj: Any, do_sau: int = 0) -> Any:
    """Bản sao payload đã bỏ mọi khoá tên `api_key` và che `api_key=...` trong chuỗi.

    Dùng cho save_raw + mọi trường đưa vào RawRecord. Quá sâu (bất thường) thì cắt bỏ để
    không có nhánh nào lọt chưa che."""
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

def _chuan_hoa_khoang_trang(text: Any) -> Optional[str]:
    if not isinstance(text, str):
        return None
    s = _KHOANG_TRANG_RE.sub(" ", text).strip()
    return s or None


def _bo_dau_cat(text: str) -> Tuple[str, bool]:
    """Bỏ dấu "…"/"..." ở cuối (Scholar cắt chuỗi dài). Trả (chuỗi sạch, có bị cắt không)."""
    s = text.rstrip()
    bi_cat = False
    while s.endswith("…") or s.endswith("..."):
        s = s[:-1] if s.endswith("…") else s[:-3]
        s = s.rstrip(" ,;")
        bi_cat = True
    return s, bi_cat


def _nam_hop_ly(nam: int) -> bool:
    return _NAM_TOI_THIEU <= nam <= date.today().year + 1


def _tach_summary(summary: Any) -> Dict[str, Any]:
    """Tách `publication_info.summary` dạng 'TÁC GIẢ - [nơi đăng, ]NĂM - tên miền'.

    Tách theo " - " (có khoảng trắng hai bên) để tên miền có gạch nối (vd
    'research-repository.st-andrews.ac.uk') không phá quy tắc. Năm CHỈ được nhận khi nó
    là token ở CUỐI phần nơi-đăng (đứng ngay trước ' - <miền>'); KHÔNG lấy 4 chữ số đầu
    tiên vì tên hội nghị có thể chứa năm ('Proceedings of the 2019 Conference…, 2020').
    Không khớp/không hợp lý -> nam=None (tuyệt đối không đoán). Đã chạy thử offline trên
    6 mẫu nguyên văn từ tài liệu SerpApi + các ca dựng theo định dạng.
    """
    kq: Dict[str, Any] = {"tac_gia": None, "tap_chi": None, "nam": None, "mien": None}
    if not isinstance(summary, str) or not summary.strip():
        return kq
    phan = [p.strip() for p in _TACH_PHAN_RE.split(summary.strip()) if p.strip()]
    if len(phan) < 2:
        return kq
    kq["tac_gia"] = _bo_dau_cat(phan[0])[0] or None
    if len(phan) >= 3:
        giua: Optional[str] = " - ".join(phan[1:-1])
        kq["mien"] = phan[-1]
    elif _MIEN_RE.match(phan[1]):
        giua = None
        kq["mien"] = phan[1]
    else:
        giua = phan[1]
    if giua:
        m = _NAM_CUOI_RE.search(giua)
        if m:
            nam = int(m.group(1))
            if _nam_hop_ly(nam):
                kq["nam"] = nam
            noi_dang = giua[:m.start()]
        else:
            noi_dang = giua
        noi_dang = _bo_dau_cat(noi_dang.strip(" ,;("))[0].strip(" ,;(")
        kq["tap_chi"] = noi_dang[:255] or None
    return kq


def _nam_tu_since_date(since_date: Optional[str]) -> Optional[int]:
    """'YYYY-MM-DD' (hoặc 'YYYY-MM'/'YYYY') -> năm; sai định dạng -> None kèm cảnh báo."""
    if not since_date:
        return None
    s = str(since_date).strip()
    if re.match(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$", s):
        nam = int(s[:4])
        if _nam_hop_ly(nam):
            return nam
    logger.warning("[serpapi_scholar] since_date không đúng định dạng YYYY-MM-DD: %r", since_date)
    return None


def _cat_ma_bai(doi: str) -> str:
    """Nền tảng Silverchair (OUP, ASH, AAP...) đặt '/<mã bài toàn chữ số>[/<tệp>]' SAU DOI
    ('…/doi/10.1093/ndt/gfad001/6998877'): cắt tại đoạn toàn chữ số đầu tiên đứng sau phần
    'tiền tố/hậu tố'. DOI hợp lệ chỉ có một dấu '/' (vd 10.1000/182) không bị đụng tới."""
    phan = doi.split("/")
    for i in range(2, len(phan)):
        if phan[i].isdigit():
            return "/".join(phan[:i])
    return doi


def _cat_doi(doi: str, tu_nha_xuat_ban: bool = False) -> Optional[str]:
    """Bỏ phần URL dính vào DOI (đuôi hiển thị, mã bài, phiên bản vN của bioRxiv/medRxiv) và
    dấu câu cuối; kiểm cú pháp DOI. `tu_nha_xuat_ban`: DOI lấy từ ĐƯỜNG DẪN URL nhà xuất bản
    (còn đuôi thừa) chứ không phải từ link doi.org (đường dẫn chính là DOI)."""
    duoi_re = _DOI_DUOI_RE if tu_nha_xuat_ban else _DOI_DUOI_DOI_ORG_RE
    for _ in range(4):
        moi = duoi_re.sub("", doi)
        if tu_nha_xuat_ban:
            moi = _cat_ma_bai(moi)
        m = _DOI_PHIEN_BAN_RE.match(moi)
        if m:
            moi = m.group(1)
        if moi == doi:
            break
        doi = moi
    doi = doi.rstrip(".,;:")
    if len(doi) > _TRAN_DOI or not _DOI_HOP_LE_RE.match(doi):
        return None
    return doi


def _trich_dinh_danh(link: Any) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Trả (doi, pmid, pmcid) CHỈ khi `link` thật sự mang định danh đó; không thì None.

    Không tra ngược từ tiêu đề, không dựng DOI từ mã bài của nhà xuất bản (vd nature.com/
    articles/s41586-… không chứa chuỗi '10.xxxx' nên KHÔNG có DOI)."""
    if not isinstance(link, str) or not link.strip():
        return None, None, None
    try:
        u = urlparse(link.strip())
    except ValueError:
        return None, None, None
    if u.scheme not in ("http", "https"):
        return None, None, None
    host = (u.hostname or "").lower()
    path = unquote(u.path or "")
    doi = pmid = pmcid = None

    if host in _DOI_HOST:
        m = _DOI_DAU_RE.match(path.lstrip("/"))
        if m:
            doi = _cat_doi(m.group(1))
    else:
        m = _DOI_DUONG_DAN_RE.search(path)
        if m:
            doi = _cat_doi(m.group(1), tu_nha_xuat_ban=True)

    if host == _HOST_PUBMED:
        m = _PMID_PUBMED_RE.match(path)
        pmid = m.group(1) if m else None
    elif host in _HOST_NCBI:
        m = _PMID_NCBI_CU_RE.match(path)
        pmid = m.group(1) if m else None
    elif host == "europepmc.org":
        m = _PMID_EUROPEPMC_RE.match(path)
        pmid = m.group(1) if m else None
    if host in _HOST_PMC:
        m = _PMCID_RE.search(path)
        pmcid = m.group(1).upper() if m else None
    return doi, pmid, pmcid


def _so_nguyen(value: Any) -> Optional[int]:
    """Số nguyên thật (loại bool) hoặc None — cited_by vắng thì KHÔNG ép thành 0."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _la_khong_co_ket_qua(chuoi_loi: str) -> bool:
    s = chuoi_loi.strip().lower().replace("’", "'").rstrip(".").strip()
    return s == _KHONG_KET_QUA


def _dem_cache_hit(http: Any) -> Optional[int]:
    v = getattr(http, "cache_hit_count", None)
    return v if isinstance(v, int) else None


class SerpApiScholarClient(SourceClient):
    name = "serpapi_scholar"
    endpoint = SEARCH

    def __init__(self) -> None:
        super().__init__()
        # Khoá API đi qua `params` (không header) nên HttpClient._redact che được nó.
        # max_retries=0: MỖI request tới SerpApi là một search TÍNH PHÍ, HỢP ĐỒNG là đúng MỘT request cho
        # mỗi search(). Vòng retry mặc định của HttpClient sẽ nhân một truy vấn thành 2 request (429/5xx)
        # hoặc 5 request (timeout/mất mạng/JSON hỏng) — mà bộ đếm ngân sách chỉ tính 1, và một timeout mà
        # phía SerpApi đã xử lý xong vẫn có thể bị tính phí nhiều lần. Lỗi thì NÉM/cảnh báo ngay (xem
        # PHÂN LOẠI LỖI), việc thử lại thuộc về lần ingest sau, có đếm ngân sách.
        self.http = HttpClient(max_retries=0)
        self._chot_loi: Optional[SerpApiLoi] = None   # lỗi chốt (key sai/hết quota): dừng gọi tiếp
        self._da_bao_het_ngan_sach = False
        self.stats: Dict[str, int] = {
            "so_lan_goi": 0, "bo_qua_ngan_sach": 0, "khong_co_ket_qua": 0,
            "rong_chua_xac_nhan": 0, "truoc_nam_since_date": 0, "bo_qua_thieu_tieu_de": 0,
            "bo_qua_khong_phai_dict": 0, "bo_qua_cu_phap_pubmed": 0,
        }

    # ------------------------------------------------------------------ search
    def search(self, query: str, clinical_area: Optional[str] = None,
               max_results: int = 20, since_date: Optional[str] = None) -> List[RawRecord]:
        if self.use_mock:
            return mock_records_for(self.name, query, clinical_area, max_results)

        khoa = settings.serpapi_api_key
        if not khoa:
            # Chặn SỚM, rõ ràng — cùng nguyên tắc fail-closed của scopus.py: nguồn BẬT mà thiếu
            # điều kiện thật phải NỔ TO, không âm thầm trả rỗng (và không đặt trong __init__ vì
            # get_enabled_sources() dựng client ngoài try -> sẽ làm sập cả ingest_all).
            raise SerpApiLoi(
                "[serpapi_scholar] ENABLE_SERPAPI_SCHOLAR=true nhưng thiếu SERPAPI_API_KEY — "
                "thêm vào ~/.ebm-secrets/medical-ebm-automation.env rồi thử lại.",
                "thieu_key")
        if self._chot_loi is not None:
            raise SerpApiLoi(
                f"{self._chot_loi.args[0]} [nguồn đã bị dừng cho phần còn lại của lượt chạy, "
                "không gọi thêm]", self._chot_loi.loai)
        if not isinstance(query, str) or not query.strip():
            raise SerpApiLoi("[serpapi_scholar] truy vấn rỗng — không gọi SerpApi (sẽ bị 400 "
                             "'Missing query' mà vẫn tốn lượt).", "tham_so_sai")
        if contains_pii_text(query):
            # Chuỗi truy vấn đi qua SerpApi tới Google và bị SerpApi lưu 31 ngày: chặn TRƯỚC khi tốn ngân sách
            # và KHÔNG đưa truy vấn vào thông báo (tránh PII lọt vào log/Source Log). Không đặt _chot_loi:
            # một truy vấn xấu không được khoá cả nguồn.
            raise SerpApiLoi(
                "[serpapi_scholar] truy vấn có dấu hiệu PII/PHI (email, CCCD/mã bệnh nhân, SĐT, ngày sinh...) — "
                "TỪ CHỐI, không gửi sang SerpApi (lưu 31 ngày, chuyển tiếp Google). Chỉ dùng chuỗi chủ đề y văn.",
                "tham_so_sai")
        if _CU_PHAP_PUBMED_RE.search(query):
            self.stats["bo_qua_cu_phap_pubmed"] += 1
            logger.warning(
                "[serpapi_scholar] BỎ QUA truy vấn cú pháp PubMed (thẻ [ta]/[pt]/...; không gọi SerpApi, không tốn "
                "ngân sách): %r", query[:120])
            return []
        if isinstance(max_results, int) and not isinstance(max_results, bool) and max_results <= 0:
            # Người gọi xin 0 (hoặc âm) kết quả: không gọi SerpApi (mỗi request là 1 search tính phí).
            return []

        self._giu_ngan_sach()
        nam_loc = _nam_tu_since_date(since_date)
        try:
            num = max(1, min(int(max_results), _TRAN_NUM))
        except (TypeError, ValueError):
            num = _TRAN_NUM
        params: Dict[str, Any] = {"engine": "google_scholar", "q": query, "api_key": khoa, "num": num}
        if nam_loc is not None:
            params["as_ylo"] = nam_loc

        cache_truoc = _dem_cache_hit(self.http)
        loi_http: Optional[SerpApiLoi] = None
        data: Any = None
        try:
            data = self.http.get_json(SEARCH, params=params)
        except requests.HTTPError as exc:
            # Chỉ DỰNG lỗi trong khối except rồi ném ở NGOÀI: `raise ... from None` chỉ đặt
            # __suppress_context__, __context__ vẫn trỏ tới HTTPError có response.url chứa api_key.
            loi_http = self._loi_tu_http(exc)
        except Exception as exc:
            # Lỗi tầng vận chuyển KHÔNG có response (timeout/mất mạng/JSON hỏng; HttpClient này không
            # retry vì max_retries=0): D1 — trả [] chứ KHÔNG bịa mock; telemetry HttpClient
            # (failure_count) vẫn làm Source Log = "error".
            logger.warning("[serpapi_scholar] lỗi gọi thật (live) — BỎ QUA, KHÔNG bịa mock: %s: %s",
                           type(exc).__name__, _sach_chuoi(str(exc))[:300])
            return []
        if loi_http is not None:
            raise loi_http
        cache_sau = _dem_cache_hit(self.http)
        if cache_truoc is not None and cache_sau is not None and cache_sau > cache_truoc:
            _hoan_ngan_sach()  # trúng cache cục bộ: không request nào rời máy -> không tốn search
            self.stats["so_lan_goi"] -= 1

        organic, sach = self._kiem_phan_hoi(data, query, params)
        self._che_cache(params, data, sach)
        if not organic:
            return []

        meta = sach.get("search_metadata") if isinstance(sach.get("search_metadata"), dict) else {}
        thong_tin = sach.get("search_information") if isinstance(sach.get("search_information"), dict) else {}
        boi_canh = {"search_id": meta.get("id"), "tong_ket_qua": thong_tin.get("total_results")}

        out: List[RawRecord] = []
        for item in organic:
            try:
                rec, ly_do_bo = self._anh_xa(item, query, clinical_area, boi_canh)
                if rec is None:
                    if ly_do_bo:
                        self.stats[ly_do_bo] += 1
                    continue
                # as_ylo là lọc PHÍA SERVER, có thể lọt bài lệch năm: kiểm lại phía client nhưng chỉ GẮN CỜ
                # (không loại) — không có căn cứ chắc để vứt dữ liệu; bài year_unknown càng không được loại.
                if nam_loc is not None and rec.publication_date and int(rec.publication_date) < nam_loc:
                    rec.raw["co"].append("before_since_year")
                    self.stats["truoc_nam_since_date"] += 1
                out.append(rec)
                if len(out) >= max_results:
                    break
            except Exception as exc:  # pragma: no cover
                logger.warning("[serpapi_scholar] bỏ qua 1 bản ghi hỏng trong trang kết quả (query=%r): %s",
                               query, _sach_chuoi(str(exc)))
                continue
        if not out:
            # Trang có organic_results nhưng KHÔNG phần tử nào dùng được: nghi SerpApi đổi schema (đổi tên
            # 'title'...). Trả [] sẽ thành 'ok/0' im lặng dù đã tốn 1 search -> NÉM, và gỡ cache để không
            # phát lại phản hồi này 24 giờ. Trang lẫn phần tử tốt/xấu vẫn trả phần tốt như cũ.
            self._xoa_cache(params)
            khoa_gap = sorted({_sach_chuoi(k) for it in organic if isinstance(it, dict) for k in it})[:15]
            raise SerpApiLoi(
                f"[serpapi_scholar] phản hồi 200 có {len(organic)} organic_results nhưng KHÔNG phần tử nào dùng "
                f"được (thiếu 'title' hoặc không phải object) — nghi SerpApi đổi cấu trúc; đã tốn 1 search. "
                f"Khoá gặp trong phần tử: {khoa_gap}", "phan_hoi_khong_hop_le")
        return out

    # ------------------------------------------------------------------ ngân sách
    def _giu_ngan_sach(self) -> None:
        """Giữ chỗ 1 lượt gọi (mỗi request là 1 search TÍNH PHÍ); hết ngân sách thì NỔ TO."""
        tran = settings.serpapi_max_calls_per_run
        if not isinstance(tran, int):
            tran = 0  # cấu hình hỏng -> fail-closed
        tran = max(tran, 0)
        if not _giu_cho_ngan_sach(tran):
            self.stats["bo_qua_ngan_sach"] += 1
            thong_bao = (
                f"[serpapi_scholar] đã dùng hết ngân sách {tran} lượt gọi SerpApi của tiến trình này "
                "(SERPAPI_MAX_CALLS_PER_RUN) — các truy vấn còn lại BỊ BỎ QUA có chủ đích để không đốt "
                "hạn mức search (gói Free 250/tháng). Tăng SERPAPI_MAX_CALLS_PER_RUN nếu thật sự cần.")
            if not self._da_bao_het_ngan_sach:
                self._da_bao_het_ngan_sach = True
                logger.warning(thong_bao)
            raise SerpApiLoi(thong_bao, "het_ngan_sach")
        self.stats["so_lan_goi"] += 1

    # ------------------------------------------------------------------ xử lý lỗi
    def _chot(self, loi: SerpApiLoi) -> SerpApiLoi:
        self._chot_loi = loi
        logger.warning("[serpapi_scholar] LỖI CHỐT (%s) — dừng gọi SerpApi cho phần còn lại của lượt chạy.",
                       loi.loai)
        return loi

    def _xoa_cache(self, params: Dict[str, Any]) -> None:
        """Gỡ mục cache GET của phản hồi lỗi — HttpClient cache 200 trong 24 giờ, mà phản hồi lỗi
        (không tính phí) mà bị cache thì mọi lần thử lại trong 24 giờ đều nhận lại đúng lỗi đó."""
        try:
            _cache_path(_cache_key("GET", SEARCH, params)).unlink(missing_ok=True)
        except Exception:  # pragma: no cover
            pass

    def _che_cache(self, params: Dict[str, Any], data: Any, sach: Dict[str, Any]) -> None:
        """HttpClient ghi NGUYÊN payload vào cache GET TRƯỚC khi connector kịp che. Nếu bản đã che
        khác bản thô (phản hồi có lặp lại api_key...), ghi đè tệp cache bằng bản đã che: vẫn giữ lợi ích
        cache 24 giờ (không đốt thêm search) mà không để khoá nằm trên đĩa (thư mục OneDrive).
        Chỉ ghi đè khi tệp đã tồn tại (tức HttpClient đã cache), không tự tạo tệp mới."""
        if sach == data:
            return
        try:
            khoa_cache = _cache_key("GET", SEARCH, params)
            if _cache_path(khoa_cache).exists():
                _write_cache(khoa_cache, {"json": sach, "text": None})
        except Exception as exc:  # pragma: no cover
            logger.warning("[serpapi_scholar] không che được tệp cache HTTP: %s", type(exc).__name__)

    def _loi_tu_http(self, exc: requests.HTTPError) -> SerpApiLoi:
        """Phân loại HTTPError (đã có status) thành SerpApiLoi; KHÔNG đưa URL/params vào thông báo."""
        resp = getattr(exc, "response", None)
        status = getattr(resp, "status_code", None)
        if not isinstance(status, int):
            m = re.match(r"\s*(\d{3})\b", str(exc))
            status = int(m.group(1)) if m else None
        chi_tiet = ""
        try:
            body = resp.json() if resp is not None else None
            if isinstance(body, dict) and body.get("error"):
                chi_tiet = str(body["error"])
        except Exception:
            chi_tiet = ""
        chi_tiet = _sach_chuoi(chi_tiet)[:300]
        low = chi_tiet.lower()
        ma = f"HTTP {status}" if status else "HTTP (không rõ mã)"

        if status == 401 or "invalid api key" in low:
            return self._chot(SerpApiLoi(
                f"[serpapi_scholar] {ma}: SerpApi từ chối SERPAPI_API_KEY (key sai/hết hiệu lực) — "
                f"sửa khoá trong ~/.ebm-secrets/medical-ebm-automation.env. {chi_tiet}".strip(),
                "key_sai"))
        if status == 429 and ("run out of searches" in low or "out of searches" in low):
            return self._chot(SerpApiLoi(
                f"[serpapi_scholar] {ma}: HẾT QUOTA search của tài khoản SerpApi (quota_exhausted) — "
                f"không retry, dừng nguồn. {chi_tiet}".strip(), "het_quota"))
        if status == 429:
            return SerpApiLoi(
                f"[serpapi_scholar] {ma}: vượt giới hạn tốc độ theo giờ của SerpApi (chuỗi lỗi riêng của "
                f"trường hợp này chưa xác minh). {chi_tiet}".strip(), "gioi_han_toc_do")
        if status == 403:
            return SerpApiLoi(
                f"[serpapi_scholar] {ma}: tài khoản/khoá không có quyền dùng engine này. {chi_tiet}".strip(),
                "cam_truy_cap")
        if status == 400:
            return SerpApiLoi(
                f"[serpapi_scholar] {ma}: tham số bị SerpApi từ chối (lỗi lập trình, không retry). "
                f"{chi_tiet}".strip(), "tham_so_sai")
        if status is not None and status >= 500:
            return SerpApiLoi(
                f"[serpapi_scholar] {ma}: lỗi phía SerpApi/Google (thử lại sau; lỗi không tính search). "
                f"{chi_tiet}".strip(), "loi_phia_serpapi")
        return SerpApiLoi(f"[serpapi_scholar] {ma}: SerpApi trả lỗi. {chi_tiet}".strip(), "khac")

    def _nem_loi_body(self, chuoi_loi: str, trang_thai: str, params: Dict[str, Any]) -> None:
        """Phản hồi HTTP 200 nhưng body báo lỗi (hoặc status Error): luôn NÉM, log nguyên chuỗi lỗi
        (đã che) để phát hiện sớm nếu SerpApi đổi lời."""
        self._xoa_cache(params)
        chi_tiet = _sach_chuoi(chuoi_loi)[:300]
        low = chi_tiet.lower()
        if "invalid api key" in low:
            raise self._chot(SerpApiLoi(
                f"[serpapi_scholar] SerpApi từ chối SERPAPI_API_KEY (key sai/hết hiệu lực): {chi_tiet}",
                "key_sai"))
        if "run out of searches" in low or "out of searches" in low:
            raise self._chot(SerpApiLoi(
                f"[serpapi_scholar] HẾT QUOTA search của tài khoản SerpApi (quota_exhausted): {chi_tiet}",
                "het_quota"))
        if "missing query" in low or "parameter" in low:
            raise SerpApiLoi(f"[serpapi_scholar] SerpApi báo tham số sai: {chi_tiet}", "tham_so_sai")
        if trang_thai.lower() == "error" or "try again later" in low:
            raise SerpApiLoi(
                f"[serpapi_scholar] lỗi phía SerpApi/Google (search_metadata.status={trang_thai or '?'}; "
                f"lỗi không tính search): {chi_tiet}", "loi_phia_serpapi")
        raise SerpApiLoi(f"[serpapi_scholar] SerpApi trả lỗi không thuộc danh mục đã biết: {chi_tiet}",
                         "khac")

    def _kiem_phan_hoi(self, data: Any, query: str,
                       params: Dict[str, Any]) -> Tuple[List[Any], Dict[str, Any]]:
        """Phân loại phản hồi: trả (organic_results, payload đã che) hoặc ([], ...) nếu rỗng hợp lệ;
        NÉM SerpApiLoi cho mọi thất bại."""
        if not isinstance(data, dict):
            self._xoa_cache(params)
            raise SerpApiLoi(
                f"[serpapi_scholar] phản hồi không phải JSON object (kiểu {type(data).__name__}).",
                "phan_hoi_khong_hop_le")
        sach = _sach_payload(data)
        meta = sach.get("search_metadata")
        trang_thai = str(meta.get("status") or "") if isinstance(meta, dict) else ""
        loi_api = sach.get("error")
        organic = sach.get("organic_results")
        co_organic = isinstance(organic, list) and len(organic) > 0

        if loi_api:
            chuoi = str(loi_api)
            if _la_khong_co_ket_qua(chuoi) and trang_thai.lower() != "error":
                if not co_organic:
                    self.stats["khong_co_ket_qua"] += 1
                    self.save_raw(query, sach)
                    return [], sach
                logger.warning("[serpapi_scholar] phản hồi vừa báo 'không có kết quả' vừa có organic_results "
                               "(lỗi lịch sử phía SerpApi) — ưu tiên dữ liệu (query=%r).", query)
            else:
                self._nem_loi_body(chuoi, trang_thai, params)
        elif trang_thai.lower() in ("error", "queued", "processing"):
            self._xoa_cache(params)
            raise SerpApiLoi(
                f"[serpapi_scholar] search_metadata.status={trang_thai} ở chế độ đồng bộ không kèm dữ liệu "
                "(bất thường/lỗi phía SerpApi; lỗi không tính search).", "loi_phia_serpapi")
        elif organic is not None and not isinstance(organic, list):
            # 'organic_results' hiện diện nhưng sai kiểu: SerpApi có thể đã đổi schema — NÉM, không coi là rỗng.
            self._xoa_cache(params)
            self.save_raw(query, sach)
            raise SerpApiLoi(
                f"[serpapi_scholar] 'organic_results' hiện diện nhưng KHÔNG phải danh sách (kiểu "
                f"{type(organic).__name__}) — SerpApi có thể đã đổi cấu trúc; đã tốn 1 search.",
                "phan_hoi_khong_hop_le")
        elif not co_organic:
            # 200/Success, không error, không organic_results: KHÔNG coi là "không có kết quả" đã xác nhận.
            self.stats["rong_chua_xac_nhan"] += 1
            logger.warning(
                "[serpapi_scholar] empty_unconfirmed: HTTP 200 nhưng không có organic_results lẫn 'error' "
                "(query=%r) — không xác nhận được là 'không có kết quả' (đã tốn 1 search).", query)
            self.save_raw(query, sach)
            return [], sach

        self.save_raw(query, sach)
        return organic if isinstance(organic, list) else [], sach

    # ------------------------------------------------------------------ ánh xạ bản ghi
    def _anh_xa(self, item: Any, query: str, clinical_area: Optional[str],
                boi_canh: Dict[str, Any]) -> Tuple[Optional[RawRecord], Optional[str]]:
        """organic_results[i] -> RawRecord. Trả (None, khoá_stats) khi bỏ; dữ liệu đã được che khoá."""
        if not isinstance(item, dict):
            return None, "bo_qua_khong_phai_dict"
        co: List[str] = []
        tieu_de_goc = _chuan_hoa_khoang_trang(item.get("title"))
        if not tieu_de_goc:
            return None, "bo_qua_thieu_tieu_de"
        # Tiền tố [PDF]/[HTML]/[BOOK]/[CITATION] chỉ là nhãn hiển thị của Scholar (tài liệu SerpApi nói
        # title đã sạch — bóc phòng hờ, giữ bản gốc ở raw["title_goc"]).
        m_the = _THE_DAU_TIEU_DE_RE.match(tieu_de_goc)
        tieu_de = _THE_DAU_TIEU_DE_RE.sub("", tieu_de_goc).strip()
        tieu_de, bi_cat = _bo_dau_cat(tieu_de)
        if not tieu_de:
            return None, "bo_qua_thieu_tieu_de"
        if bi_cat:
            co.append("title_truncated")
        if m_the:
            co.append("title_tag_removed")
            if re.search(r"\[(?:CITATION|C)\]", m_the.group(0), re.IGNORECASE):
                co.append("citation_only")

        link_tho = item.get("link")
        url = link_tho.strip() if isinstance(link_tho, str) and link_tho.strip().lower().startswith(
            ("http://", "https://")) else None
        if url is None:
            co.append("no_link")  # không tự dựng URL

        info = item.get("publication_info")
        info = info if isinstance(info, dict) else {}
        tach = _tach_summary(info.get("summary"))
        if not info:
            co.append("no_publication_info")
        if tach["nam"] is None:
            co.append("year_unknown")

        ten_tac_gia = []
        ds_tg = info.get("authors")
        if isinstance(ds_tg, list):
            for a in ds_tg:
                ten = _chuan_hoa_khoang_trang(a.get("name")) if isinstance(a, dict) else None
                if ten:
                    ten_tac_gia.append(ten)
        tac_gia = ", ".join(ten_tac_gia) if ten_tac_gia else tach["tac_gia"]

        doi, pmid, pmcid = _trich_dinh_danh(url)
        loai_tai_lieu = _chuan_hoa_khoang_trang(item.get("type"))
        loai_tai_lieu = loai_tai_lieu[:64] if loai_tai_lieu else None
        if loai_tai_lieu and loai_tai_lieu.lower() == "citation" and "citation_only" not in co:
            co.append("citation_only")

        # study_type: CHỈ preprint (tín hiệu an toàn, hạ điểm); KHÔNG suy từ tiêu đề — xem docstring module.
        host = (urlparse(url).hostname or "") if url else ""
        blob = " ".join(x for x in (tach["tap_chi"], tach["mien"], host) if x)
        study_type = "preprint" if infer_study_type("", loai_tai_lieu, blob) == "preprint" else None

        cited_by = None
        inline = item.get("inline_links")
        if isinstance(inline, dict) and isinstance(inline.get("cited_by"), dict):
            cited_by = _so_nguyen(inline["cited_by"].get("total"))

        tai_nguyen = []
        for r in (item.get("resources") if isinstance(item.get("resources"), list) else [])[:5]:
            if isinstance(r, dict) and isinstance(r.get("link"), str):
                tai_nguyen.append({"ten_mien": r.get("title"), "dinh_dang": r.get("file_format"),
                                   "link": r["link"]})

        raw = {
            "result_id": item.get("result_id"),
            "position": item.get("position"),
            # Snippet KHÔNG PHẢI abstract — chỉ để tham chiếu/kiểm tay.
            "snippet": _chuan_hoa_khoang_trang(item.get("snippet")),
            "publication_info_summary": _chuan_hoa_khoang_trang(info.get("summary")),
            "nha_xuat_ban_hoac_mien": tach["mien"],
            "cited_by_total": cited_by,
            "tai_nguyen": tai_nguyen,
            "co": co,
            "serpapi_search_id": boi_canh.get("search_id"),
            "tong_ket_qua_google": boi_canh.get("tong_ket_qua"),
            "luu_y": ("Kết quả khám phá từ Google Scholar qua SerpApi: snippet KHÔNG phải abstract; "
                      "DOI/PMID chỉ lấy khi link thật chứa; chưa kiểm rút bài; chưa xác minh."),
        }
        if tieu_de != tieu_de_goc:
            raw["title_goc"] = tieu_de_goc

        rec = RawRecord(
            source=self.name, title=tieu_de,
            authors=tac_gia,
            journal_or_organization=tach["tap_chi"],
            publication_date=str(tach["nam"]) if tach["nam"] else None,
            doi=doi, pmid=pmid, pmcid=pmcid,
            url=url,
            abstract=None,
            document_type=loai_tai_lieu,
            study_type=study_type,
            clinical_area=clinical_area,
            ingest_query=query, api_endpoint=SEARCH,
            raw=raw,
        )
        return rec, None
