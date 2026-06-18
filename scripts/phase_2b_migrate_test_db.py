#!/usr/bin/env python3
"""Apply governance migration trên isolated test database Phase 2B."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, inspect  # noqa: E402

from app.governance.migrations import GOVERNANCE_TABLES, create_governance_schema  # noqa: E402
from scripts.phase_2b_seed_governance_test_data import seed_governance_test_data  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2B test DB migration")
    parser.add_argument("--db-path", default="/private/tmp/ebm_phase_2b_governance.db")
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
        "production_database_touched": False,
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
