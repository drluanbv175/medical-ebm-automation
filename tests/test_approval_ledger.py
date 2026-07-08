"""
Tests cho ApprovalLedger — Phase 3 Offline Controlled-System.
Không có API call, không PII, hoàn toàn deterministic.
"""

from runtime.approval_ledger import ApprovalLedger
from runtime.schemas import ApprovalDecisionEnum


class TestApprovalLedgerBlock:
    """TC-04: Agent-created approval bị block."""

    def test_agent_created_approval_blocked(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="G2",
            reviewer_role="PI",
            reviewer_ref="REF-PI-001",
            scope="Ethics approval scope",
            evidence_content="Ethics committee letter",
        )
        # Ghi đè flag _created_by_agent
        record._created_by_agent = True
        success, reason = ledger.add_approval(record, created_by_agent=True)
        assert not success
        assert reason == "AGENT_CREATED_APPROVAL_BLOCKED"
        assert ledger.count() == 0

    def test_explicit_created_by_agent_flag_blocked(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="G4",
            reviewer_role="PI",
            reviewer_ref="REF-PI-002",
            scope="SAP lock scope",
            evidence_content="SAP signed document",
        )
        # Không cần ghi đè record — truyền qua param
        success, reason = ledger.add_approval(record, created_by_agent=True)
        assert not success
        assert reason == "AGENT_CREATED_APPROVAL_BLOCKED"

    def test_creator_reviewer_same_agent_blocked(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="GATE_A",
            reviewer_role="GUARDRAIL_REVIEWER",
            reviewer_ref="REVIEWER-AGENT-TRACE",
            scope="Clinical output packet review",
            evidence_content="Draft clinical packet hash source",
            artifact_creator_agent="tham-dinh-dau-ra",
            reviewer_agent="tham-dinh-dau-ra",
        )
        success, reason = ledger.add_approval(record)
        assert not success
        assert reason == "SELF_REVIEW_BLOCKED"
        assert ledger.count() == 0

    def test_creator_reviewer_different_agents_allowed(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="GATE_A",
            reviewer_role="GUARDRAIL_REVIEWER",
            reviewer_ref="REVIEWER-AGENT-TRACE",
            scope="Clinical output packet review",
            evidence_content="Draft clinical packet hash source",
            artifact_creator_agent="dieu-phoi-lam-sang",
            reviewer_agent="tham-dinh-dau-ra",
        )
        success, reason = ledger.add_approval(record)
        assert success
        assert reason == "ADDED"

    def test_self_review_audit_detects_imported_legacy_violation(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="GATE_B",
            reviewer_role="LEGACY_IMPORT_REVIEWER",
            reviewer_ref="LEGACY-TRACE",
            scope="Imported legacy approval trace",
            evidence_content="Legacy approval content",
            artifact_creator_agent="tham-dinh-dau-ra",
            reviewer_agent="tham-dinh-dau-ra",
        )
        ledger._records.append(record)
        assert ledger.has_self_review_violations()
        assert ledger.self_review_violations() == [record]


class TestApprovalLedgerValidApproval:
    """Human approval hợp lệ được add."""

    def test_valid_human_approval_added(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="G2",
            reviewer_role="IRB_CHAIR",
            reviewer_ref="IRB-QY175-2026-01",
            scope="Full ethics approval QY175",
            evidence_content="Letter ref IRB-QY175-2026-01",
        )
        success, reason = ledger.add_approval(record)
        assert success
        assert reason == "ADDED"
        assert ledger.count() == 1

    def test_has_ethics_approval_after_add(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="G2",
            reviewer_role="IRB_CHAIR",
            reviewer_ref="IRB-001",
            scope="Ethics",
            evidence_content="Ethics doc",
        )
        ledger.add_approval(record)
        assert ledger.has_ethics_approval()

    def test_no_ethics_approval_initially(self):
        ledger = ApprovalLedger()
        assert not ledger.has_ethics_approval()

    def test_no_sap_lock_initially(self):
        ledger = ApprovalLedger()
        assert not ledger.has_sap_lock()

    def test_no_pi_signoff_initially(self):
        ledger = ApprovalLedger()
        assert not ledger.has_pi_signoff()


class TestApprovalLedgerDuplicate:
    """Duplicate approval_id bị block."""

    def test_duplicate_approval_id_blocked(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="G2",
            reviewer_role="IRB",
            reviewer_ref="IRB-DUP-TEST",
            scope="Test",
            evidence_content="Content for duplicate test",
        )
        ledger.add_approval(record)
        success2, reason2 = ledger.add_approval(record)
        assert not success2
        assert "DUPLICATE_APPROVAL_ID" in reason2


class TestApprovalLedgerMissingEvidence:
    """Missing evidence_hash bị block."""

    def test_missing_evidence_hash_blocked(self):
        from runtime.schemas import ApprovalRecord
        record = ApprovalRecord(
            approval_id="test-id-001",
            gate_id="G2",
            reviewer_role="IRB",
            reviewer_identity_reference="IRB-TEST",
            decision=ApprovalDecisionEnum.APPROVED,
            scope="Test",
            evidence_hash="",  # rỗng
            timestamp_utc="2026-06-21T00:00:00+00:00",
            supersedes=None,
            _created_by_agent=False,
        )
        ledger = ApprovalLedger()
        success, reason = ledger.add_approval(record)
        assert not success
        assert reason == "MISSING_EVIDENCE_HASH"


class TestApprovalLedgerExport:
    """Export JSON không có PII."""

    def test_export_json_no_pii(self):
        ledger = ApprovalLedger()
        record = ApprovalLedger.make_human_approval(
            gate_id="G9",
            reviewer_role="PI",
            reviewer_ref="PI-SIGN-001",
            scope="Final PI sign-off",
            evidence_content="PI declaration document",
        )
        ledger.add_approval(record)
        json_str = ledger.export_json()
        # Không có _created_by_agent trong export
        assert "_created_by_agent" not in json_str
        assert "G9" in json_str

    def test_evidence_hash_verify(self):
        ledger = ApprovalLedger()
        content = "Ethics committee letter for QY175 study, ref IRB-001"
        record = ApprovalLedger.make_human_approval(
            gate_id="G2",
            reviewer_role="IRB",
            reviewer_ref="IRB-VERIFY-TEST",
            scope="Verify test",
            evidence_content=content,
        )
        ledger.add_approval(record)
        assert ledger.verify_evidence_hash(record, content)
        assert not ledger.verify_evidence_hash(record, "tampered content")
