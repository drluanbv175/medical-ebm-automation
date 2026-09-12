from __future__ import annotations

import pytest

from app.chronic_care.constants import RISKY_FLAGS_MUST_STAY_FALSE
from app.chronic_care.rules import CHRONIC_CARE_RULES
from app.chronic_care.service import ChronicCareService
from app.chronic_care.synthetic_cases import SyntheticChronicCareCase, build_synthetic_case_pack, validate_synthetic_case_pack


def test_no_real_pii_accepted_in_synthetic_seed() -> None:
    cases = build_synthetic_case_pack()
    validate_synthetic_case_pack(cases)
    bad = SyntheticChronicCareCase(
        patient_reference_id="SYN-BAD-001",
        age_band="45-64",
        sex="F",
        program_code="HTN_PROGRAM",
        synthetic_status_fields={"note": "phone 0901234567"},
    )
    with pytest.raises(ValueError):
        validate_synthetic_case_pack([bad])


def test_no_patient_facing_message_education_emr_or_medication_change() -> None:
    service = ChronicCareService()
    with pytest.raises(PermissionError):
        service.attempt_patient_facing_output()
    with pytest.raises(PermissionError):
        service.attempt_emr_write()
    with pytest.raises(PermissionError):
        service.attempt_medication_change()


def test_no_production_flag_activation() -> None:
    service = ChronicCareService(feature_flags={flag: True for flag in RISKY_FLAGS_MUST_STAY_FALSE})
    for flag in RISKY_FLAGS_MUST_STAY_FALSE:
        assert service.feature_flags[flag] is False


def test_no_approval_or_clinical_release_bypass_in_normal_shadow_run() -> None:
    # SỬA 2026-09-04 (Workflow đối kháng đa-agent) — cùng lý do đã ghi ở
    # test_phase_3a_chronic_care_functional.py: cờ export mặc định nay ĐÚNG
    # là False (an toàn), nên bật tường minh để giữ nguyên luồng "normal
    # shadow run" mà test này muốn kiểm (không có bypass phê duyệt/clinical
    # release), không lẫn với việc kiểm cổng export.
    service = ChronicCareService(feature_flags={"v7_chatgpt_project_export": True})
    service.seed_synthetic_cases()
    service.export_aggregate_json()
    state = service.dashboard_state()
    assert state.safety_counters["approval_bypass"] == 0
    assert state.safety_counters["clinical_release_flag_bypass"] == 0
    assert state.safety_counters["patient_facing_output_without_approval"] == 0
    assert state.safety_counters["audit_event_missing"] == 0


def test_audit_event_exists_for_state_changing_actions() -> None:
    service = ChronicCareService()
    service.seed_synthetic_cases()
    actions = {event.to_dict()["payload"]["action"] for event in service.audit_trail.events}
    for expected in {"create_enrollment", "create_review", "create_task", "create_risk_draft", "create_care_plan_draft"}:
        assert expected in actions


def test_rules_are_shadow_only_and_not_clinical_decisions() -> None:
    for rule in CHRONIC_CARE_RULES.values():
        assert rule.clinical_decision is False
        assert rule.patient_facing_output is False
        assert rule.emr_write is False
        assert rule.approved_by
