# R-GOV.1 Security and Technical Qualification Scope

**Document:** R_GOV_1_SECURITY_AND_TECHNICAL_QUALIFICATION_SCOPE.md  
**Date:** 2026-06-28  
**Decision ID:** IQ-GOV-01  
**Status:** READY_FOR_EXTERNAL_REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **Independent qualification is not established by this dossier.**  
> This document defines the technical qualification scope for the independent assessor.

---

## Part 1 — Qualification domain map

| Domain ID | Domain name | Phase evidence | In scope now? | Reason if out of scope |
|-----------|-------------|---------------|--------------|----------------------|
| QS-01 | Offline RBAC policy engine | R1.1 | YES | Implemented and tested |
| QS-02 | Separation of duties (SoD) | R1.1 | YES | Implemented and tested |
| QS-03 | Delegation controls | R1.1 | YES | Implemented and tested |
| QS-04 | Tamper-evident audit chain (local) | R1.1 | YES — with limitations | Local simulation only; NOT WORM |
| QS-05 | Identity adapter contract | R1.2 | YES | Design/contract; NOT_IMPLEMENTED declared |
| QS-06 | Authentication context | R1.2 | YES — limited | SyntheticIdentityAdapter only; no real SSO |
| QS-07 | Audit retention contract | R1.3 | YES | WriteReceipt fake-WORM guard; NOT_IMPLEMENTED declared |
| QS-08 | Retention policy definition | R1.3 | YES | 7/10/15-year defaults defined |
| QS-09 | Synthetic EDC — CRF versioning | R2.0 | YES | Implemented and tested |
| QS-10 | Synthetic EDC — record lifecycle | R2.0 | YES | DRAFT/ACTIVE/FROZEN/LOCKED states tested |
| QS-11 | Synthetic EDC — query lifecycle | R2.0 | YES | OPEN/ANSWERED/CLOSED/CANCELLED tested |
| QS-12 | Synthetic EDC — export gating | R2.0 | YES | LOCKED-only export enforced |
| QS-13 | Synthetic EDC — correction management | R2.0 | YES | Reason mandatory enforced |
| QS-14 | Synthetic EDC — deviation registry | R2.0 | YES | Corrective action mandatory |
| QS-15 | eHospital boundary contract — domain whitelist | R4.0 | YES | Design/contract tested |
| QS-16 | eHospital boundary contract — PII key guard | R4.0 | YES | Enforced at `ExtractRecord.__post_init__` |
| QS-17 | eHospital boundary contract — zero-write | R4.0 | YES | No write methods in interface |
| QS-18 | Pseudonymization design | R4.0 | YES — design only | SHA-256 design; not real HIS connected |
| QS-19 | Production WORM audit trail | R1.3 | NO | PROD-AUD-01 OPEN; not implemented |
| QS-20 | Production SSO/MFA | R1.2 | NO | NOT IMPLEMENTED |
| QS-21 | Production RBAC service | R1.3 | NO | NOT IMPLEMENTED |
| QS-22 | eHospital network integration | R4.0 | NO | NOT IMPLEMENTED |
| QS-23 | Encryption at rest | — | NO | NOT CONFIRMED |
| QS-24 | Independent security penetration test | — | NO | NOT CONDUCTED (ACT-R1-05) |
| QS-25 | Clinical effectiveness validation | — | NO | Beyond qualification scope |

---

## Part 2 — Security qualification details

### 2.1 Access control (in-scope QS-01/02/03/06)

| Control | Evidence | Test coverage | Limitation |
|---------|---------|--------------|-----------|
| Role assignment | R1.1 RBAC engine | Covered | Offline test only |
| Permission enforcement | R1.1 policy engine | Covered | Offline; not production runtime |
| SoD dual-role prohibition | R1.1 SoD module | Covered | Offline |
| Delegation depth limits | R1.1 delegation controls | Covered | Offline |
| MFA enforcement | R1.2 identity adapter | NOT IMPLEMENTED | SyntheticIdentityAdapter.mfa_satisfied always False |
| SSO token validation | R1.2 identity adapter | NOT IMPLEMENTED | No real IdP connected |
| Session management | — | NOT IMPLEMENTED | No real session store |

### 2.2 Audit trail (in-scope QS-04/07/08; out-of-scope QS-19)

| Property | Status | Evidence |
|---------|--------|---------|
| Local hash-chain integrity | Implemented | R1.1 audit chain tests |
| Tamper detection (modify entry) | Implemented | `verify_hash_chain()` detects modification |
| WORM/immutable storage | NOT IMPLEMENTED | PROD-AUD-01 OPEN; `LOCAL_LEDGER_CLASSIFICATION = "TAMPER_EVIDENT_LOCAL_SIMULATION_NOT_WORM"` |
| Production audit attribution | NOT IMPLEMENTED | No real identity link |
| Replace-then-rehash residual risk | OPEN | RR-02 / AC-11 MEDIUM; requires WORM to close |
| Retention policy | Defined (design) | 7/10/15-year constants in code; not enforced in production |

### 2.3 Data protection (in-scope QS-15/16/17/18)

| Control | Status | Evidence |
|---------|--------|---------|
| Domain whitelist enforcement | Implemented | `PERMITTED_READ_DOMAINS` frozenset; `ExtractRequest` rejects others |
| Domain blocklist enforcement | Implemented | `BLOCKED_READ_DOMAINS` frozenset; `ExtractRequest` rejects blocked |
| PII key guard | Implemented | `ExtractRecord.__post_init__` raises `ValueError` on PII keys |
| No-write interface | Implemented | Zero write methods in `EHospitalReadOnlyBoundaryInterface` |
| Pseudonymization | Design only | SHA-256 contract defined; no real HIS |
| Ethics prerequisite | Enforced | `ExtractRequest.__post_init__` requires non-empty `ethics_approval_ref` |

---

## Part 3 — NOT_IMPLEMENTED constants (assessor to verify)

The following constants must be non-empty strings in the source code. The assessor must verify:

| Constant | Module | Expected content |
|---------|--------|----------------|
| `PROD_SSO_DEPENDENCY` | `identity_adapter_contract.py` | Non-empty; states NOT_IMPLEMENTED |
| `PROD_MFA_DEPENDENCY` | `identity_adapter_contract.py` | Non-empty; states NOT_IMPLEMENTED |
| `PROD_SESSION_STORE_DEPENDENCY` | `identity_adapter_contract.py` | Non-empty; states NOT_IMPLEMENTED |
| `PROD_AUD_01_WORM_DEPENDENCY` | `audit_retention_contract.py` | Non-empty; states NOT_IMPLEMENTED |
| `LOCAL_LEDGER_CLASSIFICATION` | `audit_retention_contract.py` | Contains "TAMPER_EVIDENT_LOCAL_SIMULATION_NOT_WORM" |
| `PROD_EHOSPITAL_CONNECTION_DEPENDENCY` | `ehospital_boundary_contract.py` | Non-empty; states NOT_IMPLEMENTED |

---

## Part 4 — Assessor verification checklist

| Check | Method | Expected result |
|-------|--------|----------------|
| Test suite runs cleanly | `MRAQ_OFFLINE_CI=1 pytest --tb=short -q` | 1049 passed / 0 failed |
| Manifest PASS | `python3 scripts/verify_manifest_registry.py` | all_hash_verified=True; agent_count=48 |
| No prohibited states in any document | grep for AUTO_APPROVED/AI_APPROVED/SYSTEM_APPROVED | 0 matches |
| No WORM/immutable claim | grep for "is_worm_confirmed=True" outside test expecting ValueError | 0 valid matches |
| NOT_IMPLEMENTED constants non-empty | Code review | All present and non-empty |
| WriteReceipt fake-WORM guard | `audit_retention_contract.py` | `__post_init__` raises `ValueError` if `is_worm_confirmed=True` |
| Zero-write interface | Count write/update/delete methods in `EHospitalReadOnlyBoundaryInterface` | 0 |
| PII key guard | Review 18-item blocklist in `ExtractRecord.__post_init__` | All 18 present |

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
