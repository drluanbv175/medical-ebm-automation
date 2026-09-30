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

import re
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

from app.config import CLINICAL_AREAS, settings
from app.database import session_scope
from app.models import SourceLog
from app.sources import get_enabled_sources, get_fallback_sources
from app.sources.authority import assess_source_universe_coverage
from app.sources.base import RawRecord
from app.sources.openfda import OpenFDAClient
from app.utils.http import DAU_CLOUDFLARE_CHAN
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
# Nguồn tăng cường bị CLOUDFLARE chặn theo IP mạng (29/09/2026, bác sĩ chọn phương án a «ghi chú, không chặn»):
# VPN BẬT là mặc định (NCBI chạy) nên Scopus luôn nhận trang chặn Cloudflare ⇒ MỌI lượt tuần thành PARTIAL (lượt bù
# 29/09 PARTIAL chỉ vì `OPTIONAL_ENHANCED_SOURCE_UNAVAILABLE:scopus`) ⇒ chặn nối Hub mỗi tuần. Chỉ miễn khi (a) MỌI
# lỗi của nguồn là HTTP 403 kèm trang chặn Cloudflare (`DAU_CLOUDFLARE_CHAN`, gắn ở `HttpClient`) và (b) ĐỦ cả ba
# nguồn khám phá lõi (PubMed/Europe PMC/Crossref) đang bật và health «ok» (không tính «degraded»). 401 (khoá sai),
# 403 JSON của chính Elsevier, mất mạng, thiếu khoá… ⇒ vẫn PARTIAL như cũ. Nguồn vẫn được liệt kê ở
# `optional_enhanced_failed` (sự thật không đổi).
_OPTIONAL_ENHANCED_CLOUDFLARE_IP = {"scopus"}
_HTTP_403_CLOUDFLARE_RE = re.compile(r"^" + re.escape(DAU_CLOUDFLARE_CHAN) + r" .*\b403 Client Error\b")
# Feed an toàn mà NHÀ CUNG CẤP chặn truy cập tự động vĩnh viễn (29/09/2026, bác sĩ chọn «ghi chú,
# không chặn»): www.fda.gov trả 401 cho MedWatch RSS với mọi client tự động và MedWatch không có API
# openFDA tương đương. Để nguyên thì CHỈ nguồn này hỏng cũng làm mọi lượt thành PARTIAL ⇒ chặn nối Hub
# MỖI tuần. Chỉ miễn khi (a) MỌI lỗi của feed là HTTP 401/403 và (b) openFDA cùng ≥ 1 feed an toàn khác
# còn khoẻ; lỗi khác (timeout, 5xx, parse…) hoặc thiếu dự phòng ⇒ vẫn PARTIAL như cũ.
_SAFETY_FEEDS_PROVIDER_BLOCKED = {"feed_fda_medwatch"}
# Dự phòng CHÍNH THỨC đã khai (29/09/2026): feed thu hồi FDA bị chặn ⇒ rss_feed lùi sang openFDA
# drug/enforcement và gắn raw["_via"]. Trước đây bộ đếm lỗi HttpClient của lần gọi RSS hỏng vẫn làm dòng log thành
# «error» dù đã có bản ghi thật từ API chính thức ⇒ nguồn «unavailable» ⇒ MỌI lượt PARTIAL — trái ý định ở audit/15 #6
# (chỉ MedWatch mới báo lỗi thật). Nay: TOÀN BỘ bản ghi đến từ dự phòng đã khai ⇒ «degraded» + tiền tố `du_phong:` và
# một ghi chú có tên trong `mirror_notices`. Chỉ các `_via` trong tập này (chế độ Crossref-ISSN là nguồn CHÍNH,
# không phải dự phòng, nên không có ở đây).
_VIA_DU_PHONG = {"openfda_enforcement"}
_HTTP_BI_CHAN_RE = re.compile(r"\b40[13] Client Error\b|\bHTTP 40[13]\b")


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
        "paced_wait_seconds": 0.0,
    }


def _counter_delta(before: Dict[str, Any], after: Dict[str, Any], key: str) -> int:
    return max(0, int(after.get(key) or 0) - int(before.get(key) or 0))


def _paced_seconds(client: object) -> float:
    """Tổng số giây client đã CHỜ NHỊP CHỦ ĐỘNG (HttpClient.paced_wait_seconds); không đo được thì 0 — không ném lỗi."""
    try:
        return float(_http_snapshot(client).get("paced_wait_seconds") or 0.0)
    except Exception:  # noqa: BLE001 — telemetry của client giả/lạ không được làm sập lượt quét
        return 0.0


def _sweep_coverage(client, plan: List[Tuple[str, str]], reached: int) -> dict:
    """Độ phủ của MỘT lượt `sweep_source` dừng sau `reached` truy vấn đầu của `plan`.

    `not_attempted` = truy vấn nguồn này LẼ RA gửi nhưng CHƯA TỪNG được thử vì cầu dao cắt. Khác hẳn `skipped` (bỏ
    qua CÓ CHỦ ĐÍCH, vd thẻ trường PubMed tới nguồn không hiểu): truy vấn nằm sau điểm cắt mà nguồn vốn không gửi thì
    không phải độ phủ bị mất — đếm riêng ở `unreached_skippable`, KHÔNG cộng vào `not_attempted`.
    """
    rest = plan[reached:]
    lost = [(area, query) for area, query in rest if _ly_do_bo_qua(client, query) is None]
    return {
        "not_attempted": len(lost),
        "unreached_skippable": len(rest) - len(lost),
        "not_attempted_areas": dict(Counter(area for area, _query in lost)),
    }


def summarize_source_health(
    logs: List[dict],
    *,
    expected_api_sources: List[str],
    expected_feed_sources: List[str],
    safety_enabled: bool,
    coverage: Optional[Dict[str, dict]] = None,
) -> dict:
    """Tổng hợp độ phủ nguồn để pipeline phân biệt PASS/PARTIAL/FAIL.

    Một feed tùy chọn lỗi không làm hỏng cả lượt quét khi các kênh cùng nhóm còn đủ
    dự phòng. Ngược lại, mock trong live, mất toàn bộ kênh an toàn/guideline, hoặc
    thiếu phần lớn nguồn discovery lõi là lỗi cứng.

    `coverage` (30/09/2026): {tên nguồn: kết quả `_sweep_coverage`} do `sweep_source` ghi. Có thì hàng của nguồn thêm
    `not_attempted` — số truy vấn lẽ ra được gửi mà cầu dao cắt trước khi tới lượt — để health «ok» (chỉ đo trên phần
    ĐÃ gửi) không che độ phủ thật. CHỈ là số đo: KHÔNG tham gia tính `health` hay `status` (ngưỡng PASS/PARTIAL/FAIL
    giữ nguyên). Không truyền, hoặc nguồn không đi qua `sweep_source` (feed, openFDA) ⇒ hàng KHÔNG có khoá này —
    «không đo» không được hiện thành 0.
    """
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"requests": 0, "records": 0, "ok": 0, "degraded": 0, "error": 0, "mock": 0,
                 "error_http_401_403": 0, "error_http_403_cloudflare": 0, "du_phong": 0, "skipped": 0}
    )
    for row in logs:
        source = str(row.get("source") or "unknown")
        item = grouped[source]
        status = str(row.get("status") or "error")
        if status == "skipped":
            # Truy vấn bị BỎ QUA có chủ đích, không gọi mạng (xem _fetch): KHÔNG phải một request — không tính vào
            # requests/error_rate (sẽ pha loãng tỉ lệ lỗi thật), cũng KHÔNG phải một lần nguồn trả lời thành công.
            item["skipped"] += 1
            continue
        item["requests"] += 1
        item["records"] += int(row.get("record_count") or 0)
        status = status if status in {"ok", "degraded", "error", "mock"} else "error"
        item[status] += 1
        if status == "error" and _HTTP_BI_CHAN_RE.search(str(row.get("error_message") or "")):
            item["error_http_401_403"] += 1
        if status == "error" and _HTTP_403_CLOUDFLARE_RE.search(str(row.get("error_message") or "")):
            item["error_http_403_cloudflare"] += 1
        if str(row.get("error_message") or "").startswith("du_phong:"):
            item["du_phong"] += 1

    source_rows: dict[str, dict[str, Any]] = {}
    for source, item in sorted(grouped.items()):
        live_success = item["ok"] + item["degraded"]
        error_rate = item["error"] / max(1, item["requests"])
        if item["mock"]:
            health = "mock"
        elif item["requests"] == 0:
            # MỌI truy vấn của nguồn đều bị bỏ qua có chủ đích: không có lần gọi nào để đo — KHÔNG được là "ok"
            # (xanh giả) cũng KHÔNG phải "unavailable" (đỏ giả). Không nằm trong {ok, degraded} nên không bao giờ
            # được đếm là khoẻ ở các phép tính độ phủ bên dưới.
            health = "not_queried"
        elif live_success == 0:
            health = "unavailable"
        elif error_rate > 0.20:
            health = "degraded"
        else:
            health = "ok"
        source_rows[source] = {**item, "error_rate": round(error_rate, 4), "health": health}
        phu = (coverage or {}).get(source)
        if isinstance(phu, dict):
            source_rows[source]["not_attempted"] = max(0, int(phu.get("not_attempted") or 0))
            if phu.get("not_attempted_areas"):
                source_rows[source]["not_attempted_areas"] = dict(phu["not_attempted_areas"])
    not_attempted_by_source = {name: row["not_attempted"] for name, row in source_rows.items()
                               if row.get("not_attempted")}

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

    mirror_notices: list[str] = [
        f"{name.upper()}_SERVED_BY_OFFICIAL_FALLBACK"
        for name, item in sorted(source_rows.items()) if item.get("du_phong")
    ]
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
        if name in _SAFETY_FEEDS_PROVIDER_BLOCKED:
            row_bc = source_rows.get(name, {})
            du_phong = [n for n in safety_healthy if n != name]
            if (int(row_bc.get("error", 0)) > 0
                    and row_bc.get("error_http_401_403") == row_bc.get("error")
                    and "openfda" in du_phong and len(du_phong) >= 2):
                mirror_notices.append(f"{name.upper()}_PROVIDER_BLOCKS_AUTOMATED_ACCESS_401_403")
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
    # Miễn riêng ca Cloudflare chặn theo IP mạng — điều kiện đầy đủ ở chú thích _OPTIONAL_ENHANCED_CLOUDFLARE_IP.
    # ĐỦ cả ba nguồn lõi, mỗi nguồn health == "ok" (phản biện 29–30/09): máy tắt Europe PMC/Crossref thì PubMed một
    # mình không đủ bù cho Scopus; và «degraded» (vd NCBI chặn giữa lượt: 1 thành công + 3 lỗi, PubMed phải nhờ gương
    # Europe PMC/Crossref) KHÔNG tính là khoẻ — nếu không, hai nguồn cùng hỏng mà lượt vẫn PASS.
    loi_kham_pha_du = all(source_rows.get(n, {}).get("health") == "ok" for n in _DISCOVERY_CORE)
    enhanced_cloudflare = [
        name for name in enhanced_failed
        if name in _OPTIONAL_ENHANCED_CLOUDFLARE_IP and loi_kham_pha_du
        and int(source_rows[name].get("error", 0)) > 0
        and source_rows[name].get("error_http_403_cloudflare") == source_rows[name].get("error")
    ]
    for name in enhanced_cloudflare:
        mirror_notices.append(f"{name.upper()}_BLOCKED_BY_CLOUDFLARE_403_NETWORK_IP")
    enhanced_canh_bao = [name for name in enhanced_failed if name not in enhanced_cloudflare]
    if enhanced_canh_bao:
        redundancy_warnings.append("OPTIONAL_ENHANCED_SOURCE_UNAVAILABLE:" + ",".join(enhanced_canh_bao))
    # Nguồn BẮT BUỘC (lõi khám phá/an toàn) mà mọi truy vấn đều bị bỏ qua: không đo được ≠ ổn ⇒ CẢNH BÁO (PARTIAL),
    # không chặn (không đo được ≠ hỏng). Với CLINICAL_AREAS hiện hành không xảy ra (nguồn lõi nào cũng còn truy vấn
    # chủ đề) — đây là lưới cho hồi quy làm một nguồn lõi bị bỏ qua sạch mà lượt chạy vẫn PASS.
    required_not_queried = sorted(
        name for name in set(discovery_expected) | safety_expected
        if source_rows.get(name, {}).get("health") == "not_queried"
    )
    if required_not_queried:
        redundancy_warnings.append("REQUIRED_SOURCE_NOT_QUERIED:" + ",".join(required_not_queried))

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
        "optional_enhanced_blocked_by_cloudflare": enhanced_cloudflare,
        # Nguồn bị cầu dao cắt: {tên: số truy vấn lẽ ra được gửi mà chưa từng được thử}. Chỉ để NHÌN THẤY.
        "not_attempted_by_source": not_attempted_by_source,
        "source_universe": source_universe,
        "sources": source_rows,
    }


def sweep_source(client, areas: List[str], max_results_per_query: int,
                  since_date: Optional[str] = None, fetch_fn=None,
                  coverage: Optional[Dict[str, dict]] = None) -> Tuple[List[RawRecord], List[dict]]:
    """Quét 1 nguồn API qua mọi (area, query) theo CLINICAL_AREAS — tuần tự, có circuit-breaker.

    Tách khỏi `ingest_all()` (trước là closure nội bộ) để test được độc lập, không cần
    dựng toàn bộ pipeline/ThreadPoolExecutor/DB. `fetch_fn` injectable cho test (mặc định `_fetch`).
    `coverage` (tuỳ chọn): dict do người gọi cấp; hàm ghi `coverage[client.name]` = độ phủ của lượt quét này
    (xem `_sweep_coverage`) để `summarize_source_health` nói rõ bao nhiêu truy vấn CHƯA TỪNG được thử.
    """
    fetch_fn = fetch_fn or _fetch
    recs: List[RawRecord] = []
    logs: List[dict] = []
    plan = [(area, query) for area in areas for query in CLINICAL_AREAS.get(area, [])]
    consecutive_errors = 0
    for idx, (area, query) in enumerate(plan):
        paced_before = _paced_seconds(client)
        started = time.monotonic()
        r, log = fetch_fn(client, query, area, max_results_per_query, since_date)
        elapsed = time.monotonic() - started
        # Chờ nhịp CHỦ ĐỘNG (giãn cách tối thiểu cùng host, chờ tới mốc máy chủ nêu) không phải «độ trễ bất thường».
        # Không trừ thì nguồn có nhịp riêng dài (CORE 6,5 giây) bị CHÍNH nhịp của mình đẩy qua ngưỡng chậm và tự cắt.
        # Thời gian ngủ backoff sau 429/5xx/mất mạng KHÔNG nằm trong phần bị trừ — vẫn là tín hiệu nguồn trục trặc.
        abnormal = max(0.0, elapsed - max(0.0, _paced_seconds(client) - paced_before))
        recs.extend(r)
        logs.append(log)
        if log["status"] == "skipped":
            # Bỏ qua có chủ đích, không gọi mạng: không phải lỗi, cũng không phải bằng chứng nguồn đã hồi phục —
            # KHÔNG đụng bộ đếm lỗi liên tiếp (trước 29/09/2026 ba lỗi 400 của truy vấn [ta] gửi sang
            # ClinicalTrials.gov đủ làm breaker cắt mọi truy vấn phía sau).
            continue
        if log["status"] == "error" or abnormal >= _SLOW_QUERY_THRESHOLD_SEC:
            consecutive_errors += 1
            if consecutive_errors >= _MAX_CONSECUTIVE_ERRORS:
                phu = _sweep_coverage(client, plan, idx + 1)
                # «KHÔNG THỬ», không viết «bỏ qua»: «bỏ qua» là chữ của dòng status="skipped" (có chủ đích).
                logger.warning(
                    "Nguồn %s lỗi/chậm liên tiếp %d lần (có thể đang gián đoạn) — KHÔNG THỬ %d truy vấn còn lại "
                    "thay vì thử hết, tránh treo lâu: %d truy vấn lẽ ra được gửi mà chưa từng được thử, %d truy vấn "
                    "nguồn này vốn không gửi.",
                    client.name, consecutive_errors, len(plan) - (idx + 1),
                    phu["not_attempted"], phu["unreached_skippable"],
                )
                if coverage is not None:
                    coverage[client.name] = phu
                _log_tong_bo_qua(client, logs)
                return recs, logs
        else:
            consecutive_errors = 0
    if coverage is not None:
        coverage[client.name] = _sweep_coverage(client, plan, len(plan))
    _log_tong_bo_qua(client, logs)
    return recs, logs


def _log_tong_bo_qua(client, logs: List[dict]) -> None:
    """MỘT dòng INFO mỗi nguồn cho các truy vấn bị bỏ qua có chủ đích (thay vì một dòng mỗi truy vấn)."""
    ly_do = Counter(str(lg.get("error_message") or "").split(":", 1)[0]
                    for lg in logs if lg.get("status") == "skipped")
    if ly_do:
        logger.info(
            "Nguồn %s: BỎ QUA %d truy vấn có chủ đích (%s) — không gọi mạng, KHÔNG tính là lỗi; sức khoẻ nguồn chỉ "
            "đo trên %d truy vấn đã gửi.",
            client.name, sum(ly_do.values()), ", ".join(f"{k}×{v}" for k, v in sorted(ly_do.items())),
            len(logs) - sum(ly_do.values()))


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
    # Độ phủ truy vấn của từng nguồn API (mỗi luồng ghi đúng MỘT khoá là tên nguồn của mình).
    coverage: Dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=n_src_workers) as src_pool:
        src_futs = [
            src_pool.submit(sweep_fda, c) if c is _FDA_SENTINEL
            else src_pool.submit(sweep_source, c, areas, max_results_per_query, since_date, None, coverage)
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
        coverage=coverage,
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
        "Ingestion source health: %s (hard=%s; warning=%s; notice=%s)",
        source_health["status"],
        source_health["hard_fail_reasons"],
        source_health["warnings"],
        source_health.get("mirror_notices") or [],
    )
    if source_health.get("not_attempted_by_source"):
        # Dòng RIÊNG (không sửa dòng trên): trạng thái lượt chạy không đổi vì con số này, nhưng người đọc log phải thấy
        # health «ok» của các nguồn dưới đây chỉ đo trên phần truy vấn ĐÃ gửi.
        logger.warning(
            "Ingestion độ phủ truy vấn: cầu dao cắt trước khi thử hết — số truy vấn lẽ ra được gửi mà CHƯA TỪNG được "
            "thử, theo nguồn: %s. Không tính vào trạng thái lượt chạy.",
            source_health["not_attempted_by_source"],
        )
    return all_records


_FDA_SENTINEL = object()  # đánh dấu tác vụ openFDA trong danh sách nguồn


def _ly_do_bo_qua(client, query: str) -> Optional[str]:
    """Hỏi connector có CHỦ ĐÍCH không gửi truy vấn này không (vd thẻ trường PubMed tới nguồn không hiểu) — thuần.

    Chế độ mock không bỏ qua (giữ nguyên hành vi demo/seed, cùng quy ước serpapi_scholar). Client không khai
    `ly_do_bo_qua_truy_van` (test double, wrapper cũ) hoặc trả thứ không phải chuỗi => không bỏ qua (hành vi cũ).
    """
    if getattr(client, "use_mock", False):
        return None
    hoi = getattr(client, "ly_do_bo_qua_truy_van", None)
    if not callable(hoi):
        return None
    ly_do = hoi(query)
    return ly_do if isinstance(ly_do, str) and ly_do else None


def _fetch(client, query: str, area: str, max_results: int,
           since_date: Optional[str] = None) -> Tuple[List[RawRecord], dict]:
    """Gọi 1 nguồn cho 1 truy vấn. KHÔNG ghi DB (gom log trả về để ghi sau)."""
    ly_do_bo_qua = _ly_do_bo_qua(client, query)
    if ly_do_bo_qua:
        # Không gọi mạng. status="skipped" KHÔNG phải lỗi (không đẩy circuit-breaker, không vào error_rate) nhưng
        # cũng KHÔNG phải nguồn đã trả lời: summarize_source_health không tính là khoẻ, evidence_sufficiency không
        # tính là "nguồn lõi đã trả lời" (chỉ nhận ok/degraded).
        logger.debug("Nguồn %s bỏ qua query '%s' (%s) — không gọi mạng, không phải lỗi.",
                     client.name, query, ly_do_bo_qua)
        return [], dict(source=client.name, api_endpoint=getattr(client, "endpoint", ""),
                        query=f"[{area}] {query}", record_count=0, status="skipped",
                        error_message=(f"{ly_do_bo_qua}: không gửi truy vấn tới nguồn không hiểu cú pháp này — "
                                       "bỏ qua có chủ đích, không phải lỗi"),
                        mode="live")
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
        chi_du_phong = bool(records) and all(
            (r.raw or {}).get("_via") in _VIA_DU_PHONG for r in records)
        if terminal_failures and chi_du_phong:
            via = (records[0].raw or {}).get("_via")
            status = "degraded"
            err = f"du_phong:{via} sau lỗi nguồn chính: {health_after.get('last_error') or 'HTTP request failed'}"[:500]
        elif terminal_failures:
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
