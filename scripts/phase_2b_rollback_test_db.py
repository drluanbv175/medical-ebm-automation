#!/usr/bin/env python3
"""Rollback/re-apply governance schema trên isolated test database Phase 2B."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, inspect, text  # noqa: E402

from app.governance.migrations import GOVERNANCE_TABLES, create_governance_schema  # noqa: E402

# Vá 2026-09-06 (audit vòng 34, phát hiện #2 — HIGH, cùng lỗi với
# phase_2b_migrate_test_db.py): "/private/tmp" hardcode kiểu macOS làm script
# crash trên Linux khi không truyền --db-path.
_DEFAULT_DB_PATH = str(Path(tempfile.gettempdir()) / "ebm_phase_2b_governance.db")


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2B test DB rollback")
    parser.add_argument("--db-path", default=_DEFAULT_DB_PATH)
    args = parser.parse_args()
    db_path = Path(args.db_path)
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url, future=True, connect_args={"check_same_thread": False})
    create_governance_schema(engine)
    with engine.begin() as conn:
        for table in reversed(GOVERNANCE_TABLES):
            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
    after_drop = set(inspect(engine).get_table_names())
    rollback_passed = not (set(GOVERNANCE_TABLES) & after_drop)
    create_governance_schema(engine)
    after_reapply = set(inspect(engine).get_table_names())
    missing_after_reapply = sorted(set(GOVERNANCE_TABLES) - after_reapply)
    result = {
        "database_url": database_url,
        "rollback_passed": rollback_passed,
        "reapply_passed": not missing_after_reapply,
        "missing_after_reapply": missing_after_reapply,
        "production_database_touched": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["rollback_passed"] and result["reapply_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
