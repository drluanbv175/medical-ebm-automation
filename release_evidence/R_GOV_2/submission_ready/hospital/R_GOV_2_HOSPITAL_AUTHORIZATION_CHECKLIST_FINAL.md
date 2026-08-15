# R-GOV.2 Hospital Authorization Checklist — Final

**Document:** R_GOV_2_HOSPITAL_AUTHORIZATION_CHECKLIST_FINAL.md  
**Date:** 2026-06-28  
**Pack:** R-GOV.2 — Hospital authorization submission package  
**Hospital authorization:** NOT GRANTED  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **MANDATORY STATEMENT:**  
> Ethics approval (ETH-GOV-01) must be obtained BEFORE this checklist can be completed.  
> Hospital authorization does NOT permit real patient-data access on its own — all three gates (ETH-01 + HOSP-01 + IQ-01) are required.

---

## Step 0 — Confirm ethics approval obtained (prerequisite)

| # | Action | Status |
|---|--------|--------|
| 0.1 | Ethics committee approval (ETH-GOV-01) received and documented | [ ] NOT DONE — DO NOT PROCEED UNTIL COMPLETE |
| 0.2 | Ethics reference number obtained and inserted in all hospital documents | [ ] NOT DONE |
| 0.3 | Ethics approval document filed (via R_GOV_1_EXTERNAL_EVIDENCE_IMPORT_PROTOCOL.md) | [ ] NOT DONE |

**Do not continue to Step 1 until Step 0 is complete.**

---

## Step 1 — Study identification and PI details

| # | Action | Status |
|---|--------|--------|
| 1.1 | Insert institution / hospital name throughout all documents | [ ] NOT DONE |
| 1.2 | Insert department / division | [ ] NOT DONE |
| 1.3 | Confirm study title (must match ethics-approved title exactly) | [ ] NOT DONE |
| 1.4 | Confirm data access period (start / end dates) | [ ] NOT DONE |
| 1.5 | Confirm all team members (names + roles + contacts) | [ ] NOT DONE |

→ Source: R_GOV_2_HOSPITAL_HUMAN_INPUT_REGISTER.csv (HHI-03 through HHI-14)

---

## Step 2 — Technical preparation

| # | Action | Status |
|---|--------|--------|
| 2.1 | Prepare data-flow diagram with hospital IT (eHospital → pseudonymization → analysis) | [ ] NOT DONE |
| 2.2 | Prepare technical controls implementation plan (SSO / MFA / RBAC / WORM / production audit) | [ ] NOT DONE |
| 2.3 | Confirm secure data transfer channel with hospital IT | [ ] NOT DONE |
| 2.4 | Confirm data format and extraction method with hospital IT | [ ] NOT DONE |
| 2.5 | Confirm additional data domains (if any beyond D01–D08) with data owner | [ ] NOT DONE |

→ Source: R_GOV_2_HOSPITAL_HUMAN_INPUT_REGISTER.csv (HHI-08 through HHI-24)

---

## Step 3 — Data governance

| # | Action | Status |
|---|--------|--------|
| 3.1 | Finalize data retention and destruction plan (signed document) | [ ] NOT DONE |
| 3.2 | Confirm Circular 29/2020/TT-BYT compliance with legal officer | [ ] NOT DONE |
| 3.3 | Confirm Decree 13/2023/ND-CP compliance with DPO | [ ] NOT DONE |
| 3.4 | Complete DPIA with DPO (if not already done for ethics) | [ ] NOT DONE |

→ Source: R_GOV_2_HOSPITAL_HUMAN_INPUT_REGISTER.csv (HHI-30 through HHI-32)

---

## Step 4 — Incident escalation contacts

| # | Action | Status |
|---|--------|--------|
| 4.1 | Insert IT Security Officer contact details in Information Security Plan | [ ] NOT DONE |
| 4.2 | Insert DPO contact details | [ ] NOT DONE |
| 4.3 | Insert ethics committee contact (for breach notification) | [ ] NOT DONE |
| 4.4 | Insert competent authority contact (Bộ Y tế / Cục CNTT) | [ ] NOT DONE |

→ Source: R_GOV_2_HOSPITAL_HUMAN_INPUT_REGISTER.csv (HHI-26 through HHI-29)

---

## Step 5 — Approval authority engagement

| # | Action | Status |
|---|--------|--------|
| 5.1 | Approach Research Management Office — initiate research governance review | [ ] NOT DONE |
| 5.2 | Approach data owner (Department Head / CMO) — obtain data access consent | [ ] NOT DONE |
| 5.3 | Approach Hospital IT Security Officer — schedule technical security review | [ ] NOT DONE |
| 5.4 | Approach Legal / Compliance Officer — initiate regulatory compliance review | [ ] NOT DONE |
| 5.5 | Approach Finance (if cost involved) | [ ] NOT DONE |
| 5.6 | Obtain IT Security Officer signature on Information Security Plan Section 5 | [ ] NOT DONE |

→ Source: R_GOV_2_HOSPITAL_HUMAN_INPUT_REGISTER.csv (HHI-15 through HHI-25)

---

## Step 6 — Submission preparation

| # | Action | Status |
|---|--------|--------|
| 6.1 | Obtain hospital-specific institutional authorization form from Hospital Administration | [ ] NOT DONE |
| 6.2 | Complete all `[TO BE CONFIRMED BY PI]` fields in all hospital documents | [ ] NOT DONE |
| 6.3 | Complete R_GOV_2_PI_FINAL_ATTESTATION_TEMPLATE.md | [ ] NOT DONE |
| 6.4 | Complete R_GOV_2_PRE_SUBMISSION_HUMAN_CONFIRMATION_CHECKLIST.md | [ ] NOT DONE |
| 6.5 | Assemble complete submission package per hospital requirements | [ ] NOT DONE |
| 6.6 | Submit to hospital (PI action — not by this system) | [ ] NOT DONE |

---

## Step 7 — Post-authorization tracking

| # | Action | Status |
|---|--------|--------|
| 7.1 | Update R_GOV_1_EXTERNAL_DECISION_REGISTER.csv: HOSP-GOV-01 → SUBMITTED_EXTERNALLY | [ ] NOT DONE |
| 7.2 | Record submission date, hospital reference, tracking number | [ ] NOT DONE |
| 7.3 | On authorization received: follow R_GOV_1_EXTERNAL_EVIDENCE_IMPORT_PROTOCOL.md | [ ] NOT DONE |
| 7.4 | Update HOSP-GOV-01 → APPROVED_EXTERNALLY only after human confirmation of real authorization document | [ ] NOT DONE |

---

## Final verdict

**Hospital authorization checklist:** INCOMPLETE (all items marked NOT DONE; Step 0 prerequisite not met)  
**Hospital authorization readiness:** NOT_READY → target READY_FOR_PI_FINAL_REVIEW after Steps 0–6  
**Hospital authorization:** NOT GRANTED

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs DRAFT — REQUIRE HUMAN REVIEW.*
