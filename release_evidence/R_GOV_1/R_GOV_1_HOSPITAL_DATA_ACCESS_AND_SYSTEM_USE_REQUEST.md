# R-GOV.1 Hospital Data Access and System Use Request

**Document:** R_GOV_1_HOSPITAL_DATA_ACCESS_AND_SYSTEM_USE_REQUEST.md  
**Date:** 2026-06-28  
**Decision ID:** HOSP-GOV-01  
**Status:** READY_FOR_EXTERNAL_REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **This is a request template — not an authorization.**  
> Hospital authorization requires institutional decision by designated authority.

---

## Section 1 — Request metadata

| Field | Value |
|-------|-------|
| Request type | Read-only research data access + local software use approval |
| PI | Dr Luân (bsluanbv175@gmail.com) |
| Study title | [TO BE CONFIRMED BY PI] |
| Institution | [TO BE CONFIRMED BY PI] |
| Date of request | 2026-06-28 (dossier preparation date) |
| Ethics reference | [NOT YET OBTAINED — pending ETH-GOV-01] |
| Data access agreement | [TO BE PREPARED WITH LEGAL] |

---

## Section 2 — Data requested from eHospital / HIS

### 2.1 Permitted read domains (whitelisted in code)

| Domain ID | Domain name | Fields expected | Purpose |
|-----------|-------------|----------------|---------|
| D01 | patient_demographics | age_at_encounter, sex, admission_date, discharge_date | Population description |
| D02 | diagnosis_codes | icd_code, diagnosis_date, diagnosis_type | Eligibility, outcomes |
| D03 | laboratory_results | test_name, test_value, test_unit, test_date, reference_range | Primary endpoints |
| D04 | medication_records | drug_name, dose, route, start_date, end_date | Exposure, confounders |
| D05 | vital_signs | measurement_type, measurement_value, measurement_unit, measurement_date | Clinical outcomes |
| D06 | procedure_codes | [PI TO CONFIRM IF NEEDED] | [PI TO JUSTIFY] |
| D07 | encounter_history | [PI TO CONFIRM IF NEEDED] | [PI TO JUSTIFY] |
| D08 | referral_records | [PI TO CONFIRM IF NEEDED] | [PI TO JUSTIFY] |

### 2.2 Blocked domains (hard-coded prohibition)

| Domain | Category | Prohibition |
|--------|---------|------------|
| patient_identifiers | Name, DOB, address, national ID, phone, email | PERMANENTLY BLOCKED in code |
| financial_records | Billing, insurance, co-payment | PERMANENTLY BLOCKED |
| imaging_studies | PACS, radiology images | PERMANENTLY BLOCKED |
| genetic_data | All genetic material | PERMANENTLY BLOCKED |
| psychosocial_notes | Psychiatric, social work notes | PERMANENTLY BLOCKED |
| biometric_data | Biometrics, fingerprint | PERMANENTLY BLOCKED |
| social_services | Social welfare records | PERMANENTLY BLOCKED |
| staff_records | Personnel data | PERMANENTLY BLOCKED |

---

## Section 3 — Pseudonymization pre-processing

Before any data leaves eHospital for Research OS:

| Step | Action | Responsibility |
|------|--------|---------------|
| 1 | Hospital assigns patient_id from HIS | Hospital IT |
| 2 | SHA-256(patient_id ‖ institutional_salt) computed | Hospital IT (pseudonymization service) |
| 3 | 64-char hex pseudo_id generated | Hospital IT |
| 4 | Salt stored in institutional key vault | Hospital IT — NOT shared with PI or Research OS |
| 5 | Extract contains only: pseudo_id + domain fields (no PII) | Hospital IT |
| 6 | Extract delivered to PI via approved secure channel | [TO BE CONFIRMED — encrypted file / institutional server] |
| 7 | Research OS loads extract; PII guard enforced at ingest | Research OS (automated) |

**Key management:** Hospital is sole key holder. Re-identification requires hospital IT involvement; PI cannot re-identify independently.

---

## Section 4 — System use request

| System | Purpose | Use scope |
|--------|---------|----------|
| Medical Research OS (local installation) | Research data management, evidence-based medicine tools | Data analysis after pseudonymized extract received |
| EBM Copilot agent system | Decision-support literature search | No patient data access; evidence only |

**NOT requesting:**
- Real-time HIS connection
- HIS write access
- Direct database access (SQL or API to production HIS)
- Access to imaging (PACS)
- Access to electronic prescribing system
- Administrative HIS functions

---

## Section 5 — Data extraction protocol

| Parameter | Specification |
|-----------|--------------|
| Extraction method | Batch export (not real-time API) |
| Extraction frequency | [ONE-TIME / PERIODIC — PI TO CONFIRM] |
| Extraction authorizer | Data Owner (HIS administrator) |
| Extraction audit | Hospital IT maintains extraction log |
| Transfer method | [SECURE — TO BE CONFIRMED WITH IT: encrypted file / VPN / institutional share] |
| Format | [CSV / JSON / HL7 FHIR — TO BE CONFIRMED WITH IT] |

---

## Section 6 — Data use limitations

| Limitation | Commitment |
|-----------|-----------|
| Use only for stated study | YES — no secondary use without separate approval |
| No re-identification | YES — key held by hospital only |
| No onward sharing | YES — no external transfer without hospital and ethics approval |
| No commercial use | YES |
| Destruction at study end | [PI TO CONFIRM TIMELINE AND METHOD] |
| Publication acknowledgment | Hospital acknowledged per hospital policy |

---

## Section 7 — Residual data risks requiring hospital confirmation

| Risk | Confirmation required from |
|------|--------------------------|
| De-identification standard adequacy | Hospital Data Protection Officer |
| Cross-linkage prevention | Hospital IT |
| Secure extraction channel | Hospital IT |
| At-rest encryption on PI workstation | PI + Hospital IT (institutional security policy) |
| Decree 13/2023 compliance | Legal / Compliance |

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
