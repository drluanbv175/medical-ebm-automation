from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "tools" / "verify_personal_production_hardening.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_personal_production_hardening", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_personal_production_hardening_covers_all_seven_domains() -> None:
    mod = _load_module()
    report = mod.evaluate_all(generated_at="2026-07-16T00:00:00+00:00")

    assert report["kind"] == "personal_production_hardening_report"
    assert report["overall_status"] == "CONTROLLED_PERSONAL_READY_WITH_HUMAN_GATES"
    assert report["fail_count"] == 0
    assert report["human_gate_count"] >= 6
    assert report["clinical_production_allowed"] is False
    assert report["real_patient_data_allowed"] is False
    assert {row["domain_id"] for row in report["checks"]} == {
        "P1",
        "P2",
        "P3",
        "P4",
        "P5",
        "P6",
        "P7",
    }


def test_mode_separation_keeps_dangerous_flags_disabled() -> None:
    mod = _load_module()
    check = mod.check_mode_separation()

    assert check.status == mod.PASS
    assert "dangerous_flags_disabled=true" in check.findings
