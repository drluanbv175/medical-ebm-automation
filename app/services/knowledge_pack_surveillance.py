"""Cầu nối surveillance -> knowledge pack review queue.

Module này chỉ tạo hàng chờ bác sĩ duyệt. Không tự sửa YAML knowledge pack,
không tự đổi khuyến cáo lâm sàng.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from app.config import BASE_DIR
from app.database import session_scope
from app.models import EvidenceItem
from app.services import run_state

PACK_DEFINITIONS = {
    "hypertension_adult_outpatient": {
        "label": "Tăng huyết áp",
        "keywords": ("hypertension", "blood pressure", "hypertensive", "tăng huyết áp", "huyết áp"),
    },
    "diabetes_t2_adult_outpatient": {
        "label": "Đái tháo đường type 2",
        "keywords": ("diabetes", "type 2", "hba1c", "glycemic", "glp-1", "sglt2", "metformin", "đái tháo đường"),
    },
    "dyslipidemia_adult_outpatient": {
        "label": "Rối loạn lipid máu",
        "keywords": ("dyslipidemia", "lipid", "ldl", "cholesterol", "statin", "triglyceride"),
    },
    "heart_failure_adult_outpatient": {
        "label": "Suy tim",
        "keywords": ("heart failure", "hfref", "hfmref", "hfpef", "suy tim", "ejection fraction"),
    },
    "ckd_adult_outpatient": {
        "label": "Bệnh thận mạn",
        "keywords": ("chronic kidney disease", "ckd", "kdigo", "egfr", "albuminuria", "bệnh thận mạn"),
    },
    "copd_adult_outpatient": {
        "label": "COPD",
        "keywords": ("copd", "gold", "chronic obstructive pulmonary", "bệnh phổi tắc nghẽn"),
    },
    "gout_adult_outpatient": {
        "label": "Gout / Tăng acid uric",
        "keywords": ("gout", "urate", "uric acid", "allopurinol", "febuxostat", "acid uric"),
    },
    "atrial_fibrillation_adult_outpatient": {
        "label": "Rung nhĩ",
        "keywords": ("atrial fibrillation", "afib", "anticoagulation", "doac", "rung nhĩ"),
    },
    "osteoporosis_adult_outpatient": {
        "label": "Loãng xương",
        "keywords": ("osteoporosis", "fracture risk", "bisphosphonate", "dxa", "frax", "loãng xương"),
    },
    "thyroid_adult_outpatient": {
        "label": "Bệnh tuyến giáp",
        "keywords": ("thyroid", "hypothyroidism", "hyperthyroidism", "levothyroxine", "graves", "tuyến giáp"),
    },
}

QUEUE_FILENAME = "knowledge_pack_update_queue.json"
DEFAULT_RESULTS_DIR = BASE_DIR / "results"


@dataclass(frozen=True)
class PackMatch:
    pack_id: str
    pack_label: str
    score: int


def _norm(value: object) -> str:
    return str(value or "").casefold()


def _evidence_text(row: EvidenceItem) -> str:
    pieces = [
        row.title,
        row.abstract,
        row.safety_signal,
        row.practice_impact,
        row.clinical_area,
        row.ingest_query,
        row.journal_or_organization,
    ]
    return " ".join(_norm(piece) for piece in pieces if piece)


def match_pack(row: EvidenceItem) -> PackMatch | None:
    """Map một evidence item vào pack có keyword khớp mạnh nhất."""
    text = _evidence_text(row)
    best: PackMatch | None = None
    for pack_id, definition in PACK_DEFINITIONS.items():
        score = sum(1 for keyword in definition["keywords"] if keyword in text)
        if score and (best is None or score > best.score):
            best = PackMatch(pack_id, str(definition["label"]), score)
    return best


def _is_candidate(row: EvidenceItem) -> bool:
    source_type = _norm(row.source_type)
    study_type = _norm(row.study_type)
    return bool(
        source_type in {"guideline", "drug_safety"}
        or study_type in {"guideline", "regulatory_alert"}
        or row.safety_signal
        or row.is_actionable
        or row.classification == "need_full_text"
    )


def _priority(row: EvidenceItem) -> str:
    score = float(row.practice_change_score or 0)
    if row.safety_signal or _norm(row.source_type) == "drug_safety" or _norm(row.study_type) == "regulatory_alert":
        return "HIGH"
    if row.is_actionable or score >= 80:
        return "HIGH"
    if score >= 60 or _norm(row.study_type) == "guideline":
        return "MEDIUM"
    return "LOW"


def _refs(row: EvidenceItem) -> list[str]:
    refs = []
    if row.pmid:
        refs.append(f"PMID:{row.pmid}")
    if row.doi:
        refs.append(f"DOI:{row.doi}")
    if row.nct_id:
        refs.append(row.nct_id)
    if row.url:
        refs.append(row.url)
    return refs


def _reason_codes(row: EvidenceItem) -> list[str]:
    reasons = []
    if _norm(row.study_type) == "guideline" or _norm(row.source_type) == "guideline":
        reasons.append("guideline_update")
    if row.safety_signal or _norm(row.source_type) == "drug_safety":
        reasons.append("drug_safety_signal")
    if row.is_actionable:
        reasons.append("actionable_practice_change")
    if row.classification == "need_full_text":
        reasons.append("needs_full_text_before_pack_update")
    return reasons or ["surveillance_match"]


def _row_to_queue_item(row: EvidenceItem, match: PackMatch) -> dict:
    refs = _refs(row)
    return {
        "queue_id": f"KPQ-{match.pack_id}-{row.id}",
        "pack_id": match.pack_id,
        "pack_label": match.pack_label,
        "match_score": match.score,
        "priority": _priority(row),
        "review_status": "pending_physician_review",
        "human_required": True,
        "auto_apply": False,
        "evidence_id": row.id,
        "title": row.title,
        "source": row.source,
        "source_type": row.source_type,
        "study_type": row.study_type,
        "publication_date": row.publication_date,
        "practice_change_score": row.practice_change_score,
        "reliability_tier": row.reliability_tier,
        "reason_codes": _reason_codes(row),
        "source_refs": refs,
        "safety_signal": row.safety_signal,
        "practice_impact": row.practice_impact,
        "next_action": (
            "Bác sĩ kiểm chứng nguồn/toàn văn rồi mới cập nhật knowledge pack; "
            "không tự áp dụng vào lâm sàng."
        ),
    }


def _dedupe_items(items: Iterable[dict]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    out = []
    for item in items:
        key = (str(item["pack_id"]), "|".join(item.get("source_refs") or []) or str(item["title"]))
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def build_knowledge_pack_update_queue(days: int = 7, limit_per_pack: int = 5) -> dict:
    """Tạo queue cập nhật pack từ surveillance/evidence mới gần đây."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent_run_ids = run_state.recent_run_ids(days=days)

    with session_scope() as session:
        query = (
            session.query(EvidenceItem)
            .filter(EvidenceItem.is_primary_record.is_(True))
            .filter(EvidenceItem.is_mock.is_(False))
        )
        if recent_run_ids:
            query = query.filter(EvidenceItem.first_seen_run_id.in_(recent_run_ids))
        else:
            query = query.filter(EvidenceItem.created_at >= cutoff)

        rows = query.order_by(EvidenceItem.practice_change_score.desc().nullslast()).all()
        items = []
        per_pack_count: dict[str, int] = {}
        for row in rows:
            if not _is_candidate(row):
                continue
            match = match_pack(row)
            if not match:
                continue
            if per_pack_count.get(match.pack_id, 0) >= limit_per_pack:
                continue
            items.append(_row_to_queue_item(row, match))
            per_pack_count[match.pack_id] = per_pack_count.get(match.pack_id, 0) + 1

    items = _dedupe_items(items)
    return {
        "kind": "knowledge_pack_update_queue",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lookback_days": days,
        "review_policy": "review_only_no_auto_apply",
        "total_items": len(items),
        "items": items,
    }


def write_knowledge_pack_update_queue(
    days: int = 7,
    limit_per_pack: int = 5,
    output_path: Path | None = None,
) -> Path:
    """Ghi queue ra results/ để morning brief và operator cùng đọc."""
    payload = build_knowledge_pack_update_queue(days=days, limit_per_pack=limit_per_pack)
    path = output_path or DEFAULT_RESULTS_DIR / QUEUE_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path
