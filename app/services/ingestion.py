"""Bước 1: Ingestion – gọi nguồn theo chuyên khoa & từ khóa, lưu raw, ghi Source Log.

TĂNG TỐC: chạy SONG SONG để rút ngắn thời gian quét.
- Mỗi nguồn API (PubMed/EuropePMC/Crossref/OpenAlex/ClinicalTrials) chạy 1 luồng riêng,
  BÊN TRONG vẫn tuần tự các từ khoá -> tôn trọng giới hạn tốc độ từng nguồn (vd NCBI 3 req/s).
- Các RSS feed chạy song song nhưng GIỚI HẠN số luồng (tránh bị chặn 429, vd nhiều feed BMJ).
- Source Log gom lại và ghi DB MỘT LẦN ở cuối (tránh khóa SQLite khi nhiều luồng cùng ghi).
"""
from __future__ import annotations

import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

from app.config import CLINICAL_AREAS, settings
from app.database import session_scope
from app.models import SourceLog
from app.sources import get_enabled_sources
from app.sources.base import RawRecord
from app.sources.openfda import OpenFDAClient
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Số luồng tối đa cho RSS feed (vừa đủ nhanh, tránh 429 từ host dùng chung như bmj.com).
_FEED_WORKERS = 4

# --- Circuit-breaker cho sweep_source (một nguồn lỗi/chậm liên tục -> dừng sớm) ---
_MAX_CONSECUTIVE_ERRORS = 3  # nguồn lỗi liên tục (vd outage/503 diện rộng) -> dừng sớm
# Nhiều source client (vd OpenAlexClient.search) tự bắt exception mạng nội bộ và trả về [],
# nên "status" trong log luôn "ok" dù request thật sự đã lỗi — status không dùng được làm tín
# hiệu. Độ trễ bất thường (đã trải qua backoff của http.py, xem app/utils/http.py) là tín hiệu
# đáng tin cậy hơn: 1 lần gọi bình thường thường <5s; 1 lần đã retry luôn mất nhiều giây hơn hẳn.
_SLOW_QUERY_THRESHOLD_SEC = 10.0

_DISCOVERY_CORE = {"pubmed", "europepmc", "crossref"}
_SAFETY_FEEDS = {"feed_fda_medwatch", "feed_fda_recalls", "feed_mhra_dsu"}


def _http_snapshot(client: object) -> Dict[str, Any]:
    """Đọc telemetry HTTP không chứa secret; connector cũ không hỗ trợ thì trả bộ đếm 0."""
    http = getattr(client, "http", None)
    getter = getattr(http, "health_snapshot", None)
    if callable(getter):
        return dict(getter())
    return {
        "request_count": 0,
        "success_count": 0,
        "failure_count": 0,
        "transient_failure_count": 0,
        "cache_hit_count": 0,
        "last_error": "",
        "last_status_code": None,
    }


def _counter_delta(before: Dict[str, Any], after: Dict[str, Any], key: str) -> int:
    return max(0, int(after.get(key) or 0) - int(before.get(key) or 0))


def summarize_source_health(
    logs: List[dict],
    *,
    expected_api_sources: List[str],
    expected_feed_sources: List[str],
    safety_enabled: bool,
) -> dict:
    """Tổng hợp độ phủ nguồn để pipeline phân biệt PASS/PARTIAL/FAIL.

    Một feed tùy chọn lỗi không làm hỏng cả lượt quét khi các kênh cùng nhóm còn đủ
    dự phòng. Ngược lại, mock trong live, mất toàn bộ kênh an toàn/guideline, hoặc
    thiếu phần lớn nguồn discovery lõi là lỗi cứng.
    """
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"requests": 0, "records": 0, "ok": 0, "degraded": 0, "error": 0, "mock": 0}
    )
    for row in logs:
        source = str(row.get("source") or "unknown")
        item = grouped[source]
        item["requests"] += 1
        item["records"] += int(row.get("record_count") or 0)
        status = str(row.get("status") or "error")
        item[status if status in {"ok", "degraded", "error", "mock"} else "error"] += 1

    source_rows: dict[str, dict[str, Any]] = {}
    for source, item in sorted(grouped.items()):
        live_success = item["ok"] + item["degraded"]
        error_rate = item["error"] / max(1, item["requests"])
        if item["mock"]:
            health = "mock"
        elif live_success == 0:
            health = "unavailable"
        elif error_rate > 0.20:
            health = "degraded"
        else:
            health = "ok"
        source_rows[source] = {**item, "error_rate": round(error_rate, 4), "health": health}

    expected_api = set(expected_api_sources)
    expected_feeds = set(expected_feed_sources)
    discovery_expected = sorted(expected_api & _DISCOVERY_CORE)
    discovery_healthy = [
        name for name in discovery_expected
        if source_rows.get(name, {}).get("health") in {"ok", "degraded"}
    ]
    safety_expected = set(_SAFETY_FEEDS & expected_feeds)
    if safety_enabled:
        safety_expected.add("openfda")
    safety_healthy = [
        name for name in sorted(safety_expected)
        if source_rows.get(name, {}).get("health") in {"ok", "degraded"}
    ]
    guideline_expected = sorted(expected_feeds - _SAFETY_FEEDS)
    guideline_healthy = [
        name for name in guideline_expected
        if source_rows.get(name, {}).get("health") in {"ok", "degraded"}
    ]

    mock_sources = sorted(name for name, item in source_rows.items() if item["health"] == "mock")
    hard_fail_reasons: list[str] = []
    total_records = sum(int(item["records"]) for item in source_rows.values())
    min_discovery = min(2, len(discovery_expected))
    if mock_sources:
        hard_fail_reasons.append("MOCK_DETECTED_IN_LIVE")
    if total_records == 0:
        hard_fail_reasons.append("NO_RECORDS_FROM_ANY_SOURCE")
    if len(discovery_healthy) < min_discovery:
        hard_fail_reasons.append("DISCOVERY_CORE_COVERAGE_INSUFFICIENT")
    if safety_expected and not safety_healthy:
        hard_fail_reasons.append("SAFETY_SOURCE_COVERAGE_MISSING")
    if guideline_expected and not guideline_healthy:
        hard_fail_reasons.append("GUIDELINE_SOURCE_COVERAGE_MISSING")

    degraded_required = sorted(
        name for name in set(discovery_expected) | safety_expected
        if source_rows.get(name, {}).get("health") in {"degraded", "unavailable"}
    )
    redundancy_warnings: list[str] = []
    if len(safety_healthy) < min(2, len(safety_expected)):
        redundancy_warnings.append("SAFETY_REDUNDANCY_LOW")
    if len(guideline_healthy) < min(3, len(guideline_expected)):
        redundancy_warnings.append("GUIDELINE_REDUNDANCY_LOW")

    if hard_fail_reasons:
        overall = "FAIL"
    elif degraded_required or redundancy_warnings:
        overall = "PARTIAL"
    else:
        overall = "PASS"
    return {
        "status": overall,
        "hard_fail_reasons": hard_fail_reasons,
        "warnings": redundancy_warnings,
        "degraded_required_sources": degraded_required,
        "total_records": total_records,
        "discovery_core": {"expected": discovery_expected, "healthy": discovery_healthy},
        "safety": {"expected": sorted(safety_expected), "healthy": safety_healthy},
        "guideline": {"expected": guideline_expected, "healthy": guideline_healthy},
        "sources": source_rows,
    }


def sweep_source(client, areas: List[str], max_results_per_query: int,
                  since_date: Optional[str] = None, fetch_fn=None) -> Tuple[List[RawRecord], List[dict]]:
    """Quét 1 nguồn API qua mọi (area, query) theo CLINICAL_AREAS — tuần tự, có circuit-breaker.

    Tách khỏi `ingest_all()` (trước là closure nội bộ) để test được độc lập, không cần
    dựng toàn bộ pipeline/ThreadPoolExecutor/DB. `fetch_fn` injectable cho test (mặc định `_fetch`).
    """
    fetch_fn = fetch_fn or _fetch
    recs: List[RawRecord] = []
    logs: List[dict] = []
    total_queries = sum(len(CLINICAL_AREAS.get(a, [])) for a in areas)
    consecutive_errors = 0
    for area in areas:
        for query in CLINICAL_AREAS.get(area, []):
            started = time.monotonic()
            r, log = fetch_fn(client, query, area, max_results_per_query, since_date)
            elapsed = time.monotonic() - started
            recs.extend(r)
            logs.append(log)
            if log["status"] == "error" or elapsed >= _SLOW_QUERY_THRESHOLD_SEC:
                consecutive_errors += 1
                if consecutive_errors >= _MAX_CONSECUTIVE_ERRORS:
                    skipped = total_queries - len(logs)
                    logger.warning(
                        "Nguồn %s lỗi/chậm liên tiếp %d lần (có thể đang gián đoạn) — "
                        "bỏ qua %d truy vấn còn lại thay vì thử hết, tránh treo lâu.",
                        client.name, consecutive_errors, skipped,
                    )
                    return recs, logs
            else:
                consecutive_errors = 0
    return recs, logs


def ingest_all(max_results_per_query: int = 10,
               areas: Optional[List[str]] = None,
               since_date: Optional[str] = None,
               diagnostics: Optional[dict] = None) -> List[RawRecord]:
    """Quét toàn bộ nguồn đang bật theo danh mục chuyên khoa (song song).

    since_date: 'YYYY-MM-DD' – ở chế độ live chỉ lấy bài MỚI kể từ ngày này.
    Trả về danh sách RawRecord gộp từ mọi nguồn. Ghi Source Log cho từng lần gọi.
    """
    areas = areas or list(CLINICAL_AREAS.keys())
    sources = get_enabled_sources()
    all_records: List[RawRecord] = []
    all_logs: List[dict] = []

    if since_date:
        logger.info("Ingestion: lọc bài MỚI kể từ %s", since_date)

    def sweep_fda(_=None) -> Tuple[List[RawRecord], List[dict]]:
        recs: List[RawRecord] = []
        logs: List[dict] = []
        fda = OpenFDAClient()
        for drug in ("sglt2", "metformin", "warfarin", "amiodarone"):
            r, log = _fetch(fda, drug, "An toàn thuốc", max_results_per_query, since_date)
            recs.extend(r)
            logs.append(log)
        return recs, logs

    # --- Tác vụ theo FEED: mỗi feed 1 tác vụ (luồng giới hạn riêng) ---
    from app.sources.rss_feed import get_feed_clients
    feed_clients = get_feed_clients(settings.enable_drug_safety_feeds,
                                    settings.enable_guideline_feeds)

    def fetch_feed(fc) -> Tuple[List[RawRecord], List[dict]]:
        r, log = _fetch(fc, "", fc.feed.clinical_area or "",
                        max_results_per_query, since_date)
        return r, [log]

    # Chạy nguồn API + openFDA (luồng theo host) ĐỒNG THỜI với feed (luồng giới hạn).
    src_tasks = list(sources) + ([_FDA_SENTINEL] if settings.enable_openfda else [])
    n_src_workers = max(1, len(src_tasks))
    with ThreadPoolExecutor(max_workers=n_src_workers) as src_pool:
        src_futs = [
            src_pool.submit(sweep_fda, c) if c is _FDA_SENTINEL
            else src_pool.submit(sweep_source, c, areas, max_results_per_query, since_date)
            for c in src_tasks
        ]
        # Feed pool chạy song song trong khi nguồn API đang quét
        with ThreadPoolExecutor(max_workers=_FEED_WORKERS) as feed_pool:
            feed_futs = [feed_pool.submit(fetch_feed, fc) for fc in feed_clients]
            for fut in feed_futs:
                recs, logs = fut.result()
                all_records.extend(recs)
                all_logs.extend(logs)
        for fut in src_futs:
            recs, logs = fut.result()
            all_records.extend(recs)
            all_logs.extend(logs)

    # Ghi toàn bộ Source Log MỘT LẦN (tránh nhiều luồng ghi SQLite đồng thời).
    if all_logs:
        with session_scope() as s:
            s.add_all([SourceLog(**lg) for lg in all_logs])

    source_health = summarize_source_health(
        all_logs,
        expected_api_sources=[client.name for client in sources],
        expected_feed_sources=[client.name for client in feed_clients],
        safety_enabled=settings.enable_openfda,
    )
    if diagnostics is not None:
        diagnostics.update(source_health)

    logger.info("Ingestion: thu thập %d bản ghi thô từ %d nguồn API + %d feed (song song).",
                len(all_records), len(sources) + (1 if settings.enable_openfda else 0),
                len(feed_clients))
    logger.info(
        "Ingestion source health: %s (hard=%s; warning=%s)",
        source_health["status"],
        source_health["hard_fail_reasons"],
        source_health["warnings"],
    )
    return all_records


_FDA_SENTINEL = object()  # đánh dấu tác vụ openFDA trong danh sách nguồn


def _fetch(client, query: str, area: str, max_results: int,
           since_date: Optional[str] = None) -> Tuple[List[RawRecord], dict]:
    """Gọi 1 nguồn cho 1 truy vấn. KHÔNG ghi DB (gom log trả về để ghi sau)."""
    status, mode, err, records = "ok", "live", None, []
    health_before = _http_snapshot(client)
    try:
        records = client.search(query, clinical_area=area, max_results=max_results,
                                since_date=since_date)
    except Exception as exc:  # pragma: no cover
        status, err = "error", str(exc)
        logger.warning("Nguồn %s lỗi với query '%s': %s", client.name, query, exc)

    health_after = _http_snapshot(client)
    mock_records = any(bool((record.raw or {}).get("_mock")) for record in records)
    if getattr(client, "use_mock", False) or mock_records:
        mode, status = "mock", "mock"
    elif status != "error":
        terminal_failures = _counter_delta(health_before, health_after, "failure_count")
        transient_failures = _counter_delta(health_before, health_after, "transient_failure_count")
        successes = _counter_delta(health_before, health_after, "success_count")
        if terminal_failures:
            status = "error"
            err = str(health_after.get("last_error") or "HTTP request failed")
        elif transient_failures:
            status = "degraded"
            err = f"recovered_after_{transient_failures}_transient_failure(s)"
        elif successes:
            status = "ok"

    log = dict(source=client.name, api_endpoint=getattr(client, "endpoint", ""),
               query=f"[{area}] {query}", record_count=len(records),
               status=status, error_message=err, mode=mode)
    return records, log
