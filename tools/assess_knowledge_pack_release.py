#!/usr/bin/env python3
"""Assess clinical release readiness for knowledge packs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.knowledge_pack_release_gate import (  # noqa: E402
    assess_all_pack_release_readiness,
    assess_pack_release_readiness,
    release_readiness_payload,
    summarize_release_readiness,
)
from app.utils.console import configure_unicode_console  # noqa: E402


def main() -> int:
    configure_unicode_console()
    parser = argparse.ArgumentParser(description="Assess knowledge pack clinical release readiness.")
    parser.add_argument("--packs-dir", default=str(ROOT / "knowledge-packs"))
    parser.add_argument("--version", default="2026.1-draft")
    parser.add_argument("--pack", default=None)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--output", default=None, help="Write machine-readable JSON to this path.")
    parser.add_argument("--require-clinical-release-ready", action="store_true")
    args = parser.parse_args()

    packs_dir = Path(args.packs_dir)
    if args.pack:
        results = [assess_pack_release_readiness(packs_dir / args.pack, args.version)]
    else:
        results = assess_all_pack_release_readiness(packs_dir, args.version)

    payload = release_readiness_payload(results)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if args.require_clinical_release_ready and payload["summary"]["blocked"] else 0

    summary = summarize_release_readiness(results)
    print(
        "Summary: "
        f"{summary['schema_ok']}/{summary['total']} schema ok; "
        f"{summary['review_ready']}/{summary['total']} review ready; "
        f"{summary['clinical_release_ready']}/{summary['total']} clinical release ready"
    )
    for result in results:
        status = "READY" if result.clinical_release_ready else "BLOCKED"
        print(f"{status}: {result.pack_id} ({result.version_dir})")
        for issue in result.blockers[:8]:
            print(f"  - {issue.file}: {issue.message}")
        if len(result.blockers) > 8:
            print(f"  - ... {len(result.blockers) - 8} more blockers")

    if args.require_clinical_release_ready and summary["blocked"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
