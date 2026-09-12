"""Kiểm hành vi ICH E6(R3) Annex 2 tại G1/G2."""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import annex2_quality_gate as A2X  # noqa: E402


def _complete(methods=("decentralised", "pragmatic", "rwd")):
    return {"gate_params": {"G1": {"annex2": {
        "applicable": True, "methodologies": list(methods),
        "fit_for_purpose_justification": "Đủ",
        "participant_burden_and_access": "Đủ",
        "roles_and_oversight": "Đủ",
        "safety_information_flow": "Đủ",
        "remote_data_collection_plan": "Đủ",
        "usual_care_activities": "Đủ",
        "data_variability_and_sap": "Đủ",
        "data_provenance_and_quality": "Đủ",
        "irb_information_plan": "Đủ",
        "privacy_confidentiality_security": "Đủ",
        "remote_consent_and_identity": "Đủ",
        "alternative_access_path": "Đủ",
        "dht_validation_and_support": "Đủ",
        "training_and_record_sharing": "Đủ",
        "access_and_permissions": "Đủ",
        "data_governance": "Đủ",
    }}}}


def test_non_annex2_studies_are_unchanged():
    assert A2X.evaluate({}, "cohort", "G1")["status"] == "NOT_APPLICABLE"
    assert A2X.evaluate({}, "rct", "G2")["status"] == "NOT_APPLICABLE"


def test_annex2_missing_controls_blocks_both_gates():
    meta = {"gate_params": {"G1": {"annex2": {
        "applicable": True, "methodologies": ["decentralised", "rwd"],
    }}}}
    assert A2X.evaluate(meta, "rct", "G1")["status"] == "BLOCK"
    assert A2X.evaluate(meta, "rct", "G2")["status"] == "BLOCK"


def test_annex2_complete_controls_pass_both_gates():
    assert A2X.evaluate(_complete(), "rct", "G1")["status"] == "PASS"
    assert A2X.evaluate(_complete(), "rct", "G2")["status"] == "PASS"


def test_placeholder_is_not_treated_as_real_control():
    meta = _complete(("decentralised",))
    meta["gate_params"]["G1"]["annex2"]["remote_consent_and_identity"] = "[CẦN BỔ SUNG]"
    report = A2X.evaluate(meta, "rct", "G2")
    assert report["status"] == "BLOCK"
    assert any("remote_consent_and_identity" in item for item in report["missing"])


def test_annex2_cannot_be_attached_to_non_rct_design():
    report = A2X.evaluate(_complete(("rwd",)), "cohort", "G1")
    assert report["status"] == "BLOCK"
