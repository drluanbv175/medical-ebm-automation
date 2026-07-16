from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "tools" / "verify_clinical_evidence_agent_standards.py"
FIXED_NOW = "2026-07-16T00:00:00+00:00"


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_clinical_evidence_agent_standards", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_clinical_evidence_agent_standards_are_ready_with_doctor_gate() -> None:
    mod = _load_module()
    report = mod.evaluate_all(generated_at=FIXED_NOW)

    assert report["kind"] == "clinical_evidence_agent_standards_report"
    assert report["overall_status"] == "CLINICAL_EVIDENCE_AGENT_STANDARD_READY_WITH_DOCTOR_GATE"
    assert report["fail_count"] == 0
    assert report["human_gate_count"] == 1
    assert report["standards_ready"] is True
    assert report["doctor_review_required_before_apply"] is True
    assert report["clinical_production_allowed"] is False
    assert report["real_patient_data_allowed"] is False
    assert report["auto_apply_allowed"] is False


def test_clinical_evidence_agent_standards_cover_all_required_domains() -> None:
    mod = _load_module()
    report = mod.evaluate_all(generated_at=FIXED_NOW)
    rows = {row["check_id"]: row for row in report["checks"]}

    assert set(rows) == {"EAS1", "EAS2", "EAS3", "EAS4", "EAS5", "EAS6"}
    assert rows["EAS1"]["status"] == "PASS"
    assert rows["EAS2"]["status"] == "PASS"
    assert rows["EAS3"]["status"] == "PASS"
    assert rows["EAS4"]["status"] == "PASS"
    assert rows["EAS5"]["status"] == "PASS"
    assert rows["EAS6"]["status"] == "HUMAN_GATE"
    assert all(not row["missing"] for row in rows.values())


def test_clinical_evidence_agent_standards_markdown_keeps_boundaries_visible() -> None:
    mod = _load_module()
    report = mod.evaluate_all(generated_at=FIXED_NOW)
    markdown = mod.markdown_report(report)

    assert "Clinical Evidence Agent Standards" in markdown
    assert "CLINICAL_EVIDENCE_AGENT_STANDARD_READY_WITH_DOCTOR_GATE" in markdown
    assert "Doctor review required before apply: `True`" in markdown
    assert "Clinical production allowed: `False`" in markdown
    assert "Auto-apply allowed: `False`" in markdown
    assert "Cần bác sĩ kiểm chứng" in markdown
