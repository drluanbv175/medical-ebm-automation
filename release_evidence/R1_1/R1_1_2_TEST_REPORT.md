# R1.1.2 Test Report

**Document:** R1_1_2_TEST_REPORT.md  
**Date:** 2026-06-28  
**Phase:** R1.1.2 — Phase F  
**Branch:** feat/r1-1-2-design-gap-remediation  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## 1. Suite run summary

| Hạng mục | Kết quả |
|---------|--------|
| Command | `MRAQ_OFFLINE_CI=1 pytest --tb=short -q` |
| Total passed | **867** |
| Total failed | **0** |
| Total skipped | **5** (pre-existing, unrelated to R1.1.2) |
| Total warnings | 1 (urllib3/OpenSSL version mismatch — không ảnh hưởng test logic) |
| R1.1 baseline (r1.1-frozen) | 836 passed |
| R1.1.2 new tests | 31 passed |
| Network calls | 0 |
| PII in fixtures | 0 |

---

## 2. R1.1.2 test file

**File:** `tests/test_r1_1_2_gap_remediation.py`  
**Test classes:** 8  
**Test count:** 31

| Class | Tests | Gap(s) covered |
|-------|-------|---------------|
| `TestG01_CLI_Subprocess` | 4 | G-01 |
| `TestG02_ForbiddenActionDedicated` | 3 | G-02 |
| `TestG03_SysAdminLockResearchData` | 2 | G-03 |
| `TestWORM_Truthfulness` | 4 | RR-02/AC-11 — truthfulness |
| `TestWORM_TamperDetection` | 6 | RR-02/AC-11 — tamper scenarios |
| `TestWORM_CheckpointAndRootHash` | 2 | RR-02/AC-11 — root hash + checkpoint |
| `TestDEL_ReasonCodes` | 8 | DEL-REASON |
| `TestINV_Invariants` | 2 | Invariants (no network, synthetic markers) |

---

## 3. T14 fix (G-04)

| File | Change |
|------|--------|
| `tests/test_r1_1_offline_rbac_synthetic_identity.py` | T14 assertion tightened from `reason_code in (EXPIRED_ROLE, ROLE_NOT_PERMITTED)` → `reason_code == EXPIRED_ROLE` |
| Passes after fix | Yes — T14 passes with 836 baseline |
| Basis | Code reading: `evaluate_rbac()` line 424–425 definitively returns `EXPIRED_ROLE` for `active_roles=[]` |

---

## 4. Failures during development and fixes applied

| Failure | Root cause | Fix applied |
|---------|-----------|------------|
| G-01 (4 tests) | `subprocess.run([..., "research_project/project_cli.py"])` causes `ImportError: attempted relative import` | Changed to `-m research_project.project_cli` module invocation |
| WORM-01 | Test reason string `"WORM truthfulness test"` contained "worm"; assertion `"worm" not in json.dumps(d).lower()` was too broad (matched `NOT_WORM` in classification) | Changed reason string to neutral; assertion now checks specific positive claim strings (`worm_storage`, `worm_compliant`, `is_worm`) per field |
| WORM-12 | `ledger_root_hash()` used stored `audit_event_hash` values; content modification without changing stored hash didn't change root hash | Changed `ledger_root_hash()` to call `compute_event_hash(ev)` (recompute) instead of `ev.get("audit_event_hash")` |

---

## 5. Source changes summary

| File | Changes |
|------|---------|
| `research_project/project_audit_attribution.py` | Module label; WORM constants; `sequence_number` field; enhanced `verify_hash_chain()`; updated `record()`; `ledger_root_hash()` (recompute); `create_checkpoint()` |
| `research_project/project_delegation_registry.py` | `DelegationReasonCode` enum; `DelegationDecision` dataclass; `evaluate_delegation_action()` function |
| `tests/test_r1_1_offline_rbac_synthetic_identity.py` | T14 assertion fix (G-04) |
| `tests/test_r1_1_2_gap_remediation.py` | NEW — 31 tests across 8 classes |

---

## 6. Hermetic flags confirmed

- `MRAQ_OFFLINE_CI=1` set for all runs
- No `requests`, `httpx`, `urllib.request` imported in tested modules (INV-01)
- No PII in any fixture
- All `is_synthetic=True`, `production_valid=False` (INV-02)

---

## 7. Items not closed by R1.1.2

| Item | Status | Reason |
|------|--------|--------|
| PROD-AUD-01 | DEFERRED_TO_PRODUCTION_QUALIFICATION | Requires R1.3 WORM infrastructure |
| Replace-then-rehash attack | MEDIUM residual — not testable offline | By definition requires external write access |
| Production RBAC enforcement | DEFERRED | Requires R1.3 SSO |
| Independent pentest (IQ-20) | DEFERRED | Requires R1.5 external tester |

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
