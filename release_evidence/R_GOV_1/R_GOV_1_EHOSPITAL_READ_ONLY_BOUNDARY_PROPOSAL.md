# R-GOV.1 eHospital Read-Only Boundary Proposal

**Document:** R_GOV_1_EHOSPITAL_READ_ONLY_BOUNDARY_PROPOSAL.md  
**Date:** 2026-06-28  
**Decision ID:** HOSP-GOV-01  
**Status:** READY_FOR_EXTERNAL_REVIEW  
**Source module:** `research_project/ehospital_boundary_contract.py` (R4.0)  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **MANDATORY STATEMENT:**  
> This pack is a preparation dossier for institutional review.  
> It is not hospital authorization.  
> eHospital integration is NOT IMPLEMENTED.  
> The boundary described here is a design proposal only.

---

## Part 1 — Boundary design summary

The Medical Research OS implements a strict read-only boundary contract for any future eHospital integration. This boundary is enforced in code and cannot be overridden without source modification.

| Property | Design |
|---------|--------|
| Write/update/delete to eHospital | ZERO — interface has no write methods |
| Read scope | Whitelisted domains only (8 permitted) |
| Blocked domains | 8 permanently blocked categories |
| Access prerequisite | `ethics_approval_ref` must be non-empty (enforced by `ExtractRequest.__post_init__`) |
| Pseudonymization | Required before any record enters Research OS |
| PII guard | `ExtractRecord.__post_init__` raises `ValueError` on any PII key name |
| Implementation status | NOT IMPLEMENTED — design/contract only |

---

## Part 2 — Permitted read domains (whitelisted — `PERMITTED_READ_DOMAINS`)

| Domain | Justification |
|--------|--------------|
| `patient_demographics` | Population description; age, sex, encounter dates only |
| `diagnosis_codes` | ICD codes for eligibility and outcomes |
| `laboratory_results` | Primary/secondary endpoint data |
| `medication_records` | Exposure variables and confounders |
| `vital_signs` | Clinical outcomes |
| `procedure_codes` | Secondary outcome data |
| `encounter_history` | Timeline and follow-up data |
| `referral_records` | Care pathway data |

Any domain not in this list is rejected with `ValueError` at request time.

---

## Part 3 — Blocked domains (`BLOCKED_READ_DOMAINS`)

| Domain | Category blocked |
|--------|----------------|
| `patient_identifiers` | Name, DOB, address, national ID, phone, email, MRN |
| `financial_records` | Billing, insurance, co-payment |
| `imaging_studies` | PACS, radiology images, pathology images |
| `genetic_data` | All genetic and genomic material |
| `psychosocial_notes` | Psychiatric, social work, counselling notes |
| `biometric_data` | Biometrics, fingerprint, iris scan |
| `social_services` | Social welfare, housing records |
| `staff_records` | Personnel records, staff identifiers |

Any request for a blocked domain raises `ValueError("Domain blocked: ...")` — the request is rejected entirely, not silently ignored.

---

## Part 4 — Pseudonymization contract (`PseudonymizedSubject`)

| Field | Requirement |
|-------|------------|
| `pseudo_id` | Exactly 64 hex characters (SHA-256 output) |
| `pseudo_id` format | Must match `^[0-9a-f]{64}$` — rejected otherwise |
| Real ID | Never stored in Research OS |
| Salt | Held by hospital only; not accessible to Research OS or PI |

---

## Part 5 — Extract request contract (`ExtractRequest`)

| Validation | Enforcement |
|-----------|------------|
| `ethics_approval_ref` non-empty | `ValueError` if empty or None |
| `requested_domains` must be subset of `PERMITTED_READ_DOMAINS` | `ValueError` if any blocked/unknown domain |
| `requested_domains` cannot be empty | `ValueError` if empty list |
| Pseudonymized subject required | `PseudonymizedSubject` with valid pseudo_id |

---

## Part 6 — Interface zero-write guarantee (`EHospitalReadOnlyBoundaryInterface`)

The abstract interface provides ZERO write/update/delete methods:

| Method type | Count |
|------------|-------|
| `extract_records` (read) | 1 |
| Write methods | 0 |
| Update methods | 0 |
| Delete methods | 0 |
| Admin methods | 0 |

Test `test_interface_has_no_write_methods` verifies this property automatically.

---

## Part 7 — What is NOT implemented (design proposal gaps)

| Gap | Status | Required before real eHospital access |
|-----|--------|--------------------------------------|
| Real eHospital API connection | NOT IMPLEMENTED | YES |
| Real SAML/OIDC authentication to HIS | NOT IMPLEMENTED | YES |
| Real network layer (TLS, VPN) | NOT IMPLEMENTED | YES |
| Real-time audit log of HIS calls | NOT IMPLEMENTED | YES |
| Data Agreement with hospital IT | NOT SIGNED | YES |
| Hospital authorization (HOSP-GOV-01) | NOT OBTAINED | YES |
| Ethics approval (ETH-GOV-01) | NOT OBTAINED | YES |

---

## Part 8 — Proposed hospital agreement items

| Item | Proposed text |
|------|--------------|
| Read-only guarantee | "Research OS may only call read endpoints; write/update/delete to HIS are architecturally prohibited" |
| Domain restriction | "Access limited to 8 approved domains; blocked domains enforced by code" |
| Pseudonymization | "Hospital IT performs pseudonymization before data transfer; Research OS never receives real IDs" |
| Audit | "Hospital IT maintains log of all extract requests; Research OS maintains local access log" |
| Termination | "Data access immediately terminated upon study completion or ethics withdrawal" |

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*eHospital integration: NOT IMPLEMENTED*  
*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
