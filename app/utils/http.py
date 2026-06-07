"""HTTP client tiện ích với retry/backoff, rate-limit handling và cache file đơn giản.

Thiết kế nhỏ gọn, không phụ thuộc thư viện retry ngoài, để dễ kiểm soát và test.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests

from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

_CACHE_DIR = settings.raw_dir / "_http_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Thời điểm request gần nhất theo host, để giãn cách chủ động (NCBI etiquette).
_last_request_at: Dict[str, float] = {}


def _throttle(url: str, min_interval: float) -> None:
    """Ngủ vừa đủ để 2 request cùng host cách nhau >= min_interval giây."""
    if min_interval <= 0:
        return
    host = urlparse(url).netloc
    last = _last_request_at.get(host)
    now = time.monotonic()
    if last is not None:
        elapsed = now - last
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
    _last_request_at[host] = time.monotonic()


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
        key = _cache_key(method, url, params)
        if use_cache and self.cache_ttl != 0:
            cached = _read_cache(key, self.cache_ttl)
            if cached is not None:
                logger.debug("Cache hit: %s", url)
                return cached["json"] if want == "json" else cached["text"]

        attempt = 0
        last_exc: Optional[Exception] = None
        while attempt <= settings.http_max_retries:
            try:
                _throttle(url, self.min_interval)
                resp = self.session.request(
                    method, url, params=params, timeout=settings.http_timeout
                )
                # Rate limit / lỗi tạm thời → backoff
                if resp.status_code in (429, 500, 502, 503, 504):
                    wait = self._backoff_wait(attempt, resp)
                    logger.warning(
                        "HTTP %s từ %s, thử lại sau %.1fs (lần %d)",
                        resp.status_code, url, wait, attempt + 1,
                    )
                    time.sleep(wait)
                    attempt += 1
                    continue
                resp.raise_for_status()

                if want == "json":
                    data = resp.json()
                    payload = {"json": data, "text": None}
                else:
                    data = resp.text
                    payload = {"json": None, "text": data}

                if use_cache and self.cache_ttl != 0:
                    _write_cache(key, payload)
                return data
            except (requests.RequestException, ValueError) as exc:
                last_exc = exc
                wait = self._backoff_wait(attempt, None)
                logger.warning(
                    "Lỗi gọi %s: %s – thử lại sau %.1fs (lần %d)",
                    url, exc, wait, attempt + 1,
                )
                time.sleep(wait)
                attempt += 1

        raise RuntimeError(f"Gọi API thất bại sau {settings.http_max_retries} lần: {url}") from last_exc

    def _backoff_wait(self, attempt: int, resp: Optional[requests.Response]) -> float:
        if resp is not None and "Retry-After" in resp.headers:
            try:
                return float(resp.headers["Retry-After"])
            except ValueError:
                pass
        return settings.http_backoff_factor * (2 ** attempt)
