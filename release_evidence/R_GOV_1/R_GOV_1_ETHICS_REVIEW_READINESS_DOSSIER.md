# R-GOV.1 Ethics Review Readiness Dossier

**Document:** R_GOV_1_ETHICS_REVIEW_READINESS_DOSSIER.md  
**Date:** 2026-06-28  
**Decision ID:** ETH-GOV-01  
**Status:** READY_FOR_EXTERNAL_REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **MANDATORY STATEMENT:**  
> This dossier is prepared for ethics review.  
> It is not an ethics approval.  
> No study activity may begin based on this dossier alone.  
> Any applicable ethics, legal, institutional and data-protection requirements  
> must be confirmed by the competent ethics body and institution.

---

## Part 1 — Study Identification

| Field | Value |
|-------|-------|
| Study title | [TITLE: TO BE CONFIRMED BY PI] |
| Study acronym | [ACRONYM: TO BE CONFIRMED BY PI] |
| Protocol version | [VERSION: TO BE CONFIRMED BY PI] |
| Protocol date | [DATE: TO BE CONFIRMED BY PI] |
| Principal Investigator | Dr Luân (bsluanbv175@gmail.com) |
| Institution | [INSTITUTION: TO BE CONFIRMED BY PI] |
| Department | [DEPARTMENT: TO BE CONFIRMED BY PI] |
| Funding source | [FUNDING: TO BE CONFIRMED BY PI] |
| Conflict of interest status | [TO BE DECLARED BY PI AND TEAM] |
| Study registration | [TO BE REGISTERED — ClinicalTrials.gov / WHO ICTRP / national registry] |

---

## Part 2 — Study Classification

| Field | Value |
|-------|-------|
| Study type | [Observational / Interventional: TO BE CONFIRMED BY PI] |
| Design | [Retrospective / Prospective / Cross-sectional / Cohort / Case-control: TO BE CONFIRMED BY PI] |
| Phase (if interventional) | [N/A or Phase I / II / III: TO BE CONFIRMED BY PI] |
| Data-source type | Electronic health record data (eHospital) — read-only, pseudonymized extract |
| International scope | [Single-center / Multi-center: TO BE CONFIRMED BY PI] |
| Vulnerable population involvement | [YES / NO / UNKNOWN: TO BE CONFIRMED BY PI] |

---

## Part 3 — Research Question and Objectives

| Field | Value |
|-------|-------|
| Primary research question | [PICO/PECO: TO BE CONFIRMED BY PI] |
| Primary objective | [TO BE CONFIRMED BY PI] |
| Secondary objectives | [TO BE CONFIRMED BY PI] |
| Hypothesis | [TO BE CONFIRMED BY PI] |
| Expected duration | [TO BE CONFIRMED BY PI] |
| Expected sample size | [TO BE CONFIRMED BY PI — see SAP reference] |

---

## Part 4 — Population Definition

| Field | Value |
|-------|-------|
| Target population | [TO BE CONFIRMED BY PI] |
| Inclusion criteria | [TO BE CONFIRMED BY PI] |
| Exclusion criteria | [TO BE CONFIRMED BY PI] |
| Age range | [TO BE CONFIRMED BY PI] |
| Sex | [TO BE CONFIRMED BY PI] |
| Setting | Outpatient clinic, inpatient ward, or both [TO BE CONFIRMED BY PI] |
| Recruitment / identification method | [Prospective: active recruitment / Retrospective: EHR query — TO BE CONFIRMED BY PI] |

---

## Part 5 — Data Source Description

| Field | Value |
|-------|-------|
| Primary data source | eHospital / Hospital Information System (HIS) — read-only |
| Data domains requested | As specified in R_GOV_1_EHOSPITAL_READ_ONLY_BOUNDARY_PROPOSAL.md |
| Identifiable data involved | No — pseudonymized/de-identified extract only |
| Pseudonymization method | SHA-256(real_id ‖ institutional_salt) — key managed by institutional vault |
| Secondary data sources | [TO BE CONFIRMED BY PI] |
| Data linkage requirement | [YES / NO — TO BE CONFIRMED BY PI] |
| Biological samples | [YES / NO — TO BE CONFIRMED BY PI] |

---

## Part 6 — Risk-Benefit Assessment

*(Full assessment: see R_GOV_1_ETHICS_RISK_BENEFIT_AND_PRIVACY_ASSESSMENT.md)*

| Dimension | Summary |
|----------|---------|
| Direct benefit to participants | [TO BE ASSESSED — typically minimal for retrospective studies] |
| Indirect benefit (knowledge) | [TO BE CONFIRMED BY PI] |
| Risk to participants | Data privacy risk (mitigated by pseudonymization); [other risks TO BE CONFIRMED BY PI] |
| Risk magnitude | [TO BE ASSESSED BY ETHICS COMMITTEE] |
| Proportionality | [TO BE ASSESSED BY ETHICS COMMITTEE] |

---

## Part 7 — Privacy and Confidentiality Safeguards

| Safeguard | Description |
|---------|-------------|
| Pseudonymization | SHA-256 pseudo_id; real ID never enters Research OS |
| PII key guard | `ExtractRecord.__post_init__` rejects any record with PII key names |
| Data minimization | Domain whitelist — only 8 approved data categories |
| Access control | Role-based; SSO/MFA required (NOT YET IMPLEMENTED — pending institutional IT) |
| Audit trail | Synthetic harness only; production WORM pending (PROD-AUD-01 OPEN) |
| Data retention | Per R3_0_RETENTION_POLICY_REQUIREMENTS.md (7–15 years by data type) |
| Data destruction | [PLAN: TO BE CONFIRMED BY PI AND DATA OWNER] |
| Cross-border data transfer | [TO BE ASSESSED — depends on cloud storage location] |
| Decree 13/2023/ND-CP (Vietnam) | Personal data protection — compliance to be confirmed by legal |

---

## Part 8 — Consent Requirement Assessment

> **Consent requirement: TO BE DETERMINED BY COMPETENT ETHICS BODY**  
> **Waiver eligibility: TO BE ASSESSED BY COMPETENT ETHICS BODY**

| Scenario | Notes |
|---------|-------|
| Prospective study | Informed consent normally required |
| Retrospective study on existing records | Waiver may be eligible — TO BE DETERMINED BY ETHICS COMMITTEE |
| Use of de-identified data | Waiver may be eligible — TO BE DETERMINED BY ETHICS COMMITTEE |
| Re-contact of participants | Requires consent — TO BE CONFIRMED BY PI |

---

## Part 9 — System-Use Statement

The Medical Research OS is an offline software prototype for:
- Evidence-based medicine support tools
- Research data management contract definitions
- Synthetic (non-production) EDC harness

**Current qualification status:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

The system does not currently:
- Connect to eHospital or any real HIS/EMR
- Store real patient data
- Execute real research workflows
- Replace investigator judgment or clinical decision-making

---

## Part 10 — AI-Use Limitation Statement

| Limitation | Statement |
|-----------|---------|
| AI role | Decision-support only; all research decisions require investigator review |
| AI outputs | DRAFT — not for direct clinical or research use without physician verification |
| Clinical recommendation | AI does NOT make clinical recommendations without physician review |
| Diagnosis | AI does NOT make diagnoses |
| Prescription | AI does NOT prescribe treatments |
| Data generation | AI does NOT generate, invent, or infer real clinical data |
| Audit | AI does NOT constitute an independent audit |

**Disclaimer on all outputs:** "Cần bác sĩ kiểm chứng" (Requires physician verification)

---

## Part 11 — Required Attachments for Ethics Submission

| Attachment | Status |
|-----------|--------|
| Study protocol (final signed) | [NOT PREPARED] |
| ICF (Vietnamese + English) | [NOT PREPARED] |
| Participant Information Sheet | [NOT PREPARED] |
| Data management plan | See R3_0_DATA_MANAGEMENT... references |
| Statistical analysis plan (SAP) | [NOT PREPARED] |
| CV of PI and co-investigators | [NOT PREPARED] |
| Insurance / indemnity arrangements | [NOT ARRANGED] |
| COI declarations (all team members) | [NOT PREPARED] |
| Delegation log | [NOT PREPARED] |
| Deviation and CAPA plan | See R3_0_STUDY_OPERATIONS_SOP.md §4 |
| Monitoring plan | See R3_0_MONITORING_PLAN_TEMPLATE.md |
| System-use statement | This document Part 9 |

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Cần bác sĩ kiểm chứng.*
