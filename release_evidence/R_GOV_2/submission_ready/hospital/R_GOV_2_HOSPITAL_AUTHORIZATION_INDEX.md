# R-GOV.2 Hospital Authorization Submission Index

**Document:** R_GOV_2_HOSPITAL_AUTHORIZATION_INDEX.md  
**Date:** 2026-06-28  
**Pack:** R-GOV.2 — Hospital authorization submission package  
**Gate:** HOSP-01  
**Readiness status:** READY_PENDING_HUMAN_INPUT  
**Prerequisite gate:** ETH-01 (ethics approval NOT YET OBTAINED — must be obtained first)  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **MANDATORY STATEMENT:**  
> This package is prepared for hospital authorization review.  
> Ethics committee approval (ETH-GOV-01) must be obtained BEFORE hospital authorization is submitted.  
> Hospital authorization does NOT permit real patient-data access until all three gates (ETH-01 + HOSP-01 + IQ-01) are obtained.

---

## Section 1 — Package contents

### 1.1 Prepared documents (ready for review)

| # | Document | Path | Readiness |
|---|---------|------|-----------|
| 1 | Hospital Authorization Readiness Dossier | release_evidence/R_GOV_1/R_GOV_1_HOSPITAL_AUTHORIZATION_READINESS_DOSSIER.md | READY_PENDING_HUMAN_INPUT |
| 2 | Hospital Data Access and System Use Request | release_evidence/R_GOV_1/R_GOV_1_HOSPITAL_DATA_ACCESS_AND_SYSTEM_USE_REQUEST.md | READY_PENDING_HUMAN_INPUT |
| 3 | eHospital Read-Only Boundary Proposal | release_evidence/R_GOV_1/R_GOV_1_EHOSPITAL_READ_ONLY_BOUNDARY_PROPOSAL.md | COMPLETE — technical design document |
| 4 | Hospital Role and Approval Matrix | release_evidence/R_GOV_1/R_GOV_1_HOSPITAL_ROLE_AND_APPROVAL_MATRIX.md | READY_PENDING_HUMAN_INPUT |
| 5 | Hospital Information Security and Incident Plan | release_evidence/R_GOV_1/R_GOV_1_HOSPITAL_INFORMATION_SECURITY_AND_INCIDENT_PLAN.md | READY_PENDING_HUMAN_INPUT |
| 6 | Hospital Authorization Checklist | release_evidence/R_GOV_1/R_GOV_1_HOSPITAL_AUTHORIZATION_CHECKLIST.md | READY_PENDING_HUMAN_INPUT |
| 7 | Hospital Authorization Gate Go/No-Go Register | release_evidence/R_GOV_1/R_GOV_1_HOSPITAL_AUTHORIZATION_GO_NO_GO_REGISTER.md | COMPLETE |

### 1.2 Supporting technical evidence for hospital IT review

| # | Document | Path |
|---|---------|------|
| 8 | Technical Baseline Confirmation | release_evidence/R_GOV_1/R_GOV_1_TECHNICAL_BASELINE_CONFIRMATION.md |
| 9 | Security and Technical Qualification Scope | release_evidence/R_GOV_1/R_GOV_1_SECURITY_AND_TECHNICAL_QUALIFICATION_SCOPE.md |
| 10 | Validation Evidence Catalog | release_evidence/R_GOV_1/R_GOV_1_VALIDATION_EVIDENCE_CATALOG.csv |

### 1.3 Documents NOT yet prepared / external prerequisites

| # | Document required | Owner | Status |
|---|-----------------|-------|--------|
| 1 | Ethics approval (ETH-GOV-01) | Ethics committee | NOT OBTAINED — prerequisite |
| 2 | Ethics reference number | Ethics committee + PI | NOT ISSUED |
| 3 | Institutional authorization form (hospital-specific) | PI + Hospital admin | EXTERNAL_FORM_REQUIRED |
| 4 | Data-flow diagram | PI + IT | NOT PREPARED |
| 5 | Sub-investigator names and contact details | PI | NOT CONFIRMED |
| 6 | Data manager contact details | PI | NOT CONFIRMED |
| 7 | eHospital liaison contact (hospital IT) | Hospital IT | NOT CONFIRMED |
| 8 | Notification contacts (IT Security Officer; DPO; etc.) | PI + Institution | NOT CONFIRMED |
| 9 | Incident escalation hierarchy confirmation | Hospital IT | NOT CONFIRMED |
| 10 | Technical controls implementation plan (SSO/MFA/WORM/RBAC) | PI + Hospital IT | NOT PREPARED |

---

## Section 2 — How to use this package

1. PI obtains ethics approval (ETH-GOV-01) — must be first.
2. PI completes all `[TO BE CONFIRMED BY PI]` fields in the Dossier (institution name, ethics reference, team contacts).
3. PI identifies and contacts relevant approval authorities (Section 3 below).
4. PI + Hospital IT prepare data-flow diagram and technical controls implementation plan.
5. PI obtains hospital-specific institutional authorization form.
6. PI assembles submission per hospital requirements.
7. PI confirms PI attestation: R_GOV_2_PI_FINAL_ATTESTATION_TEMPLATE.md.
8. PI submits to hospital (NOT by this system).
9. After approval received, PI follows R_GOV_1_EXTERNAL_EVIDENCE_IMPORT_PROTOCOL.md.

---

## Section 3 — Required approval authorities (all must sign)

| Authority | Role | Status |
|-----------|------|--------|
| Hospital Director (or delegate) | Overall institutional approval | PENDING |
| Research Management Office | Research governance | PENDING |
| Data Owner (Department Head / CMO) | Data access consent | PENDING |
| IT Security Officer | Technical security review | PENDING |
| Legal/Compliance Officer | Regulatory compliance | PENDING |
| Finance (if cost involved) | Budget approval | PENDING |

---

## Section 4 — Critical blockers (ethics prerequisite)

```
BLOCKER 1: Ethics approval (ETH-GOV-01) NOT YET OBTAINED.
           Hospital submission cannot proceed until ethics is approved.

BLOCKER 2: SSO / MFA / RBAC / Production audit trail — NOT IMPLEMENTED.
           These are mandatory technical controls. Hospital IT must review
           the implementation plan before authorization.

BLOCKER 3: Data-flow diagram not yet prepared.
           Required by most hospital governance processes.

BLOCKER 4: No institutional authorization form from hospital.
           Must be obtained from hospital administration.
```

---

*Hospital authorization: NOT GRANTED*  
*All outputs DRAFT — REQUIRE HUMAN REVIEW.*
