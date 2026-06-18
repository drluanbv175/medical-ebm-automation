#!/usr/bin/env python3
"""Dry-run/apply-dev migration governance V7 Phase 2A.

Mặc định chỉ in kế hoạch. Chỉ dùng `--apply-dev` trên SQLite/test database đã sao lưu.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.governance.migrations import build_governance_migration_plan, create_governance_schema  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Governance V7 Phase 2A migration helper")
    parser.add_argument("--apply-dev", action="store_true", help="Tạo bảng còn thiếu trên DB cấu hình hiện tại")
    args = parser.parse_args()

    if args.apply_dev:
        plan = create_governance_schema()
        print(f"APPLIED_DEV migration_id={plan.migration_id} missing_before={len(plan.missing_tables)}")
        return 0

    plan = build_governance_migration_plan()
    print(f"DRY_RUN migration_id={plan.migration_id}")
    print(f"destructive={plan.destructive}")
    print("missing_tables=" + ",".join(plan.missing_tables))
    for statement in plan.sql:
        print(statement)
    return 0


if __name__ == "__main__":
    sys.exit(main())
