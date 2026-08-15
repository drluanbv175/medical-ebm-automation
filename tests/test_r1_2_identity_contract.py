"""
R1.2 Synthetic Identity Contract Tests.

Kiểm tra giao diện và hợp đồng identity_adapter_contract.py trong harness offline.
KHÔNG kết nối SSO/MFA/session store thật.
Chạy: MRAQ_OFFLINE_CI=1 pytest tests/test_r1_2_identity_contract.py -v
"""

import importlib
import inspect
import sys

import pytest

from research_project.identity_adapter_contract import (
    ATTRIBUTION_MODE_AUTHENTICATED,
    ATTRIBUTION_MODE_SYNTHETIC,
    DISCLAIMER_SYNTHETIC,
    PROD_MFA_DEPENDENCY,
    PROD_SESSION_STORE_DEPENDENCY,
    PROD_SSO_DEPENDENCY,
    AuthenticationContext,
    IdentityProviderAdapterInterface,
    SyntheticIdentityAdapter,
)

# ── Helpers ────────────────────────────────────────────────────────────────

def _valid_synthetic_context(**overrides) -> AuthenticationContext:
    defaults = dict(
        actor_id="actor_abc123",
        email_hash="a" * 64,
        roles=["RESEARCHER"],
        session_id="sess-001",
        issued_at_utc="2026-06-28T00:00:00Z",
        expires_at_utc="2026-06-28T08:00:00Z",
        mfa_satisfied=False,
        attribution_mode=ATTRIBUTION_MODE_SYNTHETIC,
        disclaimer=DISCLAIMER_SYNTHETIC,
    )
    defaults.update(overrides)
    return AuthenticationContext(**defaults)


# ── TC-R12-01 to TC-R12-05: Interface shape ────────────────────────────────

class TestInterfaceShape:
    def test_r12_01_interface_importable(self):
        """TC-R12-01: IdentityProviderAdapterInterface is importable."""
        assert IdentityProviderAdapterInterface is not None

    def test_r12_02_interface_has_required_methods(self):
        """TC-R12-02: Interface has all 5 required abstract methods."""
        required = {"authenticate", "validate_session", "revoke_session",
                    "get_user_roles", "is_mfa_satisfied"}
        abstract_methods = set(getattr(IdentityProviderAdapterInterface, "__abstractmethods__", set()))
        assert required == abstract_methods

    def test_r12_03_interface_cannot_be_instantiated(self):
        """TC-R12-03: Instantiating interface directly raises TypeError."""
        with pytest.raises(TypeError):
            IdentityProviderAdapterInterface()

    def test_r12_04_synthetic_adapter_implements_interface(self):
        """TC-R12-04: SyntheticIdentityAdapter implements all interface methods."""
        adapter = SyntheticIdentityAdapter()
        assert isinstance(adapter, IdentityProviderAdapterInterface)

    def test_r12_05_authenticate_returns_authentication_context(self):
        """TC-R12-05: SyntheticIdentityAdapter.authenticate() returns AuthenticationContext."""
        adapter = SyntheticIdentityAdapter(roles=["RESEARCHER"])
        ctx = adapter.authenticate("any_token")
        assert isinstance(ctx, AuthenticationContext)


# ── TC-R12-10 to TC-R12-19: AuthenticationContext validation ───────────────

class TestAuthenticationContextValidation:
    def test_r12_10_valid_context_passes(self):
        """TC-R12-10: Valid context with all 9 fields passes validation."""
        ctx = _valid_synthetic_context()
        assert ctx.actor_id == "actor_abc123"

    def test_r12_11_empty_actor_id_raises(self):
        """TC-R12-11: Empty actor_id raises ValueError."""
        with pytest.raises(ValueError, match="actor_id"):
            _valid_synthetic_context(actor_id="")

    def test_r12_12_empty_email_hash_raises(self):
        """TC-R12-12: Empty email_hash raises ValueError."""
        with pytest.raises(ValueError, match="email_hash"):
            _valid_synthetic_context(email_hash="")

    def test_r12_13_empty_roles_raises(self):
        """TC-R12-13: Empty roles list raises ValueError."""
        with pytest.raises(ValueError, match="roles"):
            _valid_synthetic_context(roles=[])

    def test_r12_14_empty_session_id_raises(self):
        """TC-R12-14: Empty session_id raises ValueError."""
        with pytest.raises(ValueError, match="session_id"):
            _valid_synthetic_context(session_id="")

    def test_r12_15_expires_before_issued_raises(self):
        """TC-R12-15: expires_at_utc ≤ issued_at_utc raises ValueError."""
        with pytest.raises(ValueError, match="expires_at_utc"):
            _valid_synthetic_context(
                issued_at_utc="2026-06-28T08:00:00Z",
                expires_at_utc="2026-06-28T00:00:00Z",
            )

    def test_r12_16_authenticated_without_mfa_raises(self):
        """TC-R12-16: AUTHENTICATED mode with mfa_satisfied=False raises ValueError."""
        with pytest.raises(ValueError, match="mfa_satisfied"):
            _valid_synthetic_context(
                attribution_mode=ATTRIBUTION_MODE_AUTHENTICATED,
                mfa_satisfied=False,
            )

    def test_r12_17_synthetic_allows_mfa_false(self):
        """TC-R12-17: SYNTHETIC mode allows mfa_satisfied=False."""
        ctx = _valid_synthetic_context(
            attribution_mode=ATTRIBUTION_MODE_SYNTHETIC,
            mfa_satisfied=False,
        )
        assert ctx.mfa_satisfied is False

    def test_r12_18_disclaimer_present_in_synthetic(self):
        """TC-R12-18: disclaimer is present (non-empty) in SYNTHETIC context."""
        ctx = _valid_synthetic_context()
        assert ctx.disclaimer
        assert len(ctx.disclaimer) > 0

    def test_r12_19_invalid_attribution_mode_raises(self):
        """TC-R12-19: attribution_mode not in valid set raises ValueError."""
        with pytest.raises(ValueError, match="attribution_mode"):
            _valid_synthetic_context(attribution_mode="PRODUCTION_APPROVED")


# ── TC-R12-20 to TC-R12-24: NOT_IMPLEMENTED guards ─────────────────────────

class TestNotImplementedGuards:
    def test_r12_20_synthetic_adapter_has_not_implemented_constant(self):
        """TC-R12-20: SyntheticIdentityAdapter.NOT_IMPLEMENTED constant present."""
        assert hasattr(SyntheticIdentityAdapter, "NOT_IMPLEMENTED")
        assert SyntheticIdentityAdapter.NOT_IMPLEMENTED

    def test_r12_21_is_mfa_satisfied_always_false(self):
        """TC-R12-21: SyntheticIdentityAdapter.is_mfa_satisfied() always False."""
        adapter = SyntheticIdentityAdapter()
        for session_id in ["sess-a", "sess-b", "", "any_id"]:
            assert adapter.is_mfa_satisfied(session_id) is False

    def test_r12_22_synthetic_adapter_attribution_mode_is_synthetic(self):
        """TC-R12-22: SyntheticIdentityAdapter.authenticate() returns SYNTHETIC mode."""
        adapter = SyntheticIdentityAdapter(roles=["RESEARCHER"])
        ctx = adapter.authenticate("token")
        assert ctx.attribution_mode == ATTRIBUTION_MODE_SYNTHETIC
        assert ctx.attribution_mode != ATTRIBUTION_MODE_AUTHENTICATED

    def test_r12_23_prod_sso_dependency_constant_present(self):
        """TC-R12-23: PROD_SSO_DEPENDENCY constant is present and non-empty."""
        assert PROD_SSO_DEPENDENCY
        assert "NOT_IMPLEMENTED" in PROD_SSO_DEPENDENCY

    def test_r12_24_prod_mfa_dependency_constant_present(self):
        """TC-R12-24: PROD_MFA_DEPENDENCY constant is present and non-empty."""
        assert PROD_MFA_DEPENDENCY
        assert "NOT_IMPLEMENTED" in PROD_MFA_DEPENDENCY

    def test_r12_24b_prod_session_store_constant_present(self):
        """PROD_SESSION_STORE_DEPENDENCY constant present and non-empty."""
        assert PROD_SESSION_STORE_DEPENDENCY
        assert "NOT_IMPLEMENTED" in PROD_SESSION_STORE_DEPENDENCY


# ── TC-R12-30 to TC-R12-32: No-network guard ───────────────────────────────

class TestNoNetworkGuard:
    def test_r12_30_no_http_imports_in_source(self):
        """TC-R12-30: identity_adapter_contract.py does not import network libs."""
        import research_project.identity_adapter_contract as mod
        source = inspect.getsource(mod)
        forbidden = ["import requests", "import httpx", "import urllib.request",
                     "import socket", "import http.client"]
        for lib in forbidden:
            assert lib not in source, f"Found forbidden import: {lib}"

    def test_r12_31_module_imports_succeed_without_network(self):
        """TC-R12-31: Module can be imported without any network dependency."""
        mod_name = "research_project.identity_adapter_contract"
        if mod_name in sys.modules:
            del sys.modules[mod_name]
        mod = importlib.import_module(mod_name)
        assert mod is not None

    def test_r12_32_offline_ci_env_respected(self, monkeypatch):
        """TC-R12-32: Synthetic adapter works correctly when MRAQ_OFFLINE_CI=1."""
        monkeypatch.setenv("MRAQ_OFFLINE_CI", "1")
        adapter = SyntheticIdentityAdapter(roles=["PI"])
        ctx = adapter.authenticate("offline_token")
        assert isinstance(ctx, AuthenticationContext)
        assert ctx.attribution_mode == ATTRIBUTION_MODE_SYNTHETIC


# ── Additional behavioral tests ─────────────────────────────────────────────

class TestSyntheticAdapterBehavior:
    def test_revoke_then_validate_returns_false(self):
        """Revoked session_id → validate_session returns False."""
        adapter = SyntheticIdentityAdapter()
        ctx = adapter.authenticate("test_token")
        assert adapter.validate_session(ctx.session_id) is True
        adapter.revoke_session(ctx.session_id)
        assert adapter.validate_session(ctx.session_id) is False

    def test_unrevoked_session_still_valid(self):
        """Sessions not explicitly revoked remain valid."""
        adapter = SyntheticIdentityAdapter()
        ctx = adapter.authenticate("token_a")
        ctx2 = adapter.authenticate("token_b")
        adapter.revoke_session(ctx.session_id)
        assert adapter.validate_session(ctx2.session_id) is True

    def test_get_user_roles_returns_configured_roles(self):
        """get_user_roles() returns the roles configured at adapter init."""
        adapter = SyntheticIdentityAdapter(roles=["PI", "DATA_MANAGER"])
        ctx = adapter.authenticate("t")
        roles = adapter.get_user_roles(ctx.actor_id)
        assert set(roles) == {"PI", "DATA_MANAGER"}

    def test_different_tokens_produce_different_actor_ids(self):
        """Different credential tokens produce different synthetic actor_ids."""
        adapter = SyntheticIdentityAdapter()
        ctx1 = adapter.authenticate("token_x")
        ctx2 = adapter.authenticate("token_y")
        assert ctx1.actor_id != ctx2.actor_id

    def test_authenticated_context_possible_with_mfa_true(self):
        """AUTHENTICATED context is valid when mfa_satisfied=True."""
        ctx = AuthenticationContext(
            actor_id="real_actor",
            email_hash="b" * 64,
            roles=["RESEARCHER"],
            session_id="real-sess-001",
            issued_at_utc="2026-06-28T00:00:00Z",
            expires_at_utc="2026-06-28T08:00:00Z",
            mfa_satisfied=True,
            attribution_mode=ATTRIBUTION_MODE_AUTHENTICATED,
            disclaimer="Production context",
        )
        assert ctx.mfa_satisfied is True
        assert ctx.attribution_mode == ATTRIBUTION_MODE_AUTHENTICATED
