# Research OS — External Dependency Register

**Document:** RESEARCH_OS_EXTERNAL_DEPENDENCY_REGISTER.md  
**Date:** 2026-06-28  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

All 15 original dependencies from the completion control document plus additions identified during phases R2.0–R6.0.

---

## Category A — Identity and Authentication

| ID | Dependency | Contract constant | Phase | Status |
|----|-----------|-------------------|-------|--------|
| DEP-01 | Institutional SSO/IdP (OAuth2/OIDC/SAML) | `PROD_SSO_DEPENDENCY` | R1.2 | NOT PROVIDED |
| DEP-02 | MFA service (TOTP or hardware key) | `PROD_MFA_DEPENDENCY` | R1.2 | NOT PROVIDED |
| DEP-03 | External session store (Redis/DB) | `PROD_SESSION_STORE_DEPENDENCY` | R1.2 | NOT PROVIDED |

---

## Category B — Audit and Storage

| ID | Dependency | Contract constant | Phase | Status |
|----|-----------|-------------------|-------|--------|
| DEP-04 | WORM-capable cloud/on-prem storage (AWS S3 Object Lock / Azure Immutable Blob / GCP WORM) | `PROD_WORM_DEPENDENCY` | R1.3 | NOT PROVIDED |
| DEP-05 | Off-system backup service (cross-region, tested restore) | `PROD_BACKUP_DEPENDENCY` | R1.3 | NOT PROVIDED |
| DEP-06 | Institutional legal hold management system | `PROD_LEGAL_HOLD_DEPENDENCY` | R1.3 | NOT PROVIDED |

---

## Category C — EDC

| ID | Dependency | Contract constant | Phase | Status |
|----|-----------|-------------------|-------|--------|
| DEP-07 | Production EDC system (REDCap / Castor / Medidata Rave) — validated per 21 CFR Part 11 or equivalent | `PROD_EDC_DEPENDENCY` | R2.0 | NOT PROVIDED |

---

## Category D — Ethics and Regulatory

| ID | Dependency | Phase | Status |
|----|-----------|-------|--------|
| DEP-08 | IRB/Ethics Committee approval letter (written, with reference number) | R3.0 | NOT OBTAINED |
| DEP-09 | Trial registration (ClinicalTrials.gov / WHO ICTRP / national registry) | R3.0 | NOT DONE |
| DEP-10 | Regulatory authority notification (if required under Vietnamese law) | R3.0 | NOT DONE |

---

## Category E — eHospital Integration

| ID | Dependency | Contract constant | Phase | Status |
|----|-----------|-------------------|-------|--------|
| DEP-11 | eHospital/HIS read-only API endpoint (authenticated, approved domains only) | `PROD_EHOSPITAL_DEPENDENCY` | R4.0 | NOT PROVIDED |
| DEP-12 | Service account credentials with read-only scope | `PROD_EHOSPITAL_AUTH_DEPENDENCY` | R4.0 | NOT PROVIDED |
| DEP-13 | Pseudonymization key vault (HSM or institutional key management) | `PROD_PSEUDONYMIZATION_DEPENDENCY` | R4.0 | NOT PROVIDED |
| DEP-14 | Network/VPN access to HIS | — | R4.0 | NOT PROVIDED |
| DEP-15 | Data access agreement (DAA) and data transfer agreement (DTA) | — | R4.0 | NOT SIGNED |

---

## Category F — Qualification

| ID | Dependency | Phase | Status |
|----|-----------|-------|--------|
| DEP-16 | Independent qualified assessor (IQ/OQ/PQ/SQ) | R5.0 | NOT ENGAGED |
| DEP-17 | Validation master plan (VMP) — co-authored with assessor | R5.0 | NOT WRITTEN |
| DEP-18 | Formal qualification report from independent assessor | R5.0 | NOT ISSUED |

---

## Summary

| Category | Total | Resolved | Open |
|---------|-------|----------|------|
| A — Identity | 3 | 0 | 3 |
| B — Storage | 3 | 0 | 3 |
| C — EDC | 1 | 0 | 1 |
| D — Ethics | 3 | 0 | 3 |
| E — eHospital | 5 | 0 | 5 |
| F — Qualification | 3 | 0 | 3 |
| **TOTAL** | **18** | **0** | **18** |

**18 external dependencies — all OPEN.**

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
