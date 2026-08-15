#!/usr/bin/env python3
"""CLI kiểm clinical output packet trước khi coi là actionable."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.clinical_output_validator import validate_clinical_output_packet  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", help="Đường dẫn JSON packet theo OUTPUT_SCHEMA clinical_runtime")
    args = parser.parse_args()

    packet = json.loads(Path(args.packet).read_text(encoding="utf-8"))
    result = validate_clinical_output_packet(packet)
    print(json.dumps({
        "actionable_allowed": result.actionable_allowed,
        "status": result.status,
        "blockers": result.blockers,
        "warnings": result.warnings,
        "disclaimer": "Cần bác sĩ kiểm chứng.",
    }, ensure_ascii=False, indent=2))
    return 0 if result.actionable_allowed else 1


if __name__ == "__main__":
    raise SystemExit(main())
