#!/usr/bin/env python3
"""Live source validation Phase 2C cho real-pack pilot.

Không sửa evidence registry, không release content. Khi network/source unavailable,
ghi `SOURCE_UNAVAILABLE` và giữ pack ở review-only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.evidence.citation_verification import CitationVerifier  # noqa: E402
from app.evidence.live_adapter_registry import build_live_adapter_registry  # noqa: E402

SOURCE_IDENTIFIERS: Dict[str, Mapping[str, str]] = {
    "pubmed": {"pmid": "12728155", "url": "https://pubmed.ncbi.nlm.nih.gov/12728155/"},
    "europepmc": {"doi": "10.1056/NEJMoa2034577", "url": "https://doi.org/10.1056/NEJMoa2034577"},
    "crossref": {"doi": "10.1056/NEJMoa2034577", "url": "https://doi.org/10.1056/NEJMoa2034577"},
    "openalex": {"doi": "10.1056/NEJMoa2034577", "url": "https://doi.org/10.1056/NEJMoa2034577"},
    "semantic_scholar": {"doi": "10.1056/NEJMoa2034577", "url": "https://doi.org/10.1056/NEJMoa2034577"},
    "guideline_rss": {
        "query": "BMJ Evidence-Based Medicine",
        "source_type": "guideline",
        "url": "https://ebm.bmj.com/rss/current.xml",
    },
    "openfda": {"drug_name": "aspirin", "source_type": "drug_safety", "url": "https://api.fda.gov/drug/event.json"},
}


def _payload(source: str, identifiers: Mapping[str, str], topic: str) -> Dict[str, object]:
    return {
        "identifiers": dict(identifiers),
        "title": "Phase 2C live source validation placeholder",
        "topic": topic,
        "source_type": identifiers.get("source_type", "article"),
        "population": "Adults",
        "claim_location": "phase_2c_live_validation",
        "year_or_version": "",
        **dict(identifiers),
    }


def _row(source: str, result, adapter) -> Dict[str, object]:
    checks = dict(result.checks)
    return {
        "source": source,
        "adapter_status": adapter.health.health_status,
        "network_status": "unavailable" if result.status.value == "SOURCE_UNAVAILABLE" else "available_or_not_required",
        "rate_limit_status": "not_rate_limited",
        "record_found": checks.get("source_found", False),
        "title_match": checks.get("title_match", False),
        "year_version_match": checks.get("year_or_version_match", False),
        "source_type_match": checks.get("source_type_match", False),
        "population_assessable": checks.get("population_assessable", False),
        "claim_location_present": checks.get("claim_location_present", False),
        "retraction_status": "not_retracted" if checks.get("not_retracted") else "unknown_or_affected",
        "verification_status": result.status.value,
        "last_verified_at": result.last_verified_date,
        "cache_status": "not_verified_from_expired_cache",
        "error_reason": "; ".join(result.reasons),
    }


def _write_markdown(rows: List[Mapping[str, object]], output: Path, topic: str, environment: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 2C Live Source Report",
        "",
        f"Generated at: `{datetime.now(timezone.utc).isoformat()}`",
        f"Topic: `{topic}`",
        f"Environment: `{environment}`",
        "",
        (
            "| Source | Adapter | Network | Rate limit | Found | Title match | Year/version | Source type | "
            "Population | Claim location | Retraction | Verification | Last verified | Cache | Error |"
        ),
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {source} | {adapter_status} | {network_status} | {rate_limit_status} | {record_found} | "
            "{title_match} | {year_version_match} | {source_type_match} | {population_assessable} | "
            "{claim_location_present} | {retraction_status} | {verification_status} | {last_verified_at} | "
            "{cache_status} | {error_reason} |".format(**row)
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2C live source validation")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--environment", default="review")
    parser.add_argument("--output", default="docs/system-v7/PHASE_2C_LIVE_SOURCE_REPORT.md")
    args = parser.parse_args()
    settings.http_max_retries = 0
    settings.http_timeout = 4
    settings.http_backoff_factor = 0
    settings.http_min_interval = 0

    registry = build_live_adapter_registry()
    rows: List[Mapping[str, object]] = []
    for source, adapter in registry.items():
        identifiers = SOURCE_IDENTIFIERS[source]
        result = CitationVerifier(adapter, today=date.today()).verify(_payload(source, identifiers, args.topic))
        rows.append(_row(source, result, adapter))
    _write_markdown(rows, Path(args.output), args.topic, args.environment)
    print(json.dumps(
        {"topic": args.topic, "environment": args.environment, "rows": rows},
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
