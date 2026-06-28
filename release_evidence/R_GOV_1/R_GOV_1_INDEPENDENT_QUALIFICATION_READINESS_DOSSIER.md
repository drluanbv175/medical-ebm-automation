# R-GOV.1 Independent Qualification Readiness Dossier

**Document:** R_GOV_1_INDEPENDENT_QUALIFICATION_READINESS_DOSSIER.md  
**Date:** 2026-06-28  
**Decision ID:** IQ-GOV-01  
**Status:** READY_FOR_EXTERNAL_REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **MANDATORY STATEMENT:**  
> Independent qualification is not established by this dossier.  
> A qualified, independent assessor must review the system evidence,  
> conduct independent verification, and issue a written qualification decision.  
> This dossier prepares the evidence package for that external review.

---

## Part 1 — What independent qualification means

| Concept | Definition |
|---------|-----------|
| Independent qualification | A structured assessment by a person who is independent of the development team, confirming that the system meets specified requirements for research use |
| Assessor independence | The assessor must not be the PI, the system developer, the sole system owner, or the creator of the test evidence being reviewed |
| Qualification scope | Software fitness for purpose as stated in the qualification scope document (IQ-GOV-01) |
| Qualification decision | Written decision issued by the assessor — not by this system, not by Claude Code |
| Effect of qualification | System may be used for the purposes and within the scope stated in the decision |
| Limitation of qualification | Qualification does not replace ethics approval or hospital authorization |

---

## Part 2 — Independence rule (binding constraint)

**The following persons CANNOT serve as the independent assessor:**

| Exclusion | Reason |
|-----------|--------|
| Dr Luân (PI) | Primary developer, sole system owner, creator of technical evidence |
| Any person who wrote or reviewed the source code in this repository | Developer — not independent |
| Any person whose name appears as a co-investigator on the study protocol | Research team — not independent |
| Any agent of this AI system (Claude Code, any sub-agent) | Not human; cannot attest independence |

**The assessor must:**
- Be external to the research team
- Have no financial interest in the outcome
- Have sufficient technical competence to evaluate the software and its test evidence
- Declare COI in writing (see R_GOV_1_INDEPENDENCE_AND_CONFLICT_OF_INTEREST_TEMPLATE.md)
- Be designated by the institution or mutually agreed by PI and institution

---

## Part 3 — System overview for assessor

| Property | Value |
|---------|-------|
| System name | Medical Research OS |
| System type | Offline Python software — research data management, EBM decision support |
| Programming language | Python 3.11+ |
| Test suite | 1049 passed / 0 failed / 5 skipped (MRAQ_OFFLINE_CI=1) |
| Current branch | feat/r1-1-2-design-gap-remediation |
| Agent manifest | 48 agents (PASS, all_hash_verified=True) |
| Qualification phase | R-GOV.1 — readiness for independent qualification |
| Prior governance gate | GATE-R1.1: ACCEPTED_WITH_ACTIONS (VL-GATE-R1.1-2026-002, Dr Luân, SELF_REVIEW) |

---

## Part 4 — What the assessor will evaluate

Full scope: R_GOV_1_SECURITY_AND_TECHNICAL_QUALIFICATION_SCOPE.md

| Domain | Evidence package |
|--------|----------------|
| Offline RBAC and separation of duties | R1.1 phase evidence; tests/test_r1_1_*.py |
| Identity and authentication contract | R1.2 modules; tests/test_r1_2_identity_contract.py |
| Audit retention contract | R1.3 modules; tests/test_r1_3_audit_retention_contract.py |
| Synthetic EDC (Electronic Data Capture) | R2.0 modules; tests/test_r2_0_*.py |
| Study operations compliance | R3.0 evidence documents |
| eHospital read-only boundary contract | R4.0 module; tests/test_r4_0_ehospital_boundary.py |
| Production readiness gaps | R5.0 gap register; R6.0 gate conditions |
| Governance compliance | This pack (R-GOV.1) |
| Agent system integrity | Manifest 48 agents, all_hash_verified=True |

---

## Part 5 — Known gaps that affect qualification scope

The assessor must be informed of and assess the following gaps:

| Gap | Description | Effect on qualification |
|-----|------------|------------------------|
| PROD-AUD-01 | Production WORM audit trail NOT IMPLEMENTED | Qualification scope excludes production audit compliance |
| SSO/MFA | NOT IMPLEMENTED | Qualification scope excludes authenticated multi-user access |
| Production RBAC | NOT IMPLEMENTED | Qualification scope limited to design/contract artifacts |
| ACT-R1-05 | Independent security pentest NOT YET CONDUCTED | Security qualification is limited without pentest evidence |
| Encryption at rest | NOT CONFIRMED | Storage security cannot be affirmed |
| eHospital connection | NOT IMPLEMENTED | Integration qualification deferred |

---

## Part 6 — Pre-requisite for full qualification

| Prerequisite | Status |
|-------------|--------|
| All 1049 tests pass | PASS |
| Ethics approval (ETH-GOV-01) | READY_FOR_EXTERNAL_REVIEW — not yet obtained |
| Hospital authorization (HOSP-GOV-01) | READY_FOR_EXTERNAL_REVIEW — not yet obtained |
| PROD-AUD-01 closed | OPEN |
| SSO/MFA implemented | NOT IMPLEMENTED |
| Production RBAC deployed | NOT IMPLEMENTED |
| Independent pentest (ACT-R1-05) | NOT CONDUCTED |

**Recommendation:** Partial qualification of offline test harness is possible now. Full qualification for research workflow use requires all prerequisites to be met.

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
