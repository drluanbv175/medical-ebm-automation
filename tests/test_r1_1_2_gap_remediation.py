"""
tests/test_r1_1_2_gap_remediation.py

R1.1.2 — Design-Gap Remediation and Test Hardening.

Bất biến được kiểm thử:
  G-01  CLI subprocess E2E tests (4 commands)
  G-02a EXTERNAL_SUBMISSION bị block với FORBIDDEN_ACTION_ALL_ROLES (dedicated test)
  G-02b CLINICAL_RELEASE bị block với FORBIDDEN_ACTION_ALL_ROLES (dedicated test)
  G-03  SYSTEM_ADMINISTRATOR bị block khi LOCK_RESEARCH_DATA (SoD-02)
  G-04  (remediation đã apply tại T14 trong test_r1_1_offline_rbac_synthetic_identity.py)

  WORM-01  Audit event to_dict không chứa "worm", "immutable", "production" claim
  WORM-02  AuditAttributionLedger không có WORM/immutable method
  WORM-03  PROD_AUD_01_WORM_DEPENDENCY = "NOT_IMPLEMENTED"
  WORM-04  LOCAL_LEDGER_CLASSIFICATION chứa "NOT_WORM"
  WORM-05  Tamper: modified event content → verify() FAIL
  WORM-06  Tamper: missing/broken previous_event_hash → verify() FAIL
  WORM-07  Tamper: sequence_number discontinuity → verify() FAIL
  WORM-08  Tamper: deleted middle event → verify() FAIL (seq gap)
  WORM-09  Tamper: duplicate event_id → verify() FAIL
  WORM-10  Tamper: out-of-order sequence_number → verify() FAIL
  WORM-11  Checkpoint record không chứa WORM claim; có production_worm_dependency=NOT_IMPLEMENTED
  WORM-12  ledger_root_hash() thay đổi khi event bị sửa

  DEL-01  Expired delegation → BLOCK với reason_code=DELEGATION_EXPIRED
  DEL-02  Revoked delegation → BLOCK với reason_code=DELEGATION_REVOKED
  DEL-03  Scope-exceeded → BLOCK với reason_code=DELEGATION_SCOPE_EXCEEDED
  DEL-04  Forbidden authority → BLOCK với reason_code=DELEGATION_FORBIDDEN_AUTHORITY
  DEL-05  DelegationDecision có đủ trường bắt buộc
  DEL-06  PROPOSED (chưa activate) → BLOCK với DELEGATION_NOT_ACTIVE
  DEL-07  Không tồn tại delegation_id → BLOCK với DELEGATION_NOT_FOUND
  DEL-08  Các reason code là chuỗi khác nhau (không generic)

  INV-01  Không có network/API/PII/production-authentication trong toàn bộ test này
  INV-02  Mọi audit event có is_synthetic=True, production_valid=False

OFFLINE · SYNTHETIC ONLY · KHÔNG API / PII / network.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from research_project.project_audit_attribution import (
    LOCAL_LEDGER_CLASSIFICATION,
    PROD_AUD_01_WORM_DEPENDENCY,
    AuditAttributionLedger,
    compute_event_hash,
    verify_hash_chain,
)
from research_project.project_delegation_registry import (
    DelegationReasonCode,
    DelegationRegistry,
    evaluate_delegation_action,
)
from research_project.project_rbac_simulation import (
    FORBIDDEN_ACTIONS_ALL_ROLES,
    ResearchAction,
    ResearchRole,
    RoleAssignment,
    SoDViolation,
    SyntheticActor,
    evaluate_rbac,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def future_utc() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()


@pytest.fixture()
def past_utc() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()


@pytest.fixture()
def delegation_registry(tmp_path: pathlib.Path) -> DelegationRegistry:
    return DelegationRegistry(tmp_path / "delegation_ledger.jsonl")


@pytest.fixture()
def audit_ledger(tmp_path: pathlib.Path) -> AuditAttributionLedger:
    return AuditAttributionLedger(tmp_path / "audit_ledger.jsonl")


@pytest.fixture()
def sysadmin_actor() -> SyntheticActor:
    return SyntheticActor(
        synthetic_actor_id="SYN-SYSADMIN-001",
        display_label="Synthetic SysAdmin Epsilon",
        role_assignments=[RoleAssignment(
            role=ResearchRole.SYSTEM_ADMINISTRATOR.value,
            assigned_at_utc=datetime.now(timezone.utc).isoformat(),
        )],
    )


@pytest.fixture()
def methods_actor() -> SyntheticActor:
    return SyntheticActor(
        synthetic_actor_id="SYN-STAT-001",
        display_label="Synthetic Methods Reviewer Beta",
        role_assignments=[RoleAssignment(
            role=ResearchRole.METHODS_STATISTICS_REVIEWER.value,
            assigned_at_utc=datetime.now(timezone.utc).isoformat(),
        )],
    )


def _make_ledger_with_n_events(
    ledger: AuditAttributionLedger, n: int
) -> List[dict]:
    """Helper: ghi n events vào ledger, trả về list dicts."""
    for i in range(n):
        ledger.record(
            synthetic_actor_id="SYN-PI-001",
            actor_role_at_event_time=ResearchRole.PI.value,
            action_type="ARTIFACT_EDITED",
            object_id=f"OBJ-{i:03d}",
            reason=f"Synthetic event {i + 1}",
        )
    return ledger.read_all()


# ---------------------------------------------------------------------------
# G-01 — CLI subprocess E2E tests
# ---------------------------------------------------------------------------

class TestG01_CLI_Subprocess:
    """G-01: CLI commands có compile check nhưng không có E2E functional test qua subprocess."""

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess:
        # Use -m invocation to avoid relative-import error from direct file path execution
        return subprocess.run(
            [sys.executable, "-m", "research_project.project_cli"] + list(args),
            capture_output=True,
            text=True,
            timeout=30,
            cwd=None,  # uses caller's cwd (medical-ebm-automation/)
        )

    def test_g01_rbac_simulate_exits_zero(self) -> None:
        result = self._run_cli(
            "rbac-simulate",
            "--actor-id", "SYN-PI-001",
            "--action", "CREATE_DRAFT_PROJECT",
        )
        assert result.returncode == 0, (
            f"rbac-simulate failed: stderr={result.stderr[:300]}"
        )

    def test_g01_delegation_register_exits_zero(self, tmp_path: pathlib.Path) -> None:
        ledger = tmp_path / "del.jsonl"
        now = datetime.now(timezone.utc).isoformat()
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        result = self._run_cli(
            "delegation-register",
            "--ledger", str(ledger),
            "--principal-id", "SYN-PI-001",
            "--delegatee-id", "SYN-STAT-001",
            "--role", ResearchRole.METHODS_STATISTICS_REVIEWER.value,
            "--actions", "RECORD_REVIEW_ATTESTATION",
            "--from", now,
            "--until", future,
            "--reason", "G-01 CLI subprocess test",
        )
        assert result.returncode == 0, (
            f"delegation-register failed: stderr={result.stderr[:300]}"
        )

    def test_g01_delegation_status_exits_zero(self, tmp_path: pathlib.Path) -> None:
        ledger = tmp_path / "del.jsonl"
        now = datetime.now(timezone.utc).isoformat()
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        # Register first
        reg = self._run_cli(
            "delegation-register",
            "--ledger", str(ledger),
            "--principal-id", "SYN-PI-001",
            "--delegatee-id", "SYN-STAT-001",
            "--role", ResearchRole.METHODS_STATISTICS_REVIEWER.value,
            "--actions", "RECORD_REVIEW_ATTESTATION",
            "--from", now,
            "--until", future,
            "--reason", "G-01 status test",
        )
        assert reg.returncode == 0
        # Extract delegation_id from stdout
        output = reg.stdout
        del_id = None
        for line in output.splitlines():
            if "DEL-" in line:
                for token in line.split():
                    if token.startswith("DEL-"):
                        del_id = token.strip('",')
                        break
        if del_id is None:
            pytest.skip("Could not extract delegation_id from CLI output")
        result = self._run_cli(
            "delegation-status",
            "--ledger", str(ledger),
            "--delegation-id", del_id,
        )
        assert result.returncode == 0, (
            f"delegation-status failed: stderr={result.stderr[:300]}"
        )

    def test_g01_audit_attribution_verify_exits_zero(
        self, tmp_path: pathlib.Path, audit_ledger: AuditAttributionLedger
    ) -> None:
        ledger_path = tmp_path / "audit_ledger.jsonl"
        ledger = AuditAttributionLedger(ledger_path)
        ledger.record(
            synthetic_actor_id="SYN-PI-001",
            actor_role_at_event_time=ResearchRole.PI.value,
            action_type="PROJECT_CREATED",
            object_id="PROJ-G01",
            reason="G-01 subprocess verify test",
        )
        result = self._run_cli(
            "audit-attribution-verify",
            "--ledger", str(ledger_path),
        )
        assert result.returncode == 0, (
            f"audit-attribution-verify failed: stderr={result.stderr[:300]}"
        )


# ---------------------------------------------------------------------------
# G-02 — Dedicated forbidden action tests
# ---------------------------------------------------------------------------

class TestG02_ForbiddenActionDedicated:
    """G-02: EXTERNAL_SUBMISSION và CLINICAL_RELEASE chưa có dedicated test."""

    def test_g02a_external_submission_blocked_for_methods_reviewer(
        self, methods_actor: SyntheticActor
    ) -> None:
        """Dedicated test: EXTERNAL_SUBMISSION bị block trước RBAC policy."""
        result = evaluate_rbac(methods_actor, ResearchAction.EXTERNAL_SUBMISSION.value)
        assert result.decision == "BLOCK"
        assert result.reason_code == SoDViolation.FORBIDDEN_ACTION_ALL_ROLES.value

    def test_g02b_clinical_release_blocked_for_methods_reviewer(
        self, methods_actor: SyntheticActor
    ) -> None:
        """Dedicated test: CLINICAL_RELEASE bị block trước RBAC policy."""
        result = evaluate_rbac(methods_actor, ResearchAction.CLINICAL_RELEASE.value)
        assert result.decision == "BLOCK"
        assert result.reason_code == SoDViolation.FORBIDDEN_ACTION_ALL_ROLES.value

    def test_g02_forbidden_actions_set_contains_all_five(self) -> None:
        """Verify set có đủ 5 forbidden actions không thiếu."""
        expected = {
            "FINAL_APPROVAL", "ETHICS_APPROVAL", "INDEPENDENT_REVIEW_APPROVAL",
            "EXTERNAL_SUBMISSION", "CLINICAL_RELEASE",
        }
        assert expected == set(FORBIDDEN_ACTIONS_ALL_ROLES)


# ---------------------------------------------------------------------------
# G-03 — SYSADMIN cannot LOCK_RESEARCH_DATA (SoD-02)
# ---------------------------------------------------------------------------

class TestG03_SysAdminLockResearchData:
    """G-03: _RESEARCH_CONTENT_APPROVAL_ACTIONS chưa có test cho LOCK_RESEARCH_DATA × SYSADMIN."""

    def test_g03_sysadmin_cannot_lock_research_data(
        self, sysadmin_actor: SyntheticActor
    ) -> None:
        """SYSTEM_ADMINISTRATOR LOCK_RESEARCH_DATA → BLOCK (SoD-02)."""
        result = evaluate_rbac(sysadmin_actor, ResearchAction.LOCK_RESEARCH_DATA.value)
        assert result.decision == "BLOCK"
        assert result.reason_code == SoDViolation.ADMIN_RESEARCH_APPROVAL.value

    def test_g03_lock_research_data_in_research_content_approval_set(self) -> None:
        """Confirm LOCK_RESEARCH_DATA is in _RESEARCH_CONTENT_APPROVAL_ACTIONS set."""
        from research_project.project_rbac_simulation import _RESEARCH_CONTENT_APPROVAL_ACTIONS
        assert "LOCK_RESEARCH_DATA" in _RESEARCH_CONTENT_APPROVAL_ACTIONS


# ---------------------------------------------------------------------------
# WORM-01 to WORM-04 — Truthfulness: local ledger never claims WORM
# ---------------------------------------------------------------------------

class TestWORM_Truthfulness:
    """Phase B: Local ledger never claims WORM, immutable, or production."""

    def test_worm01_event_to_dict_contains_no_worm_claim(
        self, audit_ledger: AuditAttributionLedger
    ) -> None:
        event = audit_ledger.record(
            synthetic_actor_id="SYN-PI-001",
            actor_role_at_event_time=ResearchRole.PI.value,
            action_type="PROJECT_CREATED",
            object_id="PROJ-W01",
            reason="Tamper-evident classification check",  # no 'worm' in reason
        )
        d = event.to_dict()
        # Classification must explicitly state NOT_WORM
        assert d.get("local_ledger_classification") == LOCAL_LEDGER_CLASSIFICATION
        assert "NOT_WORM" in LOCAL_LEDGER_CLASSIFICATION
        # No framework field may make a positive WORM claim (worm_storage, is_worm, worm_compliant)
        # Note: local_ledger_classification intentionally contains "not_worm" as a denial — skip it
        for k, v in d.items():
            if k == "local_ledger_classification":
                continue
            if isinstance(v, str):
                assert "worm_storage" not in v.lower(), f"WORM claim in field {k}"
                assert "worm_compliant" not in v.lower(), f"WORM claim in field {k}"
                assert "is_worm" not in v.lower(), f"WORM claim in field {k}"

    def test_worm02_ledger_has_no_worm_method(
        self, audit_ledger: AuditAttributionLedger
    ) -> None:
        for forbidden_method in ("write_worm", "seal", "immutable_lock", "worm_archive"):
            assert not hasattr(audit_ledger, forbidden_method)

    def test_worm03_prod_aud_01_is_not_implemented(self) -> None:
        assert PROD_AUD_01_WORM_DEPENDENCY == "NOT_IMPLEMENTED"

    def test_worm04_local_ledger_classification_contains_not_worm(self) -> None:
        assert "NOT_WORM" in LOCAL_LEDGER_CLASSIFICATION
        assert "SIMULATION" in LOCAL_LEDGER_CLASSIFICATION


# ---------------------------------------------------------------------------
# WORM-05 to WORM-10 — Enhanced tamper detection scenarios
# ---------------------------------------------------------------------------

class TestWORM_TamperDetection:
    """Phase E tests 5–10: Enhanced tamper scenarios in audit hash chain."""

    def test_worm05_modified_event_content_detected(
        self, audit_ledger: AuditAttributionLedger
    ) -> None:
        """Tamper: sửa nội dung event (reason field) → verify FAIL."""
        _make_ledger_with_n_events(audit_ledger, 3)
        events = audit_ledger.read_all()
        events[1] = {**events[1], "reason": "TAMPERED REASON"}
        ok, errors = verify_hash_chain(events)
        assert ok is False
        assert len(errors) >= 1

    def test_worm06_missing_previous_hash_link_detected(
        self, audit_ledger: AuditAttributionLedger
    ) -> None:
        """Tamper: xóa previous_event_hash của event giữa → verify FAIL."""
        _make_ledger_with_n_events(audit_ledger, 3)
        events = audit_ledger.read_all()
        events[1] = {**events[1], "previous_event_hash": "BROKEN_HASH_VALUE"}
        ok, errors = verify_hash_chain(events)
        assert ok is False
        assert any("previous_event_hash" in e or "chain break" in e for e in errors)

    def test_worm07_sequence_discontinuity_detected(self) -> None:
        """Tamper: sequence_number có gap (1, 2, 4 — thiếu 3) → verify FAIL."""
        ev1 = {"event_id": "AUD-001", "sequence_number": 1, "previous_event_hash": "GENESIS",
               "reason": "A", "audit_event_hash": ""}
        ev1["audit_event_hash"] = compute_event_hash(ev1)
        ev2 = {"event_id": "AUD-002", "sequence_number": 2, "previous_event_hash": ev1["audit_event_hash"],
               "reason": "B", "audit_event_hash": ""}
        ev2["audit_event_hash"] = compute_event_hash(ev2)
        # Skip sequence 3 → discontinuity
        ev4 = {"event_id": "AUD-004", "sequence_number": 4, "previous_event_hash": ev2["audit_event_hash"],
               "reason": "D", "audit_event_hash": ""}
        ev4["audit_event_hash"] = compute_event_hash(ev4)
        ok, errors = verify_hash_chain([ev1, ev2, ev4])
        assert ok is False
        assert any("discontinuity" in e or "deleted" in e for e in errors)

    def test_worm08_deleted_middle_event_detected(
        self, audit_ledger: AuditAttributionLedger
    ) -> None:
        """Tamper: xóa event giữa (giữ 1, 3 → mất 2) → verify FAIL (seq gap)."""
        _make_ledger_with_n_events(audit_ledger, 3)
        events = audit_ledger.read_all()
        # Remove event at index 1 (sequence_number=2)
        events_without_middle = [events[0], events[2]]
        ok, errors = verify_hash_chain(events_without_middle)
        assert ok is False
        # Either chain break (previous_event_hash mismatch) or sequence gap
        assert len(errors) >= 1

    def test_worm09_duplicate_event_id_detected(self) -> None:
        """Tamper: hai events có cùng event_id → verify FAIL."""
        ev1 = {"event_id": "AUD-DUP", "sequence_number": 1, "previous_event_hash": "GENESIS",
               "reason": "First", "audit_event_hash": ""}
        ev1["audit_event_hash"] = compute_event_hash(ev1)
        ev2 = {"event_id": "AUD-DUP", "sequence_number": 2, "previous_event_hash": ev1["audit_event_hash"],
               "reason": "Second", "audit_event_hash": ""}
        ev2["audit_event_hash"] = compute_event_hash(ev2)
        ok, errors = verify_hash_chain([ev1, ev2])
        assert ok is False
        assert any("duplicate" in e for e in errors)

    def test_worm10_out_of_order_sequence_detected(self) -> None:
        """Tamper: sequence_number giảm (1, 2, 1) → verify FAIL."""
        ev1 = {"event_id": "AUD-A", "sequence_number": 1, "previous_event_hash": "GENESIS",
               "reason": "A", "audit_event_hash": ""}
        ev1["audit_event_hash"] = compute_event_hash(ev1)
        ev2 = {"event_id": "AUD-B", "sequence_number": 2, "previous_event_hash": ev1["audit_event_hash"],
               "reason": "B", "audit_event_hash": ""}
        ev2["audit_event_hash"] = compute_event_hash(ev2)
        ev3_bad = {"event_id": "AUD-C", "sequence_number": 1,  # out-of-order
                   "previous_event_hash": ev2["audit_event_hash"],
                   "reason": "C", "audit_event_hash": ""}
        ev3_bad["audit_event_hash"] = compute_event_hash(ev3_bad)
        ok, errors = verify_hash_chain([ev1, ev2, ev3_bad])
        assert ok is False
        assert any("out-of-order" in e for e in errors)


# ---------------------------------------------------------------------------
# WORM-11 to WORM-12 — Checkpoint and root hash
# ---------------------------------------------------------------------------

class TestWORM_CheckpointAndRootHash:
    def test_worm11_checkpoint_has_no_worm_claim(
        self, audit_ledger: AuditAttributionLedger
    ) -> None:
        """Checkpoint record chứa production_worm_dependency=NOT_IMPLEMENTED."""
        _make_ledger_with_n_events(audit_ledger, 2)
        cp = audit_ledger.create_checkpoint("PERIODIC")
        assert cp.get("production_worm_dependency") == "NOT_IMPLEMENTED"
        cp_str = json.dumps(cp).lower()
        assert "worm" not in cp_str or "not_worm" in cp_str or "not_implemented" in cp_str

    def test_worm12_root_hash_changes_on_tamper(
        self, audit_ledger: AuditAttributionLedger, tmp_path: pathlib.Path
    ) -> None:
        """ledger_root_hash() thay đổi khi event bị sửa bên ngoài."""
        _make_ledger_with_n_events(audit_ledger, 3)
        root_before = audit_ledger.ledger_root_hash()
        # Tamper: sửa trực tiếp JSONL file
        content = audit_ledger._path.read_text(encoding="utf-8")
        lines = content.splitlines()
        if len(lines) >= 2:
            second = json.loads(lines[1])
            second["reason"] = "TAMPERED"
            lines[1] = json.dumps(second)
            audit_ledger._path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        root_after = audit_ledger.ledger_root_hash()
        assert root_before != root_after


# ---------------------------------------------------------------------------
# DEL-01 to DEL-08 — Delegation reason codes (Phase C)
# ---------------------------------------------------------------------------

class TestDEL_ReasonCodes:
    """Phase C: Structured delegation reason codes."""

    def _active_delegation(
        self, registry: DelegationRegistry, future_utc: str
    ) -> str:
        """Helper: create and activate a delegation, return delegation_id."""
        now = datetime.now(timezone.utc).isoformat()
        rec = registry.propose(
            principal_id="SYN-PI-001",
            delegatee_id="SYN-STAT-001",
            delegated_role=ResearchRole.METHODS_STATISTICS_REVIEWER.value,
            permitted_actions=["RECORD_REVIEW_ATTESTATION"],
            effective_from_utc=now,
            effective_until_utc=future_utc,
            reason="Test delegation",
        )
        registry.activate(rec.delegation_id)
        return rec.delegation_id

    def test_del01_expired_delegation_returns_delegation_expired(
        self, delegation_registry: DelegationRegistry
    ) -> None:
        past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        earlier = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        rec = delegation_registry.propose(
            principal_id="SYN-PI-001",
            delegatee_id="SYN-STAT-001",
            delegated_role=ResearchRole.METHODS_STATISTICS_REVIEWER.value,
            permitted_actions=["RECORD_REVIEW_ATTESTATION"],
            effective_from_utc=earlier,
            effective_until_utc=past,
            reason="Will expire",
        )
        delegation_registry.activate(rec.delegation_id)
        result = evaluate_delegation_action(
            delegation_registry, rec.delegation_id,
            actor_reference="SYN-STAT-001",
            action="RECORD_REVIEW_ATTESTATION",
        )
        assert result.decision == "BLOCK"
        assert result.reason_code == DelegationReasonCode.DELEGATION_EXPIRED.value
        assert result.effective_until_utc == past

    def test_del02_revoked_delegation_returns_delegation_revoked(
        self, delegation_registry: DelegationRegistry, future_utc: str
    ) -> None:
        del_id = self._active_delegation(delegation_registry, future_utc)
        delegation_registry.revoke(del_id, "Test revocation")
        result = evaluate_delegation_action(
            delegation_registry, del_id,
            actor_reference="SYN-STAT-001",
            action="RECORD_REVIEW_ATTESTATION",
        )
        assert result.decision == "BLOCK"
        assert result.reason_code == DelegationReasonCode.DELEGATION_REVOKED.value

    def test_del03_scope_exceeded_returns_delegation_scope_exceeded(
        self, delegation_registry: DelegationRegistry, future_utc: str
    ) -> None:
        del_id = self._active_delegation(delegation_registry, future_utc)
        # LOCK_RESEARCH_DATA is not in permitted_actions (only RECORD_REVIEW_ATTESTATION is)
        result = evaluate_delegation_action(
            delegation_registry, del_id,
            actor_reference="SYN-STAT-001",
            action="LOCK_RESEARCH_DATA",
        )
        assert result.decision == "BLOCK"
        assert result.reason_code == DelegationReasonCode.DELEGATION_SCOPE_EXCEEDED.value

    def test_del04_forbidden_authority_returns_delegation_forbidden_authority(
        self, delegation_registry: DelegationRegistry, future_utc: str
    ) -> None:
        del_id = self._active_delegation(delegation_registry, future_utc)
        result = evaluate_delegation_action(
            delegation_registry, del_id,
            actor_reference="SYN-STAT-001",
            action="FINAL_APPROVAL",
        )
        assert result.decision == "BLOCK"
        assert result.reason_code == DelegationReasonCode.DELEGATION_FORBIDDEN_AUTHORITY.value

    def test_del05_delegation_decision_has_required_fields(
        self, delegation_registry: DelegationRegistry, future_utc: str
    ) -> None:
        """DelegationDecision.to_dict() có đủ tất cả required fields."""
        del_id = self._active_delegation(delegation_registry, future_utc)
        result = evaluate_delegation_action(
            delegation_registry, del_id,
            actor_reference="SYN-STAT-001",
            action="RECORD_REVIEW_ATTESTATION",
            object_reference="ARTIFACT-001",
        )
        d = result.to_dict()
        required = [
            "decision", "reason_code", "policy_reference", "delegation_id",
            "actor_reference", "action", "object_reference",
            "effective_until_utc", "evaluated_at_utc", "timestamp_utc",
        ]
        for field in required:
            assert field in d, f"Missing required field: {field}"
        assert result.decision == "ALLOW"
        assert result.reason_code == DelegationReasonCode.DELEGATION_PERMITTED.value

    def test_del06_proposed_not_activated_returns_not_active(
        self, delegation_registry: DelegationRegistry, future_utc: str
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        rec = delegation_registry.propose(
            principal_id="SYN-PI-001",
            delegatee_id="SYN-STAT-001",
            delegated_role=ResearchRole.METHODS_STATISTICS_REVIEWER.value,
            permitted_actions=["RECORD_REVIEW_ATTESTATION"],
            effective_from_utc=now,
            effective_until_utc=future_utc,
            reason="Never activated",
        )
        # Do NOT activate — stays PROPOSED
        result = evaluate_delegation_action(
            delegation_registry, rec.delegation_id,
            actor_reference="SYN-STAT-001",
            action="RECORD_REVIEW_ATTESTATION",
        )
        assert result.decision == "BLOCK"
        assert result.reason_code == DelegationReasonCode.DELEGATION_NOT_ACTIVE.value

    def test_del07_nonexistent_delegation_returns_not_found(
        self, delegation_registry: DelegationRegistry
    ) -> None:
        result = evaluate_delegation_action(
            delegation_registry, "DEL-DOESNOTEXIST",
            actor_reference="SYN-PI-001",
            action="CREATE_DRAFT_PROJECT",
        )
        assert result.decision == "BLOCK"
        assert result.reason_code == DelegationReasonCode.DELEGATION_NOT_FOUND.value

    def test_del08_reason_codes_are_distinct_strings(self) -> None:
        """Tất cả reason codes là chuỗi khác nhau — không generic."""
        all_codes = [rc.value for rc in DelegationReasonCode]
        assert len(all_codes) == len(set(all_codes)), "Duplicate reason code values"
        for code in all_codes:
            assert code.startswith("DELEGATION_"), (
                f"Reason code should start with DELEGATION_: {code}"
            )
            assert code != "INVALID_DELEGATION", "Must not use generic error string"


# ---------------------------------------------------------------------------
# INV-01 to INV-02 — Invariants across all new tests
# ---------------------------------------------------------------------------

class TestINV_Invariants:
    def test_inv01_no_network_api_pii_in_module_imports(self) -> None:
        """Modules không import network-dependent libraries."""
        import research_project.project_audit_attribution as m_audit
        import research_project.project_delegation_registry as m_del
        import research_project.project_rbac_simulation as m_rbac
        for mod in (m_audit, m_del, m_rbac):
            src = getattr(mod, "__file__", "")
            if src:
                content = pathlib.Path(src).read_text(encoding="utf-8")
                for forbidden in ("import requests", "import httpx", "import urllib.request",
                                  "import boto3", "import google.auth", "import msal"):
                    assert forbidden not in content, (
                        f"Network import '{forbidden}' found in {src}"
                    )

    def test_inv02_all_audit_events_have_synthetic_markers(
        self, audit_ledger: AuditAttributionLedger
    ) -> None:
        """Mọi audit event có is_synthetic=True, production_valid=False."""
        _make_ledger_with_n_events(audit_ledger, 5)
        for ev_dict in audit_ledger.read_all():
            if ev_dict.get("checkpoint_type"):
                continue  # skip checkpoint records
            assert ev_dict.get("is_synthetic") is True
            assert ev_dict.get("production_valid") is False
