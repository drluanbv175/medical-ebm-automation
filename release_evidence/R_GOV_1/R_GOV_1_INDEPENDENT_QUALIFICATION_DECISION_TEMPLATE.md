# R-GOV.1 Independent Qualification Decision Template

**Document:** R_GOV_1_INDEPENDENT_QUALIFICATION_DECISION_TEMPLATE.md  
**Date:** 2026-06-28  
**Decision ID:** IQ-GOV-01  
**Status:** READY_FOR_EXTERNAL_REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **MANDATORY STATEMENT:**  
> Independent qualification is not established by this dossier.  
> This template is for use by the designated independent assessor only.  
> The completed template, signed by the assessor, constitutes the qualification decision.  
> This system (Medical Research OS, Claude Code) cannot complete, sign, or approve this template.

---

## Section 1 — Assessor identification (assessor to complete)

| Field | Assessor to complete |
|-------|---------------------|
| Assessor name | |
| Assessor title | |
| Assessor institution | |
| Date of assessment | |
| Assessment reference | |
| Independence declaration reference | R_GOV_1_INDEPENDENCE_AND_CONFLICT_OF_INTEREST_TEMPLATE.md (completed copy attached) |

---

## Section 2 — System identification

| Field | Value |
|-------|-------|
| System name | Medical Research OS |
| Version assessed | feat/r1-1-2-design-gap-remediation (commit 2afa99d) |
| Test suite result at time of assessment | [Assessor to confirm by running suite independently] |
| Assessment scope | As defined in R_GOV_1_INDEPENDENT_ASSESSOR_SCOPE_OF_WORK.md |

---

## Section 3 — Domain findings (assessor to complete)

*Use: PASS / PASS WITH CONDITIONS / FAIL / NOT ASSESSED (with reason)*

| Domain | Finding | Conditions / Deficiencies | Evidence reviewed |
|--------|---------|--------------------------|------------------|
| QS-01 Offline RBAC | | | |
| QS-02 Separation of duties | | | |
| QS-03 Delegation controls | | | |
| QS-04 Tamper-evident audit chain (local) | | | |
| QS-05 Identity adapter contract | | | |
| QS-06 Authentication context | | | |
| QS-07 Audit retention contract | | | |
| QS-08 Retention policy definition | | | |
| QS-09 Synthetic EDC — CRF versioning | | | |
| QS-10 Synthetic EDC — record lifecycle | | | |
| QS-11 Synthetic EDC — query lifecycle | | | |
| QS-12 Synthetic EDC — export gating | | | |
| QS-13 Synthetic EDC — correction management | | | |
| QS-14 Synthetic EDC — deviation registry | | | |
| QS-15 eHospital boundary — domain whitelist | | | |
| QS-16 eHospital boundary — PII key guard | | | |
| QS-17 eHospital boundary — zero-write | | | |
| QS-18 Pseudonymization design | | | |

---

## Section 4 — Out-of-scope confirmation (assessor to confirm)

| Out-of-scope domain | Assessor confirms out of scope | Reason |
|--------------------|-------------------------------|--------|
| QS-19 Production WORM audit trail | | PROD-AUD-01 OPEN |
| QS-20 Production SSO/MFA | | NOT IMPLEMENTED |
| QS-21 Production RBAC service | | NOT IMPLEMENTED |
| QS-22 eHospital integration | | NOT IMPLEMENTED |
| QS-23 Encryption at rest | | NOT CONFIRMED |
| QS-24 Independent security pentest | | NOT CONDUCTED |

---

## Section 5 — Overall qualification decision

**Select ONE:**

| Decision | Definition | Assessor selection |
|---------|-----------|-------------------|
| QUALIFIED — UNCONDITIONAL | All in-scope domains PASS; no conditions | [ ] |
| QUALIFIED — CONDITIONAL | Some in-scope domains PASS WITH CONDITIONS; conditions listed below | [ ] |
| NOT QUALIFIED | One or more in-scope domains FAIL; deficiencies listed below | [ ] |
| ASSESSMENT INCOMPLETE | Insufficient evidence to reach a decision; further evidence required | [ ] |

---

## Section 6 — Qualification scope statement (assessor to write)

*The assessor must specify exactly what is qualified and what is not.*

> "The Medical Research OS (commit ______) is qualified for the following purposes and within the following limitations:  
>  
> **Qualified for:** [assessor to state]  
>  
> **Not qualified for:**  
> — Real research workflow execution  
> — Real patient-data processing  
> — Production audit trail (PROD-AUD-01 OPEN)  
> — Production SSO/MFA (NOT IMPLEMENTED)  
> — Production RBAC enforcement (NOT IMPLEMENTED)  
> — eHospital integration (NOT IMPLEMENTED)  
> — [assessor to add any additional limitations]  
>  
> This qualification decision does not constitute ethics approval or hospital authorization."

---

## Section 7 — Conditions (if QUALIFIED — CONDITIONAL)

| Condition # | Description | Responsible | Due date |
|------------|-------------|-------------|---------|
| | | | |

---

## Section 8 — Deficiencies (if NOT QUALIFIED or ASSESSMENT INCOMPLETE)

| Deficiency # | Domain | Description | Corrective action required |
|-------------|--------|-------------|---------------------------|
| | | | |

---

## Section 9 — Assessor signature and certification

> I, the undersigned, certify that:  
> 1. I conducted this assessment independently and without bias.  
> 2. I reviewed the evidence listed in Section 3.  
> 3. The findings in Sections 3–7 reflect my independent professional judgement.  
> 4. I declare no undisclosed conflict of interest.  
> 5. This decision is valid only for the system version and scope stated above.  
> 6. This decision does not constitute ethics approval or hospital authorization.

| Field | Assessor to complete |
|-------|---------------------|
| Assessor signature | |
| Full name (print) | |
| Title | |
| Institution | |
| Date | |

---

## Section 10 — Receipt by PI

| Field | PI to complete |
|-------|---------------|
| Received by | Dr Luân |
| Date received | |
| External document reference | |
| Status update | Record in R_GOV_1_EXTERNAL_DECISION_EVIDENCE_INDEX.csv |
| IQ-GOV-01 status update | APPROVED_EXTERNALLY (if qualified) / REJECTED_EXTERNALLY (if not) |

> **Current IQ-GOV-01 status: READY_FOR_EXTERNAL_REVIEW**  
> This template has not been completed by any assessor. No qualification has been issued.

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
