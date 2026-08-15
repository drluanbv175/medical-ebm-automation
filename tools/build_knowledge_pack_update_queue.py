#!/usr/bin/env python3
"""Build review-only queue from surveillance evidence to clinical knowledge packs."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
import sys as _sys_r4
for _s_r4 in (_sys_r4.stdout, _sys_r4.stderr):
    try:
        _s_r4.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database import init_db  # noqa: E402
from app.services.knowledge_pack_surveillance import (  # noqa: E402
    build_knowledge_pack_update_queue,
    write_knowledge_pack_update_queue,
)
from app.utils.console import configure_unicode_console  # noqa: E402


def main() -> int:
    configure_unicode_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--limit-per-pack", type=int, default=5)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()

    init_db()
    if args.preview:
        payload = build_knowledge_pack_update_queue(days=args.days, limit_per_pack=args.limit_per_pack)
        print(f"Knowledge pack update queue: {payload['total_items']} pending item(s)")
        for item in payload["items"]:
            refs = ", ".join(item.get("source_refs") or ["no-ref"])
            print(f"- [{item['priority']}] {item['pack_label']}: {item['title']} ({refs})")
        return 0

    path = write_knowledge_pack_update_queue(
        days=args.days,
        limit_per_pack=args.limit_per_pack,
        output_path=args.output,
    )
    print(f"Đã ghi queue cập nhật knowledge pack: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
