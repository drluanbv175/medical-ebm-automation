# R-GOV.1 Hospital Role and Approval Matrix

**Document:** R_GOV_1_HOSPITAL_ROLE_AND_APPROVAL_MATRIX.md  
**Date:** 2026-06-28  
**Decision ID:** HOSP-GOV-01  
**Status:** READY_FOR_EXTERNAL_REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **This matrix is a preparation template — not an authorization.**  
> All decisions require signature from the designated human authority.

---

## Section 1 — Approval authority matrix

| Role | Responsibility | Required for authorization | Status |
|------|--------------|--------------------------|--------|
| Hospital Director / CEO | Institutional authorization of research activity on hospital premises | YES — formal letter or institutional decision | [NOT YET SOUGHT] |
| Head of Research / Research Management Office | Administrative approval of research protocol and data use | YES | [NOT YET SOUGHT] |
| Data Owner (HIS / eHospital administrator) | Grant of read-only data access to approved domains | YES — signed data access agreement | [NOT YET SOUGHT] |
| IT Security Officer | Network and system security review; clearance for software use | YES — security review sign-off | [NOT YET SOUGHT] |
| Legal / Compliance Officer | Data protection review (Decree 13/2023); legal basis for data processing | YES | [NOT YET SOUGHT] |
| Finance / Contracts (if applicable) | MOU or service agreement with institution | [PI TO CONFIRM IF REQUIRED] | [NOT YET ASSESSED] |

---

## Section 2 — Research team roles and responsibilities

| Role | Holder | Responsibilities |
|------|--------|-----------------|
| Principal Investigator (PI) | Dr Luân | Overall responsibility for study conduct, data integrity, regulatory compliance |
| Sub-investigator | [TO BE CONFIRMED BY PI] | Delegated data collection and analysis tasks; per delegation log |
| Data manager | [TO BE CONFIRMED BY PI] | Data extraction coordination with hospital IT; data dictionary maintenance |
| Statistician | [TO BE CONFIRMED BY PI] | SAP implementation; statistical analysis |
| Monitor | [TO BE CONFIRMED BY PI] | Protocol compliance monitoring; data quality checks |
| eHospital liaison | [TO BE CONFIRMED — hospital IT officer] | Coordinate pseudonymized extraction; maintain extraction log |

---

## Section 3 — System access roles (Research OS)

| Role | Access level | Who holds it | Status |
|------|-------------|-------------|--------|
| PI / researcher | Read research dataset; run analysis | Dr Luân | NOT YET AUTHORIZED |
| Data manager | Ingest pseudonymized extract; data dictionary | [TBD] | NOT YET AUTHORIZED |
| System administrator | Software installation and maintenance | [TBD] | NOT YET AUTHORIZED |
| Auditor (internal) | Read-only access to audit trail | [TBD] | NOT YET AUTHORIZED |
| Independent assessor | Read-only access for qualification review | [TBD — must be external/independent] | NOT YET DESIGNATED |

**Note:** SSO/MFA and RBAC are NOT IMPLEMENTED. Role enforcement is currently design-only.

---

## Section 4 — Delegation log requirement

A delegation log must be maintained by the PI. Minimum fields:

| Field | Description |
|-------|------------|
| Sub-investigator name | [PI to fill] |
| Role delegated | [PI to fill] |
| Qualifications | [PI to confirm] |
| Date of delegation | [PI to fill] |
| PI signature | [PI to sign] |
| Sub-investigator acceptance | [Sub-investigator to sign] |
| Tasks delegated | [PI to list] |
| Date ended | [PI to fill when applicable] |

---

## Section 5 — Decision record format (for hospital to complete)

| Field | Hospital to complete |
|-------|---------------------|
| Decision reference | [Hospital internal reference] |
| Decision date | [Date of institutional decision] |
| Decision made by | [Name and title of authorized signatory] |
| Decision | APPROVED / APPROVED WITH CONDITIONS / REJECTED |
| Conditions | [If applicable] |
| Valid until | [Expiry date] |
| Signature | [Authorizing officer signature] |

> **Status: TO BE COMPLETED BY HOSPITAL AUTHORITY**  
> Current status: READY_FOR_EXTERNAL_REVIEW (not yet submitted)

---

## Section 6 — Independence rule for hospital decision

| Rule | Requirement |
|------|------------|
| The authorizing hospital officer must be independent of the research team | YES |
| PI (Dr Luân) cannot authorize their own data access request | MANDATORY |
| Head of Research who is also a co-investigator must recuse | MANDATORY |

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
