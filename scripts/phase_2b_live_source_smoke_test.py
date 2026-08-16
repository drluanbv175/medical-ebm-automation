#!/usr/bin/env python3
"""Opt-in smoke test live-source adapters Phase 2B.

Script không sửa evidence registry, không release content và không ghi PII. Nguồn
ngoài unavailable được ghi nhận an toàn; không được đổi thành VERIFIED.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings  # noqa: E402
from app.evidence.citation_verification import CitationVerificationStatus, CitationVerifier  # noqa: E402
from app.evidence.live_adapter_registry import (  # noqa: E402
    ADAPTER_CLASSES,
    adapter_status_table,
    build_live_adapter_registry,
)

DEFAULT_IDENTIFIERS: Dict[str, Mapping[str, str]] = {
    "pubmed": {"pmid": "12728155"},
    "crossref": {"doi": "10.1056/NEJMoa2034577"},
    "europepmc": {"doi": "10.1056/NEJMoa2034577"},
    "openalex": {"doi": "10.1056/NEJMoa2034577"},
    "semantic_scholar": {"doi": "10.1056/NEJMoa2034577"},
    "guideline_rss": {
        "query": "BMJ Evidence-Based Medicine",
        "source_type": "guideline",
        "url": "https://ebm.bmj.com/rss/current.xml",
    },
    "openfda": {"drug_name": "aspirin", "source_type": "drug_safety", "url": "https://api.fda.gov/drug/event.json"},
}


def _evidence_payload(source_name: str, identifiers: Mapping[str, str]) -> Dict[str, object]:
    payload: Dict[str, object] = {
        "title": "COVID-19 vaccine trial" if source_name != "openfda" else "openFDA drug safety signal for aspirin",
        "source_type": identifiers.get("source_type", "article"),
        "claim_location": "live smoke test",
        "year_or_version": "",
        "identifiers": dict(identifiers),
    }
    payload.update(identifiers)
    return payload


def _write_reports(report: Mapping[str, object], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "phase_2b_live_source_smoke_report.json"
    md_path = output_dir / "phase_2b_live_source_smoke_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8",
        newline="\n")
    rows = report.get("results", [])
    lines = [
        "# Phase 2B Live Source Smoke Report",
        "",
        f"Generated at: `{report.get('generated_at')}`",
        "",
        "| Source | Status | Safe | Reason |",
        "|---|---:|---:|---|",
    ]
    if isinstance(rows, list):
        for row in rows:
            reasons = ", ".join(row.get("reasons") or [])
            lines.append(
                f"| {row.get('source')} | {row.get('status')} | {row.get('safe')} | {reasons} |"
            )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2B live-source smoke test")
    parser.add_argument("--sources", default="", help="Comma-separated sources")
    parser.add_argument("--all", action="store_true", help="Run all registered sources")
    parser.add_argument("--output-dir", default="exports/phase_2b")
    args = parser.parse_args()
    settings.http_max_retries = 0
    settings.http_timeout = 4
    settings.http_backoff_factor = 0
    settings.http_min_interval = 0

    selected = list(ADAPTER_CLASSES) if args.all or not args.sources else [
        item.strip() for item in args.sources.split(",") if item.strip()
    ]
    registry = build_live_adapter_registry(selected)
    results = []
    unsafe = False
    for source_name, adapter in registry.items():
        identifiers = DEFAULT_IDENTIFIERS.get(source_name, {})
        verifier = CitationVerifier(adapter, today=date.today())
        result = verifier.verify(_evidence_payload(source_name, identifiers))
        safe_status = result.status is not CitationVerificationStatus.VERIFIED or result.safe_for_verified_evidence
        if not safe_status:
            unsafe = True
        results.append({
            "source": source_name,
            "status": result.status.value,
            "safe": safe_status,
            "reasons": list(result.reasons),
            "health_status": adapter.health.health_status,
            "failure_reason": adapter.health.failure_reason,
        })

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "source_health": adapter_status_table(registry),
        "policy": "unavailable_or_timeout_must_not_be_verified",
    }
    _write_reports(report, Path(args.output_dir))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if unsafe else 0


if __name__ == "__main__":
    sys.exit(main())
