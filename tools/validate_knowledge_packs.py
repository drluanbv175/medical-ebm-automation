#!/usr/bin/env python3
"""Validate schema clinical knowledge packs.

Chạy:
    python tools/validate_knowledge_packs.py
    python tools/validate_knowledge_packs.py --pack hypertension_adult_outpatient
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.knowledge_pack_schema import (  # noqa: E402
    KnowledgePackSchemaIssue,
    KnowledgePackSchemaResult,
    validate_pack_version,
)
from app.utils.console import configure_unicode_console  # noqa: E402


def main() -> int:
    configure_unicode_console()
    parser = argparse.ArgumentParser(description="Validate clinical knowledge pack YAML schema.")
    parser.add_argument("--packs-dir", default=str(ROOT / "knowledge-packs"))
    parser.add_argument("--version", default="2026.1-draft")
    parser.add_argument("--pack", default=None)
    args = parser.parse_args()

    packs_dir = Path(args.packs_dir)
    if args.pack:
        pack_dirs = [packs_dir / args.pack]
    else:
        pack_dirs = sorted(path for path in packs_dir.iterdir() if path.is_dir()) if packs_dir.exists() else []

    if not pack_dirs:
        print(f"FAIL: no knowledge packs found in {packs_dir}")
        return 1

    # Vá 2026-09-06 (audit vòng 33, phát hiện #4 — HIGH): trước đây vòng lặp
    # này KHÔNG cô lập từng pack — một pack có cấu trúc thư mục lỗi (vd
    # "2026.1-draft" tồn tại dưới dạng FILE thay vì thư mục, dễ xảy ra do
    # merge lỗi/thao tác tay nhầm/đồng bộ OneDrive dở dang) khiến
    # validate_pack_version() ném NotADirectoryError (version_path.iterdir()
    # trên một file) — sập TOÀN BỘ lệnh, không pack nào (kể cả các pack hợp
    # lệ khác) được validate hay báo cáo. Một pack lỗi giờ vẫn hiện ra như
    # FAIL kèm lý do, thay vì kéo sập cả lô.
    results = []
    for pack_dir in pack_dirs:
        try:
            results.append(validate_pack_version(pack_dir, args.version))
        except OSError as exc:
            results.append(KnowledgePackSchemaResult(
                pack_id=pack_dir.name,
                version_dir=args.version,
                issues=[KnowledgePackSchemaIssue(
                    file=args.version,
                    message=f"Không đọc được cấu trúc thư mục: {type(exc).__name__}: {exc}",
                )],
            ))
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        print(f"{status}: {result.pack_id} ({result.version_dir})")
        for issue in result.issues:
            print(f"  - {issue.severity}: {issue.file}: {issue.message}")

    failed = [result for result in results if not result.ok]
    print(f"Summary: {len(results) - len(failed)}/{len(results)} packs PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
