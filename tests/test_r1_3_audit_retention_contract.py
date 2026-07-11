"""
R1.3 Audit Retention Contract Tests.

Kiểm tra giao diện và hợp đồng audit_retention_contract.py trong harness offline.
KHÔNG kết nối WORM storage thật, AWS/Azure/GCP, hay backup ngoài hệ thống.
Chạy: MRAQ_OFFLINE_CI=1 pytest tests/test_r1_3_audit_retention_contract.py -v
"""

import inspect
import pytest

from research_project.audit_retention_contract import (
    DISCLAIMER_FAKE_WORM,
    DISCLAIMER_REAL_WORM,
    LOCAL_LEDGER_CLASSIFICATION,
    PROD_BACKUP_DEPENDENCY,
    PROD_LEGAL_HOLD_DEPENDENCY,
    PROD_WORM_DEPENDENCY,
    PROVIDER_NAME_FAKE,
    FakeWormRetentionAdapter,
    RetentionPolicy,
    WriteReceipt,
    WormRetentionProviderInterface,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _sample_event(event_id: str = "evt-001") -> dict:
    return {
        "event_id": event_id,
        "actor_id": "synthetic_actor",
        "action": "READ_RECORD",
        "timestamp_utc": "2026-06-28T00:00:00Z",
        "audit_event_hash": "abc123def456",
        "attribution_mode": "SYNTHETIC",
    }


# ── Interface shape ─────────────────────────────────────────────────────────

class TestInterfaceShape:
    def test_interface_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            WormRetentionProviderInterface()

    def test_interface_has_required_methods(self):
        required = {
            "write_event", "read_event", "verify_event",
            "create_legal_hold", "release_legal_hold",
            "list_events_in_range", "get_retention_policy",
            "provider_health_check",
        }
        abstract = set(getattr(WormRetentionProviderInterface, "__abstractmethods__", set()))
        assert required == abstract

    def test_fake_adapter_implements_interface(self):
        adapter = FakeWormRetentionAdapter()
        assert isinstance(adapter, WormRetentionProviderInterface)


# ── WriteReceipt contract ───────────────────────────────────────────────────

class TestWriteReceiptContract:
    def test_valid_fake_receipt_is_accepted(self):
        receipt = WriteReceipt(
            provider_id="fake-001",
            provider_timestamp_utc="2026-06-28T00:00:00Z",
            immutability_expiry_utc=None,
            etag="abcdef01",
            provider_name=PROVIDER_NAME_FAKE,
            region="OFFLINE_SIMULATION",
            is_worm_confirmed=False,
            disclaimer=DISCLAIMER_FAKE_WORM,
        )
        assert receipt.is_worm_confirmed is False

    def test_empty_provider_id_raises(self):
        with pytest.raises(ValueError, match="provider_id"):
            WriteReceipt(
                provider_id="",
                provider_timestamp_utc="2026-06-28T00:00:00Z",
                immutability_expiry_utc=None,
                etag="abc",
                provider_name=PROVIDER_NAME_FAKE,
                region="SIM",
                is_worm_confirmed=False,
                disclaimer=DISCLAIMER_FAKE_WORM,
            )

    def test_empty_provider_name_raises(self):
        with pytest.raises(ValueError, match="provider_name"):
            WriteReceipt(
                provider_id="id",
                provider_timestamp_utc="2026-06-28T00:00:00Z",
                immutability_expiry_utc=None,
                etag="abc",
                provider_name="",
                region="SIM",
                is_worm_confirmed=False,
                disclaimer=DISCLAIMER_FAKE_WORM,
            )

    def test_worm_confirmed_true_with_fake_disclaimer_raises(self):
        with pytest.raises(ValueError, match="is_worm_confirmed"):
            WriteReceipt(
                provider_id="id",
                provider_timestamp_utc="2026-06-28T00:00:00Z",
                immutability_expiry_utc=None,
                etag="abc",
                provider_name="REAL",
                region="us-east-1",
                is_worm_confirmed=True,
                disclaimer=DISCLAIMER_FAKE_WORM,
            )

    def test_real_disclaimer_with_worm_confirmed_true_is_valid(self):
        receipt = WriteReceipt(
            provider_id="s3-object-id-001",
            provider_timestamp_utc="2026-06-28T00:00:00Z",
            immutability_expiry_utc="2033-06-28T00:00:00Z",
            etag="etag-real",
            provider_name="AWS_S3_OBJECT_LOCK",
            region="ap-southeast-1",
            is_worm_confirmed=True,
            disclaimer=DISCLAIMER_REAL_WORM,
        )
        assert receipt.is_worm_confirmed is True


# ── FakeWormRetentionAdapter behavior ──────────────────────────────────────

class TestFakeAdapterBehavior:
    def test_write_event_returns_receipt(self):
        adapter = FakeWormRetentionAdapter()
        receipt = adapter.write_event(_sample_event())
        assert isinstance(receipt, WriteReceipt)

    def test_write_receipt_is_worm_confirmed_false(self):
        adapter = FakeWormRetentionAdapter()
        receipt = adapter.write_event(_sample_event())
        assert receipt.is_worm_confirmed is False

    def test_write_receipt_provider_name_is_fake(self):
        adapter = FakeWormRetentionAdapter()
        receipt = adapter.write_event(_sample_event())
        assert receipt.provider_name == PROVIDER_NAME_FAKE

    def test_write_receipt_disclaimer_is_simulation(self):
        adapter = FakeWormRetentionAdapter()
        receipt = adapter.write_event(_sample_event())
        assert receipt.disclaimer == DISCLAIMER_FAKE_WORM
        assert "NOT WORM" in receipt.disclaimer

    def test_read_event_returns_stored_event(self):
        adapter = FakeWormRetentionAdapter()
        event = _sample_event("evt-read-001")
        adapter.write_event(event)
        retrieved = adapter.read_event("evt-read-001")
        assert retrieved["event_id"] == "evt-read-001"
        assert retrieved["action"] == "READ_RECORD"

    def test_read_unknown_event_raises_key_error(self):
        adapter = FakeWormRetentionAdapter()
        with pytest.raises(KeyError):
            adapter.read_event("evt-does-not-exist")

    def test_verify_event_correct_hash_returns_true(self):
        adapter = FakeWormRetentionAdapter()
        event = _sample_event("evt-verify-001")
        event["audit_event_hash"] = "correct_hash_value"
        adapter.write_event(event)
        assert adapter.verify_event("evt-verify-001", "correct_hash_value") is True

    def test_verify_event_wrong_hash_returns_false(self):
        adapter = FakeWormRetentionAdapter()
        event = _sample_event("evt-verify-002")
        event["audit_event_hash"] = "correct_hash_value"
        adapter.write_event(event)
        assert adapter.verify_event("evt-verify-002", "wrong_hash") is False

    def test_verify_unknown_event_returns_false(self):
        adapter = FakeWormRetentionAdapter()
        assert adapter.verify_event("evt-nonexistent", "any_hash") is False

    def test_list_events_in_range_returns_all_stored(self):
        adapter = FakeWormRetentionAdapter()
        adapter.write_event(_sample_event("e1"))
        adapter.write_event(_sample_event("e2"))
        adapter.write_event(_sample_event("e3"))
        ids = adapter.list_events_in_range("2026-01-01T00:00:00Z", "2026-12-31T00:00:00Z")
        assert set(ids) == {"e1", "e2", "e3"}

    def test_get_retention_policy_returns_defaults(self):
        adapter = FakeWormRetentionAdapter()
        policy = adapter.get_retention_policy()
        assert isinstance(policy, RetentionPolicy)
        assert policy.default_retention_years == 7
        assert policy.clinical_retention_years == 10
        assert policy.ethics_retention_years == 15
        assert policy.compliance_mode == "COMPLIANCE"

    def test_provider_health_check_returns_true(self):
        adapter = FakeWormRetentionAdapter()
        assert adapter.provider_health_check() is True


# ── Legal hold behavior ─────────────────────────────────────────────────────

class TestLegalHoldBehavior:
    def test_create_legal_hold_succeeds(self):
        adapter = FakeWormRetentionAdapter()
        adapter.create_legal_hold("hold-001", "scope: all audit events 2026")
        assert "hold-001" in adapter.active_holds

    def test_release_legal_hold_with_authority_succeeds(self):
        adapter = FakeWormRetentionAdapter()
        adapter.create_legal_hold("hold-002", "scope: test")
        adapter.release_legal_hold("hold-002", "institutional_records_officer_ref_001")
        assert "hold-002" not in adapter.active_holds

    def test_release_legal_hold_empty_authority_raises(self):
        adapter = FakeWormRetentionAdapter()
        adapter.create_legal_hold("hold-003", "scope: test")
        with pytest.raises(ValueError, match="authority"):
            adapter.release_legal_hold("hold-003", "")

    def test_release_unknown_hold_raises(self):
        adapter = FakeWormRetentionAdapter()
        with pytest.raises(KeyError):
            adapter.release_legal_hold("hold-nonexistent", "officer")

    def test_multiple_holds_can_coexist(self):
        adapter = FakeWormRetentionAdapter()
        adapter.create_legal_hold("hold-a", "scope: a")
        adapter.create_legal_hold("hold-b", "scope: b")
        assert len(adapter.active_holds) == 2


# ── NOT_IMPLEMENTED guard and constants ────────────────────────────────────

class TestNotImplementedGuards:
    def test_prod_worm_dependency_constant(self):
        assert PROD_WORM_DEPENDENCY
        assert "NOT_IMPLEMENTED" in PROD_WORM_DEPENDENCY

    def test_prod_backup_dependency_constant(self):
        assert PROD_BACKUP_DEPENDENCY
        assert "NOT_IMPLEMENTED" in PROD_BACKUP_DEPENDENCY

    def test_prod_legal_hold_dependency_constant(self):
        assert PROD_LEGAL_HOLD_DEPENDENCY
        assert "NOT_IMPLEMENTED" in PROD_LEGAL_HOLD_DEPENDENCY

    def test_local_ledger_classification_constant(self):
        assert LOCAL_LEDGER_CLASSIFICATION
        assert "NOT_WORM" in LOCAL_LEDGER_CLASSIFICATION
        assert "TAMPER_EVIDENT" in LOCAL_LEDGER_CLASSIFICATION

    def test_fake_adapter_not_implemented_constant(self):
        assert hasattr(FakeWormRetentionAdapter, "NOT_IMPLEMENTED")
        assert FakeWormRetentionAdapter.NOT_IMPLEMENTED

    def test_no_network_imports_in_source(self):
        import research_project.audit_retention_contract as mod
        source = inspect.getsource(mod)
        forbidden = ["import boto3", "import azure", "import google.cloud",
                     "import requests", "import httpx", "import socket"]
        for lib in forbidden:
            assert lib not in source, f"Found forbidden import: {lib}"

    def test_offline_ci_env_works(self, monkeypatch):
        monkeypatch.setenv("MRAQ_OFFLINE_CI", "1")
        adapter = FakeWormRetentionAdapter()
        assert adapter.provider_health_check() is True
        receipt = adapter.write_event(_sample_event("offline-test"))
        assert receipt.is_worm_confirmed is False
