# R-GOV.2 Ethics Submission Completeness Audit

**Document:** R_GOV_2_ETHICS_COMPLETENESS_AUDIT.md  
**Date:** 2026-06-28  
**Pack:** R-GOV.2 — Ethics submission package  
**Auditor:** R-GOV.2 (automated audit; human PI review required before submission)  
**Ethics approval:** NOT GRANTED  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **MANDATORY STATEMENT:**  
> This audit assesses completeness of the ethics submission package only.  
> It does NOT constitute an ethics determination. Ethics decisions are made exclusively by the competent ethics committee.

---

## Audit scope

23 required items checked against:
- `release_evidence/R_GOV_1/R_GOV_1_ETHICS_REVIEW_READINESS_DOSSIER.md`
- `release_evidence/R_GOV_1/R_GOV_1_ETHICS_SUBMISSION_CHECKLIST.md`
- `release_evidence/R_GOV_1/R_GOV_1_CONSENT_OR_WAIVER_ASSESSMENT_TEMPLATE.md`
- `release_evidence/R_GOV_1/R_GOV_1_ETHICS_RISK_BENEFIT_AND_PRIVACY_ASSESSMENT.md`
- `release_evidence/R_GOV_1/R_GOV_1_ETHICS_REQUIREMENTS_CONFIRMATION_REGISTER.csv`

---

## Item-by-item audit

| # | Required item | Source | Status | Blocking | Action required |
|---|--------------|--------|--------|----------|-----------------|
| A-01 | Study title (official) | Ethics Dossier Part 1 | INCOMPLETE — placeholder `[TITLE: TO BE CONFIRMED BY PI]` | YES | PI must provide final title |
| A-02 | Study classification (interventional/observational/registry) | Ethics Dossier Part 1 | INCOMPLETE — placeholder | YES | PI must confirm classification |
| A-03 | Protocol version/date | Ethics Dossier Part 1 | INCOMPLETE — not yet assigned | YES | PI must version-lock protocol |
| A-04 | Research objectives (primary + secondary) | Ethics Dossier Part 2 | INCOMPLETE — placeholder | YES | PI must finalize |
| A-05 | Population definition (intended study population) | Ethics Dossier Part 3 | INCOMPLETE — placeholder | YES | PI must confirm population |
| A-06 | Inclusion/exclusion criteria | Ethics Dossier Part 3 | INCOMPLETE — placeholder | YES | PI must finalize criteria |
| A-07 | Study design description | Ethics Dossier Part 4 | COMPLETE — secondary data retrospective observational design documented | NO | No action required |
| A-08 | Data-source description | Ethics Dossier Part 4 | COMPLETE — eHospital read-only boundary described with 8 permitted domains | NO | No action required |
| A-09 | Risk-benefit analysis | Risk-Benefit Assessment | INCOMPLETE — framework prepared by AI; PI assessment statement and ethics committee proportionality determination still required | YES | PI to prepare PI section; committee to determine proportionality |
| A-10 | Privacy plan (pseudonymization) | Risk-Benefit Assessment §4.2 | COMPLETE — SHA-256 pseudonymization with hospital-held key described | NO | No action required |
| A-11 | Consent/waiver assessment | Consent/Waiver Template | INCOMPLETE — template prepared; PI must select pathway (prospective/retrospective) and complete waiver criteria; committee determination required | YES | PI to complete template; committee to determine |
| A-12 | Data access plan | eHospital Boundary Proposal | COMPLETE — read-only access, 8 permitted domains, zero-write interface documented | NO | No action required |
| A-13 | Data retention/destruction plan | Ethics Dossier Part 7 | INCOMPLETE — 7–15 year retention tiers referenced in code; formal plan not finalized; destruction plan not prepared | YES | PI + Data Manager to finalize retention/destruction plan |
| A-14 | CRF/data dictionary reference | Ethics Requirements ETH-REQ-04 | COMPLETE — links to R2.0 synthetic EDC modules and data dictionary | NO | No action required |
| A-15 | SAP reference | Ethics Requirements ETH-REQ-03 | INCOMPLETE — SAP not yet written or locked | YES — blocking (pre-specification required) | PI + Biostatistician to prepare and lock SAP |
| A-16 | Delegation requirement | Ethics Dossier Part 6 | COMPLETE — delegation log requirement stated; template referenced | NO | Delegation log itself must be prepared (A-17 below) |
| A-17 | COI declaration requirement | Ethics Dossier Part 6 | COMPLETE — requirement documented for all team members | NO | COI declarations themselves must be prepared |
| A-18 | AI-use limitation statement | Ethics Dossier Part 10 | COMPLETE — limitation statement included; use is DESIGN_ONLY; no real data | NO | No action required |
| A-19 | Deviation and CAPA plan | Ethics Dossier Part 11 | COMPLETE — template referenced (R3.0 SOP §4) | NO | No action required |
| A-20 | Monitoring plan | Ethics Requirements ETH-REQ-18 | INCOMPLETE — R3.0 monitoring template referenced but plan not prepared | YES | PI + Monitor to prepare monitoring plan |
| A-21 | PI confirmation requirement | Throughout dossier | COMPLETE — `[TO BE CONFIRMED BY PI]` markers on all human-required items | NO | PI must confirm all flagged items |
| A-22 | Required external forms | Ethics Submission Checklist §1.1 | EXTERNAL_FORM_REQUIRED — ethics application form not yet obtained from target committee | YES | PI must identify target committee and obtain their specific form |
| A-23 | Study registration | Ethics Requirements ETH-REQ-23 | NOT REGISTERED — no registry number yet | CONDITIONAL (required before or at ethics approval) | PI must register on ClinicalTrials.gov or WHO ICTRP before approval |

---

## Summary

| Status | Count | Items |
|--------|-------|-------|
| COMPLETE | 9 | A-07, A-08, A-10, A-12, A-14, A-16, A-17, A-18, A-19 |
| INCOMPLETE — BLOCKING | 10 | A-01, A-02, A-03, A-04, A-05, A-06, A-09, A-11, A-13, A-15 |
| INCOMPLETE — NON-BLOCKING (but required before submission) | 1 | A-20 |
| EXTERNAL_FORM_REQUIRED | 1 | A-22 |
| NOT REGISTERED (CONDITIONAL) | 1 | A-23 |
| INCOMPLETE — PI CONFIRMATION | 1 | A-21 (required after PI actions) |

**Total: 23 items audited**

---

## Additional documents required by ethics committee (not covered by above items)

These are standard ethics committee requirements not yet prepared:

| Document | Status |
|---------|--------|
| Study protocol (final, dated, PI-signed) | NOT PREPARED |
| Informed Consent Form — Vietnamese | NOT PREPARED |
| Informed Consent Form — English | NOT PREPARED |
| Participant Information Sheet — Vietnamese | NOT PREPARED |
| Participant Information Sheet — English | NOT PREPARED |
| CV of PI and co-investigators | NOT PREPARED |
| COI declarations — all team members | NOT PREPARED |
| Delegation log (signed) | NOT PREPARED |
| Monitoring plan (final) | NOT PREPARED |
| Insurance/indemnity certificate | NOT ARRANGED |
| Funding declaration | NOT PREPARED |
| Cover letter | NOT PREPARED |

---

## Audit verdict

**Ethics submission package completeness:** INCOMPLETE — HUMAN INPUT REQUIRED

This package provides the structural framework and technical disclosure for the ethics submission. It is NOT submission-ready. The package becomes submission-ready only when:
1. All 10 blocking items (A-01 through A-15 incomplete items) are resolved by PI
2. All additional documents listed above are prepared
3. External ethics application form is obtained from the target committee
4. PI final attestation is confirmed (R_GOV_2_PI_FINAL_ATTESTATION_TEMPLATE.md)

**Ethics approval: NOT GRANTED**

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs DRAFT — REQUIRE HUMAN REVIEW.*
