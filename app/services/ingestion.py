"""Bước 1: Ingestion – gọi nguồn theo chuyên khoa & từ khóa, lưu raw, ghi Source Log.

TĂNG TỐC: chạy SONG SONG để rút ngắn thời gian quét.
- Mỗi nguồn API (PubMed/EuropePMC/Crossref/OpenAlex/ClinicalTrials) chạy 1 luồng riêng,
  BÊN TRONG vẫn tuần tự các từ khoá -> tôn trọng giới hạn tốc độ từng nguồn (vd NCBI 3 req/s).
- Các RSS feed chạy song song nhưng GIỚI HẠN số luồng (tránh bị chặn 429, vd nhiều feed BMJ).
- Source Log gom lại và ghi DB MỘT LẦN ở cuối (tránh khóa SQLite khi nhiều luồng cùng ghi).

BẬC THANG DỰ PHÒNG (20/09/2026): Consensus (tầng 1) và SerpApi Scholar (tầng 2) KHÔNG nằm trong vòng quét song
song ở trên. Chúng chỉ chạy SAU KHI mọi nguồn miễn phí đã quét xong và TRƯỚC lần ghi Source Log duy nhất, chỉ cho
(nhóm, truy vấn) còn thiếu chứng cứ đáng tin — xem `app/services/fallback_ladder.py`. Sức khoẻ nguồn (summarize_
source_health) tính từ log của nguồn CHÍNH; kết quả dự phòng chỉ ở diagnostics["fallback"] và dòng Source Log riêng.
Cả hai cờ ENABLE_CONSENSUS/ENABLE_SERPAPI_SCHOLAR tắt (hoặc USE_MOCK_SOURCES=true) thì khối này TRƠ HOÀN TOÀN.
"""
from __future__ import annotations

import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

from app.config import CLINICAL_AREAS, settings
from app.database import session_scope
from app.models import SourceLog
from app.sources import get_enabled_sources, get_fallback_sources
from app.sources.authority import assess_source_universe_coverage
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
# Nguồn TĂNG CƯỜNG tuỳ chọn — thêm 22/09/2026, đo được bằng đọc mã: các nguồn này CÓ trong
# get_enabled_sources() (Scopus/CORE/Epistemonikos khi bật) nên get_enabled_sources()/ingest_all()
# THẬT SỰ gọi chúng mỗi lượt live-update và source_rows ghi nhận đúng sức khoẻ — nhưng vì
# _DISCOVERY_CORE chỉ khai 3 tên, một nguồn ở đây hỏng 100% (health='unavailable') KHÔNG BAO GIỜ
# đổi `status` tổng ("PASS" dù hỏng hoàn toàn). CỐ Ý KHÔNG đưa vào _DISCOVERY_CORE (sẽ biến chúng
# thành BẮT BUỘC — một máy chưa có SCOPUS_API_KEY sẽ khiến TOÀN BỘ live-update FAIL, sai mục đích
# "nguồn TĂNG CƯỜNG tuỳ chọn"); thay vào đó CHỈ hạ `status` xuống tối đa "PARTIAL" (cảnh báo, không
# chặn) khi một nguồn Ở ĐÂY đã THẬT SỰ được gọi (có mặt trong source_rows, tức đang bật) mà hỏng
# 100%. Consensus/SerpApi KHÔNG ở đây — chúng đi qua `diagnostics["fallback"]` riêng (xem docstring
# module), không qua summarize_source_health().
_OPTIONAL_ENHANCED = {"scopus", "core", "epistemonikos"}


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
    healthy_sources = [
        name for name, item in source_rows.items()
        if item.get("health") in {"ok", "degraded"}
    ]
    if any(name.startswith("feed_") for name in healthy_sources):
        healthy_sources.append("guideline_feeds")
    source_universe = assess_source_universe_coverage(healthy_sources)

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

    mirror_notices: list[str] = []
    degraded_required: list[str] = []
    for name in sorted(set(discovery_expected) | safety_expected):
        health = source_rows.get(name, {}).get("health")
        if health not in {"degraded", "unavailable"}:
            continue
        # PubMed E-utilities thỉnh thoảng trả HTML/429/abuse gate dù PMID vẫn đối chiếu được
        # qua Europe PMC MEDLINE. Chỉ coi là dự phòng đủ khi CẢ Europe PMC và Crossref còn khỏe:
        # Europe PMC giữ PMID/MEDLINE, Crossref giữ DOI/publisher metadata. Nếu thiếu một trong hai,
        # vẫn PARTIAL để không xanh giả.
        if (
            name == "pubmed"
            and source_rows.get("europepmc", {}).get("health") in {"ok", "degraded"}
            and source_rows.get("crossref", {}).get("health") in {"ok", "degraded"}
        ):
            mirror_notices.append("PUBMED_EUTILS_MIRRORED_BY_EUROPEPMC_AND_CROSSREF")
            continue
        degraded_required.append(name)
    redundancy_warnings: list[str] = []
    if len(safety_healthy) < min(2, len(safety_expected)):
        redundancy_warnings.append("SAFETY_REDUNDANCY_LOW")
    if len(guideline_healthy) < min(3, len(guideline_expected)):
        redundancy_warnings.append("GUIDELINE_REDUNDANCY_LOW")
    # Nguồn tăng cường tuỳ chọn (Scopus/CORE/Epistemonikos) ĐÃ được gọi (có mặt trong source_rows,
    # tức đang bật) mà hỏng 100% — CẢNH BÁO, không chặn. Xem chú thích đầy đủ ở _OPTIONAL_ENHANCED.
    enhanced_failed = sorted(
        name for name in _OPTIONAL_ENHANCED
        if name in source_rows and source_rows[name].get("health") == "unavailable"
    )
    if enhanced_failed:
        redundancy_warnings.append("OPTIONAL_ENHANCED_SOURCE_UNAVAILABLE:" + ",".join(enhanced_failed))

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
        "mirror_notices": mirror_notices,
        "degraded_required_sources": degraded_required,
        "total_records": total_records,
        "discovery_core": {"expected": discovery_expected, "healthy": discovery_healthy},
        "safety": {"expected": sorted(safety_expected), "healthy": safety_healthy},
        "guideline": {"expected": guideline_expected, "healthy": guideline_healthy},
        "optional_enhanced_failed": enhanced_failed,
        "source_universe": source_universe,
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


_KHOA_LOG_SOURCELOG = ("source", "api_endpoint", "query", "record_count", "status", "error_message", "mode")


def _dung_tang_du_phong() -> List[Any]:
    """Dựng các tầng dự phòng đang bật — gọi TRƯỚC mọi lời gọi mạng để cấu hình sai NỔ TO sớm.

    Cả hai cờ tắt hoặc chế độ mock -> [] và KHÔNG chạm `get_fallback_sources()` (không dựng client, không đọc
    cấu hình tầng). FALLBACK_ORDER chứa tên lạ / tầng đang bật mà không nạp được thì `get_fallback_sources()` nổ
    ValueError/ImportError cùng phong cách `get_enabled_sources()`: chủ ý, trước khi tốn bất kỳ lời gọi nào.
    """
    if settings.use_mock_sources or not (settings.enable_consensus or settings.enable_serpapi_scholar):
        return []
    return get_fallback_sources()


def _chay_du_phong(all_records: List[RawRecord], all_logs: List[dict], areas: List[str],
                   max_results_per_query: int, since_date: Optional[str],
                   clients: List[Any]) -> Tuple[List[RawRecord], List[dict], Optional[dict]]:
    """Chạy bậc thang dự phòng sau khi mọi nguồn chính đã quét xong. Không bao giờ ném lỗi.

    Trả (bản ghi đã xác minh, dòng SourceLog thêm, tóm tắt cho diagnostics["fallback"] hoặc None).
    None = cả hai cờ tắt: KHÔNG thêm gì vào diagnostics (hành vi y hệt trước khi có bậc thang). Có cờ bật mà không
    chạy (mock / nguồn chính trả mock ở live / không dựng được tầng) thì trả dấu hiệu {"active": False, "ly_do": ...}
    — nói rõ là KHÔNG chạy chứ không im lặng.
    """
    if not (settings.enable_consensus or settings.enable_serpapi_scholar):
        return [], [], None
    if settings.use_mock_sources:
        return [], [], {"active": False, "ly_do": "mock"}
    if any(str(lg.get("status")) == "mock" for lg in all_logs):
        # Một nguồn chính trả mock ở chế độ live (vd PubMed thiếu email): lượt này sẽ bị đánh dấu lỗi
        # (MOCK_DETECTED_IN_LIVE) và bản ghi mock không phải bằng chứng — không tiêu hạn mức trả phí cho nó.
        return [], [], {"active": False, "ly_do": "nguon_chinh_tra_mock_o_che_do_live"}
    if not clients:
        return [], [], {"active": False, "ly_do": "khong_co_tang_du_phong_nao_duoc_dung"}
    try:
        from app.services.fallback_ladder import chay_du_phong_ingest  # noqa: PLC0415 — tránh vòng import

        extra_records, extra_logs, tom_tat = chay_du_phong_ingest(
            all_records, all_logs, areas, max_results_per_query, since_date, clients=clients)
    except Exception as exc:  # noqa: BLE001 — bậc thang không được làm sập ingest_all
        logger.error("Bậc thang dự phòng lỗi bất ngờ (%s) — lượt quét tiếp tục không có phần dự phòng.",
                     type(exc).__name__)
        return [], [], {"active": True, "loi_noi_bo": type(exc).__name__}
    # SourceLog(**lg) không có try/except: chỉ cho đi qua đúng các cột của model.
    extra_logs = [{k: lg.get(k) for k in _KHOA_LOG_SOURCELOG} for lg in extra_logs]
    return extra_records, extra_logs, tom_tat


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
    tang_du_phong = _dung_tang_du_phong()   # không quét song song; chạy sau khi mọi nguồn chính xong
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

    # Sức khoẻ nguồn tính từ log của nguồn CHÍNH (chụp TRƯỚC khi thêm dòng của tầng dự phòng): kết quả dự phòng
    # không được cộng vào total_records (che NO_RECORDS_FROM_ANY_SOURCE), không được gây MOCK_DETECTED_IN_LIVE,
    # và một tầng dự phòng hỏng không được biến PASS thành FAIL hay che lỗi của nguồn chính.
    primary_logs = list(all_logs)

    # BẬC THANG DỰ PHÒNG: sau khi mọi nguồn xong, trước lần ghi Source Log duy nhất.
    extra_records, extra_logs, fallback_summary = _chay_du_phong(
        all_records, all_logs, areas, max_results_per_query, since_date, tang_du_phong)
    if extra_records:
        all_records.extend(extra_records)
    if extra_logs:
        all_logs.extend(extra_logs)

    # Ghi toàn bộ Source Log MỘT LẦN (tránh nhiều luồng ghi SQLite đồng thời).
    if all_logs:
        with session_scope() as s:
            s.add_all([SourceLog(**lg) for lg in all_logs])

    source_health = summarize_source_health(
        primary_logs,
        expected_api_sources=[client.name for client in sources],
        expected_feed_sources=[client.name for client in feed_clients],
        safety_enabled=settings.enable_openfda,
    )
    if diagnostics is not None:
        diagnostics.update(source_health)
        if fallback_summary is not None:
            # Chỉ gắn vào bản diagnostics: dict sức khoẻ của nguồn CHÍNH giữ nguyên, không bị sửa bởi kết quả dự phòng.
            diagnostics["fallback"] = fallback_summary

    logger.info("Ingestion: thu thập %d bản ghi thô từ %d nguồn API + %d feed (song song).",
                len(all_records), len(sources) + (1 if settings.enable_openfda else 0),
                len(feed_clients))
    if extra_records or extra_logs:
        logger.info("Ingestion: trong đó %d bản ghi từ bậc thang dự phòng (đã xác minh Crossref/PubMed), "
                    "%d dòng Source Log dự phòng.", len(extra_records), len(extra_logs))
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
