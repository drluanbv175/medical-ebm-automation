# R-GOV.1 External Review Handover Pack

**Document:** R_GOV_1_EXTERNAL_REVIEW_HANDOVER_PACK.md  
**Date:** 2026-06-28  
**Status:** READY_FOR_EXTERNAL_REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## 1. Who this pack is addressed to

This handover pack is addressed to the following external reviewers. Each reviewer receives a subset of this pack as listed below.

| Reviewer | Gate | Pack subset |
|---------|------|-------------|
| Institutional Ethics Committee / IRB | ETH-01 | Sections 2, 4, 6 |
| Hospital Director / Research Management Office / Data Owner | HOSP-01 | Sections 2, 5, 6 |
| Independent Qualified Assessor | IQ-01 | Sections 2, 3, 6 |
| All reviewers | ALL | Section 7 (Limitations and invariants) |

---

## 2. What is in this governance pack (for all reviewers)

| Document | Purpose |
|---------|---------|
| R_GOV_1_EXTERNAL_DECISION_STATE_MODEL.md | Defines valid decision states; prohibits self-approval |
| R_GOV_1_EXTERNAL_DECISION_REGISTER.csv | Three-line register of all pending decisions |
| R_GOV_1_GOVERNANCE_READINESS_EXECUTIVE_SUMMARY.md | Overall readiness status |
| R_GOV_1_CROSS_GATE_TRACEABILITY_MATRIX.csv | 30 requirements traced to gates and documents |
| R_GOV_1_MASTER_EXTERNAL_DEPENDENCY_REGISTER.csv | 18 external dependencies |
| R_GOV_1_EXTERNAL_EVIDENCE_IMPORT_PROTOCOL.md | How external decisions will be recorded |
| R_GOV_1_FREEZE_SUMMARY.md | Final freeze summary |

---

## 3. Documents for the Independent Assessor (IQ-01)

| Document | Purpose |
|---------|---------|
| R_GOV_1_INDEPENDENT_QUALIFICATION_READINESS_DOSSIER.md | System overview; independence rule |
| R_GOV_1_INDEPENDENT_ASSESSOR_SCOPE_OF_WORK.md | Assessment scope; methods; deliverables |
| R_GOV_1_INDEPENDENCE_AND_CONFLICT_OF_INTEREST_TEMPLATE.md | COI form — must be completed before assessment begins |
| R_GOV_1_VALIDATION_EVIDENCE_CATALOG.csv | 32 evidence items with file paths and status |
| R_GOV_1_SECURITY_AND_TECHNICAL_QUALIFICATION_SCOPE.md | Technical domain map; in-scope / out-of-scope |
| R_GOV_1_INDEPENDENT_QUALIFICATION_DECISION_TEMPLATE.md | Decision template for assessor to complete |
| R_GOV_1_INDEPENDENT_QUALIFICATION_GO_NO_GO_REGISTER.md | Gate register; transition conditions |

**Assessor first step:** Complete R_GOV_1_INDEPENDENCE_AND_CONFLICT_OF_INTEREST_TEMPLATE.md before receiving any other document.

**Assessor evidence package:** The full source code, test suite, and evidence documents in the repository are available to the assessor. Entry point: `release_evidence/` directory. Run `MRAQ_OFFLINE_CI=1 pytest --tb=short -q` to verify test suite independently.

---

## 4. Documents for the Ethics Committee (ETH-01)

| Document | Purpose |
|---------|---------|
| R_GOV_1_ETHICS_REVIEW_READINESS_DOSSIER.md | Full ethics dossier — study identification; data; safeguards |
| R_GOV_1_ETHICS_SUBMISSION_CHECKLIST.md | Pre-submission checklist |
| R_GOV_1_CONSENT_OR_WAIVER_ASSESSMENT_TEMPLATE.md | Consent/waiver assessment for ethics committee |
| R_GOV_1_ETHICS_RISK_BENEFIT_AND_PRIVACY_ASSESSMENT.md | Risk-benefit and privacy analysis |
| R_GOV_1_ETHICS_GO_NO_GO_REGISTER.md | Ethics gate; transition conditions |

**Note to ethics committee:** Fields marked `[TO BE CONFIRMED BY PI]` must be completed by PI before formal submission. This dossier is a preparation framework, not a complete submission package.

---

## 5. Documents for the Hospital Authority (HOSP-01)

| Document | Purpose |
|---------|---------|
| R_GOV_1_HOSPITAL_AUTHORIZATION_READINESS_DOSSIER.md | Authorization dossier overview |
| R_GOV_1_HOSPITAL_DATA_ACCESS_AND_SYSTEM_USE_REQUEST.md | Data access and system use request |
| R_GOV_1_EHOSPITAL_READ_ONLY_BOUNDARY_PROPOSAL.md | Read-only boundary technical proposal |
| R_GOV_1_HOSPITAL_ROLE_AND_APPROVAL_MATRIX.md | Approval authority and team roles |
| R_GOV_1_HOSPITAL_INFORMATION_SECURITY_AND_INCIDENT_PLAN.md | Security posture and incident response |
| R_GOV_1_HOSPITAL_AUTHORIZATION_CHECKLIST.md | Pre-authorization checklist |
| R_GOV_1_HOSPITAL_AUTHORIZATION_GO_NO_GO_REGISTER.md | Hospital gate; transition conditions |

**Critical disclosure to hospital authority:** SSO, MFA, production RBAC, and WORM audit trail are NOT YET IMPLEMENTED. Hospital authorization may only proceed after these are confirmed per the checklist. See Part 1 of R_GOV_1_HOSPITAL_INFORMATION_SECURITY_AND_INCIDENT_PLAN.md for honest disclosure.

---

## 6. PI responsibilities before external submission

| Action | Target reviewer |
|--------|---------------|
| Finalize and sign study protocol | Ethics committee |
| Complete all [TO BE CONFIRMED BY PI] fields in ethics dossier | Ethics committee |
| Prepare ICF/PIS (Vietnamese + English) | Ethics committee |
| Prepare SAP and lock before data access | Ethics / Hospital |
| Complete COI declarations for all team members | Ethics / Hospital |
| Prepare delegation log | Ethics / Hospital |
| Obtain GCP training certificates | Hospital |
| Engage institutional IT for SSO/MFA/WORM | Hospital |
| Complete DPIA with DPO | Hospital |
| Approach Research Management Office for assessor designation | Independent assessor |
| Submit ethics application to committee | Ethics committee |
| Submit hospital authorization request (after ethics approval) | Hospital |

---

## 7. Limitations and invariants (all reviewers)

| Invariant | Status |
|----------|--------|
| Ethics approval | NOT GRANTED — cannot be self-granted |
| Hospital authorization | NOT GRANTED — cannot be self-granted |
| Independent qualification | NOT COMPLETED — assessor not yet designated |
| eHospital integration | NOT IMPLEMENTED |
| SSO/MFA | NOT IMPLEMENTED |
| Production audit trail | NOT IMPLEMENTED (PROD-AUD-01 OPEN) |
| Real patient data | BLOCKED |
| Study activation | BLOCKED |
| Global qualification | NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE |
| AI self-approval | PROHIBITED — no document in this pack constitutes approval |

---

## 8. Contact

| Role | Contact |
|------|---------|
| Principal Investigator | Dr Luân (bsluanbv175@gmail.com) |
| Institution | [TO BE CONFIRMED BY PI] |
| Date pack prepared | 2026-06-28 |
| Pack version | R-GOV.1 (initial) |

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
