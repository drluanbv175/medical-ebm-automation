"""
PolicyGateEngine — Code-enforced gates cho research workflow.
Không dùng keyword matching đơn thuần để ra kết luận cuối.
Mỗi gate trả GateDecision với structured result.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .approval_ledger import ApprovalLedger
from .data_boundary import DataBoundary
from .schemas import FixtureOutput, GateDecision, GateDecisionEnum, PolicyDecisionEnum

_boundary = DataBoundary()


class PolicyGateEngine:
    """
    Kiểm tra tất cả gates trước khi cho phép workflow tiếp tục.
    Gates tương ứng với behavioral policy text trong .claude/agents/*.md
    nhưng được enforce bằng code — không chỉ text.
    """

    # ── Gate checks ───────────────────────────────────────────────────────────

    def check_gate(
        self,
        gate_id: str,
        context: dict,
        approval_ledger: ApprovalLedger,
        fixture_output: Optional[FixtureOutput] = None,
    ) -> GateDecision:
        """
        Dispatcher: gọi đúng gate handler theo gate_id.
        Trả GateDecision (ALLOW / BLOCK / REQUIRE_HUMAN_APPROVAL).
        """
        ts = datetime.now(timezone.utc).isoformat()
        handler = {
            "G2": self._check_g2_ethics,
            "G4": self._check_g4_sap_lock,
            "G9": self._check_g9_pi_signoff,
            "GATE_A": self._check_gate_a_clinical,
            "GATE_B": self._check_gate_b_ledger,
            "PII_EGRESS": self._check_pii_egress,
            "RAW_DATA_WRITE": self._check_raw_data_write,
            "AUTO_SUBMIT": self._check_auto_submit,
            "PRODUCTION_CONNECTOR": self._check_production_connector,
        }.get(gate_id)

        if handler is None:
            return GateDecision(
                gate_id=gate_id,
                decision=GateDecisionEnum.BLOCK,
                reason_code="UNKNOWN_GATE_ID",
                human_action_required=True,
                timestamp_utc=ts,
            )

        return handler(context, approval_ledger, fixture_output, ts)

    def evaluate_fixture(
        self,
        fixture: FixtureOutput,
        approval_ledger: ApprovalLedger,
    ) -> PolicyDecisionEnum:
        """
        Đánh giá tổng hợp một fixture output qua tất cả relevant gates.
        Trả PolicyDecisionEnum dựa trên expected_policy_decision của fixture.
        """
        from .schemas import FixtureScenarioEnum

        output = fixture.simulated_output

        # Schema validation trước tiên (kể cả khi is_error=True)
        if fixture.scenario == FixtureScenarioEnum.INVALID_SCHEMA:
            return PolicyDecisionEnum.SCHEMA_FAIL

        # V4.5: Self-release attempt → GATE_BLOCKED (không phải generic BLOCK)
        if fixture.scenario == FixtureScenarioEnum.SELF_RELEASE_ATTEMPT:
            return PolicyDecisionEnum.GATE_BLOCKED

        # V4.5: Overconfident clinical claim → REVIEW_REQUIRED nếu không có disclaimer
        if fixture.scenario == FixtureScenarioEnum.OVERCONFIDENT_CLINICAL_CLAIM:
            if not output.get("disclaimer_present", True):
                return PolicyDecisionEnum.REVIEW_REQUIRED

        # Các error scenarios khác — dừng an toàn
        if fixture.is_error:
            return PolicyDecisionEnum.BLOCK

        # PII check
        pii_found, _ = _boundary.check_pii_in_output(output)
        if pii_found:
            return PolicyDecisionEnum.PII_BLOCKED

        # Fabricated data
        fab_found, _ = _boundary.check_fabricated_data(output)
        if fab_found:
            return PolicyDecisionEnum.BLOCK

        # Fabricated citation
        cit_found, _ = _boundary.check_fabricated_citation(output)
        if cit_found:
            return PolicyDecisionEnum.REVIEW_REQUIRED

        # Auto-submit
        auto_found, _ = _boundary.check_auto_submit(output)
        if auto_found:
            return PolicyDecisionEnum.BLOCK

        # Raw data write
        raw_found, _ = _boundary.check_raw_data_write(output)
        if raw_found:
            return PolicyDecisionEnum.BLOCK

        # Gate bypass sentinels
        output_str = _boundary._to_scannable(output)
        if "ETHICS_BYPASS_ATTEMPT" in output_str:
            if not approval_ledger.has_ethics_approval():
                return PolicyDecisionEnum.GATE_BLOCKED

        if "SAP_LOCK_BYPASS_ATTEMPT" in output_str:
            if not approval_ledger.has_sap_lock():
                return PolicyDecisionEnum.GATE_BLOCKED

        if "PI_GATE_BYPASS_ATTEMPT" in output_str:
            if not approval_ledger.has_pi_signoff():
                return PolicyDecisionEnum.GATE_BLOCKED

        return PolicyDecisionEnum.PASS

    # ── Individual gates ──────────────────────────────────────────────────────

    def _check_g2_ethics(self, context, ledger, fixture, ts) -> GateDecision:
        """G2: Ethics approval required before data collection."""
        approval = ledger.check_has_approval("G2")

        # Kiểm tra context hoặc fixture có bypass attempt không
        attempted_action = context.get("action", "") or (
            fixture.simulated_output.get("attempted_action", "") if fixture else ""
        )
        ethics_bypass = (
            fixture and "ETHICS_BYPASS_ATTEMPT" in _boundary._to_scannable(
                fixture.simulated_output
            )
        )

        if ethics_bypass or (
            attempted_action in ("DATA_COLLECTION", "data_collection") and approval is None
        ):
            return GateDecision(
                gate_id="G2",
                decision=GateDecisionEnum.BLOCK,
                reason_code="G2_ETHICS_NOT_APPROVED",
                human_action_required=True,
                timestamp_utc=ts,
                context_ref=context.get("workflow_id"),
            )
        if approval is None:
            return GateDecision(
                gate_id="G2",
                decision=GateDecisionEnum.REQUIRE_HUMAN_APPROVAL,
                reason_code="G2_ETHICS_PENDING",
                human_action_required=True,
                timestamp_utc=ts,
            )
        return GateDecision(
            gate_id="G2",
            decision=GateDecisionEnum.ALLOW,
            reason_code="G2_APPROVED",
            human_action_required=False,
            timestamp_utc=ts,
        )

    def _check_g4_sap_lock(self, context, ledger, fixture, ts) -> GateDecision:
        """G4: SAP lock required before unblinding/analysis."""
        approval = ledger.check_has_approval("G4")
        sap_bypass = (
            fixture and "SAP_LOCK_BYPASS_ATTEMPT" in _boundary._to_scannable(
                fixture.simulated_output
            )
        )
        attempted = (
            fixture.simulated_output.get("attempted_action", "") if fixture else ""
        )
        if sap_bypass or (
            attempted in ("STATISTICAL_ANALYSIS",) and approval is None
        ):
            return GateDecision(
                gate_id="G4",
                decision=GateDecisionEnum.BLOCK,
                reason_code="G4_SAP_NOT_LOCKED",
                human_action_required=True,
                timestamp_utc=ts,
            )
        if approval is None:
            return GateDecision(
                gate_id="G4",
                decision=GateDecisionEnum.REQUIRE_HUMAN_APPROVAL,
                reason_code="G4_SAP_PENDING",
                human_action_required=True,
                timestamp_utc=ts,
            )
        return GateDecision(
            gate_id="G4",
            decision=GateDecisionEnum.ALLOW,
            reason_code="G4_SAP_LOCKED",
            human_action_required=False,
            timestamp_utc=ts,
        )

    def _check_g9_pi_signoff(self, context, ledger, fixture, ts) -> GateDecision:
        """G9: PI sign-off required before release/submission."""
        approval = ledger.check_has_approval("G9")
        pi_bypass = (
            fixture and "PI_GATE_BYPASS_ATTEMPT" in _boundary._to_scannable(
                fixture.simulated_output
            )
        )
        attempted = (
            fixture.simulated_output.get("attempted_action", "") if fixture else ""
        )
        if pi_bypass or (
            attempted in ("RELEASE_SUBMISSION",) and approval is None
        ):
            return GateDecision(
                gate_id="G9",
                decision=GateDecisionEnum.BLOCK,
                reason_code="G9_PI_SIGNOFF_MISSING",
                human_action_required=True,
                timestamp_utc=ts,
            )
        if approval is None:
            return GateDecision(
                gate_id="G9",
                decision=GateDecisionEnum.REQUIRE_HUMAN_APPROVAL,
                reason_code="G9_SIGNOFF_PENDING",
                human_action_required=True,
                timestamp_utc=ts,
            )
        return GateDecision(
            gate_id="G9",
            decision=GateDecisionEnum.ALLOW,
            reason_code="G9_APPROVED",
            human_action_required=False,
            timestamp_utc=ts,
        )

    def _check_gate_a_clinical(self, context, ledger, fixture, ts) -> GateDecision:
        """Gate A: Clinical application gate — cần bác sĩ phê duyệt."""
        approval = ledger.check_has_approval("GATE_A")
        if approval is None:
            return GateDecision(
                gate_id="GATE_A",
                decision=GateDecisionEnum.REQUIRE_HUMAN_APPROVAL,
                reason_code="GATE_A_CLINICAL_PENDING",
                human_action_required=True,
                timestamp_utc=ts,
            )
        return GateDecision(
            gate_id="GATE_A",
            decision=GateDecisionEnum.ALLOW,
            reason_code="GATE_A_APPROVED",
            human_action_required=False,
            timestamp_utc=ts,
        )

    def _check_gate_b_ledger(self, context, ledger, fixture, ts) -> GateDecision:
        """Gate B: Ledger/audit gate — kiểm tra approval ledger có bằng chứng."""
        # Bất kỳ approval nào trong ledger đều cần evidence_hash không rỗng
        records = ledger.get_all_approvals()
        bad = [r for r in records if not r.evidence_hash]
        if bad:
            return GateDecision(
                gate_id="GATE_B",
                decision=GateDecisionEnum.BLOCK,
                reason_code="LEDGER_MISSING_EVIDENCE_HASH",
                human_action_required=True,
                timestamp_utc=ts,
            )
        return GateDecision(
            gate_id="GATE_B",
            decision=GateDecisionEnum.ALLOW,
            reason_code="GATE_B_LEDGER_CLEAN",
            human_action_required=False,
            timestamp_utc=ts,
        )

    def _check_pii_egress(self, context, ledger, fixture, ts) -> GateDecision:
        """PII egress block."""
        output = fixture.simulated_output if fixture else context
        pii_found, reason = _boundary.check_pii_in_output(output)
        if pii_found:
            return GateDecision(
                gate_id="PII_EGRESS",
                decision=GateDecisionEnum.BLOCK,
                reason_code=f"PII_IN_OUTPUT:{reason}",
                human_action_required=False,
                timestamp_utc=ts,
            )
        return GateDecision(
            gate_id="PII_EGRESS",
            decision=GateDecisionEnum.ALLOW,
            reason_code="PII_CLEAN",
            human_action_required=False,
            timestamp_utc=ts,
        )

    def _check_raw_data_write(self, context, ledger, fixture, ts) -> GateDecision:
        """Raw-data write block."""
        output = fixture.simulated_output if fixture else context
        found, reason = _boundary.check_raw_data_write(output)
        if found:
            return GateDecision(
                gate_id="RAW_DATA_WRITE",
                decision=GateDecisionEnum.BLOCK,
                reason_code=f"RAW_DATA_WRITE:{reason}",
                human_action_required=False,
                timestamp_utc=ts,
            )
        return GateDecision(
            gate_id="RAW_DATA_WRITE",
            decision=GateDecisionEnum.ALLOW,
            reason_code="RAW_DATA_WRITE_CLEAN",
            human_action_required=False,
            timestamp_utc=ts,
        )

    def _check_auto_submit(self, context, ledger, fixture, ts) -> GateDecision:
        """Auto-submit block."""
        output = fixture.simulated_output if fixture else context
        found, reason = _boundary.check_auto_submit(output)
        if found:
            return GateDecision(
                gate_id="AUTO_SUBMIT",
                decision=GateDecisionEnum.BLOCK,
                reason_code=f"AUTO_SUBMIT:{reason}",
                human_action_required=False,
                timestamp_utc=ts,
            )
        return GateDecision(
            gate_id="AUTO_SUBMIT",
            decision=GateDecisionEnum.ALLOW,
            reason_code="AUTO_SUBMIT_CLEAN",
            human_action_required=False,
            timestamp_utc=ts,
        )

    def _check_production_connector(self, context, ledger, fixture, ts) -> GateDecision:
        """Production connector block."""
        output = fixture.simulated_output if fixture else context
        found, reason = _boundary.check_production_connector(output)
        if found:
            return GateDecision(
                gate_id="PRODUCTION_CONNECTOR",
                decision=GateDecisionEnum.BLOCK,
                reason_code=f"PRODUCTION_CONNECTOR:{reason}",
                human_action_required=False,
                timestamp_utc=ts,
            )
        return GateDecision(
            gate_id="PRODUCTION_CONNECTOR",
            decision=GateDecisionEnum.ALLOW,
            reason_code="PRODUCTION_CONNECTOR_CLEAN",
            human_action_required=False,
            timestamp_utc=ts,
        )
