"""HTTP client tiện ích với retry/backoff, rate-limit handling và cache file đơn giản.

Thiết kế nhỏ gọn, không phụ thuộc thư viện retry ngoài, để dễ kiểm soát và test.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import socket
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests

from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Thêm 17/09/2026: ép một HttpClient thoát qua MỘT card mạng vật lý cụ thể, bất kể
# bảng định tuyến hệ điều hành đang trỏ đi đâu (vd VPN toàn tuyến chiếm route mặc
# định). Lý do: xác nhận 13/09/2026 (xem medical-ebm-automation/CLAUDE.md, mục
# "Nguồn dữ liệu" — Scopus) rằng Cloudflare chặn 403 request tới api.elsevier.com
# khi đi qua IP thoát của VPN cá nhân, TRƯỚC khi chạm logic xác thực của Elsevier —
# đổi header/User-Agent không giúp gì, và tắt hẳn VPN thì mất bảo vệ VPN cho mọi
# việc khác đang chạy cùng lúc. IP_BOUND_IF là socket option CHỈ CÓ trên macOS/
# Darwin (giá trị 25, xem <netinet/in.h>) — đây CHÍNH XÁC là cơ chế `curl
# --interface <tên-card>` dùng để ép gói tin đi qua một interface nhất định bất kể
# route mặc định; không có API tương đương SO_BINDTODEVICE của Linux. Python
# không định nghĩa hằng số này (không có socket.IP_BOUND_IF) nên phải dùng số
# nguyên đã xác minh trực tiếp từ SDK header, không đoán từ tài liệu web.
_IP_BOUND_IF = 25  # macOS-only; xem $(xcrun --show-sdk-path)/usr/include/netinet/in.h


class _InterfaceBoundHTTPAdapter(requests.adapters.HTTPAdapter):
    """HTTPAdapter ép mọi kết nối của session thoát qua MỘT card mạng cụ thể.

    Chỉ hỗ trợ macOS/Darwin — nền tảng khác (Windows) không có socket option
    tương đương đơn giản, và dự án này không cần tính năng này ở đó (chỉ Mac có
    VPN cá nhân toàn tuyến gây xung đột với Scopus)."""

    def __init__(self, if_index: int, *args: Any, **kwargs: Any) -> None:
        self._if_index = if_index
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args: Any, **kwargs: Any) -> None:
        kwargs["socket_options"] = [(socket.IPPROTO_IP, _IP_BOUND_IF, self._if_index)]
        return super().init_poolmanager(*args, **kwargs)

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


# Thêm 20/09/2026 (Consensus gửi khoá qua HEADER `x-api-key`, không qua query): nếu một ngoại lệ vận chuyển mang theo
# nguyên văn header (dạng `x-api-key: <giá trị>` hoặc `'x-api-key': '<giá trị>'`), giá trị cũng phải bị che trước khi
# ghi log. `requests` thường không nhét header vào thông báo lỗi — đây là lớp phòng thủ chiều sâu.
_SENSITIVE_HEADER_RE = re.compile(
    r"""((?:x-api-key|authorization)['"]?\s*[:=]\s*['"]?(?:bearer\s+)?)[^'"\s,}&]+""",
    re.IGNORECASE,
)


def _redact(text: str) -> str:
    """Che giá trị tham số/header nhạy cảm trong một chuỗi URL/thông báo lỗi trước khi ghi log."""
    return _SENSITIVE_HEADER_RE.sub(r"\1***", _SENSITIVE_QUERY_RE.sub(r"\1***", text))


# SỬA 24/09/2026 (kiểm nguồn chứng cứ trên phiên Cloud): proxy thoát mạng của MÔI TRƯỜNG từ chối
# lệnh CONNECT theo CHÍNH SÁCH (403 Forbidden / 407 Proxy Authentication Required). Đo thật trên môi
# trường Cloud «Default — Trusted network access»: MỌI host API y văn (NCBI, Europe PMC, Crossref,
# OpenAlex, ClinicalTrials.gov, openFDA, Semantic Scholar, CORE…) đều nhận đúng lỗi này, dạng
# `ProxyError(... OSError('Tunnel connection failed: 403 Forbidden'))`. Trước bản vá nó bị coi là lỗi
# TẠM THỜI ⇒ retry đủ `http_max_retries` với backoff ≈ 48 giây cho MỖI lời gọi (đo: 7 nguồn × 48 s)
# mà không bao giờ thành công — chính sách không đổi giữa hai lần thử. Chỉ khớp ĐÍCH DANH mã 403/407
# ở bước CONNECT: ProxyError khác (proxy chưa lên, reset kết nối…) vẫn giữ nguyên đường retry cũ.
_PROXY_TU_CHOI_RE = re.compile(r"Tunnel connection failed:\s*(403|407)\b")


def _la_proxy_tu_choi_chinh_sach(exc: BaseException) -> bool:
    """True khi `exc` là proxy thoát mạng TỪ CHỐI theo chính sách (CONNECT → 403/407)."""
    return isinstance(exc, requests.exceptions.ProxyError) and bool(_PROXY_TU_CHOI_RE.search(str(exc)))


# SỬA 29/09/2026 (bác sĩ chọn phương án a cho Scopus): Cloudflare chặn theo IP mạng (VPN) TRƯỚC khi request
# tới máy chủ nguồn. Đo thật cùng ngày: api.elsevier.com trả 403 `server: cloudflare` + `cf-ray`, thân HTML
# «Attention Required! | Cloudflare» có `cf-error-details` và «Cloudflare Ray ID» — GIỐNG HỆT cho khoá đúng lẫn
# khoá sai (lỗi thật của Elsevier là JSON `service-error`). Gắn tiền tố này vào `last_error` để tầng tổng hợp sức
# khoẻ phân biệt «bị chặn theo mạng» với «khoá sai/không có quyền». Đặt ĐẦU chuỗi vì `last_error` bị cắt 500 ký tự.
# Chỉ HTTP 403: trang 5xx/52x của Cloudflare (máy chủ nguồn sập) cũng có «Cloudflare Ray ID» nhưng không phải «bị
# chặn». KHÔNG dùng `/cdn-cgi/challenge-platform/` làm dấu (phản biện 29/09): tính năng JS Detections chèn script đó
# vào MỌI trang HTML đi qua Cloudflare, kể cả trang 403 do chính máy chủ nguồn sinh ra ⇒ trang thách thức nhận qua
# tiêu đề `cf-mitigated` (Cloudflare chỉ đặt khi thật sự ra thách thức).
DAU_CLOUDFLARE_CHAN = "[cloudflare-chan]"
_THAN_TRANG_CHAN_CLOUDFLARE = ("cf-error-details", "cloudflare ray id")


def _la_trang_chan_cloudflare(resp: Any) -> bool:
    """True khi phản hồi 403 là trang chặn/thách thức của CHÍNH Cloudflare (cần tiêu đề Cloudflare VÀ dấu chặn).

    Chỉ `server: cloudflare`/`cf-ray` thì chưa đủ: nguồn đứng sau Cloudflare (vd Elsevier) gắn `cf-ray` cho MỌI phản
    hồi, kể cả lỗi JSON của chính máy chủ nguồn. Dấu chặn = thân có `cf-error-details`/«Cloudflare Ray ID», hoặc tiêu
    đề `cf-mitigated`. Hàm đo đạc — không bao giờ ném lỗi (response giả trong test có thể thiếu trường).
    """
    try:
        if getattr(resp, "status_code", None) != 403:
            return False
        tieu_de = {str(k).lower(): str(v) for k, v in (getattr(resp, "headers", None) or {}).items()}
        if not (tieu_de.get("server", "").lower().startswith("cloudflare") or tieu_de.get("cf-ray")):
            return False
        if tieu_de.get("cf-mitigated"):
            return True
        than = str(getattr(resp, "text", "") or "")[:20000].lower()
        return any(dau in than for dau in _THAN_TRANG_CHAN_CLOUDFLARE)
    except Exception:  # noqa: BLE001 — telemetry không được làm hỏng đường báo lỗi chính
        return False


# THÊM 01/10/2026 (bác sĩ yêu cầu «giải quyết vấn đề VPN triệt để»): ngoài Cloudflare, lỗi TRÊN ĐƯỜNG MẠNG còn mấy
# dạng nữa, trước đây đều lẫn vào «HTTPError 403»/«RuntimeError: Gọi API thất bại sau N lần» nên không ai biết nguồn
# hỏng hay đường mạng hỏng. Đo thật 01/10/2026 qua VPN:
#   • www.ecdc.europa.eu + www.ema.europa.eu: 403 `server: CloudFront`, `x-cache: Error from cloudfront`, thân «ERROR:
#     The request could not be satisfied … Request blocked … Generated by cloudfront (CloudFront)» — trang do CHÍNH mạng
#     phân phối sinh ra, request chưa tới máy chủ nguồn (feed_ecdc_threats lỗi 4/4 lượt 29/09);
#   • iris.who.int: `ConnectTimeout` (máy chủ không đáp lệnh mở kết nối từ IP thoát này) — feed_who_iris lỗi 4/4 lượt
#     29/09 mà Source Log chỉ còn «Gọi API thất bại sau 4 lần», mất kiểu lỗi.
# Nhãn mô tả CÁI ĐO ĐƯỢC (tầng nào chặn/hỏng), KHÔNG phán nguyên nhân: cùng ECDC qua VPN vẫn chạy ngày 21/09 — IP thoát
# đổi theo máy chủ VPN, và IP trực tiếp cũng từng bị NCBI gắn cờ (01→16/09). Đọc nguyên nhân kèm dấu vân đường mạng của
# lượt (`app/utils/mang.py`) và so nhiều lượt. Các nhãn đứng ĐẦU `last_error` (bị cắt 500 ký tự), như
# `DAU_CLOUDFLARE_CHAN`.
DAU_CLOUDFRONT_CHAN = "[cloudfront-chan]"   # trang chặn 403 do CloudFront sinh
DAU_NCBI_CHAN = "[ncbi-chan]"               # NCBI gắn cờ misuse cho IP này (chuyển hướng/trang chặn) — xem `_request`
DAU_PROXY_CHAN = "[proxy-chan]"             # proxy thoát mạng của môi trường từ chối theo chính sách (CONNECT 403/407)
DAU_KET_NOI_HET_GIO = "[ket-noi-het-gio]"   # hết giờ khi MỞ kết nối TCP (không phải hết giờ đọc phản hồi)
DAU_KET_NOI_HONG = "[ket-noi-hong]"         # kết nối bị từ chối/cắt/không tới được
DAU_DNS_HONG = "[dns-hong]"                 # không phân giải được tên máy chủ
DAU_TLS_HONG = "[tls-hong]"                 # bắt tay TLS hỏng (chứng chỉ, bị chen giữa…)
NHAN_DUONG_MANG = (DAU_CLOUDFLARE_CHAN, DAU_CLOUDFRONT_CHAN, DAU_NCBI_CHAN, DAU_PROXY_CHAN, DAU_KET_NOI_HET_GIO,
                   DAU_KET_NOI_HONG, DAU_DNS_HONG, DAU_TLS_HONG)
_THAN_TRANG_CHAN_CLOUDFRONT = ("generated by cloudfront", "the request could not be satisfied")
_DAU_LOI_DNS = ("nameresolutionerror", "failed to resolve", "nodename nor servname", "name or service not known",
                "getaddrinfo failed", "temporary failure in name resolution")


def _la_trang_chan_cloudfront(resp: Any) -> bool:
    """True khi phản hồi 403 là trang lỗi do CHÍNH CloudFront sinh (cần dấu CloudFront ở tiêu đề VÀ ở thân).

    Lỗi 403 của máy chủ nguồn đứng sau CloudFront cũng có `x-amz-cf-id`/`x-cache: Error from cloudfront`, nhưng thân
    là trang của máy chủ nguồn — không có «Generated by cloudfront»/«The request could not be satisfied». Hàm đo đạc —
    không bao giờ ném lỗi."""
    try:
        if getattr(resp, "status_code", None) != 403:
            return False
        tieu_de = {str(k).lower(): str(v) for k, v in (getattr(resp, "headers", None) or {}).items()}
        if not (tieu_de.get("server", "").lower().startswith("cloudfront") or "x-amz-cf-id" in tieu_de):
            return False
        than = str(getattr(resp, "text", "") or "")[:20000].lower()
        return any(dau in than for dau in _THAN_TRANG_CHAN_CLOUDFRONT)
    except Exception:  # noqa: BLE001 — telemetry không được làm hỏng đường báo lỗi chính
        return False


def nhan_trang_chan(resp: Any) -> Optional[str]:
    """Nhãn trang chặn của mạng phân phối (Cloudflare/CloudFront) cho một phản hồi 403, hoặc None."""
    if _la_trang_chan_cloudflare(resp):
        return DAU_CLOUDFLARE_CHAN
    if _la_trang_chan_cloudfront(resp):
        return DAU_CLOUDFRONT_CHAN
    return None


def nhan_loi_ket_noi(exc: Optional[BaseException]) -> Optional[str]:
    """Nhãn tầng mạng cho một ngoại lệ VẬN CHUYỂN của requests, hoặc None.

    Chỉ các lỗi trước khi có phản hồi HTTP: hết giờ ĐỌC (`ReadTimeout` — máy chủ đã nhận kết nối nhưng trả chậm), lỗi
    HTTP, lỗi đọc JSON… KHÔNG có nhãn. Thứ tự kiểm theo cây lớp của requests: ProxyError/SSLError/ConnectTimeout đều là
    lớp con của ConnectionError nên phải xét trước."""
    if exc is None:
        return None
    if isinstance(exc, requests.exceptions.ProxyError):
        return DAU_PROXY_CHAN
    if isinstance(exc, requests.exceptions.SSLError):
        return DAU_TLS_HONG
    if isinstance(exc, requests.exceptions.ConnectTimeout):
        return DAU_KET_NOI_HET_GIO
    if isinstance(exc, requests.exceptions.ConnectionError):
        chuoi = str(exc).lower()
        return DAU_DNS_HONG if any(dau in chuoi for dau in _DAU_LOI_DNS) else DAU_KET_NOI_HONG
    return None


def nhan_duong_mang_cua(thong_diep: Any) -> Optional[str]:
    """Tên nhãn đường mạng (không ngoặc, vd «cloudfront-chan») mà thông điệp lỗi Source Log MỞ ĐẦU bằng, hoặc None."""
    chuoi = str(thong_diep or "")
    for nhan in NHAN_DUONG_MANG:
        if chuoi.startswith(nhan + " "):
            return nhan[1:-1]
    return None


def _raise_for_status_redacted(resp: "requests.Response") -> None:
    """resp.raise_for_status() nhưng che tham số nhạy cảm trong thông báo lỗi trước khi
    exception rời khỏi HttpClient — nơi gọi (vd resolve_pmids() ở evidence_workbench.py)
    log thẳng exc, không đi qua http.py nữa nên phải che tại nguồn."""
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        raise requests.HTTPError(_redact(str(exc)), response=resp) from None


# THÊM 30/09/2026 — nguồn báo giới hạn nhịp qua HEADER RIÊNG, không phải `Retry-After` chuẩn.
# Ca gốc (data/archive/launchd_weekly.log, lượt weekly 29/09/2026, run #44): CORE trả 429, `_backoff_wait` chỉ hiểu
# `Retry-After` dạng SỐ GIÂY nên lùi về backoff 1,5 s, gửi lại khi cửa sổ token của CORE chưa mở ⇒ 429 lần nữa ⇒
# truy vấn kế tiếp gửi ngay sau 0,34 s cũng 429 ⇒ 3 truy vấn liên tiếp hỏng ⇒ cầu dao cắt phần còn lại của nguồn.
# CORE nêu mốc được gọi lại ở `X-RateLimit-Retry-After` dạng MỐC THỜI GIAN ISO-8601 (đo thật 30/09/2026:
# `x-ratelimit-limit: 10`, `x-ratelimit-remaining: 9`, `x-ratelimit-retry-after: 2026-09-30T12:16:23+0000`).
# CHỈ client khai `rate_limit_headers` mới đọc các header này; mọi client khác giữ nguyên hành vi cũ.
@dataclass(frozen=True)
class RateLimitHeaders:
    """Tên các header giới hạn nhịp của MỘT nguồn + trần chờ, để `HttpClient` chờ đúng mốc máy chủ nêu.

    retry_after: header mang thời điểm «được gọi lại» — mốc ISO-8601/HTTP-date/epoch, hoặc số giây tương đối.
    remaining: header mang số lượt/token CÒN LẠI trong cửa sổ hiện tại (None = nguồn không có).
    limit: header mang trần của cửa sổ — chỉ để ghi log cho người đọc (None = không ghi).
    max_wait: trần MỘT lần chờ (giây). Máy chủ hẹn xa hơn trần này ⇒ KHÔNG chờ, truy vấn bị bỏ ngay.
    wait_429_without_hint: số giây chờ khi nhận 429 mà header `retry_after` thiếu, không đọc được hoặc không ở
        tương lai. None = backoff mũ mặc định, y như client không khai chính sách.
    margin: cộng thêm vào mốc máy chủ nêu — header chỉ chính xác tới giây, tới sớm một nhịp là 429 lần nữa.
    """

    retry_after: str
    remaining: Optional[str] = None
    limit: Optional[str] = None
    max_wait: float = 30.0
    wait_429_without_hint: Optional[float] = None
    margin: float = 1.0

    def __post_init__(self) -> None:
        # Cấu hình sai NỔ TO lúc dựng client (một trần ≤ 0 sẽ thành time.sleep(số âm) giữa lượt quét).
        if not isinstance(self.retry_after, str) or not self.retry_after.strip():
            raise ValueError("RateLimitHeaders.retry_after phải là tên header không rỗng")
        if not (isinstance(self.max_wait, (int, float)) and math.isfinite(self.max_wait) and self.max_wait > 0):
            raise ValueError(f"RateLimitHeaders.max_wait phải là số hữu hạn > 0, nhận {self.max_wait!r}")
        if not (isinstance(self.margin, (int, float)) and math.isfinite(self.margin) and self.margin >= 0):
            raise ValueError(f"RateLimitHeaders.margin phải là số hữu hạn >= 0, nhận {self.margin!r}")
        cho = self.wait_429_without_hint
        if cho is not None and not (isinstance(cho, (int, float)) and math.isfinite(cho) and cho >= 0):
            raise ValueError(f"RateLimitHeaders.wait_429_without_hint phải là None hoặc số hữu hạn >= 0, nhận {cho!r}")


# Số ≥ mốc này (09/09/2001) là THỜI ĐIỂM epoch tính bằng giây; ≥ 10^12 là epoch mili-giây; nhỏ hơn là số giây tương đối.
_EPOCH_GIAY_TOI_THIEU = 1_000_000_000
_EPOCH_MILI_GIAY_TOI_THIEU = 1_000_000_000_000


def _parse_moment(value: str) -> Optional[datetime]:
    """Mốc ISO-8601 hoặc HTTP-date → datetime CÓ múi giờ (mốc không ghi múi giờ coi là UTC); None = không đọc được."""
    # strptime trước: nhận đúng dạng CORE trả thật (`2026-09-30T12:16:23+0000`) trên mọi phiên bản Python đang hỗ trợ.
    for doc in (lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z"), datetime.fromisoformat,
                parsedate_to_datetime):
        try:
            moc = doc(value)
        except (TypeError, ValueError):
            continue
        if not isinstance(moc, datetime):
            continue
        return moc if moc.tzinfo is not None else moc.replace(tzinfo=timezone.utc)
    return None


def _seconds_until(value: Any, now: datetime) -> Optional[float]:
    """Giá trị header «được gọi lại lúc nào» → SỐ GIÂY phải chờ tính từ `now` (có thể ≤ 0); None = không đọc được.

    Nhận mốc ISO-8601 (kể cả `+00:00`, `Z`, giây lẻ), HTTP-date (RFC 7231), số epoch (giây hoặc mili-giây) và số
    giây tương đối. Hàm đo đạc — không bao giờ ném lỗi.
    """
    try:
        chuoi = str(value).strip()
        if not chuoi:
            return None
        try:
            so = float(chuoi)
        except ValueError:
            moc = _parse_moment(chuoi)
            return None if moc is None else (moc - now).total_seconds()
        if not math.isfinite(so):
            return None
        if so >= _EPOCH_MILI_GIAY_TOI_THIEU:
            so /= 1000.0
        return so - now.timestamp() if so >= _EPOCH_GIAY_TOI_THIEU else so
    except Exception:  # noqa: BLE001 — telemetry không được làm hỏng đường gọi chính
        return None


def _read_rate_limit(resp: Any, policy: RateLimitHeaders) -> Dict[str, Any]:
    """Đọc header giới hạn nhịp của MỘT phản hồi theo `policy`. Hàm đo đạc — không bao giờ ném lỗi.

    Trả {"remaining": int|None, "wait": float|None, "raw": {tên header: giá trị đã cắt gọn để ghi log}}. `wait` là số
    giây từ «bây giờ» tới mốc được gọi lại (≤ 0 = mốc không ở tương lai; None = thiếu header hoặc không đọc được).
    «Bây giờ» lấy theo ĐỒNG HỒ MÁY CHỦ (header `Date` của chính phản hồi): so mốc của máy chủ với giờ của máy chủ thì
    đồng hồ máy này lệch cũng không làm sai; phản hồi không có `Date` đọc được mới dùng giờ UTC của máy.
    """
    ket_qua: Dict[str, Any] = {"remaining": None, "wait": None, "raw": {}}
    try:
        headers = {str(k).lower(): str(v) for k, v in (getattr(resp, "headers", None) or {}).items()}
        for ten in (policy.limit, policy.remaining, policy.retry_after):
            if ten and ten.lower() in headers:
                ket_qua["raw"][ten] = re.sub(r"[^\x20-\x7e]", "?", headers[ten.lower()])[:60]
        if policy.remaining and policy.remaining.lower() in headers:
            try:
                ket_qua["remaining"] = int(float(headers[policy.remaining.lower()].strip()))
            except (ValueError, OverflowError):
                pass
        if policy.retry_after.lower() in headers:
            bay_gio = _parse_moment(headers.get("date", "")) or datetime.now(timezone.utc)
            ket_qua["wait"] = _seconds_until(headers[policy.retry_after.lower()], bay_gio)
    except Exception:  # noqa: BLE001 — telemetry không được làm hỏng đường gọi chính
        pass
    return ket_qua


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


def _cache_key(method: str, url: str, params: Optional[Dict[str, Any]],
               json_body: Optional[Dict[str, Any]] = None) -> str:
    raw = (f"{method}|{url}|{json.dumps(params or {}, sort_keys=True)}"
           f"|{json.dumps(json_body or {}, sort_keys=True)}")
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
        bind_interface: tên card mạng vật lý (vd "en1") để ép MỌI request của
            client này thoát qua đúng card đó, bỏ qua bảng định tuyến hệ điều
            hành. Chỉ dùng khi cần lách một VPN toàn tuyến cho MỘT nguồn cụ thể
            (xem _InterfaceBoundHTTPAdapter phía trên). None/rỗng = giữ hành vi
            cũ. Chỉ hỗ trợ macOS/Darwin — nền tảng khác nổ lỗi rõ ràng ngay lúc
            khởi tạo thay vì âm thầm bỏ qua, để không ai tưởng lầm nó đang hoạt
            động trên Windows.
        max_retries: trần số LẦN THỬ LẠI riêng cho client này (thêm 20/09/2026). None
            (mặc định) = dùng `settings.http_max_retries` như mọi nguồn khác, hành vi cũ
            giữ nguyên. Đặt 0 = ĐÚNG MỘT request cho mỗi lần gọi, không thử lại bất kể
            lỗi gì (429/5xx, timeout, mất mạng, JSON hỏng). Dành cho API TÍNH PHÍ THEO
            REQUEST (SerpApi: mỗi request là một search bị trừ quota): vòng retry toàn cục
            có thể nhân một truy vấn thành 2-5 request, timeout mà phía server đã xử lý
            xong vẫn có thể bị tính phí nhiều lần. Đặt trần > 0 thì 429/5xx vẫn chỉ thử
            lại tối đa min(1, trần) lần như cũ.
        rate_limit_headers: chính sách đọc header giới hạn nhịp RIÊNG của nguồn (thêm 30/09/2026,
            xem `RateLimitHeaders`). None (mặc định) = hành vi cũ. Có khai thì: (a) 429 ⇒ chờ
            tới đúng mốc máy chủ nêu rồi mới thử lại, thay cho backoff 1,5 giây; (b) phản hồi
            báo hết lượt (remaining ≤ 0, hoặc 429) kèm mốc ở TƯƠNG LAI ⇒ request KẾ TIẾP của
            client này chờ tới mốc đó trước khi gửi. Mốc xa hơn `max_wait` thì không chờ:
            429 đó thành lỗi ngay (chờ tới trần rồi gửi lại cũng vẫn bị từ chối).
    """

    def __init__(
        self,
        default_headers: Optional[Dict[str, str]] = None,
        cache_ttl: Optional[int] = None,
        min_interval: Optional[float] = None,
        bind_interface: Optional[str] = None,
        max_retries: Optional[int] = None,
        rate_limit_headers: Optional[RateLimitHeaders] = None,
    ) -> None:
        if max_retries is not None and (isinstance(max_retries, bool) or not isinstance(max_retries, int)
                                        or max_retries < 0):
            raise ValueError(f"max_retries phải là số nguyên >= 0 hoặc None, nhận {max_retries!r}")
        if rate_limit_headers is not None and not isinstance(rate_limit_headers, RateLimitHeaders):
            raise ValueError(f"rate_limit_headers phải là RateLimitHeaders hoặc None, nhận {rate_limit_headers!r}")
        self.max_retries = max_retries
        self.rate_limit_headers = rate_limit_headers
        # Mốc time.monotonic() mà máy chủ đã nêu: không gửi request kế tiếp trước mốc này (None = không có).
        self._not_before: Optional[float] = None
        self.session = requests.Session()
        if default_headers:
            self.session.headers.update(default_headers)
        self.session.headers.setdefault(
            "User-Agent",
            f"medical-ebm-automation/0.1 (mailto:{settings.ncbi_email or settings.openalex_email or 'unknown'})",
        )
        self.cache_ttl = settings.http_cache_ttl if cache_ttl is None else cache_ttl
        self.min_interval = settings.http_min_interval if min_interval is None else min_interval
        self.bind_interface = bind_interface or None
        if self.bind_interface:
            if sys.platform != "darwin":
                raise RuntimeError(
                    f"bind_interface={self.bind_interface!r} chỉ hỗ trợ macOS/Darwin "
                    f"(IP_BOUND_IF); nền tảng hiện tại là {sys.platform!r}. Bỏ biến môi "
                    "trường tương ứng (vd SCOPUS_BIND_INTERFACE) trên máy này."
                )
            try:
                if_index = socket.if_nametoindex(self.bind_interface)
            except OSError as exc:
                raise RuntimeError(
                    f"Không tìm thấy card mạng '{self.bind_interface}' để ép thoát qua "
                    f"(bind_interface) — kiểm lại tên bằng `ifconfig`/`networksetup "
                    f"-listallhardwareports`: {exc}"
                ) from exc
            adapter = _InterfaceBoundHTTPAdapter(if_index)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
        # Telemetry chỉ chứa trạng thái kỹ thuật, tuyệt đối không giữ URL/query có thể có API key.
        # Ingestion dùng các bộ đếm này để không ghi nhầm lỗi live thành request "ok".
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.transient_failure_count = 0
        self.cache_hit_count = 0
        self.last_error = ""
        self.last_status_code: Optional[int] = None
        # Tổng số giây đã CHỜ NHỊP CHỦ ĐỘNG trước khi gửi (giãn cách tối thiểu cùng host + chờ tới mốc máy chủ nêu).
        # Cầu dao của ingestion trừ phần này khỏi «độ trễ bất thường»: chờ có chủ đích không phải dấu hiệu nguồn
        # trục trặc. KHÔNG gồm thời gian ngủ backoff sau lỗi (429/5xx/mất mạng) — phần đó vẫn là tín hiệu trục trặc.
        self.paced_wait_seconds = 0.0
        # Header giới hạn nhịp của phản hồi gần nhất (chỉ khi khai `rate_limit_headers`) — đưa vào dòng log 429.
        self.last_rate_limit: Dict[str, str] = {}

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
            "paced_wait_seconds": self.paced_wait_seconds,
        }

    def _paced_wait(self, url: str) -> None:
        """Chờ CHỦ ĐỘNG trước khi gửi: tới mốc máy chủ đã nêu (nếu có), rồi giãn cách tối thiểu cùng host.

        Thời gian đã chờ cộng dồn vào `paced_wait_seconds` (đo bằng đồng hồ, không phải bằng số đã xin ngủ)."""
        bat_dau = time.monotonic()
        moc, self._not_before = self._not_before, None
        if moc is not None and moc > bat_dau:
            logger.info("Máy chủ %s báo hết lượt — chờ %.1fs tới mốc được gọi lại rồi mới gửi tiếp%s.",
                        urlparse(url).netloc, moc - bat_dau, self._rate_limit_note())
            time.sleep(moc - bat_dau)
        _throttle(url, self.min_interval)
        self.paced_wait_seconds += max(0.0, time.monotonic() - bat_dau)

    def _note_rate_limit(self, resp: Any) -> Optional[float]:
        """Ghi nhận header giới hạn nhịp của phản hồi vừa nhận; hết lượt kèm mốc TƯƠNG LAI ⇒ đặt mốc «không gửi trước».

        Chỉ đặt mốc khi máy chủ nói RÕ hai điều: đã hết lượt (remaining ≤ 0, hoặc chính phản hồi là 429) VÀ thời
        điểm được gọi lại còn ở phía trước. Còn lượt, hoặc mốc không ở tương lai ⇒ không chờ gì thêm (không đoán).

        Trả số giây phải chờ tới mốc máy chủ nêu (đã cộng lề) khi mốc ở tương lai, ngược lại None — `_backoff_wait`
        dùng lại đúng con số này cho 429, không đọc header lần thứ hai. Mốc XA HƠN `max_wait` (vd hết hạn mức theo
        ngày) ⇒ trả `math.inf` và KHÔNG đặt mốc: chờ tới trần rồi gửi lại chắc chắn vẫn bị từ chối, nên `_request`
        bỏ truy vấn ngay thay vì ngủ vô ích — ba truy vấn hỏng nhanh thì cầu dao cắt trong vài giây."""
        policy = self.rate_limit_headers
        if policy is None:
            return None
        nhip = _read_rate_limit(resp, policy)
        self.last_rate_limit = nhip["raw"]
        if nhip["wait"] is None or nhip["wait"] <= 0:
            return None
        cho = nhip["wait"] + policy.margin
        if cho > policy.max_wait:
            return math.inf
        if (nhip["remaining"] is not None and nhip["remaining"] <= 0) or getattr(resp, "status_code", None) == 429:
            self._not_before = time.monotonic() + cho
        return cho

    def _rate_limit_note(self) -> str:
        """Đuôi dòng log: các header giới hạn nhịp của phản hồi gần nhất (rỗng nếu không có)."""
        if not self.last_rate_limit:
            return ""
        return " [" + ", ".join(f"{k}={v}" for k, v in self.last_rate_limit.items()) + "]"

    def _record_terminal_failure(self, exc: Exception, status_code: Optional[int] = None,
                                 resp: Any = None, nguyen_nhan: Optional[BaseException] = None,
                                 nhan: Optional[str] = None) -> None:
        """Ghi một lỗi cuối cùng sau khi retry đã hết; thông báo luôn được che secret.

        Nhãn đường mạng đứng ĐẦU chuỗi (xem chú thích `NHAN_DUONG_MANG`): `nhan` do nơi gọi chỉ định (vd chặn NCBI),
        nếu không thì suy từ `resp` (trang chặn Cloudflare/CloudFront) hoặc từ `nguyen_nhan` — ngoại lệ vận chuyển
        cuối cùng trước khi bỏ cuộc. Có `nguyen_nhan` khác `exc` thì ghi thêm tên lớp của nó: thông điệp ngoại lệ ném
        ra ngoài GIỮ NGUYÊN, chỉ chuỗi telemetry `last_error` (→ Source Log) có thêm thông tin."""
        self.failure_count += 1
        ten_lop = exc.__class__.__name__
        if nguyen_nhan is not None and nguyen_nhan is not exc:
            ten_lop = f"{ten_lop} (lỗi cuối: {nguyen_nhan.__class__.__name__})"
        loi = _redact(f"{ten_lop}: {exc}")
        nhan = nhan or (nhan_trang_chan(resp) if resp is not None else None) or nhan_loi_ket_noi(nguyen_nhan)
        if nhan:
            loi = f"{nhan} {loi}"
        self.last_error = loi[:500]
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

    def get_bytes(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """GET rồi trả về bytes thô — dùng để tải PDF/nhị phân (thêm 23/09/2026 cho
        các connector toàn văn guideline như GOLD/GINA). KHÔNG cache: định dạng cache
        file hiện có (`_write_cache`) lưu JSON {"json","text"}, không phù hợp với nội
        dung nhị phân lớn — mỗi lần gọi luôn tải mới, nhưng vẫn hưởng đủ retry/backoff/
        throttle/phát hiện chặn NCBI của `_request()`."""
        return self._request("GET", url, params=params, use_cache=False, want="bytes")

    def post_json(
        self,
        url: str,
        json_body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_cache: bool = False,
    ) -> Dict[str, Any]:
        """POST + đọc JSON. `use_cache` mặc định FALSE (khác GET) vì POST trong
        repo này thường gọi endpoint cấp TOKEN OAuth2 (client_credentials) —
        access_token là bí mật, TUYỆT ĐỐI không được ghi ra cache file trên đĩa
        (`data/raw/_http_cache/`). Truyền use_cache=True tường minh cho các POST
        không mang bí mật (vd endpoint tìm kiếm chỉ có query công khai)."""
        return self._request("POST", url, params=params, use_cache=use_cache,
                              want="json", json_body=json_body, headers=headers)

    def _request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]],
        use_cache: bool,
        want: str,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        self.request_count += 1
        key = _cache_key(method, url, params, json_body)
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

        # Trần retry riêng của client (xem tham số `max_retries` ở docstring lớp). None = hành vi
        # cũ, dùng cấu hình toàn cục; số cụ thể (vd 0 cho API tính phí theo request) thì cả vòng
        # lặp lẫn hạn mức retry của 429/5xx đều không được vượt trần đó.
        rieng = getattr(self, "max_retries", None)
        max_retries = settings.http_max_retries if rieng is None else rieng
        tran_retryable = _MAX_RETRYABLE_RETRIES if rieng is None else min(_MAX_RETRYABLE_RETRIES, rieng)

        attempt = 0
        attempt_retryable = 0
        last_exc: Optional[Exception] = None
        while attempt <= max_retries:
            try:
                self._paced_wait(url)
                # Chỉ thêm json=/headers= khi THẬT SỰ dùng (POST) — giữ nguyên
                # đúng chữ ký lời gọi cũ (method, url, params=, timeout=) cho
                # mọi GET hiện có, để không phá vỡ các test/fake session.request
                # đã viết trước khi có post_json() (chúng không khai kwargs này).
                extra: Dict[str, Any] = {}
                if json_body is not None:
                    extra["json"] = json_body
                if headers is not None:
                    extra["headers"] = headers
                resp = self.session.request(
                    method, url, params=params, timeout=settings.http_timeout, **extra
                )
            except requests.RequestException as exc:
                # Proxy môi trường từ chối theo CHÍNH SÁCH ⇒ bỏ ngay, không retry (xem
                # `_la_proxy_tu_choi_chinh_sach`). Nói rõ host bị chặn và chỗ sửa để người đọc
                # không nhầm «môi trường chặn» thành «nguồn hỏng» (họ BH08).
                if _la_proxy_tu_choi_chinh_sach(exc):
                    host = urlparse(url).hostname or url
                    loi = RuntimeError(
                        f"Proxy thoát mạng của môi trường này TỪ CHỐI kết nối tới {host} theo "
                        "chính sách mạng (CONNECT 403/407) — KHÔNG phải nguồn hỏng hay lỗi tạm "
                        "thời, retry không giúp gì. Trên phiên Cloud: sửa môi trường → Network "
                        f"access → Custom, thêm «{host}» vào Allowed domains (hoặc chọn Full)."
                    )
                    logger.warning("Proxy từ chối theo chính sách (bỏ ngay, không retry): %s",
                                   _redact(url))
                    self._record_terminal_failure(loi, nguyen_nhan=exc)
                    raise loi from exc
                last_exc = exc
                self.transient_failure_count += 1
                wait = self._backoff_wait(attempt, None)
                if self._con_luot_thu_lai(attempt, max_retries):
                    logger.warning(
                        "Lỗi gọi %s: %s – thử lại sau %.1fs (lần %d)",
                        url, _redact(str(exc)), wait, attempt + 1,
                    )
                    time.sleep(wait)
                else:
                    logger.warning(
                        "Lỗi gọi %s: %s – KHÔNG thử lại (max_retries=%d riêng của client này)",
                        url, _redact(str(exc)), max_retries,
                    )
                attempt += 1
                continue

            # Nguồn khai header giới hạn nhịp riêng: ghi nhận NGAY khi có phản hồi (kể cả 429/5xx) để request kế tiếp
            # — lần thử lại của chính truy vấn này hoặc truy vấn sau — không gửi trước mốc máy chủ nêu.
            cho_theo_may_chu = self._note_rate_limit(resp)

            # SỬA 2026-09-16: NCBI đôi khi CHUYỂN HƯỚNG (302) mọi request
            # eutils.ncbi.nlm.nih.gov sang misuse.ncbi.nlm.nih.gov/error/abuse.shtml —
            # trang cảnh báo lạm dụng CHÍNH THỨC, trả về HTTP 200 (không phải 4xx/5xx)
            # kèm nội dung HTML "NCBI Error Access Denied". Vì status là 200, request
            # KHÔNG rơi vào hai nhánh retryable/permanent ngay dưới đây; nó chỉ bị bắt
            # muộn ở `resp.json()` (ValueError vì thân HTML không phải JSON) và từ đó
            # bị đối xử như lỗi TẠM THỜI — retry đủ `settings.http_max_retries` lần với
            # backoff mũ (mặc định ~46 giây tổng cộng CHO MỖI truy vấn) dù chặn này
            # KHÔNG BAO GIỜ tự hết bằng cách gọi lại — đây là chặn IP phía máy chủ
            # NCBI (nghi ngờ misuse/abuse từ mạng dùng chung), không phải lỗi mạng.
            # Với pipeline gọi hàng chục truy vấn PubMed liên tiếp, hành vi cũ có thể
            # tiêu tốn hàng chục phút vô ích trước khi các nguồn dự phòng (Europe PMC,
            # Retraction Watch ngoại tuyến) được thử. Phát hiện ĐÍCH DANH host đích sau
            # khi chuyển hướng và bỏ ngay, không retry — để dây chuyền chuyển sang
            # nguồn khác gần như tức thì. Không thể "sửa" được chặn này bằng mã nguồn:
            # chỉ NCBI (qua info@ncbi.nlm.nih.gov) hoặc thời gian mới gỡ được.
            # `getattr(resp, "url", "")` — không `resp.url` trần: response giả trong
            # nhiều bộ test cũ (test_http_retry.py, ...vong22_unlisted_status...) chỉ
            # khai status_code/json_data/text/headers, KHÔNG có `.url`. requests.Response
            # thật LUÔN có `.url`; chỉ fake tối giản trong test mới thiếu — đọc trần sẽ
            # làm AttributeError bung ra ở toàn bộ test cũ đó (đã tái hiện và xác nhận).
            if urlparse(getattr(resp, "url", "")).netloc.endswith("misuse.ncbi.nlm.nih.gov"):
                exc = RuntimeError(
                    "NCBI đã CHẶN mạng này do nghi ngờ lạm dụng/misuse (chuyển hướng "
                    "sang misuse.ncbi.nlm.nih.gov) — đây là chặn PHÍA MÁY CHỦ NCBI, "
                    "KHÔNG phải lỗi mạng tạm thời, retry không giúp ích. Nhờ quản trị "
                    "mạng liên hệ info@ncbi.nlm.nih.gov để xin gỡ chặn, hoặc chờ nhãn "
                    "misuse tự hết sau một khoảng thời gian không hoạt động."
                )
                logger.warning("NCBI misuse-block (bỏ ngay, không retry): %s", url)
                self._record_terminal_failure(exc, resp.status_code, nhan=DAU_NCBI_CHAN)
                raise exc

            # SỬA 2026-09-16 (vòng 2, đo thật ngay sau bản vá ở trên): redirect sang
            # misuse.ncbi.nlm.nih.gov KHÔNG PHẢI biểu hiện DUY NHẤT của chặn NCBI. Gọi
            # count_hits() thật hai lần liên tiếp (cùng ngày, cùng query) cho kết quả
            # KHÁC NHAU: lần đầu/ba raise ngay đúng như bản vá phía trên dự tính, nhưng
            # lần hai lại rơi trở lại vòng retry 5 lần cũ (~46-53 giây) — trang chặn vẫn
            # xuất hiện (đã xác nhận bằng cách gọi `session.request()` thủ công ngay sau
            # đó, cùng tham số, `resp.url` VẪN là misuse.ncbi.nlm.nih.gov) nhưng đường
            # phát hiện phía trên không bắt được ở lượt đó — khả năng cao do NCBI không
            # trả redirect/nội dung nhất quán 100% cho một IP đã bị gắn cờ. Vá bằng lớp
            # phòng thủ THỨ HAI, độc lập với `resp.url`: đọc thẳng THÂN response — cùng
            # chữ ký trang chặn mà `app/sources/pubmed.py::_trang_chan_ncbi()` đã dùng
            # cho nhánh efetch (tiêu đề "WWW Error Blocked Diagnostic" hoặc câu "blocked
            # for possible abuse") — nhưng CỐ Ý chỉ áp dụng khi URL đang gọi thuộc domain
            # *.ncbi.nlm.nih.gov, để không lặp lại kiểu quá tay mà
            # test_chuyen_huong_sang_host_khac_khong_trung_bo_loi_misuse() đã canh: một
            # trang lỗi HTML của host KHÁC (vd trang bảo trì) không được coi là chặn NCBI
            # chỉ vì thân không phải JSON.
            if urlparse(url).hostname and urlparse(url).hostname.endswith("ncbi.nlm.nih.gov"):
                than = (getattr(resp, "text", "") or "")[:400].lower()
                if "blocked diagnostic" in than or "blocked for possible abuse" in than:
                    exc = RuntimeError(
                        "NCBI đã CHẶN mạng này do nghi ngờ lạm dụng/misuse (trang "
                        "'WWW Error Blocked Diagnostic' trong thân response, không qua "
                        "redirect sang misuse.ncbi.nlm.nih.gov lần này) — đây là chặn "
                        "PHÍA MÁY CHỦ NCBI, KHÔNG phải lỗi mạng tạm thời, retry không "
                        "giúp ích. Nhờ quản trị mạng liên hệ info@ncbi.nlm.nih.gov để "
                        "xin gỡ chặn, hoặc chờ nhãn misuse tự hết sau một khoảng thời "
                        "gian không hoạt động."
                    )
                    logger.warning(
                        "NCBI misuse-block qua thân response (bỏ ngay, không retry): %s", url,
                    )
                    self._record_terminal_failure(exc, resp.status_code, nhan=DAU_NCBI_CHAN)
                    raise exc

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
                    self._record_terminal_failure(exc, resp.status_code, resp)
                    raise
            if resp.status_code == 429 and cho_theo_may_chu == math.inf:
                logger.warning("HTTP 429 từ %s — máy chủ hẹn gọi lại SAU trần chờ %.0fs của nguồn này; bỏ truy vấn "
                               "ngay, không ngủ rồi gửi lại vô ích.%s",
                               url, self.rate_limit_headers.max_wait, self._rate_limit_note())
                try:
                    _raise_for_status_redacted(resp)
                except requests.HTTPError as exc:
                    self._record_terminal_failure(exc, resp.status_code)
                    raise
            if resp.status_code in _RETRYABLE_STATUS and attempt_retryable >= tran_retryable:
                logger.warning("HTTP %s từ %s — đã hết hạn mức retry, bỏ qua.%s",
                               resp.status_code, url, self._rate_limit_note())
                try:
                    _raise_for_status_redacted(resp)
                except requests.HTTPError as exc:
                    self._record_terminal_failure(exc, resp.status_code)
                    raise

            # Rate limit / lỗi tạm thời → backoff có giới hạn tối đa rồi thử lại.
            if resp.status_code in _RETRYABLE_STATUS:
                self.transient_failure_count += 1
                attempt_retryable += 1
                wait = self._backoff_wait(attempt, resp, cho_theo_may_chu)
                logger.warning(
                    "HTTP %s từ %s, thử lại sau %.1fs (lần %d)%s",
                    resp.status_code, url, wait, attempt + 1, self._rate_limit_note(),
                )
                time.sleep(wait)
                attempt += 1
                continue

            try:
                _raise_for_status_redacted(resp)
                if want == "json":
                    data = resp.json()
                    payload = {"json": data, "text": None}
                elif want == "bytes":
                    data = resp.content
                    payload = None  # get_bytes() luôn use_cache=False, xem docstring
                else:
                    data = resp.text
                    payload = {"json": None, "text": data}
            except (requests.RequestException, ValueError) as exc:
                last_exc = exc
                self.transient_failure_count += 1
                wait = self._backoff_wait(attempt, None)
                if self._con_luot_thu_lai(attempt, max_retries):
                    logger.warning(
                        "Lỗi gọi %s: %s – thử lại sau %.1fs (lần %d)",
                        url, _redact(str(exc)), wait, attempt + 1,
                    )
                    time.sleep(wait)
                else:
                    logger.warning(
                        "Lỗi gọi %s: %s – KHÔNG thử lại (max_retries=%d riêng của client này)",
                        url, _redact(str(exc)), max_retries,
                    )
                attempt += 1
                continue

            if use_cache and self.cache_ttl != 0 and payload is not None:
                _write_cache(key, payload)
            self.success_count += 1
            self.last_error = ""
            self.last_status_code = resp.status_code
            return data

        if rieng is None:
            terminal = RuntimeError(f"Gọi API thất bại sau {settings.http_max_retries} lần: {url}")
        else:
            terminal = RuntimeError(f"Gọi API thất bại (max_retries={rieng} riêng của client, "
                                    f"đã gửi {attempt} request): {url}")
        # Ngoại lệ ném ra GIỮ NGUYÊN thông điệp; `last_error` mang thêm nhãn tầng mạng + tên lớp lỗi cuối (01/10/2026:
        # trước đây Source Log chỉ còn «Gọi API thất bại sau N lần», không phân biệt mất kết nối với JSON hỏng).
        self._record_terminal_failure(terminal, nguyen_nhan=last_exc)
        raise terminal from last_exc

    def _con_luot_thu_lai(self, attempt: int, max_retries: int) -> bool:
        """Còn lượt thử lại sau lần thử thứ `attempt` (đánh số từ 0) không?

        Client mặc định (max_retries=None) luôn trả True để giữ NGUYÊN hành vi cũ, kể cả việc
        ngủ backoff sau lần thử cuối. Client có trần riêng thì hết lượt là không ngủ vô ích."""
        return getattr(self, "max_retries", None) is None or attempt < max_retries

    def _backoff_wait(self, attempt: int, resp: Optional[requests.Response],
                      rate_limit_wait: Optional[float] = None) -> float:
        # Nguồn khai header giới hạn nhịp riêng (vd CORE) bị 429: chờ tới ĐÚNG mốc máy chủ nêu (`rate_limit_wait`, do
        # `_note_rate_limit` tính từ chính phản hồi này). Máy chủ không nêu mốc dùng được ⇒ chờ `wait_429_without_hint`
        # (nếu khai), không đoán bằng backoff 1,5 giây — chính khoảng chờ quá ngắn đó làm lượt weekly 29/09/2026 hỏng
        # 3 truy vấn liên tiếp.
        policy = getattr(self, "rate_limit_headers", None)
        if policy is not None and resp is not None and getattr(resp, "status_code", None) == 429:
            if rate_limit_wait is not None and math.isfinite(rate_limit_wait):
                return rate_limit_wait
            if policy.wait_429_without_hint is not None:
                return min(policy.wait_429_without_hint, policy.max_wait)
        # Giới hạn tối đa 30s để không chặn startup quá lâu (vd BMJ Retry-After: 600)
        _MAX_WAIT = 30.0
        if resp is not None and "Retry-After" in resp.headers:
            try:
                return min(float(resp.headers["Retry-After"]), _MAX_WAIT)
            except ValueError:
                pass
        return min(settings.http_backoff_factor * (2 ** attempt), _MAX_WAIT)
