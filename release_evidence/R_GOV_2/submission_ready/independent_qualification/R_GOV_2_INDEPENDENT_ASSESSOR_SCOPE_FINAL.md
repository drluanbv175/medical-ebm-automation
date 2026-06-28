# R-GOV.2 Independent Assessor Scope — Final

**Document:** R_GOV_2_INDEPENDENT_ASSESSOR_SCOPE_FINAL.md  
**Date:** 2026-06-28  
**Pack:** R-GOV.2 — Independent qualification submission package  
**Gate:** IQ-01  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **MANDATORY STATEMENT:**  
> Independent qualification is not established by this document.  
> This document defines the scope for the independent assessor.  
> The qualification decision belongs exclusively to the designated independent assessor.

---

## Section 1 — Assessor scope acceptance (to be completed by assessor)

By accepting this scope, the assessor confirms they have:
1. Reviewed and accepted the 18 in-scope domains (QS-01 through QS-18) listed below.
2. Noted the 7 out-of-scope items (QS-19 through QS-25) and the reasons.
3. Confirmed their independence per R_GOV_1_INDEPENDENCE_AND_CONFLICT_OF_INTEREST_TEMPLATE.md.
4. Received the full evidence package (listed in Section 4).

```
Assessor name:         ___________________________________________
Assessor institution:  ___________________________________________
Scope acceptance date: ___________________________________________
Signature:             ___________________________________________
```

---

## Section 2 — In-scope assessment domains

The assessor must assess all 18 domains listed below. Each domain maps to one or more qualification scopes (QS-xx) from R_GOV_1_SECURITY_AND_TECHNICAL_QUALIFICATION_SCOPE.md.

| # | Domain | Scope ID | Primary evidence |
|---|--------|----------|-----------------|
| 1 | Intended-use and non-intended-use boundaries | QS-01 | R_GOV_1_INDEPENDENT_QUALIFICATION_READINESS_DOSSIER.md §2; Technical Baseline §7 |
| 2 | Architecture and design documentation completeness | QS-02 | release_evidence/R1_1/ through R4_0/ |
| 3 | Requirements traceability | QS-03 | R_GOV_1_VALIDATION_EVIDENCE_CATALOG.csv (E01–E32) |
| 4 | Test suite validity and completeness | QS-05 | Technical Baseline §3; test files in tests/ |
| 5 | Manifest and registry integrity | QS-06 | runtime/manifests/agent_source_manifest.csv; verify_manifest_registry.py |
| 6 | Pseudonymization design (SHA-256 with hospital-held key) | QS-07 | R1.2 design; R_GOV_1_EHOSPITAL_READ_ONLY_BOUNDARY_PROPOSAL.md §4 |
| 7 | eHospital read-only boundary design and test coverage | QS-08 | release_evidence/R4_0/; tests/test_r4_0_ehospital_boundary.py |
| 8 | PII protection controls (design; test; runtime guards) | QS-09 | R1.2; PII key guard at ExtractRecord.__post_init__ |
| 9 | Audit trail design and production gap | QS-10 | R1.3 design; PROD-AUD-01 OPEN; retention constants |
| 10 | RBAC design and production gap | QS-11 | Design; PROD-RBAC-01 NOT_IMPLEMENTED |
| 11 | Identity and authentication design and production gap | QS-12 | SSO=NOT_IMPLEMENTED; MFA=NOT_IMPLEMENTED |
| 12 | Agent manifest integrity and governance controls | QS-13 | Agent manifest; tham-dinh-dau-ra guardrail |
| 13 | Synthetic / offline-only mode enforcement | QS-14 | MRAQ_OFFLINE_CI=1; test assertions; no real data in tests |
| 14 | eHospital zero-write interface verification | QS-15 | ehospital_boundary_contract.py; 0 write/update/delete methods |
| 15 | Bias and safety disclaimer compliance | QS-16 | Disclaimer enforcement in agent outputs; tham-dinh-dau-ra checks |
| 16 | Scope lock and design-only authorization | QS-17 | R1_1_4_R1_2_SCOPE_LOCK.md; R1_1_4_R1_2_DESIGN_ONLY_AUTHORIZATION.md |
| 17 | Residual risk register review | QS-18 | R1_1_4_ACTION_AND_RESIDUAL_RISK_REGISTER.md; 5 open actions |
| 18 | Production gap completeness and disclosure integrity | QS-18 | Technical Baseline §7; Information Security Plan §2 |

---

## Section 3 — Out-of-scope items (with reasons)

| # | Scope ID | Description | Reason out-of-scope |
|---|----------|-------------|---------------------|
| 1 | QS-19 | Production deployment readiness | System is DESIGN_ONLY; no production deployment exists |
| 2 | QS-20 | eHospital live integration testing | eHospital integration NOT_IMPLEMENTED; cannot be tested |
| 3 | QS-21 | Production penetration testing | System not yet production-deployed; ACT-R1-05 OPEN |
| 4 | QS-22 | Real patient data processing validation | Real data processing is BLOCKED by design; no real data may be used |
| 5 | QS-23 | Clinical decision-making validation | System is DESIGN_ONLY; no clinical decisions are made |
| 6 | QS-24 | Ethics and hospital authorization determination | These are decisions of the competent ethics committee and hospital authority; outside qualification scope |
| 7 | QS-25 | Post-market / post-deployment surveillance | System not yet deployed; surveillance scope applies only after deployment |

---

## Section 4 — Evidence package contents (transmitted to assessor after COI accepted)

| # | Item | Path |
|---|------|------|
| E-01 | This scope document | release_evidence/R_GOV_2/submission_ready/independent_qualification/R_GOV_2_INDEPENDENT_ASSESSOR_SCOPE_FINAL.md |
| E-02 | Qualification Readiness Dossier | release_evidence/R_GOV_1/R_GOV_1_INDEPENDENT_QUALIFICATION_READINESS_DOSSIER.md |
| E-03 | Validation Evidence Catalog | release_evidence/R_GOV_1/R_GOV_1_VALIDATION_EVIDENCE_CATALOG.csv |
| E-04 | Security and Technical Qualification Scope | release_evidence/R_GOV_1/R_GOV_1_SECURITY_AND_TECHNICAL_QUALIFICATION_SCOPE.md |
| E-05 | Technical Baseline Confirmation | release_evidence/R_GOV_1/R_GOV_1_TECHNICAL_BASELINE_CONFIRMATION.md |
| E-06 | eHospital Boundary Proposal | release_evidence/R_GOV_1/R_GOV_1_EHOSPITAL_READ_ONLY_BOUNDARY_PROPOSAL.md |
| E-07 | Qualification Decision Template (blank) | release_evidence/R_GOV_1/R_GOV_1_INDEPENDENT_QUALIFICATION_DECISION_TEMPLATE.md |
| E-08 | Human Governance Decision Record | release_evidence/R1_1/R1_1_4_HUMAN_GOVERNANCE_DECISION_RECORD.md |
| E-09 | Action and Residual Risk Register | release_evidence/R1_1/R1_1_4_ACTION_AND_RESIDUAL_RISK_REGISTER.md |
| E-10 | IQ Gate Go/No-Go Register | release_evidence/R_GOV_1/R_GOV_1_INDEPENDENT_QUALIFICATION_GO_NO_GO_REGISTER.md |
| E-11 | Cross-Gate Traceability Matrix | release_evidence/R_GOV_1/R_GOV_1_CROSS_GATE_TRACEABILITY_MATRIX.csv |
| E-12 | R-GOV.1 Freeze Summary | release_evidence/R_GOV_1/R_GOV_1_FREEZE_SUMMARY.md |

---

## Section 5 — Assessor deliverables

| Deliverable | Format | Expected recipient | Timeline |
|------------|--------|-------------------|----------|
| Signed COI declaration | R_GOV_1_INDEPENDENCE_AND_CONFLICT_OF_INTEREST_TEMPLATE.md (completed) | PI | Before assessment begins |
| Scope acceptance (Section 1 above) | This document (Section 1 signed) | PI | Before evidence package transmission |
| Qualification decision | R_GOV_1_INDEPENDENT_QUALIFICATION_DECISION_TEMPLATE.md (completed + signed) | PI | Per agreed timeline |
| Any interim queries | Written communication to PI | PI | Per agreed turnaround |

---

## Section 6 — Mandatory assessor guidance

- The assessor must NOT accept any modification or clarification from the PI, developer, or co-investigator that alters the findings.
- The assessor must NOT seek or accept direction on the decision outcome from any party.
- The assessor IS permitted to query the PI for factual clarifications about system behavior, provided the query is documented.
- The assessor's decision is final. It is not subject to revision by the PI, developer, or any AI agent.
- The current status of the system is `NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE`. The assessor's decision may confirm, extend, or partially lift this status — per the 4 decision options in the qualification decision template.

---

*Independent qualification: NOT STARTED*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs DRAFT — REQUIRE HUMAN REVIEW.*
