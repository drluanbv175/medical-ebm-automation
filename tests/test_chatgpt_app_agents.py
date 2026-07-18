"""Test cầu nối agent EBM cho ChatGPT App."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.chatgpt_app.agents import SYNC_CONFIRMATION, SafeAgentCatalog

ROOT = Path(__file__).resolve().parents[1]


def test_catalog_exposes_orchestrators_and_guardrail() -> None:
    catalog = SafeAgentCatalog(ROOT)
    ids = {row["id"] for row in catalog.list_payload()["agents"]}
    assert "dieu-phoi-lam-sang" in ids
    assert "dieu-phoi-nghien-cuu" in ids
    assert "tham-dinh-dau-ra" in ids
    assert len(ids) >= 50


def test_agent_payload_is_proposal_only() -> None:
    payload = SafeAgentCatalog(ROOT).get_payload("ke-don-an-toan")
    contract = payload["execution_contract"]
    assert contract["mode"] == "proposal_only"
    assert contract["must_call_guardrail_last"] is True
    assert contract["automatic_gate_approval"] is False


def test_clinical_workflow_blocks_pii() -> None:
    payload = SafeAgentCatalog(ROOT).workflow_payload(
        "clinical", "Bệnh nhân Nguyễn Văn An, CCCD 012345678901, đau ngực"
    )
    assert payload["status"] == "blocked"
    assert payload["reason"] == "possible_pii_detected"


def test_clinical_workflow_includes_gate_a_b_and_guardrail() -> None:
    payload = SafeAgentCatalog(ROOT).workflow_payload(
        "clinical", "Nam 68 tuổi, đau ngực khi gắng sức, không có thông tin định danh"
    )
    assert payload["status"] == "ready_to_orchestrate"
    assert payload["entry_agent"] == "dieu-phoi-lam-sang"
    assert "GATE_A_PHYSICIAN_APPLICATION" in payload["hard_gates"]
    assert "tham-dinh-dau-ra" in payload["final_guardrail_instructions"]


def test_research_workflow_includes_hard_gates() -> None:
    payload = SafeAgentCatalog(ROOT).workflow_payload(
        "research", "Đề tài hiệu quả can thiệp tuân thủ ở người bệnh tăng huyết áp"
    )
    assert payload["status"] == "ready_to_orchestrate"
    assert payload["entry_agent"] == "dieu-phoi-nghien-cuu"
    assert {"G2_IRB", "G4_SAP_LOCK", "G8_INDEPENDENT_REVIEW", "G9_PI_INTEGRITY"} <= set(payload["hard_gates"])


def test_agent_path_traversal_is_blocked() -> None:
    with pytest.raises(KeyError):
        SafeAgentCatalog(ROOT).get_payload("../secrets")


def test_sync_requires_exact_confirmation() -> None:
    payload = SafeAgentCatalog(ROOT).synchronize("yes")
    assert payload["status"] == "confirmation_required"
    assert payload["required_confirmation"] == SYNC_CONFIRMATION
