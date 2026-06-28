# R-GOV.1 Technical Baseline Confirmation

**Document:** R_GOV_1_TECHNICAL_BASELINE_CONFIRMATION.md  
**Date:** 2026-06-28  
**Status:** CONFIRMED  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## 1. Purpose

This document confirms the technical baseline against which the R-GOV.1 governance readiness pack was assembled. It provides the assessor and governance reviewers with a snapshot of the system state at the time this pack was prepared.

---

## 2. Repository state

| Parameter | Value |
|-----------|-------|
| Branch | feat/r1-1-2-design-gap-remediation |
| Latest commit at pack preparation | 2afa99d (chore: update phase status) |
| Working tree | Clean (no uncommitted changes at verification time) |
| Remote | feat/r1-1-2-design-gap-remediation |

---

## 3. Test suite result

| Metric | Value |
|--------|-------|
| Test mode | MRAQ_OFFLINE_CI=1 (offline — no network; no real data) |
| Total tests | 1049 passed / 0 failed / 5 skipped |
| Test runner | pytest |
| Warnings | 1 (non-fatal) |
| Duration | ~6.37s |
| Verified at | 2026-06-28 (session start) |

**Test files in scope for governance pack:**

| Test file | Phase | Tests |
|-----------|-------|-------|
| tests/test_r1_2_identity_contract.py | R1.2 | 29 |
| tests/test_r1_3_audit_retention_contract.py | R1.3 | 32 |
| tests/test_r2_0_synthetic_edc_core.py | R2.0 | 36 |
| tests/test_r2_0_synthetic_edc_lifecycle.py | R2.0 | 39 |
| tests/test_r4_0_ehospital_boundary.py | R4.0 | 46 |
| All other tests (R1.1, R3.0, R5.0, etc.) | Various | ~867 |

---

## 4. Manifest verification

| Parameter | Value |
|-----------|-------|
| Manifest path | runtime/manifests/agent_source_manifest.csv |
| manifest_self_check | MATCH |
| agent_count | 48 (minimum 48 required) |
| all_hash_verified | True |
| required_4_enforced_and_present | True |
| RESULT | PASS |
| Verified at | 2026-06-28 (session start) |

---

## 5. Governance baseline

| Parameter | Value |
|-----------|-------|
| Governance gate | GATE-R1.1: ACCEPTED_WITH_ACTIONS |
| Human decision | VL-GATE-R1.1-2026-002 (Dr Luân; SELF_REVIEW; 2026-06-28T05:30:28Z) |
| Authorization mode | AUTHORIZED_FOR_DESIGN_ONLY |
| Open actions | ACT-R1-01, ACT-R1-02, ACT-R1-03, ACT-R1-04, ACT-R1-05 (all OPEN) |
| Open residual risks | RR-02/AC-11 (MEDIUM), PROD-AUD-01 (OPEN), PROD-RBAC-01 (NOT IMPLEMENTED), IQ-20 (NOT CONDUCTED) |

---

## 6. Phase completion baseline

| Phase | Status | Commit | Test result |
|-------|--------|--------|------------|
| R1.1.2 | COMPLETE | e806e0e | 867/0/5 |
| R1.2 | COMPLETE | 4a65d82 | 896/0/5 |
| R1.3 | COMPLETE | 88661b9 | 928/0/5 |
| R2.0 | COMPLETE | 289c98d | 1003/0/5 |
| R3.0 | COMPLETE | 228f6ce | 1003/0/5 |
| R4.0 | COMPLETE | 830710f | 1049/0/5 |
| R5.0 | COMPLETE | bc52018 | 1049/0/5 |
| R6.0 | COMPLETE | bc52018 | 1049/0/5 |
| PROGRAM | COMPLETE | e674ee4 | 1049/0/5 |
| R-GOV.1 | IN PROGRESS | 2afa99d (baseline) | 1049/0/5 |

---

## 7. Invariants at baseline

| Item | Status |
|------|--------|
| SSO | NOT IMPLEMENTED |
| MFA | NOT IMPLEMENTED |
| Authenticated identity | NOT IMPLEMENTED |
| Production audit trail (PROD-AUD-01) | NOT IMPLEMENTED |
| Production RBAC | NOT IMPLEMENTED |
| eHospital integration | NOT IMPLEMENTED |
| Ethics approval | NOT GRANTED |
| Hospital authorization | NOT GRANTED |
| Independent qualification | NOT COMPLETED |
| Real patient-data processing | BLOCKED |
| Study activation | BLOCKED |
| Qualification | NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE |

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
