"""
tests/test_r1_1_offline_rbac_synthetic_identity.py

R1.1 — Offline RBAC và Synthetic Identity Test Harness.

Bất biến được kiểm thử:
  T01  SyntheticActor không chứa PII (email, phone, long numeric ID)
  T02  SyntheticActor không thể đặt authentication_state='AUTHENTICATED'
  T03  synthetic_actor_id không đúng format SYN-ROLE-NNN bị từ chối
  T04  PI có thể CREATE_DRAFT_PROJECT → ALLOW
  T05  PI có thể EDIT_DRAFT_ARTIFACT → ALLOW
  T06  PI có thể RECORD_REVIEW_ATTESTATION (SELF_REVIEW) → ALLOW
  T07  PI không thể INDEPENDENT_REVIEW artifact của chính mình → BLOCK (SoD-01)
  T08  SYSTEM_ADMINISTRATOR không thể RECORD_REVIEW_ATTESTATION → BLOCK (SoD-02)
  T09  READ_ONLY_AUDITOR không thể EDIT_DRAFT_ARTIFACT → BLOCK (SoD-03)
  T10  DATA_MANAGER không thể UNLOCK_RESEARCH_DATA không có authorization → BLOCK (SoD-04)
  T11  DATA_MANAGER có thể UNLOCK khi có controlled-change authorization → ALLOW
  T12  EVIDENCE_CITATION_REVIEWER không thể tự attest source họ tạo → BLOCK (SoD-05)
  T13  Actor DISABLED bị block mọi action
  T14  Actor với role hết hạn bị block cho action của role đó
  T15  FORBIDDEN_ACTIONS_ALL_ROLES bị block cho mọi role (FINAL_APPROVAL)
  T16  ETHICS_APPROVAL bị block cho PI
  T17  INDEPENDENT_REVIEW_APPROVAL bị block cho METHODS_STATISTICS_REVIEWER
  T18  BLOCK decision chứa đủ trường bắt buộc (reason_code, policy_reference, actor_reference, action, object_reference, timestamp_utc)
  T19  Self-delegation bị từ chối (DelegationError)
  T20  Delegation với forbidden action bị từ chối (DelegationError)
  T21  Delegation lifecycle: PROPOSED → ACTIVE → REVOKED
  T22  Expired delegation trả về status EXPIRED
  T23  Audit event chứa đủ 17 trường + is_synthetic=True + production_valid=False
  T24  AuditAttributionLedger không có DELETE/UPDATE method
  T25  Hash chain verification PASS cho ledger hợp lệ
  T26  Hash chain verification FAIL sau khi sửa event
  T27  Mọi output không tuyên bố production_valid=True
  T28  Rejected delegation không thể activate

OFFLINE · SYNTHETIC ONLY · KHÔNG API / PII.
"""

from __future__ import annotations

import json
import pathlib
from datetime import datetime, timedelta, timezone

import pytest

from research_project.project_audit_attribution import (
    AuditAttributionLedger,
)
from research_project.project_delegation_registry import (
    DelegationError,
    DelegationRegistry,
    DelegationStatus,
)
from research_project.project_rbac_simulation import (
    EvaluationContext,
    ResearchAction,
    ResearchRole,
    RoleAssignment,
    SoDViolation,
    SyntheticActor,
    SyntheticActorRegistry,
    SyntheticIdentityError,
    build_default_registry,
    evaluate_rbac,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def now_utc() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture()
def future_utc() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()


@pytest.fixture()
def past_utc() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()


@pytest.fixture()
def default_registry() -> SyntheticActorRegistry:
    return build_default_registry()


@pytest.fixture()
def pi_actor(future_utc: str) -> SyntheticActor:
    return SyntheticActor(
        synthetic_actor_id="SYN-PI-001",
        display_label="Synthetic PI Alpha",
        role_assignments=[RoleAssignment(
            role=ResearchRole.PI.value,
            assigned_at_utc=datetime.now(timezone.utc).isoformat(),
        )],
    )


@pytest.fixture()
def delegation_registry(tmp_path: pathlib.Path) -> DelegationRegistry:
    return DelegationRegistry(tmp_path / "delegation_ledger.jsonl")


@pytest.fixture()
def audit_ledger(tmp_path: pathlib.Path) -> AuditAttributionLedger:
    return AuditAttributionLedger(tmp_path / "audit_ledger.jsonl")


# ---------------------------------------------------------------------------
# T01 — No PII in SyntheticActor
# ---------------------------------------------------------------------------

class TestT01_NoPII:
    def test_email_in_display_label_rejected(self) -> None:
        with pytest.raises(SyntheticIdentityError, match="PII"):
            SyntheticActor(
                synthetic_actor_id="SYN-PI-002",
                display_label="bsluanbv175@gmail.com",
                role_assignments=[RoleAssignment(
                    role=ResearchRole.PI.value,
                    assigned_at_utc=datetime.now(timezone.utc).isoformat(),
                )],
            )

    def test_phone_number_in_display_label_rejected(self) -> None:
        with pytest.raises(SyntheticIdentityError, match="PII"):
            SyntheticActor(
                synthetic_actor_id="SYN-PI-003",
                display_label="+84987654321",
                role_assignments=[RoleAssignment(
                    role=ResearchRole.PI.value,
                    assigned_at_utc=datetime.now(timezone.utc).isoformat(),
                )],
            )

    def test_valid_display_label_accepted(self) -> None:
        actor = SyntheticActor(
            synthetic_actor_id="SYN-PI-004",
            display_label="Synthetic PI Delta",
            role_assignments=[RoleAssignment(
                role=ResearchRole.PI.value,
                assigned_at_utc=datetime.now(timezone.utc).isoformat(),
            )],
        )
        assert actor.is_synthetic is True


# ---------------------------------------------------------------------------
# T02 — Cannot set authentication_state=AUTHENTICATED
# ---------------------------------------------------------------------------

class TestT02_NoAuthentication:
    def test_authenticated_state_rejected(self) -> None:
        with pytest.raises(SyntheticIdentityError, match="AUTHENTICATED"):
            SyntheticActor(
                synthetic_actor_id="SYN-PI-005",
                display_label="Synthetic PI Epsilon",
                role_assignments=[RoleAssignment(
                    role=ResearchRole.PI.value,
                    assigned_at_utc=datetime.now(timezone.utc).isoformat(),
                )],
                authentication_state="AUTHENTICATED",
            )

    def test_default_authentication_state_is_not_authenticated(
        self, pi_actor: SyntheticActor
    ) -> None:
        assert pi_actor.authentication_state == "NOT_AUTHENTICATED"
        assert pi_actor.identity_assurance == "SIMULATED_ONLY"


# ---------------------------------------------------------------------------
# T03 — Invalid synthetic_actor_id format
# ---------------------------------------------------------------------------

class TestT03_InvalidIDFormat:
    def test_bad_format_rejected(self) -> None:
        with pytest.raises(SyntheticIdentityError, match="SYN-"):
            SyntheticActor(
                synthetic_actor_id="REAL-USER-001",
                display_label="Not Synthetic",
                role_assignments=[RoleAssignment(
                    role=ResearchRole.PI.value,
                    assigned_at_utc=datetime.now(timezone.utc).isoformat(),
                )],
            )

    def test_missing_prefix_rejected(self) -> None:
        with pytest.raises(SyntheticIdentityError):
            SyntheticActor(
                synthetic_actor_id="PI-001",
                display_label="Bad Prefix",
                role_assignments=[],
            )


# ---------------------------------------------------------------------------
# T04–T06 — PI permitted actions
# ---------------------------------------------------------------------------

class TestT04T05T06_PIPermittedActions:
    def test_t04_pi_can_create_draft_project(self, pi_actor: SyntheticActor) -> None:
        result = evaluate_rbac(pi_actor, ResearchAction.CREATE_DRAFT_PROJECT.value)
        assert result.decision == "ALLOW"

    def test_t05_pi_can_edit_draft_artifact(self, pi_actor: SyntheticActor) -> None:
        result = evaluate_rbac(pi_actor, ResearchAction.EDIT_DRAFT_ARTIFACT.value)
        assert result.decision == "ALLOW"

    def test_t06_pi_can_record_self_review(self, pi_actor: SyntheticActor) -> None:
        ctx = EvaluationContext(is_own_artifact=True, review_type="SELF_REVIEW")
        result = evaluate_rbac(pi_actor, ResearchAction.RECORD_REVIEW_ATTESTATION.value, ctx)
        assert result.decision == "ALLOW"


# ---------------------------------------------------------------------------
# T07 — SoD-01: PI cannot INDEPENDENT_REVIEW own artifact
# ---------------------------------------------------------------------------

class TestT07_SoD01_PIIndependentReview:
    def test_pi_cannot_independent_review_own_artifact(
        self, pi_actor: SyntheticActor
    ) -> None:
        ctx = EvaluationContext(is_own_artifact=True, review_type="INDEPENDENT_REVIEW")
        result = evaluate_rbac(
            pi_actor, ResearchAction.RECORD_REVIEW_ATTESTATION.value, ctx
        )
        assert result.decision == "BLOCK"
        assert result.reason_code == SoDViolation.PI_SELF_INDEPENDENT_REVIEW.value


# ---------------------------------------------------------------------------
# T08 — SoD-02: SYSTEM_ADMINISTRATOR cannot approve research content
# ---------------------------------------------------------------------------

class TestT08_SoD02_AdminResearchApproval:
    def test_sysadmin_cannot_record_review_attestation(self) -> None:
        sysadmin = SyntheticActor(
            synthetic_actor_id="SYN-SYSADMIN-002",
            display_label="Synthetic SysAdmin",
            role_assignments=[RoleAssignment(
                role=ResearchRole.SYSTEM_ADMINISTRATOR.value,
                assigned_at_utc=datetime.now(timezone.utc).isoformat(),
            )],
        )
        result = evaluate_rbac(
            sysadmin, ResearchAction.RECORD_REVIEW_ATTESTATION.value
        )
        assert result.decision == "BLOCK"
        assert result.reason_code == SoDViolation.ADMIN_RESEARCH_APPROVAL.value


# ---------------------------------------------------------------------------
# T09 — SoD-03: READ_ONLY_AUDITOR cannot modify
# ---------------------------------------------------------------------------

class TestT09_SoD03_ReadOnlyAuditor:
    def test_auditor_cannot_edit_artifact(self) -> None:
        auditor = SyntheticActor(
            synthetic_actor_id="SYN-AUDITOR-002",
            display_label="Synthetic Auditor Beta",
            role_assignments=[RoleAssignment(
                role=ResearchRole.READ_ONLY_AUDITOR.value,
                assigned_at_utc=datetime.now(timezone.utc).isoformat(),
            )],
        )
        result = evaluate_rbac(auditor, ResearchAction.EDIT_DRAFT_ARTIFACT.value)
        assert result.decision == "BLOCK"
        assert result.reason_code == SoDViolation.READ_ONLY_WRITE_ATTEMPT.value


# ---------------------------------------------------------------------------
# T10–T11 — SoD-04: DATA_MANAGER UNLOCK
# ---------------------------------------------------------------------------

class TestT10T11_SoD04_DataManagerUnlock:
    def test_t10_dm_cannot_unlock_without_auth(self) -> None:
        dm = SyntheticActor(
            synthetic_actor_id="SYN-DM-002",
            display_label="Synthetic Data Manager",
            role_assignments=[RoleAssignment(
                role=ResearchRole.DATA_MANAGER.value,
                assigned_at_utc=datetime.now(timezone.utc).isoformat(),
            )],
        )
        ctx = EvaluationContext(has_controlled_change_authorization=False)
        result = evaluate_rbac(dm, ResearchAction.UNLOCK_RESEARCH_DATA.value, ctx)
        assert result.decision == "BLOCK"
        assert result.reason_code == SoDViolation.DATA_MANAGER_UNLOCK_NO_AUTH.value

    def test_t11_dm_can_unlock_with_authorization(self) -> None:
        dm = SyntheticActor(
            synthetic_actor_id="SYN-DM-003",
            display_label="Synthetic Data Manager Gamma",
            role_assignments=[RoleAssignment(
                role=ResearchRole.DATA_MANAGER.value,
                assigned_at_utc=datetime.now(timezone.utc).isoformat(),
            )],
        )
        ctx = EvaluationContext(has_controlled_change_authorization=True)
        result = evaluate_rbac(dm, ResearchAction.UNLOCK_RESEARCH_DATA.value, ctx)
        assert result.decision == "ALLOW"


# ---------------------------------------------------------------------------
# T12 — SoD-05: EVIDENCE_CITATION_REVIEWER cannot self-attest own source
# ---------------------------------------------------------------------------

class TestT12_SoD05_EvidenceReviewerSelfAttest:
    def test_ecr_cannot_attest_own_source(self) -> None:
        ecr = SyntheticActor(
            synthetic_actor_id="SYN-EVID-002",
            display_label="Synthetic Evidence Reviewer Beta",
            role_assignments=[RoleAssignment(
                role=ResearchRole.EVIDENCE_CITATION_REVIEWER.value,
                assigned_at_utc=datetime.now(timezone.utc).isoformat(),
            )],
        )
        ctx = EvaluationContext(is_own_source=True)
        result = evaluate_rbac(
            ecr, ResearchAction.RECORD_EVIDENCE_ATTESTATION.value, ctx
        )
        assert result.decision == "BLOCK"
        assert result.reason_code == SoDViolation.EVIDENCE_REVIEWER_SELF_ATTEST.value

    def test_ecr_can_attest_external_source(self) -> None:
        ecr = SyntheticActor(
            synthetic_actor_id="SYN-EVID-003",
            display_label="Synthetic Evidence Reviewer Gamma",
            role_assignments=[RoleAssignment(
                role=ResearchRole.EVIDENCE_CITATION_REVIEWER.value,
                assigned_at_utc=datetime.now(timezone.utc).isoformat(),
            )],
        )
        ctx = EvaluationContext(is_own_source=False)
        result = evaluate_rbac(
            ecr, ResearchAction.RECORD_EVIDENCE_ATTESTATION.value, ctx
        )
        assert result.decision == "ALLOW"


# ---------------------------------------------------------------------------
# T13 — Disabled actor is blocked
# ---------------------------------------------------------------------------

class TestT13_DisabledActor:
    def test_disabled_actor_blocked_for_any_action(
        self, default_registry: SyntheticActorRegistry
    ) -> None:
        pi = default_registry.get("SYN-PI-001")
        assert pi is not None
        default_registry.disable("SYN-PI-001")
        result = evaluate_rbac(pi, ResearchAction.VIEW_AUDIT_LOG.value)
        assert result.decision == "BLOCK"
        assert result.reason_code == SoDViolation.DISABLED_ACTOR.value


# ---------------------------------------------------------------------------
# T14 — Expired role assignment is blocked
# ---------------------------------------------------------------------------

class TestT14_ExpiredRole:
    def test_expired_role_is_blocked(self) -> None:
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        actor = SyntheticActor(
            synthetic_actor_id="SYN-MON-002",
            display_label="Synthetic Monitor Beta",
            role_assignments=[RoleAssignment(
                role=ResearchRole.MONITOR.value,
                assigned_at_utc=(datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
                expires_at_utc=past,
            )],
        )
        result = evaluate_rbac(actor, ResearchAction.VIEW_AUDIT_LOG.value)
        assert result.decision == "BLOCK"
        # G-04 remediation: all-roles-expired path returns EXPIRED_ROLE specifically.
        # active_roles()=[] triggers "if not active_roles" block in evaluate_rbac.
        # ROLE_NOT_PERMITTED is reserved for has-active-role-but-lacks-permission scenarios.
        assert result.reason_code == SoDViolation.EXPIRED_ROLE.value


# ---------------------------------------------------------------------------
# T15–T17 — Forbidden actions blocked for all roles
# ---------------------------------------------------------------------------

class TestT15T16T17_ForbiddenActions:
    def test_t15_final_approval_blocked_for_pi(self, pi_actor: SyntheticActor) -> None:
        result = evaluate_rbac(pi_actor, ResearchAction.FINAL_APPROVAL.value)
        assert result.decision == "BLOCK"
        assert result.reason_code == SoDViolation.FORBIDDEN_ACTION_ALL_ROLES.value

    def test_t16_ethics_approval_blocked_for_pi(self, pi_actor: SyntheticActor) -> None:
        result = evaluate_rbac(pi_actor, ResearchAction.ETHICS_APPROVAL.value)
        assert result.decision == "BLOCK"
        assert result.reason_code == SoDViolation.FORBIDDEN_ACTION_ALL_ROLES.value

    def test_t17_independent_review_approval_blocked_for_reviewer(self) -> None:
        reviewer = SyntheticActor(
            synthetic_actor_id="SYN-STAT-002",
            display_label="Synthetic Methods Reviewer Beta",
            role_assignments=[RoleAssignment(
                role=ResearchRole.METHODS_STATISTICS_REVIEWER.value,
                assigned_at_utc=datetime.now(timezone.utc).isoformat(),
            )],
        )
        result = evaluate_rbac(
            reviewer, ResearchAction.INDEPENDENT_REVIEW_APPROVAL.value
        )
        assert result.decision == "BLOCK"
        assert result.reason_code == SoDViolation.FORBIDDEN_ACTION_ALL_ROLES.value


# ---------------------------------------------------------------------------
# T18 — BLOCK decision has required fields
# ---------------------------------------------------------------------------

class TestT18_BlockDecisionFields:
    def test_block_decision_has_all_required_fields(
        self, pi_actor: SyntheticActor
    ) -> None:
        result = evaluate_rbac(pi_actor, ResearchAction.FINAL_APPROVAL.value)
        assert result.decision == "BLOCK"
        d = result.to_dict()
        required = [
            "decision", "reason_code", "policy_reference",
            "actor_reference", "action", "object_reference", "timestamp_utc",
        ]
        for field in required:
            assert field in d, f"Missing field: {field}"
        assert d["actor_reference"] == "SYN-PI-001"
        assert d["action"] == ResearchAction.FINAL_APPROVAL.value


# ---------------------------------------------------------------------------
# T19–T20 — Delegation validation
# ---------------------------------------------------------------------------

class TestT19T20_DelegationValidation:
    def test_t19_self_delegation_rejected(
        self, delegation_registry: DelegationRegistry, future_utc: str
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with pytest.raises(DelegationError, match="Self-delegation"):
            delegation_registry.propose(
                principal_id="SYN-PI-001",
                delegatee_id="SYN-PI-001",
                delegated_role=ResearchRole.CO_INVESTIGATOR.value,
                permitted_actions=["EDIT_DRAFT_ARTIFACT"],
                effective_from_utc=now,
                effective_until_utc=future_utc,
                reason="Test self-delegation",
            )

    def test_t20_delegation_with_forbidden_action_rejected(
        self, delegation_registry: DelegationRegistry, future_utc: str
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with pytest.raises(DelegationError, match="forbidden"):
            delegation_registry.propose(
                principal_id="SYN-PI-001",
                delegatee_id="SYN-STAT-001",
                delegated_role=ResearchRole.CO_INVESTIGATOR.value,
                permitted_actions=["EDIT_DRAFT_ARTIFACT", "FINAL_APPROVAL"],
                effective_from_utc=now,
                effective_until_utc=future_utc,
                reason="Delegation with forbidden action",
            )


# ---------------------------------------------------------------------------
# T21 — Delegation lifecycle: PROPOSED → ACTIVE → REVOKED
# ---------------------------------------------------------------------------

class TestT21_DelegationLifecycle:
    def test_delegation_lifecycle(
        self, delegation_registry: DelegationRegistry, future_utc: str
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()

        # PROPOSED
        record = delegation_registry.propose(
            principal_id="SYN-PI-001",
            delegatee_id="SYN-STAT-001",
            delegated_role=ResearchRole.CO_INVESTIGATOR.value,
            permitted_actions=["EDIT_DRAFT_ARTIFACT", "VIEW_AUDIT_LOG"],
            effective_from_utc=now,
            effective_until_utc=future_utc,
            reason="Synthetic delegation for dry run",
        )
        assert record.status == DelegationStatus.PROPOSED.value
        did = record.delegation_id

        # ACTIVE
        activated = delegation_registry.activate(did)
        assert activated.status == DelegationStatus.ACTIVE.value
        status = delegation_registry.get_status(did)
        assert status == DelegationStatus.ACTIVE.value

        # REVOKED
        revoked = delegation_registry.revoke(did, "Test revocation reason")
        assert revoked.status == DelegationStatus.REVOKED.value
        status_after = delegation_registry.get_status(did)
        assert status_after == DelegationStatus.REVOKED.value


# ---------------------------------------------------------------------------
# T22 — Expired delegation
# ---------------------------------------------------------------------------

class TestT22_ExpiredDelegation:
    def test_delegation_expired_after_effective_until(
        self, delegation_registry: DelegationRegistry, past_utc: str
    ) -> None:
        start = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        record = delegation_registry.propose(
            principal_id="SYN-PI-001",
            delegatee_id="SYN-DM-001",
            delegated_role=ResearchRole.DATA_MANAGER.value,
            permitted_actions=["EDIT_DRAFT_ARTIFACT"],
            effective_from_utc=start,
            effective_until_utc=past_utc,  # already in the past
            reason="Expired delegation test",
        )
        # Activate it
        delegation_registry.activate(record.delegation_id)
        # Check status at "now" — should be EXPIRED
        status = delegation_registry.get_status(
            record.delegation_id, now_utc=datetime.now(timezone.utc)
        )
        assert status == DelegationStatus.EXPIRED.value


# ---------------------------------------------------------------------------
# T23 — Audit event required fields
# ---------------------------------------------------------------------------

class TestT23_AuditEventFields:
    def test_audit_event_has_required_fields(
        self, audit_ledger: AuditAttributionLedger
    ) -> None:
        event = audit_ledger.record(
            synthetic_actor_id="SYN-PI-001",
            actor_role_at_event_time=ResearchRole.PI.value,
            action_type="ARTIFACT_EDITED",
            object_id="ARTIFACT-PROTOCOL-001",
            reason="Synthetic dry run edit",
        )
        d = event.to_dict()
        required_fields = [
            "event_id", "synthetic_actor_id", "actor_role_at_event_time",
            "delegation_reference_if_any", "authentication_context",
            "action_type", "object_id", "object_version",
            "before_state_hash_if_applicable", "after_state_hash_if_applicable",
            "timestamp_utc", "reason", "integrity_protection_method",
            "is_synthetic", "production_valid", "audit_event_hash",
            "previous_event_hash",
        ]
        for field in required_fields:
            assert field in d, f"Missing required field: {field}"
        assert d["is_synthetic"] is True
        assert d["production_valid"] is False
        assert d["authentication_context"] == "SIMULATED_NOT_AUTHENTICATED"

    def test_audit_event_hash_is_present_and_non_empty(
        self, audit_ledger: AuditAttributionLedger
    ) -> None:
        event = audit_ledger.record(
            synthetic_actor_id="SYN-STAT-001",
            actor_role_at_event_time=ResearchRole.METHODS_STATISTICS_REVIEWER.value,
            action_type="REVIEW_ATTESTATION_RECORDED",
            object_id="ARTIFACT-SAP-001",
            reason="Synthetic review",
        )
        assert event.audit_event_hash != ""
        assert len(event.audit_event_hash) == 64  # SHA-256 hex


# ---------------------------------------------------------------------------
# T24 — Audit ledger is append-only
# ---------------------------------------------------------------------------

class TestT24_AuditLedgerAppendOnly:
    def test_no_delete_or_update_method_on_ledger(
        self, audit_ledger: AuditAttributionLedger
    ) -> None:
        assert not hasattr(audit_ledger, "delete")
        assert not hasattr(audit_ledger, "update")
        assert not hasattr(audit_ledger, "remove")
        assert not hasattr(audit_ledger, "truncate")
        assert not hasattr(audit_ledger, "clear")

    def test_events_accumulate_across_records(
        self, audit_ledger: AuditAttributionLedger
    ) -> None:
        audit_ledger.record(
            synthetic_actor_id="SYN-PI-001",
            actor_role_at_event_time=ResearchRole.PI.value,
            action_type="PROJECT_CREATED",
            object_id="PROJ-001",
            reason="Created project",
        )
        audit_ledger.record(
            synthetic_actor_id="SYN-DM-001",
            actor_role_at_event_time=ResearchRole.DATA_MANAGER.value,
            action_type="ARTIFACT_EDITED",
            object_id="ARTIFACT-001",
            reason="Edited artifact",
        )
        assert audit_ledger.event_count() == 2


# ---------------------------------------------------------------------------
# T25 — Hash chain verification PASS
# ---------------------------------------------------------------------------

class TestT25_HashChainValid:
    def test_hash_chain_passes_for_valid_ledger(
        self, audit_ledger: AuditAttributionLedger
    ) -> None:
        for i in range(3):
            audit_ledger.record(
                synthetic_actor_id="SYN-PI-001",
                actor_role_at_event_time=ResearchRole.PI.value,
                action_type="ARTIFACT_EDITED",
                object_id=f"ARTIFACT-{i:03d}",
                reason=f"Event {i}",
            )
        ok, errors = audit_ledger.verify()
        assert ok is True
        assert errors == []


# ---------------------------------------------------------------------------
# T26 — Hash chain fails after tampering
# ---------------------------------------------------------------------------

class TestT26_HashChainTamper:
    def test_hash_chain_fails_after_event_tamper(
        self, tmp_path: pathlib.Path
    ) -> None:
        ledger_path = tmp_path / "tamper_test.jsonl"
        ledger = AuditAttributionLedger(ledger_path)

        ledger.record(
            synthetic_actor_id="SYN-PI-001",
            actor_role_at_event_time=ResearchRole.PI.value,
            action_type="PROJECT_CREATED",
            object_id="PROJ-TAMPER",
            reason="Before tamper",
        )
        ledger.record(
            synthetic_actor_id="SYN-STAT-001",
            actor_role_at_event_time=ResearchRole.METHODS_STATISTICS_REVIEWER.value,
            action_type="REVIEW_ATTESTATION_RECORDED",
            object_id="ARTIFACT-TAMPER",
            reason="Second event before tamper",
        )

        # Verify valid first
        ok_before, _ = ledger.verify()
        assert ok_before is True

        # Tamper: read JSONL, modify first event, write back
        lines = ledger_path.read_text(encoding="utf-8").splitlines()
        first_event = json.loads(lines[0])
        first_event["reason"] = "TAMPERED_REASON"
        lines[0] = json.dumps(first_event)
        ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

        # Verify should now FAIL
        new_ledger = AuditAttributionLedger(ledger_path)
        ok_after, errors = new_ledger.verify()
        assert ok_after is False
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# T27 — No output claims production_valid=True
# ---------------------------------------------------------------------------

class TestT27_NoProductionValidClaim:
    def test_audit_event_never_has_production_valid_true(
        self, audit_ledger: AuditAttributionLedger
    ) -> None:
        event = audit_ledger.record(
            synthetic_actor_id="SYN-EVID-001",
            actor_role_at_event_time=ResearchRole.EVIDENCE_CITATION_REVIEWER.value,
            action_type="EVIDENCE_ATTESTATION_RECORDED",
            object_id="SOURCE-001",
            reason="Synthetic evidence attestation",
        )
        assert event.production_valid is False
        assert event.to_dict()["production_valid"] is False

    def test_synthetic_actor_never_has_production_valid_attribute(
        self, pi_actor: SyntheticActor
    ) -> None:
        d = pi_actor.to_dict()
        assert d.get("production_valid", False) is False
        assert d["is_synthetic"] is True

    def test_rbac_decision_disclaimer_present(
        self, pi_actor: SyntheticActor
    ) -> None:
        result = evaluate_rbac(pi_actor, ResearchAction.FINAL_APPROVAL.value)
        assert "Not valid for production authorization" in result.disclaimer


# ---------------------------------------------------------------------------
# T28 — Rejected delegation cannot be activated
# ---------------------------------------------------------------------------

class TestT28_RejectedDelegationCannotActivate:
    def test_rejected_delegation_cannot_activate(
        self, delegation_registry: DelegationRegistry, future_utc: str
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        record = delegation_registry.propose(
            principal_id="SYN-PI-001",
            delegatee_id="SYN-QA-001",
            delegated_role=ResearchRole.DATA_GOVERNANCE_QA_REVIEWER.value,
            permitted_actions=["RECORD_REVIEW_ATTESTATION"],
            effective_from_utc=now,
            effective_until_utc=future_utc,
            reason="Will be rejected",
        )
        delegation_registry.reject(record.delegation_id, "Rejected by PI")
        with pytest.raises(DelegationError, match="PROPOSED"):
            delegation_registry.activate(record.delegation_id)


# ---------------------------------------------------------------------------
# Bonus — Default registry actors all have valid IDs and are active
# ---------------------------------------------------------------------------

class TestDefaultRegistry:
    def test_all_default_actors_have_valid_ids(
        self, default_registry: SyntheticActorRegistry
    ) -> None:
        actor_ids = default_registry.all_actor_ids()
        assert len(actor_ids) >= 9
        for aid in actor_ids:
            assert aid.startswith("SYN-"), f"Bad ID: {aid}"

    def test_all_default_actors_are_not_authenticated(
        self, default_registry: SyntheticActorRegistry
    ) -> None:
        for aid in default_registry.all_actor_ids():
            actor = default_registry.get(aid)
            assert actor is not None
            assert actor.authentication_state == "NOT_AUTHENTICATED"
            assert actor.is_synthetic is True
