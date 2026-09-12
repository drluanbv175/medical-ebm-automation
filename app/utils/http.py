"""HTTP client tiện ích với retry/backoff, rate-limit handling và cache file đơn giản.

Thiết kế nhỏ gọn, không phụ thuộc thư viện retry ngoài, để dễ kiểm soát và test.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests

from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Audit 2026-07-11: requests tự nhúng URL ĐẦY ĐỦ (kèm query string, gồm cả api_key) vào
# thông báo exception (HTTPError/ConnectionError…) — nếu không che, khóa API (vd
# NCBI_API_KEY, chỉ chấp nhận qua query param theo thiết kế E-utilities, không thể chuyển
# sang header) sẽ lọt nguyên văn vào data/archive/app.log/stdout ngay khi có lỗi mạng thật
# (401 sai key/429 hết lượt retry/timeout) — tái hiện được: gọi HttpClient với api_key giả
# tới NCBI thật, HTTPError trả về chứa "...&api_key=FAKESECRETKEY..." nguyên văn.
# SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 16) — regex gốc chỉ che
# `api_key=`/`email=`, nhưng 2 nguồn BẬT MẶC ĐỊNH (Crossref, OpenAlex —
# xem app/sources/crossref.py, app/sources/openalex.py) dùng tên tham số
# `mailto` (đúng chuẩn "polite pool" của cả 2 API), không phải `email`.
# Một lỗi HTTP (404/429/timeout — rất phổ biến khi ingest hàng chục query)
# làm lộ nguyên văn địa chỉ email vận hành viên trong exception message,
# lọt vào SourceLog.error_message rồi vào export_source_log_csv() — đúng
# lớp dữ liệu mà cơ chế redact này được xây ra để bảo vệ.
_SENSITIVE_QUERY_RE = re.compile(
    r"((?:api[_-]?key|email|mailto)=)[^&\s]+",
    re.IGNORECASE,
)


def _redact(text: str) -> str:
    """Che giá trị tham số nhạy cảm trong một chuỗi URL/thông báo lỗi trước khi ghi log."""
    return _SENSITIVE_QUERY_RE.sub(r"\1***", text)


def _raise_for_status_redacted(resp: "requests.Response") -> None:
    """resp.raise_for_status() nhưng che tham số nhạy cảm trong thông báo lỗi trước khi
    exception rời khỏi HttpClient — nơi gọi (vd resolve_pmids() ở evidence_workbench.py)
    log thẳng exc, không đi qua http.py nữa nên phải che tại nguồn."""
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        raise requests.HTTPError(_redact(str(exc)), response=resp) from None

_CACHE_DIR = settings.raw_dir / "_http_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Thời điểm request gần nhất theo host, để giãn cách chủ động (NCBI etiquette).
_last_request_at: Dict[str, float] = {}
# Khoá ngắn chỉ bảo vệ việc tạo khoá riêng cho từng host.
_throttle_lock = threading.Lock()
_throttle_host_locks: Dict[str, threading.Lock] = {}


def _throttle(url: str, min_interval: float) -> float:
    """Ngủ vừa đủ để 2 request cùng host cách nhau >= min_interval giây.

    SỬA 2026-09-05 (Workflow đối kháng đa-agent, task #84, MEDIUM) — bản gốc đọc
    `_last_request_at.get(host)`, tính `elapsed`, `sleep()`, rồi mới GHI mốc mới —
    một chuỗi đọc-kiểm-ngủ-ghi KHÔNG khoá. `app/services/ingestion.py::ingest_all()`
    chạy RSS feed qua `ThreadPoolExecutor(max_workers=_FEED_WORKERS)` (4 luồng), và
    3 feed trong `app/sources/feeds.py` cùng trỏ `link.springer.com` (cùng `netloc`
    ⇒ cùng khoá `host` trong `_last_request_at`) — hai luồng có thể ĐỌC cùng một
    `last` TRƯỚC KHI luồng nào kịp GHI mốc mới, mỗi luồng tự tính "đủ giãn cách" một
    cách ĐỘC LẬP rồi cùng gọi mạng gần như đồng thời — đánh bại đúng mục đích giãn
    cách NCBI etiquette mà comment ở `_FEED_WORKERS` tự khai ("tránh 429 từ host
    dùng chung như bmj.com").

    SỬA 2026-09-12: cách đặt-trước mốc rồi ngủ ngoài khoá vẫn có thể cho hai request
    dồn sát nhau nếu một luồng thức dậy muộn do scheduler (thấy rõ trên Windows).
    Mỗi host nay có khoá riêng: cùng host ngủ tuần tự và chốt mốc THỰC sau khi ngủ;
    host khác vẫn chạy độc lập, không bị một khoá toàn cục chặn. Hàm trả mốc được
    cấp phép để test đo ngay bên trong ranh giới throttle, không bị scheduler chen
    vào giữa lúc hàm trả về và lúc test gọi `time.monotonic()`.
    """
    if min_interval <= 0:
        return time.monotonic()
    host = urlparse(url).netloc
    with _throttle_lock:
        host_lock = _throttle_host_locks.setdefault(host, threading.Lock())

    with host_lock:
        last = _last_request_at.get(host)
        now = time.monotonic()
        if last is not None:
            deadline = last + min_interval
            while now < deadline:
                time.sleep(deadline - now)
                now = time.monotonic()
        _last_request_at[host] = now
        return now


def _cache_key(method: str, url: str, params: Optional[Dict[str, Any]]) -> str:
    raw = f"{method}|{url}|{json.dumps(params or {}, sort_keys=True)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_path(key: str) -> Path:
    return _CACHE_DIR / f"{key}.json"


def _read_cache(key: str, ttl: int) -> Optional[Dict[str, Any]]:
    path = _cache_path(key)
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if ttl >= 0 and age > ttl:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(key: str, payload: Dict[str, Any]) -> None:
    try:
        _cache_path(key).write_text(json.dumps(payload), encoding="utf-8")
    except OSError as exc:  # pragma: no cover
        logger.warning("Không ghi được cache: %s", exc)


class HttpClient:
    """Wrapper requests có retry/backoff + cache GET.

    Tham số:
        cache_ttl: thời gian cache (giây). -1 = cache vĩnh viễn, 0 = không cache.
    """

    def __init__(
        self,
        default_headers: Optional[Dict[str, str]] = None,
        cache_ttl: Optional[int] = None,
        min_interval: Optional[float] = None,
    ) -> None:
        self.session = requests.Session()
        if default_headers:
            self.session.headers.update(default_headers)
        self.session.headers.setdefault(
            "User-Agent",
            f"medical-ebm-automation/0.1 (mailto:{settings.ncbi_email or settings.openalex_email or 'unknown'})",
        )
        self.cache_ttl = settings.http_cache_ttl if cache_ttl is None else cache_ttl
        self.min_interval = settings.http_min_interval if min_interval is None else min_interval
        # Telemetry chỉ chứa trạng thái kỹ thuật, tuyệt đối không giữ URL/query có thể có API key.
        # Ingestion dùng các bộ đếm này để không ghi nhầm lỗi live thành request "ok".
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.transient_failure_count = 0
        self.cache_hit_count = 0
        self.last_error = ""
        self.last_status_code: Optional[int] = None

    def health_snapshot(self) -> Dict[str, Any]:
        """Trả telemetry không chứa secret để Source Log và deployment gate sử dụng."""
        return {
            "request_count": self.request_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "transient_failure_count": self.transient_failure_count,
            "cache_hit_count": self.cache_hit_count,
            "last_error": self.last_error,
            "last_status_code": self.last_status_code,
        }

    def _record_terminal_failure(self, exc: Exception, status_code: Optional[int] = None) -> None:
        """Ghi một lỗi cuối cùng sau khi retry đã hết; thông báo luôn được che secret."""
        self.failure_count += 1
        self.last_error = _redact(f"{exc.__class__.__name__}: {exc}")[:500]
        self.last_status_code = status_code

    def get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        return self._request("GET", url, params=params, use_cache=use_cache, want="json")

    def get_text(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> str:
        return self._request("GET", url, params=params, use_cache=use_cache, want="text")

    def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]],
        use_cache: bool,
        want: str,
    ) -> Any:
        self.request_count += 1
        key = _cache_key(method, url, params)
        if use_cache and self.cache_ttl != 0:
            cached = _read_cache(key, self.cache_ttl)
            if cached is not None:
                logger.debug("Cache hit: %s", url)
                self.cache_hit_count += 1
                self.success_count += 1
                self.last_error = ""
                self.last_status_code = 200
                return cached["json"] if want == "json" else cached["text"]

        # Lỗi tạm thời (429 rate-limit, 500/502/503/504 server) — chỉ thử lại 1 lần rồi bỏ.
        # Quan trọng khi ingestion gọi HÀNG CHỤC query liên tiếp tới cùng một nguồn (vd 45 query
        # theo CLINICAL_AREAS): nếu nguồn đó đang lỗi/quá tải, retry đủ http_max_retries cho MỖI
        # query sẽ nhân số phút chờ lên hàng chục lần (từng gây treo thật ở OpenAlex 503 và BMJ 429).
        _RETRYABLE_STATUS = (429, 500, 502, 503, 504)
        _MAX_RETRYABLE_RETRIES = 1

        attempt = 0
        attempt_retryable = 0
        last_exc: Optional[Exception] = None
        while attempt <= settings.http_max_retries:
            try:
                _throttle(url, self.min_interval)
                resp = self.session.request(
                    method, url, params=params, timeout=settings.http_timeout
                )
            except requests.RequestException as exc:
                last_exc = exc
                self.transient_failure_count += 1
                wait = self._backoff_wait(attempt, None)
                logger.warning(
                    "Lỗi gọi %s: %s – thử lại sau %.1fs (lần %d)",
                    url, _redact(str(exc)), wait, attempt + 1,
                )
                time.sleep(wait)
                attempt += 1
                continue

            # SỬA 2026-09-05 (Workflow đối kháng đa-agent, vòng 22, phát hiện #2):
            # trước đây chỉ đúng 5 mã (400/401/403/404/410) được coi là "vĩnh
            # viễn". Mọi mã lỗi KHÁC không nằm trong danh sách đó VÀ cũng
            # không nằm trong _RETRYABLE_STATUS (vd 402, 405, 406, 409, 415,
            # 422, 423, 428, 431, 451, 501, 505...) rơi thẳng vào nhánh
            # try/except cuối cùng (dòng ~276) — vốn để bắt lỗi PARSE JSON/kết
            # nối SAU KHI status đã "coi là OK". Vì requests.HTTPError là
            # subclass của requests.RequestException, exception đó bị đối xử
            # y như lỗi tạm thời: retry đủ settings.http_max_retries lần rồi
            # cuối cùng raise một RuntimeError CHUNG CHUNG, mất luôn status
            # code thật (last_status_code không được cập nhật ở nhánh đó) —
            # đúng ngược với chính ý định "4xx vĩnh viễn: retry vô ích, bỏ
            # ngay lần đầu" mà comment gốc tự khai. Với ingestion chạy hàng
            # chục query liên tiếp, một endpoint trả mã lỗi ngoài 2 danh sách
            # gây treo lặp lại nhiều phút — đúng sự cố mà _MAX_RETRYABLE_
            # RETRIES được viết ra để tránh, nhưng lọt qua đường vòng này.
            # Nay MỌI mã lỗi (>=400) không thuộc _RETRYABLE_STATUS đều coi là
            # vĩnh viễn — raise ngay, giữ đúng status code thật.
            if resp.status_code >= 400 and resp.status_code not in _RETRYABLE_STATUS:
                logger.warning("HTTP %s (lỗi vĩnh viễn) từ %s – bỏ qua", resp.status_code, url)
                try:
                    _raise_for_status_redacted(resp)
                except requests.HTTPError as exc:
                    self._record_terminal_failure(exc, resp.status_code)
                    raise
            if resp.status_code in _RETRYABLE_STATUS and attempt_retryable >= _MAX_RETRYABLE_RETRIES:
                logger.warning("HTTP %s từ %s — đã hết hạn mức retry, bỏ qua.", resp.status_code, url)
                try:
                    _raise_for_status_redacted(resp)
                except requests.HTTPError as exc:
                    self._record_terminal_failure(exc, resp.status_code)
                    raise

            # Rate limit / lỗi tạm thời → backoff có giới hạn tối đa rồi thử lại.
            if resp.status_code in _RETRYABLE_STATUS:
                self.transient_failure_count += 1
                attempt_retryable += 1
                wait = self._backoff_wait(attempt, resp)
                logger.warning(
                    "HTTP %s từ %s, thử lại sau %.1fs (lần %d)",
                    resp.status_code, url, wait, attempt + 1,
                )
                time.sleep(wait)
                attempt += 1
                continue

            try:
                _raise_for_status_redacted(resp)
                if want == "json":
                    data = resp.json()
                    payload = {"json": data, "text": None}
                else:
                    data = resp.text
                    payload = {"json": None, "text": data}
            except (requests.RequestException, ValueError) as exc:
                last_exc = exc
                self.transient_failure_count += 1
                wait = self._backoff_wait(attempt, None)
                logger.warning(
                    "Lỗi gọi %s: %s – thử lại sau %.1fs (lần %d)",
                    url, _redact(str(exc)), wait, attempt + 1,
                )
                time.sleep(wait)
                attempt += 1
                continue

            if use_cache and self.cache_ttl != 0:
                _write_cache(key, payload)
            self.success_count += 1
            self.last_error = ""
            self.last_status_code = resp.status_code
            return data

        terminal = RuntimeError(f"Gọi API thất bại sau {settings.http_max_retries} lần: {url}")
        self._record_terminal_failure(terminal)
        raise terminal from last_exc

    def _backoff_wait(self, attempt: int, resp: Optional[requests.Response]) -> float:
        # Giới hạn tối đa 30s để không chặn startup quá lâu (vd BMJ Retry-After: 600)
        _MAX_WAIT = 30.0
        if resp is not None and "Retry-After" in resp.headers:
            try:
                return min(float(resp.headers["Retry-After"]), _MAX_WAIT)
            except ValueError:
                pass
        return min(settings.http_backoff_factor * (2 ** attempt), _MAX_WAIT)
