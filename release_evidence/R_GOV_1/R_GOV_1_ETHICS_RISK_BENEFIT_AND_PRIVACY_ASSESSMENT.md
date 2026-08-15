# R-GOV.1 Ethics Risk-Benefit and Privacy Assessment

**Document:** R_GOV_1_ETHICS_RISK_BENEFIT_AND_PRIVACY_ASSESSMENT.md  
**Date:** 2026-06-28  
**Decision ID:** ETH-GOV-01  
**Status:** READY_FOR_EXTERNAL_REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **MANDATORY STATEMENT:**  
> This assessment is prepared for ethics review.  
> It is not an ethics approval.  
> The risk-benefit and privacy assessment is ultimately the responsibility  
> of the ethics committee and the institution, not of this system.

---

## Part 1 — Identified risks

### 1.1 Privacy and data protection risks

| Risk | Likelihood | Severity | Mitigation | Residual risk |
|------|-----------|---------|-----------|--------------|
| Re-identification of pseudonymized subjects | LOW | HIGH | SHA-256 pseudo_id; PII key guard enforced in code; no real-ID data enters Research OS | MEDIUM (inherent to any EHR data use) |
| Unauthorized access to research dataset | LOW | HIGH | Role-based access control (AUTHORIZED_FOR_DESIGN_ONLY — implementation PENDING) | HIGH until RBAC production deployed |
| Data breach — unauthorized disclosure | LOW | HIGH | Pseudonymization; no cloud storage of PII; local encrypted storage plan (PENDING) | HIGH until encryption confirmed |
| Linkage attack with auxiliary data | VERY LOW | HIGH | Minimum necessary data principle; domain whitelist; no direct identifiers | LOW-MEDIUM |
| Audit trail tampering | LOW | MEDIUM | Local hash-chain (TAMPER_EVIDENT_LOCAL_SIMULATION_NOT_WORM); PROD-AUD-01 OPEN | MEDIUM until WORM implemented |
| Non-compliance with Decree 13/2023 (Vietnam DPA) | UNKNOWN | HIGH | Legal review required; DPA impact assessment not yet completed | [TO BE ASSESSED BY LEGAL] |

### 1.2 Research integrity risks

| Risk | Likelihood | Severity | Mitigation |
|------|-----------|---------|-----------|
| Bias in retrospective data extraction | MODERATE | MODERATE | Pre-specified extraction protocol; blinded extraction plan [TO BE CONFIRMED] |
| Missing data bias | MODERATE | MODERATE | Missing data plan in SAP; sensitivity analysis planned |
| Selection bias (incomplete EHR records) | MODERATE | MODERATE | Data completeness audit prior to analysis |
| AI hallucination in research outputs | LOW | HIGH | All AI outputs DRAFT; require physician verification |

### 1.3 Participant-level risks

| Risk | Applicable | Notes |
|------|-----------|-------|
| Physical harm | Not applicable (retrospective observational) | No invasive procedures |
| Psychological distress | Not applicable (data study) | No contact with participants during data phase |
| Coercion | Not applicable (retrospective) | No prospective enrollment |
| Loss of confidentiality | YES | See 1.1 above |
| Denial of benefit | [TO BE ASSESSED BY PI] | [If any control-arm design] |

---

## Part 2 — Anticipated benefits

| Benefit | Description | Evidence of likelihood |
|---------|------------|----------------------|
| Direct benefit to participants | Minimal to none (retrospective) | Standard for retrospective observational studies |
| Indirect benefit: knowledge generation | [TO BE CONFIRMED BY PI] | [PI to cite existing evidence gap] |
| Benefit to future patients | Potential improvement in clinical practice if evidence translated | Contingent on study quality and dissemination |
| Benefit to healthcare system | Potential EBM tool for outpatient clinics | Depends on system qualification reaching production |
| Methodological benefit | Development of reproducible EHR research infrastructure | Ongoing |

---

## Part 3 — Risk-benefit proportionality assessment

| Dimension | Assessment |
|----------|-----------|
| Is the research design the least invasive practicable? | [PI TO CONFIRM — retrospective design minimizes participant burden] |
| Are risks minimized to the extent possible? | [PI TO CONFIRM with data protection officer] |
| Do benefits outweigh risks? | [TO BE ASSESSED BY ETHICS COMMITTEE] |
| Is the population proposed appropriate (not unfairly burdened)? | [TO BE ASSESSED BY ETHICS COMMITTEE] |

**PI statement on risk-benefit:**  
> [TO BE WRITTEN BY PI AND ATTACHED]

---

## Part 4 — Privacy assessment

### 4.1 Data minimization

| Data type | Justification for inclusion | Covered by domain whitelist? |
|----------|---------------------------|------------------------------|
| Demographics (age, sex) | Required for population description and confounding | YES — `patient_demographics` |
| Diagnoses (ICD codes) | Required for eligibility and outcomes | YES — `diagnosis_codes` |
| Laboratory results | Primary/secondary endpoints | YES — `laboratory_results` |
| Medications | Exposure variable / confounders | YES — `medication_records` |
| Vital signs | Clinical outcome data | YES — `vital_signs` |
| [Other — PI to specify] | [PI to justify] | [To be confirmed] |

**Blocked domains (must not be accessed):**
```
patient_identifiers — name, DOB, address, national ID, phone, email
financial_records
imaging_studies
genetic_data
psychosocial_notes
biometric_data
social_services
staff_records
```

### 4.2 Pseudonymization protocol

| Step | Description |
|------|------------|
| 1. Real ID assigned | Hospital system assigns patient_id |
| 2. Pseudonymization | SHA-256(patient_id ‖ institutional_salt) → 64-char hex pseudo_id |
| 3. Salt storage | Institutional vault — NOT accessible to Research OS |
| 4. Extract delivery | Only pseudo_id enters Research OS; real_id stays in hospital system |
| 5. PII guard | `ExtractRecord.__post_init__` raises ValueError for any PII key |

### 4.3 Data storage and transfer

| Element | Plan |
|---------|------|
| Storage location | [TO BE CONFIRMED BY PI — local encrypted drive / institutional server] |
| Encryption at rest | [TO BE CONFIRMED — plan PENDING] |
| Transfer method | [TO BE CONFIRMED — no unencrypted transfer of pseudonymized data] |
| Access control | Role-based (PENDING implementation — see HOSP-GOV-01 pack) |
| Backup | [TO BE CONFIRMED BY PI] |
| Destruction plan | [TO BE CONFIRMED BY PI — secure deletion at study end] |

### 4.4 Decree 13/2023/ND-CP compliance notes

| Article | Requirement | Status |
|---------|------------|--------|
| Article 11 | Lawful basis for processing | [TO BE CONFIRMED — research exemption or ethics approval] |
| Article 15 | Consent or exemption basis | [TO BE DETERMINED BY ETHICS BODY] |
| Article 20 | Data subject rights | [TO BE CONFIRMED — waiver may apply for retrospective research] |
| Article 26 | Security measures | [PENDING — encryption, access control] |
| Article 43 | Data Protection Impact Assessment (DPIA) | [TO BE COMPLETED BY PI + DATA PROTECTION OFFICER] |

---

## Part 5 — Assessment summary for ethics committee

| Dimension | PI Assessment | Ethics Committee Assessment |
|----------|--------------|----------------------------|
| Risk level | MODERATE — primarily privacy risk | [TO BE ASSESSED] |
| Benefit level | MODERATE — knowledge generation | [TO BE ASSESSED] |
| Proportionality | [PI TO CONFIRM] | [TO BE ASSESSED] |
| Privacy safeguards adequate | [PI TO CONFIRM] | [TO BE ASSESSED] |
| Consent/waiver pathway | See R_GOV_1_CONSENT_OR_WAIVER_ASSESSMENT_TEMPLATE.md | [TO BE DETERMINED] |
| Recommendation | [PI TO STATE] | [TO BE DETERMINED BY COMMITTEE] |

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
