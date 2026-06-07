"""Orchestrator pipeline EBM: Ingest -> Normalize -> Dedup -> Score -> Filter ->
Synthesize -> Persist -> Changelog -> Archive.

Bảo đảm: KHÔNG ghi đè/không mất dữ liệu cũ; mỗi lần chạy lưu processed snapshot.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.config import settings
from app.database import session_scope
from app.models import ChangeLogEntry, DuplicateLink, EvidenceItem
from app.scoring import (
    evidence_quality_score,
    operational_evidence_level,
    practice_change_score,
    reliability_tier,
)
from app.services import run_state
from app.services.deduplication import deduplicate
from app.services.filtering import classify
from app.services.ingestion import ingest_all
from app.services.normalization import normalize
from app.services.synthesis import synthesize
from app.sources.base import RawRecord
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def score_item(item: Dict) -> Dict:
    """Áp dụng toàn bộ scoring engine cho 1 item đã normalize (mutates & returns)."""
    eq, eq_bd = evidence_quality_score(item)
    pc, pc_bd = practice_change_score(item)
    tier = reliability_tier(item, eq, pc)
    op_level, is_official = operational_evidence_level(item, eq)

    item["evidence_quality_score"] = eq
    item["practice_change_score"] = pc
    item["reliability_tier"] = tier
    item["operational_evidence_level"] = op_level
    item["_score_breakdown"] = {"evidence_quality": eq_bd, "practice_change": pc_bd,
                                "operational_is_official": is_official}
    return item


def run_pipeline(records: Optional[List[RawRecord]] = None,
                 max_results_per_query: int = 10,
                 incremental: bool = True,
                 window_days: Optional[int] = None) -> Dict[str, int]:
    """Chạy toàn bộ pipeline. Trả về thống kê số lượng theo phân loại.

    incremental: nếu True (mặc định) và đang ở chế độ live, chỉ LẤY bài mới kể từ
                 mốc lần chạy trước (watermark). Mock luôn lấy toàn bộ pool.
    window_days: cửa sổ nhìn lùi cho lần chạy đầu (mặc định 30 ngày).

    Cơ chế "mới tuần này": mỗi lần chạy được ghi vào PipelineRun (run_id). Bản ghi
    LẦN ĐẦU vào kho mang first_seen_run_id = run_id hiện tại -> đó là "mới".
    """
    mode = "mock" if settings.use_mock_sources else "live"
    since_date = None
    if incremental and mode == "live":
        since_date = run_state.compute_since_date(window_days)

    run_id = run_state.start_run(mode=mode, window_days=window_days,
                                 since_date=since_date, until_date=None)

    if records is None:
        records = ingest_all(max_results_per_query=max_results_per_query,
                             since_date=since_date)

    # 2) Normalize
    normalized_all: List[Dict] = [normalize(r) for r in records]

    # 2b) Gộp các bản ghi trùng TRONG CÙNG MỘT NGUỒN (cùng source + định danh/title)
    #     thành 1 đại diện. Mỗi phần tử còn lại sẽ là 1 hàng DB duy nhất, nên upsert
    #     ổn định và không tự ghi đè cờ is_primary trong cùng một lần chạy.
    normalized: List[Dict] = _collapse_same_source(normalized_all)

    # 3) Deduplicate xuyên nguồn (theo vị trí) -> chọn record chính + liên kết trùng
    primary_positions, links = deduplicate(normalized)
    primary_set = set(primary_positions)

    stats = {"total": len(normalized_all), "unique_records": len(normalized),
             "primary": len(primary_positions), "duplicates": len(links),
             "actionable": 0, "need_full_text": 0, "watch_only": 0,
             "excluded": 0, "inserted": 0, "updated": 0,
             "new_items": 0, "new_actionable": 0, "new_drug_safety": 0,
             "run_id": run_id, "mode": mode, "since_date": since_date}

    persisted_ids: List[Optional[int]] = [None] * len(normalized)

    with session_scope() as s:
        for pos, item in enumerate(normalized):
            is_primary = pos in primary_set
            # 4-5) Score + classify + synthesize chỉ cho record chính.
            if is_primary:
                score_item(item)
                classification, actionable, a_reason, x_reason = classify(item)
                item["classification"] = classification
                item["is_actionable"] = actionable
                item["actionable_reason"] = a_reason or None
                item["reason_for_exclusion"] = x_reason or None
                item["synthesis"] = synthesize(item)
                stats[classification] = stats.get(classification, 0) + 1
            else:
                # Bản trùng: không phân loại, reset cờ để không mang giá trị cũ.
                item["classification"] = "duplicate"
                item["is_actionable"] = False
                item["actionable_reason"] = None

            db_obj, created = _upsert(s, item, is_primary, run_id)
            persisted_ids[pos] = db_obj.id
            stats["inserted" if created else "updated"] += 1
            # "Mới" = lần đầu vào kho trong lần chạy này (record chính).
            if created and is_primary:
                stats["new_items"] += 1
                if item.get("is_actionable"):
                    stats["new_actionable"] += 1
                if item.get("safety_signal") or item.get("source_type") == "drug_safety":
                    stats["new_drug_safety"] += 1

        # 3b) Lưu liên kết trùng (không xóa bản ghi)
        for primary_pos, dup_pos, reason in links:
            pid, did = persisted_ids[primary_pos], persisted_ids[dup_pos]
            if pid and did:
                exists = s.query(DuplicateLink).filter_by(
                    primary_id=pid, duplicate_id=did).first()
                if not exists:
                    s.add(DuplicateLink(primary_id=pid, duplicate_id=did,
                                        match_reason=reason))

        # 7) Changelog
        s.add(ChangeLogEntry(
            change_summary=(f"Pipeline [{mode}] run #{run_id}: {stats['total']} bản ghi, "
                            f"{stats['new_items']} MỚI ({stats['new_actionable']} actionable mới), "
                            f"{stats['actionable']} actionable, {stats['excluded']} bị loại."),
            source="pipeline", module="services.pipeline",
            created_by="pipeline", review_status="pending",
        ))

    # 7b) Ghi nhận kết thúc lần chạy (watermark).
    run_state.finish_run(run_id, total_fetched=stats["total"],
                         new_items=stats["new_items"],
                         new_actionable=stats["new_actionable"],
                         new_drug_safety=stats["new_drug_safety"],
                         stats=stats, status="ok")

    # 7c) Archive processed snapshot (không ghi đè)
    _archive_processed(normalized, stats)
    logger.info("Pipeline hoàn tất (run #%d, %s): %s", run_id, mode, stats)
    return stats


def _collapse_same_source(items: List[Dict]) -> List[Dict]:
    """Giữ 1 đại diện cho mỗi (source + định danh mạnh nhất / title).

    Bảo đảm mỗi hàng DB là duy nhất theo nguồn, tránh việc một bản trùng cùng nguồn
    ghi đè cờ is_primary của bản chính trong cùng một lần chạy.
    """
    seen: Dict[str, Dict] = {}
    ordered: List[Dict] = []
    for it in items:
        ident = it.get("doi") or it.get("pmid") or it.get("nct_id") or it.get("title", "")
        key = f"{it.get('source')}|{ident}".lower()
        if key in seen:
            continue
        seen[key] = it
        ordered.append(it)
    return ordered


def _upsert(session, item: Dict, is_primary: bool, run_id: Optional[int] = None):
    """Tìm bản ghi cũ theo (source + định danh mạnh); cập nhật nếu có, thêm nếu chưa.

    Khóa upsert bao gồm `source` để mỗi nguồn giữ bản ghi RIÊNG (cùng DOI ở 2 nguồn
    là 2 bản ghi khác nhau, liên kết qua DuplicateLink). Nhờ vậy chạy lại pipeline
    là idempotent và cờ is_primary_record ổn định. KHÔNG xóa dữ liệu cũ.
    Trả về (obj, created).
    """
    q = session.query(EvidenceItem).filter(EvidenceItem.source == item["source"])
    existing = None
    if item.get("doi"):
        existing = q.filter(EvidenceItem.doi == item["doi"]).first()
    if not existing and item.get("pmid"):
        existing = q.filter(EvidenceItem.pmid == item["pmid"]).first()
    if not existing and item.get("nct_id"):
        existing = q.filter(EvidenceItem.nct_id == item["nct_id"]).first()
    if not existing and not (item.get("doi") or item.get("pmid") or item.get("nct_id")):
        # Không có định danh mạnh: khớp theo source + title để tránh nhân bản mỗi lần chạy.
        existing = q.filter(EvidenceItem.title == item["title"]).first()

    payload = {k: v for k, v in item.items() if not k.startswith("_")}
    payload["is_primary_record"] = is_primary
    payload["dedup_key"] = item.get("doi") or item.get("pmid") or item.get("nct_id")

    if existing:
        for k, v in payload.items():
            if hasattr(existing, k):
                setattr(existing, k, v)
        # Đã thấy lại ở lần chạy này; GIỮ NGUYÊN first_seen_run_id (không phải "mới").
        if run_id is not None:
            existing.last_run_id = run_id
        return existing, False

    obj = EvidenceItem(**{k: v for k, v in payload.items()
                          if hasattr(EvidenceItem, k)})
    # Lần đầu vào kho -> đánh dấu "mới" bằng first_seen_run_id.
    if run_id is not None:
        obj.first_seen_run_id = run_id
        obj.last_run_id = run_id
    session.add(obj)
    session.flush()  # để có id
    return obj, True


def _archive_processed(items: List[Dict], stats: Dict) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    path = settings.processed_dir / f"pipeline_{ts}.json"
    try:
        path.write_text(
            json.dumps({"stats": stats, "items": items}, ensure_ascii=False,
                       indent=2, default=str),
            encoding="utf-8",
        )
    except OSError as exc:  # pragma: no cover
        logger.warning("Không lưu được processed snapshot: %s", exc)
