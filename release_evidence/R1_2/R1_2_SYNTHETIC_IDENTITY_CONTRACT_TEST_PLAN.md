# R1.2 Synthetic Identity Contract Test Plan

**Document:** R1_2_SYNTHETIC_IDENTITY_CONTRACT_TEST_PLAN.md  
**Date:** 2026-06-28  
**Phase:** R1.2 — Design Only  
**Status:** TEST PLAN — Offline synthetic tests only  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Purpose

Define the contract tests that verify the `identity_adapter_contract.py` module behaves correctly in the offline synthetic harness. These tests verify the INTERFACE CONTRACT — not a real SSO implementation. No real credentials, real SSO providers, or real sessions are used.

---

## 1. Test scope

| Scope | Status |
|-------|--------|
| `IdentityProviderAdapterInterface` — shape and required methods | INCLUDED |
| `AuthenticationContext` — field validation contract | INCLUDED |
| `AuthenticationContextContract` — all 9 field rules | INCLUDED |
| `SyntheticIdentityAdapter` — offline synthetic adapter for testing | INCLUDED |
| Real SSO provider integration | EXCLUDED — external dependency |
| Real MFA token validation | EXCLUDED — external dependency |
| Real session store operations | EXCLUDED — external dependency |

---

## 2. Test plan by requirement category

### 2.1 Interface shape tests

| Test ID | Description | Expected result |
|---------|-------------|----------------|
| TC-R12-01 | `IdentityProviderAdapterInterface` is importable as abstract class | Pass without error |
| TC-R12-02 | Interface has required methods: authenticate, validate_session, revoke_session, get_user_roles, is_mfa_satisfied | All 5 methods present |
| TC-R12-03 | Instantiating interface directly raises TypeError (abstract) | TypeError raised |
| TC-R12-04 | `SyntheticIdentityAdapter` implements all interface methods | No abstract method error |
| TC-R12-05 | `SyntheticIdentityAdapter.authenticate()` returns `AuthenticationContext` | Type matches |

### 2.2 AuthenticationContext validation tests

| Test ID | Description | Expected result |
|---------|-------------|----------------|
| TC-R12-10 | Valid context with all 9 fields passes validation | VALID |
| TC-R12-11 | Empty `actor_id` raises ValueError | ValueError |
| TC-R12-12 | Empty `email_hash` raises ValueError | ValueError |
| TC-R12-13 | Empty `roles` list raises ValueError | ValueError |
| TC-R12-14 | Empty `session_id` raises ValueError | ValueError |
| TC-R12-15 | `expires_at_utc` ≤ `issued_at_utc` raises ValueError | ValueError |
| TC-R12-16 | `attribution_mode` = AUTHENTICATED with `mfa_satisfied`=False raises ValueError | ValueError |
| TC-R12-17 | `attribution_mode` = SYNTHETIC allows `mfa_satisfied`=False | VALID |
| TC-R12-18 | `disclaimer` is present in SYNTHETIC context | Non-empty string |
| TC-R12-19 | `attribution_mode` not in {AUTHENTICATED, SYNTHETIC} raises ValueError | ValueError |

### 2.3 NOT_IMPLEMENTED guard tests

| Test ID | Description | Expected result |
|---------|-------------|----------------|
| TC-R12-20 | `SyntheticIdentityAdapter` has `NOT_IMPLEMENTED` constant | Constant present |
| TC-R12-21 | `SyntheticIdentityAdapter.is_mfa_satisfied()` always returns False | False |
| TC-R12-22 | Synthetic context has `attribution_mode = SYNTHETIC` not AUTHENTICATED | SYNTHETIC |
| TC-R12-23 | `identity_adapter_contract.PROD_SSO_DEPENDENCY` constant is present | Present |
| TC-R12-24 | `identity_adapter_contract.PROD_MFA_DEPENDENCY` constant is present | Present |

### 2.4 No-network guard tests

| Test ID | Description | Expected result |
|---------|-------------|----------------|
| TC-R12-30 | `SyntheticIdentityAdapter` contains no HTTP/socket calls | No network in source |
| TC-R12-31 | Module imports no `requests`, `httpx`, `urllib`, `socket` | ImportError not raised; no net deps |
| TC-R12-32 | Running tests with `MRAQ_OFFLINE_CI=1` does not trigger any network call | Pass in CI mode |

---

## 3. Test implementation location

**Source:** `tests/test_r1_2_identity_contract.py`  
**Run command:** `MRAQ_OFFLINE_CI=1 pytest tests/test_r1_2_identity_contract.py -v`

---

## 4. Pass criteria

- All test cases TC-R12-01 through TC-R12-32 must PASS
- 0 tests FAILED
- No network calls triggered
- No real credentials loaded
- `NOT_IMPLEMENTED` and `PROD_*_DEPENDENCY` constants present and non-empty

---

## 5. Non-pass actions

| Failure type | Action |
|------------|--------|
| Test FAILED | Fix source code; re-run; do NOT modify tests to pass around the failure |
| Network call detected | Remove network call immediately; this is a scope violation |
| Real credential loaded | Remove immediately; destroy credential if accidentally committed |
| `NOT_IMPLEMENTED` missing | Add constant; re-run |

---

## Conclusion

```
Institutional SSO: DESIGN ONLY
MFA: DESIGN ONLY
Authenticated production identity: NOT IMPLEMENTED
Contract tests: OFFLINE SYNTHETIC ONLY
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
