"""
Tests cho PolicyGateEngine — Phase 3 Offline Controlled-System.
Không có API call, không PII, hoàn toàn deterministic.
"""

from runtime.approval_ledger import ApprovalLedger
from runtime.mock_agent_runtime import FIXTURE_CATALOG
from runtime.policy_gate_engine import PolicyGateEngine
from runtime.schemas import GateDecisionEnum, PolicyDecisionEnum


def _engine() -> PolicyGateEngine:
    return PolicyGateEngine()


def _empty_ledger() -> ApprovalLedger:
    return ApprovalLedger()


def _ledger_with(gate_id: str) -> ApprovalLedger:
    ledger = ApprovalLedger()
    role_by_gate = {
        "G2": "IRB_ETHICS_COMMITTEE",
        "G4": "METHODS_STATISTICS_REVIEWER",
        "G9": "PI_PROJECT_OWNER",
    }
    record = ApprovalLedger.make_human_approval(
        gate_id=gate_id,
        reviewer_role=role_by_gate.get(gate_id, "TEST_REVIEWER"),
        reviewer_ref=f"REF-{gate_id}-TEST",
        scope=f"Test scope for {gate_id}",
        evidence_content=f"Evidence content for {gate_id}",
    )
    ledger.add_approval(record)
    return ledger


class TestG2EthicsGate:
    """TC-05: G2 ethics gate."""

    def test_g2_blocks_when_no_ethics_approval(self):
        engine = _engine()
        fixture = FIXTURE_CATALOG["FX-005"]  # ETHICS_BYPASS_ATTEMPT
        decision = engine.check_gate("G2", {}, _empty_ledger(), fixture)
        assert decision.decision == GateDecisionEnum.BLOCK
        assert "G2" in decision.reason_code

    def test_g2_allows_when_ethics_approved(self):
        engine = _engine()
        ledger = _ledger_with("G2")
        decision = engine.check_gate("G2", {}, ledger, None)
        assert decision.decision == GateDecisionEnum.ALLOW

    def test_g2_rejects_wrong_stakeholder_role(self):
        engine = _engine()
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="G2",
            reviewer_role="PI_PROJECT_OWNER",
            reviewer_ref="REF-G2-WRONG-ROLE",
            scope="Wrong role fixture",
            evidence_content="Ethics content",
        )
        ledger.add_approval(record)
        decision = engine.check_gate("G2", {}, ledger, None)
        assert decision.decision == GateDecisionEnum.REQUIRE_HUMAN_APPROVAL
        assert "IRB" in decision.reason_code

    def test_g2_requires_human_when_pending(self):
        engine = _engine()
        decision = engine.check_gate("G2", {}, _empty_ledger(), None)
        assert decision.decision == GateDecisionEnum.REQUIRE_HUMAN_APPROVAL
        assert decision.human_action_required


class TestG4SapGate:
    """TC-06: G4 SAP lock gate."""

    def test_g4_blocks_sap_bypass(self):
        engine = _engine()
        fixture = FIXTURE_CATALOG["FX-006"]  # SAP_LOCK_BYPASS_ATTEMPT
        decision = engine.check_gate("G4", {}, _empty_ledger(), fixture)
        assert decision.decision == GateDecisionEnum.BLOCK
        assert "G4" in decision.reason_code

    def test_g4_allows_with_sap_locked(self):
        engine = _engine()
        ledger = _ledger_with("G4")
        decision = engine.check_gate("G4", {}, ledger, None)
        assert decision.decision == GateDecisionEnum.ALLOW

    def test_g4_rejects_pi_only_when_statistician_missing(self):
        engine = _engine()
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="G4",
            reviewer_role="PI",
            reviewer_ref="REF-G4-PI-ONLY",
            scope="PI-only SAP fixture",
            evidence_content="SAP content",
        )
        ledger.add_approval(record)
        decision = engine.check_gate("G4", {}, ledger, None)
        assert decision.decision == GateDecisionEnum.REQUIRE_HUMAN_APPROVAL
        assert "STATISTICIAN" in decision.reason_code


class TestG9PIGate:
    """TC-07: G9 PI sign-off gate."""

    def test_g9_blocks_auto_release(self):
        engine = _engine()
        fixture = FIXTURE_CATALOG["FX-007"]  # PI_GATE_BYPASS_ATTEMPT
        decision = engine.check_gate("G9", {}, _empty_ledger(), fixture)
        assert decision.decision == GateDecisionEnum.BLOCK
        assert "G9" in decision.reason_code

    def test_g9_allows_with_pi_signoff(self):
        engine = _engine()
        ledger = _ledger_with("G9")
        decision = engine.check_gate("G9", {}, ledger, None)
        assert decision.decision == GateDecisionEnum.ALLOW


class TestPiiEgressGate:
    """TC-08: PII egress gate."""

    def test_pii_egress_blocks_fx004(self):
        engine = _engine()
        fixture = FIXTURE_CATALOG["FX-004"]  # PII_LEAK
        decision = engine.check_gate("PII_EGRESS", {}, _empty_ledger(), fixture)
        assert decision.decision == GateDecisionEnum.BLOCK
        assert not decision.human_action_required

    def test_pii_egress_allows_clean_output(self):
        engine = _engine()
        fixture = FIXTURE_CATALOG["FX-001"]  # VALID_RESPONSE
        decision = engine.check_gate("PII_EGRESS", {}, _empty_ledger(), fixture)
        assert decision.decision == GateDecisionEnum.ALLOW


class TestAutoSubmitGate:
    """Auto-submit bị block."""

    def test_auto_submit_blocked(self):
        engine = _engine()
        fixture = FIXTURE_CATALOG["FX-008"]  # AUTO_SUBMIT_ATTEMPT
        decision = engine.check_gate("AUTO_SUBMIT", {}, _empty_ledger(), fixture)
        assert decision.decision == GateDecisionEnum.BLOCK

    def test_auto_submit_clean_passes(self):
        engine = _engine()
        fixture = FIXTURE_CATALOG["FX-001"]
        decision = engine.check_gate("AUTO_SUBMIT", {}, _empty_ledger(), fixture)
        assert decision.decision == GateDecisionEnum.ALLOW


class TestRawDataWriteGate:
    """Raw data write bị block."""

    def test_raw_data_write_blocked(self):
        engine = _engine()
        fixture = FIXTURE_CATALOG["FX-009"]  # RAW_DATA_WRITE_ATTEMPT
        decision = engine.check_gate("RAW_DATA_WRITE", {}, _empty_ledger(), fixture)
        assert decision.decision == GateDecisionEnum.BLOCK


class TestEvaluateFixture:
    """evaluate_fixture tổng hợp toàn bộ gates."""

    def test_fx001_valid_response_passes(self):
        engine = _engine()
        result = engine.evaluate_fixture(FIXTURE_CATALOG["FX-001"], _empty_ledger())
        assert result == PolicyDecisionEnum.PASS

    def test_fx002_fabricated_data_blocked(self):
        engine = _engine()
        result = engine.evaluate_fixture(FIXTURE_CATALOG["FX-002"], _empty_ledger())
        assert result == PolicyDecisionEnum.BLOCK

    def test_fx003_fabricated_citation_review_required(self):
        engine = _engine()
        result = engine.evaluate_fixture(FIXTURE_CATALOG["FX-003"], _empty_ledger())
        assert result == PolicyDecisionEnum.REVIEW_REQUIRED

    def test_fx004_pii_leak_blocked(self):
        engine = _engine()
        result = engine.evaluate_fixture(FIXTURE_CATALOG["FX-004"], _empty_ledger())
        assert result == PolicyDecisionEnum.PII_BLOCKED

    def test_fx010_invalid_schema_fails(self):
        engine = _engine()
        result = engine.evaluate_fixture(FIXTURE_CATALOG["FX-010"], _empty_ledger())
        assert result == PolicyDecisionEnum.SCHEMA_FAIL

    def test_fx011_timeout_blocked(self):
        engine = _engine()
        result = engine.evaluate_fixture(FIXTURE_CATALOG["FX-011"], _empty_ledger())
        assert result == PolicyDecisionEnum.BLOCK

    def test_unknown_gate_blocked(self):
        engine = _engine()
        decision = engine.check_gate("UNKNOWN_GATE", {}, _empty_ledger(), None)
        assert decision.decision == GateDecisionEnum.BLOCK
        assert decision.reason_code == "UNKNOWN_GATE_ID"

    def test_gate_b_ledger_clean(self):
        engine = _engine()
        ledger = _ledger_with("G2")
        decision = engine.check_gate("GATE_B", {}, ledger, None)
        assert decision.decision == GateDecisionEnum.ALLOW
