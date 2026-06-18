import json
import subprocess
import sys


def _run_script(script, *args):
    completed = subprocess.run(
        [sys.executable, script, *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_phase_2b_migrate_and_rollback_test_database(tmp_path):
    db_path = tmp_path / "phase_2b_governance.db"

    migration = _run_script("scripts/phase_2b_migrate_test_db.py", "--db-path", str(db_path), "--fresh")
    rollback = _run_script("scripts/phase_2b_rollback_test_db.py", "--db-path", str(db_path))

    assert migration["migration_passed"]
    assert migration["production_database_touched"] is False
    assert migration["seed"]["valid_transition_applied"]
    assert migration["seed"]["invalid_transition_blocked"]
    assert migration["seed"]["unapproved_release_blocked"]
    assert migration["seed"]["approved_release_allowed_in_test"]
    assert migration["seed"]["audit_count"] >= 4
    assert rollback["rollback_passed"]
    assert rollback["reapply_passed"]
    assert rollback["production_database_touched"] is False
