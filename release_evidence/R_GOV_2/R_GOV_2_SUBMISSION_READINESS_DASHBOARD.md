# R-GOV.2 Submission Readiness Dashboard

**Document:** R_GOV_2_SUBMISSION_READINESS_DASHBOARD.md  
**Date:** 2026-06-28  
**Pack:** R-GOV.2 — Phase G  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **MANDATORY STATEMENT:**  
> Status values in this dashboard are derived only from documented evidence.  
> Prohibited status values: SUBMITTED_EXTERNALLY / APPROVED_EXTERNALLY / ETHICS_APPROVED / HOSPITAL_APPROVED / INDEPENDENTLY_QUALIFIED  
> These statuses may only appear after human-confirmed external evidence is imported per R_GOV_1_EXTERNAL_EVIDENCE_IMPORT_PROTOCOL.md.

---

## Gate status summary

| Gate | ID | AI status | Human decision status | Package readiness |
|------|----|-----------|-----------------------|-------------------|
| Ethics | ETH-01 | NO-GO | NOT GRANTED | READY_PENDING_HUMAN_INPUT |
| Hospital authorization | HOSP-01 | NO-GO | NOT GRANTED | NOT_READY |
| Independent qualification | IQ-01 | NO-GO | NOT STARTED | NOT_READY |

---

## Per-package readiness detail

### Ethics submission package

| Dimension | Status |
|-----------|--------|
| **Package readiness** | **READY_PENDING_HUMAN_INPUT** |
| Structural framework | COMPLETE — all 5 dossier documents prepared |
| Completeness audit (23 items) | 9 COMPLETE / 10 INCOMPLETE — BLOCKING / 4 INCOMPLETE — other |
| Human input register | 50 items catalogued; 36 BLOCKING or EXTERNAL_FORM_REQUIRED |
| AI-use limitation | COMPLETE |
| Disclaimer / ethical disclosures | COMPLETE |
| Consent/waiver determination | PENDING ETHICS COMMITTEE |
| Ethics approval | NOT GRANTED |

**What is ready:** Framework, disclosures, risk-benefit template, consent/waiver template, system-use statement, AI-use statement, data boundary description, pseudonymization design  
**What is not ready:** Study title/protocol/SAP/objectives/population/criteria/team/COI/ICF/PIS/delegation/monitoring/insurance/registration/DPIA (50 items in human input register)

---

### Hospital authorization package

| Dimension | Status |
|-----------|--------|
| **Package readiness** | **NOT_READY** |
| Sequential prerequisite (ETH-01) | NOT MET — ethics approval not obtained |
| Structural framework | COMPLETE — all 6 dossier documents prepared |
| Completeness audit (20 items) | 9 COMPLETE / 10 INCOMPLETE — BLOCKING / 1 EXTERNAL_FORM_REQUIRED |
| Human input register | 34 items catalogued; 30 BLOCKING or EXTERNAL_FORM_REQUIRED |
| eHospital boundary design | COMPLETE (NOT_IMPLEMENTED in production) |
| System limitations disclosure | COMPLETE |
| Hospital authorization | NOT GRANTED |

**What is ready:** eHospital boundary technical design, system limitations disclosure, role/approval matrix template, data access request template, infosec plan template  
**What is not ready:** Ethics approval (prerequisite); all team contacts; data-flow diagram; technical controls plan; incident contacts; institutional form; all 6 approval authority sign-offs

---

### Independent qualification package

| Dimension | Status |
|-----------|--------|
| **Package readiness** | **NOT_READY** |
| Sequential prerequisites (ETH-01 + HOSP-01) | NOT MET |
| Assessor designation | NOT STARTED |
| COI declaration | NOT COMPLETED |
| Structural framework | COMPLETE — all 4 IQ dossier documents prepared |
| Evidence catalog | COMPLETE — 32 items; all available |
| Technical baseline | COMPLETE — 1049/0/5; 48 agents PASS |
| Completeness audit (20 items) | 12 COMPLETE / 8 INCOMPLETE (5 known gaps; 2 operational; 1 infrastructure) |
| Known qualification gaps | 8 gaps documented; assessor must evaluate |
| Independent qualification | NOT STARTED |

**What is ready:** Evidence catalog, technical baseline, security scope, system boundary documentation, manifest verification, test evidence  
**What is not ready:** Assessor designation; COI declaration; prerequisites; assessor decision

---

## Cross-pack status

| Dimension | Status |
|-----------|--------|
| **Cross-pack consistency** | **HOLD** |
| Hold ID | HOLD-2026-001 |
| Hold type | Minor terminology inconsistency (D-19 IQ status) |
| Substantive impact | NONE |
| Resolution | PI reviews → updates R_GOV_1_TECHNICAL_BASELINE_CONFIRMATION.md §7 → HOLD → PASS |

---

## PI actions dashboard

| Priority | Action | Target | Prerequisite |
|---------|--------|--------|-------------|
| 1 | Resolve HOLD-2026-001 (terminology update) | R_GOV_1_TECHNICAL_BASELINE_CONFIRMATION.md §7 | None |
| 2 | Finalize study protocol and lock SAP | PI | None |
| 3 | Complete ethics human input items (EHI-01 through EHI-50) | PI | Protocol/SAP |
| 4 | Prepare ICF/PIS and conduct DPIA with DPO | PI + DPO | Protocol |
| 5 | Prepare team documents (CVs; COI; delegation; monitoring; insurance) | PI + Team | Protocol |
| 6 | Obtain ethics application form; submit to ethics committee | PI | All ethics items complete |
| 7 | After ethics approval: complete hospital package and submit | PI + Hospital IT | ETH-01 |
| 8 | Approach Research Management Office to designate independent assessor | PI | None — can start in parallel |
| 9 | After assessor COI accepted: transmit evidence package | PI | Assessor designated |
| 10 | After all 3 approvals: import per protocol; re-evaluate qualification | PI | All gates |

---

## Invariants (must remain true at all times)

| Invariant | Status |
|-----------|--------|
| No AI submission on PI's behalf | MAINTAINED |
| No AI approval of external decisions | MAINTAINED |
| Real patient data processing | BLOCKED |
| eHospital integration | NOT IMPLEMENTED |
| Study activation | BLOCKED |
| Qualification | NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE |

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs DRAFT — REQUIRE HUMAN REVIEW.*
