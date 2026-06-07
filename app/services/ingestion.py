"""Bước 1: Ingestion – gọi nguồn theo chuyên khoa & từ khóa, lưu raw, ghi Source Log.

TĂNG TỐC: chạy SONG SONG để rút ngắn thời gian quét.
- Mỗi nguồn API (PubMed/EuropePMC/Crossref/OpenAlex/ClinicalTrials) chạy 1 luồng riêng,
  BÊN TRONG vẫn tuần tự các từ khoá -> tôn trọng giới hạn tốc độ từng nguồn (vd NCBI 3 req/s).
- Các RSS feed chạy song song nhưng GIỚI HẠN số luồng (tránh bị chặn 429, vd nhiều feed BMJ).
- Source Log gom lại và ghi DB MỘT LẦN ở cuối (tránh khóa SQLite khi nhiều luồng cùng ghi).
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple

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


def ingest_all(max_results_per_query: int = 10,
               areas: Optional[List[str]] = None,
               since_date: Optional[str] = None) -> List[RawRecord]:
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

    # --- Tác vụ theo NGUỒN API: mỗi nguồn 1 luồng, bên trong tuần tự ---
    def sweep_source(client) -> Tuple[List[RawRecord], List[dict]]:
        recs: List[RawRecord] = []
        logs: List[dict] = []
        for area in areas:
            for query in CLINICAL_AREAS.get(area, []):
                r, log = _fetch(client, query, area, max_results_per_query, since_date)
                recs.extend(r)
                logs.append(log)
        return recs, logs

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
        src_futs = [src_pool.submit(sweep_fda if c is _FDA_SENTINEL else sweep_source, c)
                    for c in src_tasks]
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

    logger.info("Ingestion: thu thập %d bản ghi thô từ %d nguồn API + %d feed (song song).",
                len(all_records), len(sources) + (1 if settings.enable_openfda else 0),
                len(feed_clients))
    return all_records


_FDA_SENTINEL = object()  # đánh dấu tác vụ openFDA trong danh sách nguồn


def _fetch(client, query: str, area: str, max_results: int,
           since_date: Optional[str] = None) -> Tuple[List[RawRecord], dict]:
    """Gọi 1 nguồn cho 1 truy vấn. KHÔNG ghi DB (gom log trả về để ghi sau)."""
    status, mode, err, records = "ok", "live", None, []
    try:
        records = client.search(query, clinical_area=area, max_results=max_results,
                                since_date=since_date)
        mode = "mock" if client.use_mock else "live"
        status = "mock" if client.use_mock else "ok"
    except Exception as exc:  # pragma: no cover
        status, err = "error", str(exc)
        logger.warning("Nguồn %s lỗi với query '%s': %s", client.name, query, exc)

    log = dict(source=client.name, api_endpoint=getattr(client, "endpoint", ""),
               query=f"[{area}] {query}", record_count=len(records),
               status=status, error_message=err, mode=mode)
    return records, log
