# R-GOV.2 Independent Qualification Submission Index

**Document:** R_GOV_2_INDEPENDENT_QUALIFICATION_INDEX.md  
**Date:** 2026-06-28  
**Pack:** R-GOV.2 — Independent qualification submission package  
**Gate:** IQ-01  
**Readiness status:** READY_PENDING_HUMAN_INPUT  
**Prerequisite gates:** ETH-01 (NOT OBTAINED) + HOSP-01 (NOT OBTAINED)  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **MANDATORY STATEMENT:**  
> Independent qualification is not established by this package.  
> This package is prepared to facilitate and scope the independent qualification assessment.  
> The qualification decision is made exclusively by a qualified external independent assessor.  
> No AI agent (including this system), PI, developer, or co-investigator may serve as the independent assessor.

---

## Section 1 — Package contents

### 1.1 Core qualification documents

| # | Document | Path | Readiness |
|---|---------|------|-----------|
| 1 | Independent Qualification Readiness Dossier | release_evidence/R_GOV_1/R_GOV_1_INDEPENDENT_QUALIFICATION_READINESS_DOSSIER.md | COMPLETE — system overview; 18 evaluation domains; 5 known gaps |
| 2 | Independent Assessor Scope of Work | release_evidence/R_GOV_1/R_GOV_1_INDEPENDENT_ASSESSOR_SCOPE_OF_WORK.md | COMPLETE — 18 in-scope domains QS-01 to QS-18 |
| 3 | Independence and COI Declaration Template | release_evidence/R_GOV_1/R_GOV_1_INDEPENDENCE_AND_CONFLICT_OF_INTEREST_TEMPLATE.md | READY FOR ASSESSOR — blank; assessor must complete before evidence package is transmitted |
| 4 | Independent Qualification Decision Template | release_evidence/R_GOV_1/R_GOV_1_INDEPENDENT_QUALIFICATION_DECISION_TEMPLATE.md | READY FOR ASSESSOR — blank; assessor completes and returns |

### 1.2 Technical evidence for assessor

| # | Document | Path |
|---|---------|------|
| 5 | Validation Evidence Catalog | release_evidence/R_GOV_1/R_GOV_1_VALIDATION_EVIDENCE_CATALOG.csv |
| 6 | Security and Technical Qualification Scope | release_evidence/R_GOV_1/R_GOV_1_SECURITY_AND_TECHNICAL_QUALIFICATION_SCOPE.md |
| 7 | Technical Baseline Confirmation | release_evidence/R_GOV_1/R_GOV_1_TECHNICAL_BASELINE_CONFIRMATION.md |
| 8 | eHospital Boundary Proposal | release_evidence/R_GOV_1/R_GOV_1_EHOSPITAL_READ_ONLY_BOUNDARY_PROPOSAL.md |
| 9 | External Decision State Model | release_evidence/R_GOV_1/R_GOV_1_EXTERNAL_DECISION_STATE_MODEL.md |
| 10 | Master External Dependency Register | release_evidence/R_GOV_1/R_GOV_1_MASTER_EXTERNAL_DEPENDENCY_REGISTER.csv |

### 1.3 Governance evidence (context for assessor)

| # | Document | Path |
|---|---------|------|
| 11 | Human Governance Decision Record | release_evidence/R1_1/R1_1_4_HUMAN_GOVERNANCE_DECISION_RECORD.md |
| 12 | Action and Residual Risk Register | release_evidence/R1_1/R1_1_4_ACTION_AND_RESIDUAL_RISK_REGISTER.md |
| 13 | IQ Gate Go/No-Go Register | release_evidence/R_GOV_1/R_GOV_1_INDEPENDENT_QUALIFICATION_GO_NO_GO_REGISTER.md |

### 1.4 Prerequisites NOT yet met

| # | Prerequisite | Status |
|---|-------------|--------|
| 1 | Independent assessor designated by Research Management Office or hospital | NOT DESIGNATED |
| 2 | Independence and COI declaration completed by assessor | NOT COMPLETED |
| 3 | Assessor institutional acceptance (Section 6 of COI template) | NOT COMPLETED |
| 4 | Ethics approval (ETH-GOV-01) | NOT OBTAINED — sequential prerequisite |
| 5 | Hospital authorization (HOSP-GOV-01) | NOT OBTAINED — sequential prerequisite |

---

## Section 2 — How to use this package

1. PI approaches Research Management Office or institutional authority to designate an independent assessor.
2. PI provides the COI declaration template to the assessor.
3. Assessor completes COI declaration independently and returns to PI.
4. PI verifies assessor is eligible (not PI; not developer; not co-investigator; not AI agent).
5. Only after COI accepted: PI transmits the full evidence package (Section 1.2 + 1.3) to assessor.
6. Assessor conducts independent review per R_GOV_2_INDEPENDENT_ASSESSOR_SCOPE_FINAL.md.
7. Assessor completes R_GOV_1_INDEPENDENT_QUALIFICATION_DECISION_TEMPLATE.md.
8. Assessor returns signed decision to PI.
9. PI follows R_GOV_1_EXTERNAL_EVIDENCE_IMPORT_PROTOCOL.md to record the decision.

---

## Section 3 — Known qualification gaps (for assessor awareness)

| # | Gap | Category | Notes |
|---|-----|----------|-------|
| QG-01 | Production audit trail (PROD-AUD-01 OPEN) | Security | NOT_IMPLEMENTED; ACT-R1-01 open |
| QG-02 | RBAC in production (PROD-RBAC-01) | Access control | NOT_IMPLEMENTED; ACT-R1-05 open |
| QG-03 | SSO / MFA | Identity | NOT_IMPLEMENTED; ACT-R1-02 / ACT-R1-03 open |
| QG-04 | eHospital integration | Data access | NOT_IMPLEMENTED; design only |
| QG-05 | WORM / tamper-evident archive (production) | Data integrity | NOT_IMPLEMENTED; ACT-R1-04 open |

---

## Section 4 — Independence rule

The following persons are INELIGIBLE to serve as the independent assessor:

- Dr Luân (PI; bsluanbv175@gmail.com)
- Any developer or system contributor
- Any co-investigator
- Any person who reviewed, designed, or has beneficial interest in this system
- Any AI agent (including Claude, GPT, or any automated system)

---

*Independent qualification: NOT STARTED*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs DRAFT — REQUIRE HUMAN REVIEW.*
