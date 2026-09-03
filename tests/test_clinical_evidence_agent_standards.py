from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

import pytest  # noqa: E402 — guard đặt sau REPO để dùng Path đã có

# CI HERMETIC ĐƠN-REPO (16/08/2026): bộ kiểm này chấm chuẩn trên TOÀN WORKSPACE
# (.claude/agents + tools/ ở thư mục MẸ) — checkout một-repo không có chúng nên
# tool fail-closed ĐÚNG THIẾT KẾ và test đỏ oan. Skip CÓ KHAI BÁO, không giả đạt:
# phán quyết chuẩn-agent chỉ có nghĩa khi đứng trong workspace thật (máy bác sĩ).
_WORKSPACE_ME = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(
    not (_WORKSPACE_ME / ".claude" / "agents").is_dir(),
    reason="cần workspace gốc (.claude/agents ở thư mục mẹ) — CI checkout đơn-repo không chấm được chuẩn agent",
)

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

    assert set(rows) == {
        "EAS1",
        "EAS2",
        "EAS3",
        "EAS4",
        "EAS5",
        "EAS6",
        "EAS7",
        "EAS8",
        "EAS9",
        "EAS10",
        "EAS11",
        "EAS12",
    }
    assert rows["EAS1"]["status"] == "PASS"
    assert rows["EAS2"]["status"] == "PASS"
    assert rows["EAS3"]["status"] == "PASS"
    assert rows["EAS4"]["status"] == "PASS"
    assert rows["EAS5"]["status"] == "PASS"
    assert rows["EAS6"]["status"] == "HUMAN_GATE"
    assert rows["EAS7"]["status"] == "PASS"
    assert rows["EAS8"]["status"] == "PASS"
    assert rows["EAS9"]["status"] == "PASS"
    assert rows["EAS10"]["status"] == "PASS"
    assert rows["EAS11"]["status"] == "PASS"
    assert rows["EAS12"]["status"] == "PASS"
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
    assert "Source Authority Registry" in markdown
    assert "Source authority registry: `AUTHORITY_TIERED_WITH_CROSSCHECK`" in markdown
    assert "Evidence Currency Policy" in markdown
    assert "Evidence currency policy: `CURRENCY_CONTROLLED_WITH_RETRACTION_CHECK`" in markdown
    assert "Question Frame Policy" in markdown
    assert "Question frame policy: `FRAME_TOOL_LOCKED_BY_QUESTION_TYPE`" in markdown
    assert "Conflicting Evidence Policy" in markdown
    assert (
        "Conflicting evidence policy: `CONFLICTS_MUST_BE_MAPPED_BEFORE_PRACTICE_CHANGE`"
        in markdown
    )
    assert "Operational Completeness Policy" in markdown
    assert (
        "Operational completeness policy: "
        "`TECHNICAL_COMPLETENESS_WITH_DOCTOR_GATE_NOT_CLINICAL_PRODUCTION`"
        in markdown
    )
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
    assert "appraisal_tool_selection_audit" in packet["minimum_artifacts"]
    assert "clinical_use_boundary_attestation" in packet["minimum_artifacts"]
    assert "conflicting_evidence_matrix" in packet["minimum_artifacts"]
    assert "conflicting_evidence_resolution_note" in packet["minimum_artifacts"]
    assert "evidence_currency_audit" in packet["minimum_artifacts"]
    assert "effect_measure_traceability_log" in packet["minimum_artifacts"]
    assert "final_guardrail_result" in packet["minimum_artifacts"]
    assert "verify_dashboard.py <dashboard>.html --online --strict-sources" in packet[
        "required_commands"
    ]
    assert "international_standard_profile" in packet["minimum_artifacts"]
    assert "operational_completeness_manifest" in packet["minimum_artifacts"]
    assert "question_frame_selection_audit" in packet["minimum_artifacts"]
    assert "source_authority_registry" in packet["minimum_artifacts"]
    assert "source_authority_tiering_rationale" in packet["minimum_artifacts"]
    assert "search_date_log" in packet["minimum_artifacts"]
    assert "standard_selection_rationale" in packet["minimum_artifacts"]
    assert "retraction_withdrawal_check" in packet["minimum_artifacts"]
    assert "superseded_guideline_check" in packet["minimum_artifacts"]
    assert "PII_DETECTED" in packet["hard_stop_reason_codes"]
    assert "SOURCE_UNVERIFIED" in packet["hard_stop_reason_codes"]
    assert "SOURCE_NOT_AUTHORITY_TIERED" in packet["hard_stop_reason_codes"]
    assert "DISCOVERY_SOURCE_USED_AS_RECORD" in packet["hard_stop_reason_codes"]
    assert "QUESTION_FRAME_MISSING" in packet["hard_stop_reason_codes"]
    assert "FRAME_TOOL_MISMATCH" in packet["hard_stop_reason_codes"]
    assert "PICO_FOR_NON_INTERVENTION_WITHOUT_RATIONALE" in packet["hard_stop_reason_codes"]
    assert "CONFLICTING_EVIDENCE_NOT_REPORTED" in packet["hard_stop_reason_codes"]
    assert "CHERRY_PICKED_GUIDELINE_OR_TRIAL" in packet["hard_stop_reason_codes"]
    assert "SOURCE_HIERARCHY_OVERRIDE_WITHOUT_RATIONALE" in packet["hard_stop_reason_codes"]
    assert (
        "SINGLE_SOURCE_PRACTICE_CHANGE_WITH_CONFLICT_UNCHECKED"
        in packet["hard_stop_reason_codes"]
    )
    assert "SEARCH_DATE_MISSING" in packet["hard_stop_reason_codes"]
    assert "CLAIMED_LATEST_WITHOUT_FRESH_SEARCH" in packet["hard_stop_reason_codes"]
    assert "WRONG_APPRAISAL_TOOL" in packet["hard_stop_reason_codes"]
    assert "INTERNATIONAL_STANDARD_PROFILE_MISSING" in packet["hard_stop_reason_codes"]
    assert "IDENTIFIER_CROSSCHECK_MISSING" in packet["hard_stop_reason_codes"]
    assert "EFFECT_MEASURE_NOT_SOURCE_TRACEABLE" in packet["hard_stop_reason_codes"]
    assert "RETRACTION_STATUS_UNKNOWN" in packet["hard_stop_reason_codes"]
    assert "SOURCE_RETRACTED_OR_WITHDRAWN" in packet["hard_stop_reason_codes"]
    assert "SUPERSEDED_GUIDELINE_USED_AS_CURRENT" in packet["hard_stop_reason_codes"]
    assert "COMPLETION_MANIFEST_MISSING" in packet["hard_stop_reason_codes"]
    assert "DOCTOR_GATE_BYPASSED" in packet["hard_stop_reason_codes"]
    assert "REAL_PATIENT_DATA_WORKFLOW_ENABLED" in packet["hard_stop_reason_codes"]
    assert "AUTO_APPLY_ENABLED" in packet["hard_stop_reason_codes"]
    assert "CLINICAL_PRODUCTION_CLAIMED_WITH_BLOCKERS" in packet["hard_stop_reason_codes"]
    assert "SECURITY_UAT_APPROVAL_MISSING" in packet["hard_stop_reason_codes"]
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
    assert "QUADAS-3" in profile["appraisal_tools"]["diagnostic_accuracy"]
    assert any("QUADAS-C" in item for item in profile["appraisal_tools"]["diagnostic_accuracy"])
    assert "PROBAST" in profile["appraisal_tools"]["prediction_model"]
    assert any("GRADE Evidence-to-Decision" in item for item in profile["certainty_and_decision"])
    assert any("GRADE-ADOLOPMENT" in item for item in profile["certainty_and_decision"])
    assert any("WHO AWaRe" in item for item in profile["safety_and_adaptation"])
    assert "PMID/DOI/URL for each practice-changing item" in profile[
        "transparency_requirements"
    ]
    assert "WRONG_APPRAISAL_TOOL" in profile["hard_stop_misuse_codes"]
    assert "SELF_ASSIGNED_GRADE" in profile["hard_stop_misuse_codes"]


def test_source_authority_registry_tiers_clinical_sources_and_blocks_misuse() -> None:
    mod = _load_module()
    report = mod.evaluate_all(generated_at=FIXED_NOW)
    registry = report["source_authority_registry"]

    assert report["source_authority_registry_status"] == "AUTHORITY_TIERED_WITH_CROSSCHECK"
    tier0 = registry["source_of_record_tiers"]["tier_0_guideline_hta_regulatory"]
    for source in [
        "Cochrane",
        "NICE",
        "USPSTF",
        "WHO",
        "CDC",
        "ESC",
        "ACC",
        "AHA",
        "ADA",
        "KDIGO",
        "GOLD",
        "GINA",
        "IDSA",
        "ESCMID",
        "ASCO",
        "ESMO",
        "NCCN",
        "kcb.vn/phac-do",
    ]:
        assert source in tier0
    safety = registry["safety_sources"]
    for source in ["openFDA", "DailyMed", "EMA/PRAC", "MHRA Drug Safety Update", "WHO AWaRe"]:
        assert source in safety
    assert "PubMed/MEDLINE" in registry["identifier_crosscheck_sources"]
    assert "Europe PMC" in registry["identifier_crosscheck_sources"]
    assert "Crossref" in registry["identifier_crosscheck_sources"]
    assert "Consensus" in registry["discovery_only_sources"]
    assert "bioRxiv/medRxiv preprint" in registry["discovery_only_sources"]
    assert any("ChEMBL" in item for item in registry["not_for_clinical_recommendation"])
    assert any("preprint alone" in item for item in registry["not_for_clinical_recommendation"])
    assert "DISCOVERY_SOURCE_USED_AS_RECORD" in registry["hard_stop_codes"]
    assert "PREPRINT_USED_TO_CHANGE_PRACTICE" in registry["hard_stop_codes"]
    assert "TRIAL_REGISTRY_USED_AS_EFFICACY_RESULT" in registry["hard_stop_codes"]
    assert "CHEMBL_USED_FOR_CLINICAL_RECOMMENDATION" in registry["hard_stop_codes"]
    assert "IDENTIFIER_CROSSCHECK_MISSING" in registry["hard_stop_codes"]


def test_evidence_currency_policy_requires_fresh_search_and_retraction_checks() -> None:
    mod = _load_module()
    report = mod.evaluate_all(generated_at=FIXED_NOW)
    policy = report["evidence_currency_policy"]

    assert report["evidence_currency_policy_status"] == "CURRENCY_CONTROLLED_WITH_RETRACTION_CHECK"
    windows = policy["recency_windows_days"]
    assert windows["drug_safety_or_regulatory_alert"] <= 7
    assert windows["living_guideline_or_rapid_update"] <= 14
    assert windows["clinical_guideline_or_society_statement"] <= 90
    assert windows["systematic_review_or_meta_analysis"] <= 180
    assert windows["practice_changing_trial_or_observational_study"] <= 365
    checks = " ".join(policy["mandatory_checks"])
    assert "search date" in checks
    assert "verify_dashboard.py --online --strict-sources" in checks
    assert "retraction" in checks
    assert "superseded" in checks
    assert "Do not say latest/current/up-to-date" in checks
    assert policy["freshness_labels"]["blocked"].startswith("Retracted")
    assert "SEARCH_DATE_MISSING" in policy["hard_stop_codes"]
    assert "CLAIMED_LATEST_WITHOUT_FRESH_SEARCH" in policy["hard_stop_codes"]
    assert "RETRACTION_STATUS_UNKNOWN" in policy["hard_stop_codes"]
    assert "SOURCE_RETRACTED_OR_WITHDRAWN" in policy["hard_stop_codes"]
    assert "SUPERSEDED_GUIDELINE_USED_AS_CURRENT" in policy["hard_stop_codes"]
    assert "SAFETY_ALERT_WINDOW_STALE" in policy["hard_stop_codes"]


def test_question_frame_policy_locks_frame_tool_and_effect_measure_choice() -> None:
    mod = _load_module()
    report = mod.evaluate_all(generated_at=FIXED_NOW)
    policy = report["question_frame_policy"]

    assert report["question_frame_policy_status"] == "FRAME_TOOL_LOCKED_BY_QUESTION_TYPE"
    frame_map = policy["frame_map"]
    assert frame_map["intervention"]["frame"] == "PICO(T)(S)"
    assert "RoB 2" in frame_map["intervention"]["appraisal_tools"]
    assert "AMSTAR 2" in frame_map["intervention"]["appraisal_tools"]
    assert frame_map["harm_or_etiology"]["frame"] == "PECO"
    assert "ROBINS-E" in frame_map["harm_or_etiology"]["appraisal_tools"]
    assert frame_map["diagnostic_accuracy"]["frame"] == "PIRT"
    assert "QUADAS-3" in frame_map["diagnostic_accuracy"]["appraisal_tools"]
    assert "STARD" in frame_map["diagnostic_accuracy"]["reporting"]
    assert frame_map["prognosis"]["frame"] == "PROGRESS/PICOTS"
    assert "PROBAST" in frame_map["prognosis"]["appraisal_tools"]
    assert frame_map["prevalence"]["frame"] == "CoCoPop"
    assert "JBI prevalence checklist" in frame_map["prevalence"]["appraisal_tools"]
    assert frame_map["qualitative"]["frame"] == "SPIDER"
    assert "COREQ" in frame_map["qualitative"]["reporting"]
    assert frame_map["service_policy"]["frame"] == "ECLIPSE"
    assert frame_map["economic"]["frame"] == "PICO + cost/QALY"
    assert "CHEERS" in frame_map["economic"]["reporting"]

    checks = " ".join(policy["mandatory_checks"])
    assert "Đã dùng khung [X] vì câu hỏi thuộc loại [Y]" in checks
    assert "frame/frameLabels" in checks
    assert "do not invent or silently calculate NNT/NNH" in checks
    assert "QUESTION_FRAME_MISSING" in policy["hard_stop_codes"]
    assert "FRAME_TOOL_MISMATCH" in policy["hard_stop_codes"]
    assert "DIAGNOSTIC_ACCURACY_WITHOUT_PIRT_OR_QUADAS" in policy["hard_stop_codes"]
    assert "PREDICTION_MODEL_WITHOUT_PROBAST_OR_TRIPOD" in policy["hard_stop_codes"]
    assert "EFFECT_MEASURE_NOT_SOURCE_TRACEABLE" in policy["hard_stop_codes"]
    assert "FRAME_LABELS_MISSING_IN_DASHBOARD" in policy["hard_stop_codes"]


def test_conflicting_evidence_policy_requires_matrix_and_blocks_cherry_picking() -> None:
    mod = _load_module()
    report = mod.evaluate_all(generated_at=FIXED_NOW)
    policy = report["conflicting_evidence_policy"]

    assert (
        report["conflicting_evidence_policy_status"]
        == "CONFLICTS_MUST_BE_MAPPED_BEFORE_PRACTICE_CHANGE"
    )
    for conflict_type in [
        "guideline_vs_guideline",
        "guideline_vs_new_trial",
        "meta_analysis_vs_large_trial",
        "benefit_vs_harm",
        "international_vs_vietnam",
        "population_mismatch",
    ]:
        assert conflict_type in policy["conflict_types"]
    for column in [
        "source_tier",
        "effect_estimate_from_source",
        "source_grading_or_certainty",
        "direction_of_effect",
        "applicability_to_outpatient_vietnam",
        "resolution_rationale",
    ]:
        assert column in policy["evidence_matrix_columns"]
    checks = " ".join(policy["mandatory_checks"])
    assert "conflicting_evidence_matrix" in checks
    assert "do not cherry-pick" in checks
    assert "Chưa đủ để thay đổi thực hành" in checks
    assert policy["decision_labels"]["unresolved_notyet"].startswith("Chưa đủ")
    assert "CONFLICTING_EVIDENCE_NOT_REPORTED" in policy["hard_stop_codes"]
    assert "CHERRY_PICKED_GUIDELINE_OR_TRIAL" in policy["hard_stop_codes"]
    assert "SOURCE_HIERARCHY_OVERRIDE_WITHOUT_RATIONALE" in policy["hard_stop_codes"]
    assert "BENEFIT_HARM_CONFLICT_NOT_EXPLAINED" in policy["hard_stop_codes"]
    assert "LOCAL_GUIDELINE_CONFLICT_NOT_LABELED" in policy["hard_stop_codes"]
    assert "UNRESOLVED_CONFLICT_MARKED_APPLY_NOW" in policy["hard_stop_codes"]


def test_operational_completeness_policy_closes_technical_scope_without_production_claim() -> None:
    mod = _load_module()
    report = mod.evaluate_all(generated_at=FIXED_NOW)
    policy = report["operational_completeness_policy"]

    assert (
        report["operational_completeness_policy_status"]
        == "TECHNICAL_COMPLETENESS_WITH_DOCTOR_GATE_NOT_CLINICAL_PRODUCTION"
    )
    required = policy["required_policy_modules"]
    assert "agent_gate_contract CEG1-CEG7" in required
    assert "release_packet_contract" in required
    assert "source_authority_registry" in required
    assert "evidence_currency_policy" in required
    assert "question_frame_policy" in required
    assert "conflicting_evidence_policy" in required
    assert "final_guardrail R1-R7 + Q1-Q7" in required

    evidence = " ".join(policy["completeness_evidence"])
    assert "upgrade_verify.py requires 28/28 PASS before technical release" in evidence
    assert "check_claude_codex_sync_health.py PASS" in evidence
    assert "verify_clinical_production_control_plane.py keeps production blocked" in evidence
    assert "doctor_review_packet present before clinical use" in evidence

    blocked = " ".join(policy["blocked_capabilities"])
    assert "Real patient data ingestion" in blocked
    assert "Autonomous diagnosis or prescription" in blocked
    assert "Auto-apply to patient care" in blocked
    assert "Bypass CEG7 doctor review" in blocked
    assert "Claim clinical production readiness while blockers remain" in blocked
    assert "COMPLETION_MANIFEST_MISSING" in policy["hard_stop_codes"]
    assert "REAL_PATIENT_DATA_WORKFLOW_ENABLED" in policy["hard_stop_codes"]
    assert "AUTO_APPLY_ENABLED" in policy["hard_stop_codes"]
    assert "CLINICAL_PRODUCTION_CLAIMED_WITH_BLOCKERS" in policy["hard_stop_codes"]
    assert "SECURITY_UAT_APPROVAL_MISSING" in policy["hard_stop_codes"]
