# R-GOV.2 Hospital Authorization Completeness Audit

**Document:** R_GOV_2_HOSPITAL_COMPLETENESS_AUDIT.md  
**Date:** 2026-06-28  
**Pack:** R-GOV.2 — Hospital authorization submission package  
**Gate:** HOSP-01  
**Prerequisite gate:** ETH-01 (NOT YET OBTAINED)  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **MANDATORY STATEMENT:**  
> This audit assesses completeness of the hospital authorization package only.  
> Ethics approval (ETH-GOV-01) is a prerequisite. Hospital authorization does NOT permit real patient-data access on its own.

---

## Audit scope

20 required items checked against:
- `release_evidence/R_GOV_1/R_GOV_1_HOSPITAL_AUTHORIZATION_READINESS_DOSSIER.md`
- `release_evidence/R_GOV_1/R_GOV_1_HOSPITAL_DATA_ACCESS_AND_SYSTEM_USE_REQUEST.md`
- `release_evidence/R_GOV_1/R_GOV_1_EHOSPITAL_READ_ONLY_BOUNDARY_PROPOSAL.md`
- `release_evidence/R_GOV_1/R_GOV_1_HOSPITAL_ROLE_AND_APPROVAL_MATRIX.md`
- `release_evidence/R_GOV_1/R_GOV_1_HOSPITAL_INFORMATION_SECURITY_AND_INCIDENT_PLAN.md`
- `release_evidence/R_GOV_1/R_GOV_1_HOSPITAL_AUTHORIZATION_CHECKLIST.md`

---

## Item-by-item audit

| # | Required item | Source | Status | Blocking | Action required |
|---|--------------|--------|--------|----------|-----------------|
| H-01 | PI and department reference | Hospital Dossier Part 1 | INCOMPLETE — institution name and department are placeholders | YES | PI must provide institution name and department |
| H-02 | Study purpose (clear description) | Hospital Dossier Part 2 | COMPLETE — EBM automation for outpatient clinical practice; design only | NO | No action required |
| H-03 | Ethics dependency status | Hospital Dossier Part 2; HOSP gate register | COMPLETE — ETH-GOV-01 dependency documented; ethics NOT YET OBTAINED; BLOCKER 1 documented | NO — dependency is accurately documented | PI must obtain ethics approval before submitting hospital request |
| H-04 | Data-owner authorization | Hospital Dossier Part 3 | INCOMPLETE — data owner (Department Head/CMO) not yet approached; sign-off pending | YES | PI must identify and contact data owner for authorization |
| H-05 | Research-management review | Hospital Role Matrix Section 2 | INCOMPLETE — Research Management Office not yet contacted | YES | PI must engage Research Management Office |
| H-06 | IT/digital-health review | Hospital Role Matrix Section 2 | INCOMPLETE — hospital IT not yet contacted | YES | PI must engage hospital IT security officer |
| H-07 | Information-security review | Information Security Plan Section 5 | INCOMPLETE — IT Security Officer sign-off blank; review not yet conducted | YES | Hospital IT Security Officer must review and sign Section 5 |
| H-08 | Legal/compliance review | Hospital Role Matrix Section 2 | INCOMPLETE — legal officer not yet contacted | YES | PI must engage legal/compliance officer |
| H-09 | eHospital read-only boundary | eHospital Boundary Proposal | COMPLETE — 8 permitted domains; 8 blocked domains; zero-write interface; PseudonymizedSubject constraint documented | NO | Hospital IT must review and approve implementation |
| H-10 | Minimum-necessary dataset | Hospital Data Access Request Section 2 | COMPLETE — 8 domains listed; justification for each domain required | CONDITIONAL | PI to confirm justification for each domain in the request |
| H-11 | Pseudonymization approach | Hospital Data Access Request Section 3 | COMPLETE — SHA-256(real_id ‖ institutional_salt) → 64-char pseudo_id; hospital holds key | NO | No action required |
| H-12 | Data-flow diagram | Hospital Data Access Request Section 4 | INCOMPLETE — not yet prepared | YES | PI + IT to prepare data-flow diagram showing eHospital → pseudonymization → analysis |
| H-13 | Approved extract workflow | Hospital Data Access Request Section 4 | INCOMPLETE — workflow designed but not yet approved by hospital IT | YES | Hospital IT must approve the extract workflow |
| H-14 | No AI write-back statement | eHospital Boundary Proposal Section 3 | COMPLETE — zero-write interface; 0 write/update/delete methods documented | NO | No action required |
| H-15 | Data retention/destruction plan | Hospital Dossier Part 5 | INCOMPLETE — framework (7–15 year tiers) referenced; formal plan pending | YES | PI + Data Manager to finalize retention and destruction plan |
| H-16 | Incident escalation plan | Information Security Plan Section 4 | INCOMPLETE — contact information blank (IT Security Officer; DPO; ethics committee; competent authority all blank) | YES | PI must provide contact details for incident escalation chain |
| H-17 | Audit-log and access-control requirement | Information Security Plan Section 2; Technical Baseline | COMPLETE — gaps documented honestly; PROD-AUD-01 OPEN; PROD-RBAC-01 NOT_IMPLEMENTED; implementation targets noted | NO — limitation is disclosed; hospital must decide acceptability | Hospital must assess whether control gaps are acceptable for authorization |
| H-18 | System limitations disclosure | Hospital Dossier Part 4; Infosec Plan Section 2 | COMPLETE — all NOT_IMPLEMENTED items (SSO; MFA; WORM; RBAC; eHospital integration) disclosed honestly | NO — required disclosure is complete | Hospital decision-makers must assess acceptability |
| H-19 | Study stop conditions | Hospital Dossier Part 6 | COMPLETE — breach protocol; unauthorized disclosure; data integrity breach; scope violation all documented | NO | No action required |
| H-20 | Required institutional forms | Hospital Authorization Checklist Section 3 | EXTERNAL_FORM_REQUIRED — hospital-specific institutional authorization form not yet obtained | YES | PI must obtain hospital's specific form from Hospital Administration |

---

## Summary

| Status | Count | Items |
|--------|-------|-------|
| COMPLETE | 9 | H-02, H-03, H-09, H-11, H-14, H-17, H-18, H-19 + H-10 (conditional) |
| INCOMPLETE — BLOCKING | 10 | H-01, H-04, H-05, H-06, H-07, H-08, H-12, H-13, H-15, H-16 |
| EXTERNAL_FORM_REQUIRED | 1 | H-20 |

**CRITICAL BLOCKER (pre-condition):** ETH-01 ethics approval must be obtained before this package can be submitted.

---

## Control gap assessment

Hospital IT Security Officer and Hospital Director must assess acceptability of the following:

| Control | Status | Risk level |
|---------|--------|-----------|
| SSO / Single Sign-On | NOT IMPLEMENTED | HIGH — access cannot be authenticated by hospital identity |
| MFA / Multi-Factor Authentication | NOT IMPLEMENTED | HIGH — cannot enforce MFA for system access |
| Production audit trail (WORM) | NOT IMPLEMENTED (PROD-AUD-01 OPEN) | HIGH — audit trail not tamper-evident |
| Role-Based Access Control (production) | NOT IMPLEMENTED (PROD-RBAC-01) | HIGH — role boundaries not enforced in production |
| eHospital integration | NOT IMPLEMENTED | HIGH — data access channel not yet built |

**These 5 items are the subject of ACT-R1-01 through ACT-R1-05. Hospital must not authorize production data access until these controls are implemented.**

---

## Audit verdict

**Hospital authorization package completeness:** INCOMPLETE — HUMAN INPUT REQUIRED

Ethics approval (ETH-GOV-01) prerequisite not yet met. 10 blocking items pending PI/hospital action. Package is NOT submission-ready.

**Hospital authorization: NOT GRANTED**

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs DRAFT — REQUIRE HUMAN REVIEW.*
