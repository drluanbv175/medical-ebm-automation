#!/usr/bin/env python3
"""Import nguồn chính thức Phase 2D với provenance, không tự VERIFIED claim."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.evidence.manual_source_import import import_official_source  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2D manual official source import")
    parser.add_argument("--source-file", required=True)
    parser.add_argument("--source-origin-url", required=True)
    parser.add_argument("--organization", required=True)
    parser.add_argument("--source-type", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--publication-date", required=True)
    parser.add_argument("--imported-by", required=True)
    parser.add_argument("--import-date", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--page-count-or-html-snapshot", required=True)
    parser.add_argument("--copyright-or-access-note", required=True)
    parser.add_argument("--section-heading", default="")
    parser.add_argument("--text-extraction-reliable", action="store_true")
    args = parser.parse_args()

    result = import_official_source({
        "source_file": args.source_file,
        "source_origin_url": args.source_origin_url,
        "organization": args.organization,
        "source_type": args.source_type,
        "title": args.title,
        "version": args.version,
        "publication_date": args.publication_date,
        "imported_by": args.imported_by,
        "import_date": args.import_date,
        "sha256": args.sha256,
        "page_count_or_html_snapshot": args.page_count_or_html_snapshot,
        "copyright_or_access_note": args.copyright_or_access_note,
        "section_heading": args.section_heading,
        "text_extraction_reliable": args.text_extraction_reliable,
    })
    payload = {
        "imported": result.imported,
        "status": result.status,
        "issues": result.issues,
        "provenance": result.provenance.__dict__ if result.provenance else None,
        "snapshot": result.snapshot.__dict__ if result.snapshot else None,
        "note": "Import nguồn không tự chuyển claim sang VERIFIED; cần reviewer validation và claim mapping.",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.imported else 2


if __name__ == "__main__":
    sys.exit(main())
