from __future__ import annotations

import copy
import json
import subprocess
import sys
import unicodedata
from pathlib import Path

from app.core.clinical_output_validator import validate_clinical_output_packet


def _approved_packet() -> dict:
    return {
        "output_id": "OUT-2026-000101",
        "session_id": "SYNTH-CLINICAL-OUTPUT",
        "timestamp_utc": "2026-07-16T00:00:00Z",
        "release_state": "approved_for_use",
        "recommendation_summary": "Khuyến cáo synthetic đã qua kiểm soát. Cần bác sĩ kiểm chứng trước khi áp dụng.",
        "evidence_basis": [
            {
                "source_id": "10.1056/NEJMoa000000",
                "source_type": "doi",
                "title": "[SYNTHETIC] outpatient evidence source",
                "study_type": "Guideline",
                "grade_level": "mod",
                "decision": "apply",
                "effect_size": "ARR reported in source",
                "retraction_checked": True,
                "source_status": "active",
                "source_integrity_note": "strict source gate PASS",
            }
        ],
        "grade_summary": {
            "certainty": "moderate",
            "direction": "benefit",
            "balance_benefits_harms": "benefit likely outweighs harm",
        },
        "safety_alerts": [],
        "red_flags_detected": [],
        "source_integrity": {
            "all_sources_checked": True,
            "retracted_sources_detected": [],
            "quarantined_source_ids": [],
            "retraction_watch_logged": True,
        },
        "prompt_injection_review": {
            "retrieved_content_treated_as_data": True,
            "injection_detected": False,
            "sanitized_source_ids": [],
            "audit_logged": True,
        },
        "conflict_review": {
            "conflicting_evidence_flag": False,
            "shared_decision_required": False,
            "conflict_sets": [],
        },
        "outpatient_apply_review": {
            "question_frame": "PICO",
            "strict_source_gate_passed": True,
            "evidence_currency_checked": True,
            "absolute_effects_status": "reported",
            "red_flag_screen_done": True,
            "safety_review_done": True,
            "medication_recommendation_present": True,
            "medication_safety_checked": True,
            "organ_function_checked": True,
            "special_population_checked": True,
            "local_feasibility_checked": True,
            "local_applicability_status": "confirmed",
            "shared_decision_ready": True,
            "safety_netting_present": True,
            "follow_up_plan_present": True,
            "doctor_final_approval_required": True,
        },
        "audit_trail": {
            "requesting_agent": "dieu-phoi-lam-sang",
            "guardrail_result": "PASS",
            "human_approval_id": "HA-2026-000101",
        },
    }


def test_approved_packet_is_actionable_allowed():
    result = validate_clinical_output_packet(_approved_packet())

    assert result.actionable_allowed is True
    assert result.blockers == []


def test_review_state_is_not_actionable_even_if_safe_for_review():
    packet = _approved_packet()
    packet["release_state"] = "doctor_review_required"
    packet["audit_trail"].pop("human_approval_id")

    result = validate_clinical_output_packet(packet)

    assert result.actionable_allowed is False
    assert "not_actionable_release_state:doctor_review_required" in result.blockers
    assert "missing_human_approval_id" in result.blockers


def test_strict_source_gate_is_required_for_actionable_release():
    packet = _approved_packet()
    packet["outpatient_apply_review"]["strict_source_gate_passed"] = False

    result = validate_clinical_output_packet(packet)

    assert result.actionable_allowed is False
    assert "apply_gate_false:strict_source_gate_passed" in result.blockers


def test_weak_evidence_cannot_be_marked_apply():
    packet = _approved_packet()
    packet["evidence_basis"][0]["grade_level"] = "low"

    result = validate_clinical_output_packet(packet)

    assert result.actionable_allowed is False
    assert "weak_evidence_marked_apply:1:low" in result.blockers


def test_medication_recommendation_requires_medication_safety_check():
    packet = _approved_packet()
    packet["outpatient_apply_review"]["medication_safety_checked"] = False

    result = validate_clinical_output_packet(packet)

    assert result.actionable_allowed is False
    assert "apply_gate_false:medication_safety_checked" in result.blockers
    assert "medication_without_safety_check" in result.blockers


def test_red_flag_blocks_actionable_release():
    packet = _approved_packet()
    packet["red_flags_detected"] = [{"flag": "khó thở cấp", "urgency": "IMMEDIATE"}]

    result = validate_clinical_output_packet(packet)

    assert result.actionable_allowed is False
    assert "red_flags_detected" in result.blockers


def test_pii_blocks_actionable_release():
    packet = _approved_packet()
    packet["recommendation_summary"] += " SĐT 0912345678."

    result = validate_clinical_output_packet(packet)

    assert result.actionable_allowed is False
    assert "pii_detected" in result.blockers


def test_pii_blocks_actionable_release_even_in_nfd_unicode_form():
    """Hồi quy: nhãn 'số hồ sơ' trong PII_PATTERNS liệt kê ở dạng NFC (tổ hợp sẵn); văn bản
    NFD (chữ nền + dấu rời, vd dán từ macOS) trước bản vá khớp trượt hoàn toàn, cho phép
    một gói có PII lọt qua Clinical V2 Apply Gate mà không bị chặn."""
    packet = _approved_packet()
    marker_nfc = " Ghi chú: số hồ sơ ABC123."
    packet["recommendation_summary"] += unicodedata.normalize("NFD", marker_nfc)

    result = validate_clinical_output_packet(packet)

    assert result.actionable_allowed is False
    assert "pii_detected" in result.blockers


def test_cli_returns_json_and_nonzero_when_blocked(tmp_path: Path):
    packet = copy.deepcopy(_approved_packet())
    packet["outpatient_apply_review"]["local_applicability_status"] = "needs_unit_confirmation"
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, "scripts/verify_clinical_output_gate.py", str(packet_path)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["actionable_allowed"] is False
    assert "local_applicability_not_confirmed:needs_unit_confirmation" in payload["blockers"]
