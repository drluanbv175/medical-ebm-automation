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
    assert report["agent_contract_gate_count"] == 7
    assert report["agent_contract_human_gate_ids"] == ["CEG7"]


def test_clinical_evidence_agent_standards_cover_all_required_domains() -> None:
    mod = _load_module()
    report = mod.evaluate_all(generated_at=FIXED_NOW)
    rows = {row["check_id"]: row for row in report["checks"]}

    assert set(rows) == {"EAS1", "EAS2", "EAS3", "EAS4", "EAS5", "EAS6", "EAS7"}
    assert rows["EAS1"]["status"] == "PASS"
    assert rows["EAS2"]["status"] == "PASS"
    assert rows["EAS3"]["status"] == "PASS"
    assert rows["EAS4"]["status"] == "PASS"
    assert rows["EAS5"]["status"] == "PASS"
    assert rows["EAS6"]["status"] == "HUMAN_GATE"
    assert rows["EAS7"]["status"] == "PASS"
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
    assert "Release Packet Contract" in markdown
    assert "Release packet decision: `BLOCKED_UNTIL_DOCTOR_REVIEW`" in markdown
    assert "International Standards Profile" in markdown
    assert "International standard profile: `MAPPED_WITH_DOCTOR_GATE`" in markdown
    assert "Agent Gate Contract" in markdown
    assert "CEG7 Guardrail cuối và bác sĩ quyết định áp dụng" in markdown
    assert "Cần bác sĩ kiểm chứng" in markdown


def test_clinical_evidence_agent_contract_is_ordered_and_fail_closed() -> None:
    mod = _load_module()
    report = mod.evaluate_all(generated_at=FIXED_NOW)
    contract = report["agent_contract"]

    assert [gate["gate_id"] for gate in contract] == [
        "CEG1",
        "CEG2",
        "CEG3",
        "CEG4",
        "CEG5",
        "CEG6",
        "CEG7",
    ]
    assert contract[1]["owner_agent"] == "tra-cuu-chung-cu"
    assert "PMID/DOI/URL" in " ".join(contract[1]["fail_closed_when"])
    assert "verify_dashboard.py --online --strict-sources" in " ".join(
        contract[3]["automated_checks"]
    )
    assert "drug_safety_scan.py" in " ".join(contract[4]["automated_checks"])
    assert contract[-1]["human_gate"] is True
    assert contract[-1]["output_state"] == "doctor_gate_required_before_clinical_use"
    assert "Không auto_apply" in " ".join(contract[-1]["automated_checks"])


def test_release_packet_contract_blocks_until_doctor_review() -> None:
    mod = _load_module()
    report = mod.evaluate_all(generated_at=FIXED_NOW)
    packet = report["release_packet_contract"]

    assert packet["kind"] == "clinical_evidence_update_release_packet_contract"
    assert packet["decision"] == "BLOCKED_UNTIL_DOCTOR_REVIEW"
    assert packet["covered_gate_ids"] == [
        "CEG1",
        "CEG2",
        "CEG3",
        "CEG4",
        "CEG5",
        "CEG6",
        "CEG7",
    ]
    assert "doctor_review_packet" in packet["minimum_artifacts"]
    assert "final_guardrail_result" in packet["minimum_artifacts"]
    assert "verify_dashboard.py <dashboard>.html --online --strict-sources" in packet[
        "required_commands"
    ]
    assert "international_standard_profile" in packet["minimum_artifacts"]
    assert "standard_selection_rationale" in packet["minimum_artifacts"]
    assert "PII_DETECTED" in packet["hard_stop_reason_codes"]
    assert "SOURCE_UNVERIFIED" in packet["hard_stop_reason_codes"]
    assert "WRONG_APPRAISAL_TOOL" in packet["hard_stop_reason_codes"]
    assert "INTERNATIONAL_STANDARD_PROFILE_MISSING" in packet["hard_stop_reason_codes"]
    assert "FINAL_GUARDRAIL_RED" in packet["hard_stop_reason_codes"]
    assert "DOCTOR_REVIEW_MISSING" in packet["hard_stop_reason_codes"]
    assert any("Không tự áp dụng" in item for item in packet["non_goals"])


def test_international_standard_profile_maps_core_clinical_ebm_standards() -> None:
    mod = _load_module()
    report = mod.evaluate_all(generated_at=FIXED_NOW)
    profile = report["international_standard_profile"]

    assert report["international_standard_profile_status"] == "MAPPED_WITH_DOCTOR_GATE"
    assert profile["reporting_standards"]["clinical_guideline"] == [
        "RIGHT",
        "source guideline reporting statement when available",
    ]
    assert "CONSORT" in profile["reporting_standards"]["rct"]
    assert "STROBE" in profile["reporting_standards"]["observational"]
    assert "PRISMA 2020" in profile["reporting_standards"]["systematic_review"]
    assert "STARD" in profile["reporting_standards"]["diagnostic_accuracy"]
    assert "TRIPOD" in profile["reporting_standards"]["prediction_model"]
    assert "AGREE II" in profile["appraisal_tools"]["clinical_guideline"]
    assert "AGREE-REX" in profile["appraisal_tools"]["clinical_guideline"]
    assert "AMSTAR 2" in profile["appraisal_tools"]["systematic_review"]
    assert "RoB 2" in profile["appraisal_tools"]["rct"]
    assert "ROBINS-I" in profile["appraisal_tools"]["nonrandomized_intervention"]
    assert "ROBINS-E" in profile["appraisal_tools"]["harm_or_etiology"]
    assert "QUADAS-2" in profile["appraisal_tools"]["diagnostic_accuracy"]
    assert "QUADAS-C" in profile["appraisal_tools"]["diagnostic_accuracy"]
    assert "PROBAST" in profile["appraisal_tools"]["prediction_model"]
    assert any("GRADE Evidence-to-Decision" in item for item in profile["certainty_and_decision"])
    assert any("GRADE-ADOLOPMENT" in item for item in profile["certainty_and_decision"])
    assert any("WHO AWaRe" in item for item in profile["safety_and_adaptation"])
    assert "PMID/DOI/URL for each practice-changing item" in profile[
        "transparency_requirements"
    ]
    assert "WRONG_APPRAISAL_TOOL" in profile["hard_stop_misuse_codes"]
    assert "SELF_ASSIGNED_GRADE" in profile["hard_stop_misuse_codes"]
