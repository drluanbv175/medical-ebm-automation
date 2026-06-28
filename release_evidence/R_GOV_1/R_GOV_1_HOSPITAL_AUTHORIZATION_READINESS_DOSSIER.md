# R-GOV.1 Hospital Authorization Readiness Dossier

**Document:** R_GOV_1_HOSPITAL_AUTHORIZATION_READINESS_DOSSIER.md  
**Date:** 2026-06-28  
**Decision ID:** HOSP-GOV-01  
**Status:** READY_FOR_EXTERNAL_REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **MANDATORY STATEMENT:**  
> This pack is a preparation dossier for institutional review.  
> It is not hospital authorization.  
> No data access, system connection, or study activation may occur  
> based on this dossier alone.  
> Hospital authorization requires a formal decision from the designated  
> institutional authority (Director, Research Management Office, Data Owner,  
> IT Security, and Legal/Compliance).

---

## Part 1 — Request identification

| Field | Value |
|-------|-------|
| Requesting PI | Dr Luân (bsluanbv175@gmail.com) |
| Institution | [INSTITUTION NAME: TO BE CONFIRMED BY PI] |
| Department | [DEPARTMENT: TO BE CONFIRMED BY PI] |
| Study title | [TITLE: TO BE CONFIRMED BY PI] |
| Data source | eHospital / HIS — read-only |
| System to be authorized | Medical Research OS (offline software) |
| Ethics approval reference | [TO BE SUPPLIED — ETH-GOV-01 decision NOT yet obtained] |
| Requested data access period | [TO BE CONFIRMED BY PI] |

---

## Part 2 — System description

| System | Description |
|--------|-------------|
| Name | Medical Research OS |
| Type | Offline Python application (no real-time HIS connection) |
| Version | [TO BE CONFIRMED — current branch: feat/r1-1-2-design-gap-remediation] |
| Location | Local workstation / institutional network [TO BE CONFIRMED] |
| Cloud connectivity | NONE during research phase — requires institutional confirmation |
| AI component | EBM Copilot agent system — decision-support only; does NOT store patient data |
| External network access | NONE required for core research functions |

---

## Part 3 — Current system limitations (mandatory disclosure)

| Limitation | Status |
|-----------|--------|
| SSO / LDAP / SAML / OIDC | NOT IMPLEMENTED |
| Multi-factor authentication (MFA) | NOT IMPLEMENTED |
| Authenticated identity attribution | NOT IMPLEMENTED |
| Production WORM audit trail | NOT IMPLEMENTED (PROD-AUD-01 OPEN) |
| Production RBAC enforcement | NOT IMPLEMENTED |
| Encrypted storage (at-rest) | NOT IMPLEMENTED — plan PENDING |
| Certified information security management | NOT CERTIFIED |
| Qualification for research use | NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE |

These limitations must be resolved before hospital authorization can be sought.

---

## Part 4 — Requested data access

*(Detail: R_GOV_1_HOSPITAL_DATA_ACCESS_AND_SYSTEM_USE_REQUEST.md)*  
*(eHospital boundary: R_GOV_1_EHOSPITAL_READ_ONLY_BOUNDARY_PROPOSAL.md)*

| Data domain | Request | Justification |
|------------|---------|---------------|
| patient_demographics | READ ONLY | Population description, eligibility confirmation |
| diagnosis_codes | READ ONLY | Study outcome and eligibility criteria |
| laboratory_results | READ ONLY | Primary/secondary endpoints |
| medication_records | READ ONLY | Exposure variable, confounders |
| vital_signs | READ ONLY | Clinical outcome data |
| [Additional domains] | [PI TO SPECIFY] | [PI TO JUSTIFY] |

**All identifiable fields pseudonymized before entering Research OS.**  
**No write access to eHospital is requested.**

---

## Part 5 — Approvals required

| Authority | Role | Status |
|-----------|------|--------|
| Hospital Director / CEO | Institutional authorization | [NOT YET SOUGHT] |
| Research Management Office | Administrative approval | [NOT YET SOUGHT] |
| Data Owner (HIS/eHospital administrator) | Data access grant | [NOT YET SOUGHT] |
| IT Security officer | Network and security clearance | [NOT YET SOUGHT] |
| Legal / Compliance officer | Data protection review | [NOT YET SOUGHT] |
| Ethics committee (parallel) | Ethics approval prerequisite | [NOT YET OBTAINED — ETH-GOV-01 pending] |

---

## Part 6 — Data governance commitments

| Commitment | Statement |
|-----------|---------|
| No write access | Research OS has ZERO write/update/delete methods to eHospital |
| Pseudonymization before transfer | SHA-256 pseudo_id only; hospital holds key |
| Data minimization | Only domain-whitelisted categories accessed |
| PII exclusion | PII key guard enforced at software level |
| No cloud transfer | Pseudonymized data stored locally or on institutional server |
| Audit of data access | Access log maintained per hospital IT policy |
| No onward sharing | Research data NOT shared externally without separate approval |
| Publication compliance | Hospital authorship/acknowledgment policy to be followed |

---

## Part 7 — Hospital authorization gate

| Condition for authorization | Required? |
|---------------------------|---------|
| Ethics approval in place (ETH-GOV-01) | YES — prerequisite |
| Data access agreement (DAA) signed | YES — to be prepared with legal |
| SSO/MFA implemented and tested | YES — before real data access |
| WORM audit trail confirmed (PROD-AUD-01) | YES — before real data access |
| Production RBAC deployed | YES — before real data access |
| Encryption at rest confirmed | YES — before real data access |
| Independent qualification (IQ-GOV-01) | RECOMMENDED — before real data access |

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
