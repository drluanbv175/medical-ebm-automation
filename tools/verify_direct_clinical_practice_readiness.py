#!/usr/bin/env python3
"""Kiểm cổng sẵn sàng áp dụng lâm sàng trực tiếp cho sổ cái EBM.

Verifier này không tự biến chứng cứ mới thành khuyến cáo điều trị. Nó chỉ tách riêng
hàng "physician-direct-use ready": thẻ phải đã được bác sĩ/master duyệt, truy nguyên được,
đủ mới theo lần rà soát, GRADE cao/vừa, không có dấu PII và không còn nhãn cần bổ sung.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from app.sources.authority import match_authority_source  # noqa: E402

DEFAULT_MASTER = ROOT / "EBM_MASTER" / "EBM_MASTER.json"
DEFAULT_JSON = REPO / "reports" / "DIRECT_CLINICAL_PRACTICE_READINESS.json"
DEFAULT_MD = REPO / "reports" / "DIRECT_CLINICAL_PRACTICE_READINESS.md"

READY = "READY_FOR_PHYSICIAN_DIRECT_USE"
REVIEW = "REVIEW_REQUIRED"
BLOCKED = "BLOCKED_FOR_DIRECT_USE"
DISCLAIMER = "Cần bác sĩ kiểm chứng. Không tự động áp dụng cho bệnh nhân hoặc ghi EMR/HIS."

ACCEPTED_GRADES = {"high", "mod", "moderate"}
TRUSTED_SOURCE_TERMS = (
    "guideline",
    "practice guideline",
    "systematic",
    "meta-analysis",
    "rct",
    "randomized",
    "regulatory",
    "drug safety",
    "hta",
)
TRUSTED_AGENCY_TERMS = (
    "kdigo",
    "nejm",
    "n engl j med",
    "lancet",
    "jama",
    "bmj",
    "cochrane",
    "nice",
    "who",
    "cdc",
    "fda",
    "ema",
    "mhra",
    "acg",
    "aga",
    "esc",
    "aha",
    "acc",
    "ada",
    "easl",
    "aasld",
    "gold",
)
TRUSTED_OFFICIAL_HOSTS = (
    "who.int",
    "cdc.gov",
    "fda.gov",
    "ema.europa.eu",
    "nice.org.uk",
    "mhra.gov.uk",
    "moh.gov.vn",
    "kcb.vn",
    "cochranelibrary.com",
)

UNVERIFIED_TERMS = (
    "chua xac minh",
    "chưa xác minh",
    "can truy nguyen",
    "cần truy nguyên",
    "can xac minh",
    "cần xác minh",
    "needs_verification",
    "unverified",
    "pending",
)
VERIFIED_TERMS = ("da xac minh", "đã xác minh", "verified")
UNRESOLVED_TERMS = (
    "[can",
    "[cần",
    "todo",
    "placeholder",
    "can bo sung",
    "cần bổ sung",
    "can xac nhan",
    "cần xác nhận",
)
PII_PATTERNS = (
    re.compile(r"\b0\d{9,10}\b"),
    re.compile(r"\b\d{12}\b"),
    re.compile(r"\b(MRN|CCCD|CMND|so ho so|số hồ sơ)\b", re.IGNORECASE),
    re.compile(r"\b[A-Z]{2}\d{6,}\b"),
)


@dataclass(frozen=True)
class CardReadiness:
    card_id: str
    status: str
    decision: str
    grade_level: str
    topic: str
    source_date: str
    review_date: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def ensure_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            encoding = (getattr(stream, "encoding", "") or "").lower()
            if encoding and "utf" not in encoding and hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            continue


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower()


def _norm(text: Any) -> str:
    return _strip_accents(str(text or "")).strip()


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        out: list[str] = []
        for item in value.values():
            out.extend(_walk_strings(item))
        return out
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        out: list[str] = []
        for item in value:
            out.extend(_walk_strings(item))
        return out
    return []


def _parse_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    patterns = (
        (r"(\d{4})-(\d{2})-(\d{2})", lambda m: date(int(m[1]), int(m[2]), int(m[3]))),
        (r"(\d{4})/(\d{2})/(\d{2})", lambda m: date(int(m[1]), int(m[2]), int(m[3]))),
        (r"\b(\d{2})/(\d{2})/(\d{4})\b", lambda m: date(int(m[3]), int(m[2]), int(m[1]))),
        (r"\b(\d{4})-(\d{2})\b", lambda m: date(int(m[1]), int(m[2]), 28)),
        (r"\b(20\d{2})\b", lambda m: date(int(m[1]), 12, 31)),
    )
    for pattern, build in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        try:
            return build(match)
        except ValueError:
            return None
    return None


def _card_source(card: Mapping[str, Any]) -> Mapping[str, Any]:
    source = card.get("source")
    return source if isinstance(source, Mapping) else {}


def _source_urls(card: Mapping[str, Any]) -> list[str]:
    source = _card_source(card)
    values = [str(source.get("url", "") or "")]
    values.extend(str(item or "") for item in card.get("references", []) if isinstance(item, str))
    return [value for value in values if value.startswith(("http://", "https://", "URL:http"))]


def _has_durable_identifier(card: Mapping[str, Any]) -> bool:
    source = _card_source(card)
    pmid = str(source.get("pmid", "") or "").strip()
    doi = str(source.get("doi", "") or "").strip()
    if pmid or doi:
        return True
    refs = " ".join(str(item or "") for item in card.get("references", []))
    return bool(re.search(r"\bPMID:\s*\d+\b", refs, re.IGNORECASE) or re.search(r"\bDOI:\s*\S+", refs, re.IGNORECASE))


def _has_trusted_official_url(card: Mapping[str, Any]) -> bool:
    for raw_url in _source_urls(card):
        url = raw_url.removeprefix("URL:")
        host = urlparse(url).netloc.lower()
        if any(host == trusted or host.endswith("." + trusted) for trusted in TRUSTED_OFFICIAL_HOSTS):
            return True
    return False


def _is_verified(card: Mapping[str, Any]) -> bool:
    status = str(card.get("verification_status", "") or "")
    compact = _norm(status)
    if any(term in status.lower() for term in UNVERIFIED_TERMS) or any(term in compact for term in UNVERIFIED_TERMS):
        return False
    return any(term in status.lower() for term in VERIFIED_TERMS) or any(term in compact for term in VERIFIED_TERMS)


def _has_doctor_gate_evidence(card: Mapping[str, Any]) -> tuple[bool, list[str]]:
    warnings: list[str] = []
    approval_keys = ("doctor_approval_id", "human_approval_id", "approved_by", "approval_ledger_id")
    if any(str(card.get(key, "") or "").strip() for key in approval_keys):
        return True, warnings
    provenance = _norm(card.get("provenance", ""))
    if provenance in {"from_doctor_master", "claude_verified", "doctor_verified"}:
        warnings.append("legacy_doctor_curated_without_signed_approval_id")
        return True, warnings
    return False, warnings


def _has_trusted_source_type(card: Mapping[str, Any]) -> bool:
    source = _card_source(card)
    if match_authority_source(
        source.get("agency"),
        source.get("journal_or_organization"),
        source.get("title"),
        card.get("topic"),
        card.get("critical_appraisal"),
    ):
        return True
    joined = " ".join(
        str(value or "")
        for value in (
            source.get("type"),
            source.get("agency"),
            source.get("title"),
            card.get("critical_appraisal"),
        )
    )
    compact = _norm(joined)
    return any(term in compact for term in TRUSTED_SOURCE_TERMS + TRUSTED_AGENCY_TERMS)


def _has_explicit_day_or_month(value: Any) -> bool:
    text = str(value or "")
    return bool(
        re.search(r"\d{4}[-/]\d{2}[-/]\d{2}", text)
        or re.search(r"\b\d{2}/\d{2}/\d{4}\b", text)
        or re.search(r"\b\d{4}-\d{2}\b", text)
    )


def _pii_suspected(card: Mapping[str, Any]) -> bool:
    checked = {
        "id": card.get("id", ""),
        "topic": card.get("topic", ""),
        "recommendation": card.get("recommendation", ""),
        "pico": card.get("pico", ""),
        "pico_question": card.get("pico_question", ""),
        "vietnam_context": card.get("vietnam_context", ""),
        "operational_assessment": card.get("operational_assessment", ""),
    }
    for text in _walk_strings(checked):
        normalized = unicodedata.normalize("NFC", text)
        compact = _strip_accents(normalized)
        if any(pattern.search(normalized) or pattern.search(compact) for pattern in PII_PATTERNS):
            return True
    return False


def evaluate_card(card: Mapping[str, Any], *, today: date, freshness_days: int = 90) -> CardReadiness:
    blockers: list[str] = []
    warnings: list[str] = []
    card_id = str(card.get("id", "") or "UNKNOWN")
    decision = _norm(card.get("decision", ""))
    grade_level = _norm(card.get("gradeLevel", ""))
    topic = str(card.get("topic", "") or card.get("source", {}).get("title", "") or "")
    source_date_raw = str(card.get("date_source", "") or "")
    review_date_raw = str(card.get("date_added", "") or card.get("last_reviewed", "") or "")

    if decision != "apply":
        blockers.append(f"decision_not_apply:{decision or 'missing'}")
    if not _is_verified(card):
        blockers.append("verification_not_confirmed")
    if grade_level not in ACCEPTED_GRADES:
        blockers.append(f"grade_not_direct_ready:{grade_level or 'missing'}")
    if not (_has_durable_identifier(card) or _has_trusted_official_url(card)):
        blockers.append("missing_pmid_doi_or_trusted_official_url")
    if not _has_trusted_source_type(card):
        blockers.append("source_type_not_high_authority")

    review_date = _parse_date(review_date_raw)
    if review_date is None:
        blockers.append("freshness_review_date_missing")
    else:
        age_days = (today - review_date).days
        if age_days < -7:
            blockers.append("freshness_review_date_in_future")
        elif age_days > freshness_days:
            blockers.append(f"freshness_review_stale:{age_days}d")

    source_date = _parse_date(source_date_raw)
    if source_date and _has_explicit_day_or_month(source_date_raw) and (source_date - today).days > 30:
        blockers.append("source_date_too_far_in_future")

    joined_card_text = " ".join(_walk_strings(card))
    compact_card_text = _norm(joined_card_text)
    if any(term in compact_card_text for term in UNRESOLVED_TERMS):
        blockers.append("unresolved_review_marker_present")
    if _pii_suspected(card):
        blockers.append("pii_suspected")

    doctor_gate_ok, doctor_gate_warnings = _has_doctor_gate_evidence(card)
    warnings.extend(doctor_gate_warnings)
    if not doctor_gate_ok:
        blockers.append("missing_doctor_gate_evidence")

    if not blockers:
        status = READY
    elif decision == "apply":
        status = BLOCKED
    else:
        status = REVIEW

    return CardReadiness(
        card_id=card_id,
        status=status,
        decision=decision or "missing",
        grade_level=grade_level or "missing",
        topic=topic,
        source_date=source_date_raw,
        review_date=review_date_raw,
        blockers=blockers,
        warnings=warnings,
    )


def evaluate_master(
    master: Mapping[str, Any],
    *,
    today: date,
    freshness_days: int = 90,
) -> dict[str, Any]:
    cards = master.get("evidence_cards", [])
    if not isinstance(cards, list):
        cards = []
    results = [
        evaluate_card(card, today=today, freshness_days=freshness_days)
        for card in cards
        if isinstance(card, Mapping)
    ]
    counts = Counter(result.status for result in results)
    blocker_counts: Counter[str] = Counter()
    for result in results:
        blocker_counts.update(result.blockers)
    apply_blocked = [result for result in results if result.status == BLOCKED]
    ready = [result for result in results if result.status == READY]
    system_status = "DIRECT_USE_QUEUE_READY_WITH_DOCTOR_GATE"
    if apply_blocked:
        system_status = "DIRECT_USE_QUEUE_READY_WITH_BLOCKED_APPLY_ITEMS"
    return {
        "kind": "direct_clinical_practice_readiness_report",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "today": today.isoformat(),
        "freshness_days": freshness_days,
        "system_status": system_status,
        "auto_apply_allowed": False,
        "doctor_final_decision_required": True,
        "total_cards": len(results),
        "ready_for_physician_direct_use": counts[READY],
        "review_required": counts[REVIEW],
        "blocked_apply_items": counts[BLOCKED],
        "ready_cards": [asdict(item) for item in ready],
        "blocked_apply_cards": [asdict(item) for item in apply_blocked],
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "disclaimer": DISCLAIMER,
    }


def markdown_report(report: Mapping[str, Any], *, top: int = 30) -> str:
    lines = [
        "# Direct Clinical Practice Readiness",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Today: `{report['today']}`",
        f"- System status: `{report['system_status']}`",
        f"- Total cards: `{report['total_cards']}`",
        f"- Ready for physician direct use: `{report['ready_for_physician_direct_use']}`",
        f"- Review required: `{report['review_required']}`",
        f"- Blocked apply items: `{report['blocked_apply_items']}`",
        f"- Auto-apply allowed: `{report['auto_apply_allowed']}`",
        f"- Doctor final decision required: `{report['doctor_final_decision_required']}`",
        "",
        "## Top Ready Cards",
        "",
    ]
    ready_cards = list(report.get("ready_cards", []))[:top]
    if ready_cards:
        lines.append("| ID | Grade | Review date | Topic |")
        lines.append("|---|---|---|---|")
        for card in ready_cards:
            topic = str(card.get("topic", "")).replace("|", "/")
            lines.append(f"| {card.get('card_id')} | {card.get('grade_level')} | {card.get('review_date')} | {topic} |")
    else:
        lines.append("No card is direct-use ready under the current gate.")
    lines.extend(["", "## Blocker Summary", "", "| Blocker | Count |", "|---|---:|"])
    for blocker, count in sorted(dict(report.get("blocker_counts", {})).items()):
        lines.append(f"| `{blocker}` | {count} |")
    lines.extend(["", DISCLAIMER, ""])
    return "\n".join(lines)


def _load_master(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    ensure_utf8_console()
    parser = argparse.ArgumentParser(description="Verify direct clinical practice readiness from EBM_MASTER.json.")
    parser.add_argument("--master", type=Path, default=DEFAULT_MASTER)
    parser.add_argument("--today", default=date.today().isoformat())
    parser.add_argument("--freshness-days", type=int, default=90)
    parser.add_argument("--json", action="store_true", help="print JSON report")
    parser.add_argument("--write", action="store_true", help="write JSON and Markdown reports")
    parser.add_argument("--strict-apply", action="store_true", help="return non-zero if any apply card is blocked")
    args = parser.parse_args(argv)

    today = date.fromisoformat(args.today)
    report = evaluate_master(_load_master(args.master), today=today, freshness_days=args.freshness_days)
    if args.write:
        DEFAULT_JSON.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        DEFAULT_MD.write_text(markdown_report(report), encoding="utf-8")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"system_status={report['system_status']}")
        print(f"total_cards={report['total_cards']}")
        print(f"ready_for_physician_direct_use={report['ready_for_physician_direct_use']}")
        print(f"review_required={report['review_required']}")
        print(f"blocked_apply_items={report['blocked_apply_items']}")
        print(f"auto_apply_allowed={report['auto_apply_allowed']}")
        print("Cần bác sĩ kiểm chứng.")
    return 1 if args.strict_apply and report["blocked_apply_items"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
