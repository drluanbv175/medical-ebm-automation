# R5.0 Qualification Test Plan

**Document:** R5_0_QUALIFICATION_TEST_PLAN.md  
**Date:** 2026-06-28  
**Phase:** R5.0  
**Status:** TEST PLAN DESIGN — NOT EXECUTED EXTERNALLY  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Purpose

Define the test plan that an independent assessor would execute to qualify the Research OS. This plan cannot be self-executed by the development team — execution must be by an external, independent party.

---

## 1. IQ test scripts (Installation)

| Test ID | Description | Expected result |
|---------|-------------|----------------|
| IQ-T01 | Verify Python version ≥ 3.11 | Pass |
| IQ-T02 | Verify all requirements.txt dependencies installed | Pass |
| IQ-T03 | Verify venv outside OneDrive path | Pass |
| IQ-T04 | Verify .env not committed to git | Pass |
| IQ-T05 | Verify no secrets in source files | Pass |
| IQ-T06 | Verify git history integrity (signed commits) | TBD |
| IQ-T07 | Verify MRAQ_OFFLINE_CI=1 disables all network calls | Pass |

---

## 2. OQ test scripts (Operational)

| Test ID | Description | Expected result |
|---------|-------------|----------------|
| OQ-T01 | RBAC role assignment enforces permissions | Pass (offline suite) |
| OQ-T02 | Audit log entry created for every mutation | Pass (offline suite) |
| OQ-T03 | WORM provider interface correctly abstracted | Pass (offline suite) |
| OQ-T04 | EDC record lifecycle DRAFT→FROZEN→LOCKED | Pass (offline suite) |
| OQ-T05 | Export fails if any record not LOCKED | Pass (offline suite) |
| OQ-T06 | Query cannot be closed without answer | Pass (offline suite) |
| OQ-T07 | Correction without reason raises error | Pass (offline suite) |
| OQ-T08 | eHospital boundary has zero write methods | Pass (offline suite) |
| OQ-T09 | PII keys rejected in ExtractRecord | Pass (offline suite) |
| OQ-T10 | Ethics approval required for extract request | Pass (offline suite) |
| OQ-T11 | Production WORM adapter | NOT TESTABLE (external) |
| OQ-T12 | Production SSO/MFA adapter | NOT TESTABLE (external) |

---

## 3. PQ test scripts (Performance)

| Test ID | Description | Expected result |
|---------|-------------|----------------|
| PQ-T01 | Full suite runs in < 30s | TBD in production environment |
| PQ-T02 | Audit log scales to 10,000 entries | TBD |
| PQ-T03 | Concurrent user simulation (if applicable) | TBD |
| PQ-T04 | EDC export of 500 records completes correctly | TBD |
| PQ-T05 | eHospital boundary handles network timeout | TBD |

---

## 4. SQ test scripts (Security)

| Test ID | Description | Expected result |
|---------|-------------|----------------|
| SQ-T01 | No unauthenticated access to research data | TBD (needs production auth) |
| SQ-T02 | Session expiry enforced | TBD |
| SQ-T03 | MFA required for LOCKED record operations | TBD |
| SQ-T04 | Penetration test of eHospital boundary | EXTERNAL SECURITY TEAM |
| SQ-T05 | Audit log cannot be tampered (WORM) | EXTERNAL (production only) |

---

## Conclusion

```
Qualification test plan: DESIGN COMPLETE
IQ/OQ (offline): Partial evidence from suite (1049 passed)
PQ/SQ: NOT TESTABLE without production environment
Independent execution: REQUIRED BEFORE QUALIFICATION
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
