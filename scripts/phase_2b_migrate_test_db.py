#!/usr/bin/env python3
"""Apply governance migration trên isolated test database Phase 2B."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, inspect  # noqa: E402

from app.governance.migrations import GOVERNANCE_TABLES, create_governance_schema  # noqa: E402
from scripts.phase_2b_seed_governance_test_data import (  # noqa: E402
    is_production_database,
    seed_governance_test_data,
)

# Vá 2026-09-06 (audit vòng 34, phát hiện #2 — HIGH): "/private/tmp" là
# symlink-target đặc thù macOS ("/tmp" -> "/private/tmp"); trên Linux (môi
# trường CI/dev/server thật của repo này) thư mục "/private" không tồn tại
# -> chạy script không kèm --db-path (cách gọi ngắn gọn thông thường) sẽ
# crash OperationalError ngay khi mở file, không migrate được gì.
# tempfile.gettempdir() tự resolve đúng thư mục tạm theo từng hệ điều hành.
_DEFAULT_DB_PATH = str(Path(tempfile.gettempdir()) / "ebm_phase_2b_governance.db")


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2B test DB migration")
    parser.add_argument("--db-path", default=_DEFAULT_DB_PATH)
    parser.add_argument("--fresh", action="store_true", help="Remove existing isolated test DB first")
    args = parser.parse_args()
    db_path = Path(args.db_path)
    if args.fresh and db_path.exists():
        db_path.unlink()
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url, future=True, connect_args={"check_same_thread": False})
    plan = create_governance_schema(engine)
    seed = seed_governance_test_data(database_url)
    existing = set(inspect(engine).get_table_names())
    missing_after = sorted(set(GOVERNANCE_TABLES) - existing)
    result = {
        "database_url": database_url,
        "migration_id": plan.migration_id,
        "missing_before": plan.missing_tables,
        "missing_after": missing_after,
        "migration_passed": not missing_after,
        "seed": seed,
        # Vá 2026-09-06 (audit vòng 42, phát hiện #2 — HIGH): trước đây literal
        # hardcode False, không phải kết quả so sánh — xem is_production_database().
        "production_database_touched": is_production_database(database_url),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    passed = (
        result["migration_passed"]
        and seed["invalid_transition_blocked"]
        and seed["unapproved_release_blocked"]
    )
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
