# R-GOV.1 Independent Assessor Scope of Work

**Document:** R_GOV_1_INDEPENDENT_ASSESSOR_SCOPE_OF_WORK.md  
**Date:** 2026-06-28  
**Decision ID:** IQ-GOV-01  
**Status:** READY_FOR_EXTERNAL_REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **Independent qualification is not established by this dossier.**  
> This document defines the scope for the independent assessor to execute.

---

## Section 1 — Background

The Medical Research OS is an offline Python software system developed to support evidence-based medicine and research data management. Before the system may be used for real research workflows involving real patient data, an independent qualified assessor must confirm that the system meets specified requirements within the scope defined in this document.

---

## Section 2 — Assessor designation

| Requirement | Detail |
|------------|--------|
| Independence | External to research team; not PI, not co-developer, not co-investigator |
| COI declaration | Required (R_GOV_1_INDEPENDENCE_AND_CONFLICT_OF_INTEREST_TEMPLATE.md) |
| Competencies required | Python software review, clinical research software, GCP/ICH E6, data protection |
| Designated by | Institution / Research Management Office (not PI) |
| Assessor name | [TO BE DESIGNATED BY INSTITUTION] |
| Designation date | [TO BE CONFIRMED] |

---

## Section 3 — Assessment scope

### 3.1 In-scope

| Domain | Evidence to review |
|--------|-------------------|
| S01 — Test suite integrity | Verify 1049/0/5 pass/fail/skip result; review test logic for meaningful coverage |
| S02 — RBAC and SoD offline design | R1.1 phase evidence; policy engine; separation of duties; delegation controls |
| S03 — Identity contract design | R1.2 modules; identity adapter interface; SyntheticIdentityAdapter disclaimers |
| S04 — Audit retention contract | R1.3 modules; WriteReceipt fake-WORM guard; retention policy constants |
| S05 — Synthetic EDC | R2.0 modules; CRF versioning; record lifecycle; query management; deviation registry; export gating |
| S06 — eHospital boundary contract | R4.0 module; domain whitelist/blocklist; PII key guard; zero-write interface |
| S07 — Governance compliance | R-GOV.1 pack; decision state model; open actions register |
| S08 — Agent manifest integrity | 48 agents; all_hash_verified=True; 4 required agents present |
| S09 — NOT_IMPLEMENTED constants | Verify all production dependency constants are non-empty and accurate |
| S10 — Prohibited state absence | Verify no AUTO_APPROVED / AI_APPROVED states appear in any document or code |

### 3.2 Out-of-scope for this qualification round

| Domain | Reason out of scope |
|--------|-------------------|
| Production SSO/MFA integration | NOT IMPLEMENTED |
| Production WORM audit trail | NOT IMPLEMENTED (PROD-AUD-01 OPEN) |
| Production RBAC enforcement service | NOT IMPLEMENTED |
| eHospital network integration | NOT IMPLEMENTED |
| Encryption at rest | NOT CONFIRMED |
| Real patient data processing | BLOCKED |
| Independent security penetration test | Deferred to R1.5 (ACT-R1-05) |
| Clinical effectiveness validation | Beyond software qualification scope |

---

## Section 4 — Assessment method

| Method | Description |
|--------|------------|
| Document review | Read all evidence documents in release_evidence/ |
| Test suite audit | Run `MRAQ_OFFLINE_CI=1 pytest --tb=short -q` independently; verify result matches claimed 1049/0/5 |
| Code review | Review in-scope source modules for NOT_IMPLEMENTED declarations, fake-WORM guards, PII guards |
| Independence of evidence | Confirm evidence was not wholly self-generated (review commit history, self-review disclosure) |
| Gap register review | Review R5.0/R6.0 gap registers; confirm all known gaps are disclosed |
| Prohibited language check | Confirm no self-approval language in any document |

---

## Section 5 — Assessment deliverables

| Deliverable | Description |
|------------|-------------|
| Independence declaration | COI form completed; independence confirmed in writing |
| Assessment report | Findings per domain (S01–S10); gaps noted; questions raised |
| Qualification decision | Written decision using R_GOV_1_INDEPENDENT_QUALIFICATION_DECISION_TEMPLATE.md |
| Scope statement | Clear statement of what is and is not qualified |
| Recommendation | Unconditional / Conditional / Decline — with conditions if applicable |

---

## Section 6 — Assessment timeline (to be agreed with assessor)

| Milestone | Target date |
|----------|------------|
| Assessor designated by institution | [TO BE CONFIRMED] |
| COI declaration submitted | [TO BE CONFIRMED] |
| Evidence package received by assessor | [TO BE CONFIRMED — after IQ-GOV-01 submitted] |
| Questions from assessor to PI | [TO BE CONFIRMED] |
| PI responses to assessor questions | [TO BE CONFIRMED] |
| Draft assessment report | [TO BE CONFIRMED] |
| Final qualification decision | [TO BE CONFIRMED] |

---

## Section 7 — Evidence package contents

The assessor will receive:

| # | Item | Location |
|---|------|---------|
| 1 | Source code (all in-scope modules) | `research_project/*.py` |
| 2 | Full test suite | `tests/test_r1_1_*.py`, `test_r1_2_*.py`, `test_r1_3_*.py`, `test_r2_0_*.py`, `test_r4_0_*.py` |
| 3 | Phase evidence documents | `release_evidence/R1_1/`, `R1_2/`, `R1_3/`, `R2_0/`, `R3_0/`, `R4_0/`, `R5_0/`, `R6_0/`, `PROGRAM/` |
| 4 | R-GOV.1 governance pack | `release_evidence/R_GOV_1/` (this pack) |
| 5 | Agent manifest | `runtime/manifests/agent_source_manifest.csv` |
| 6 | Plans.md | Research OS sprint plans |
| 7 | AGENTS.md | Agent descriptions and role boundaries |

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
