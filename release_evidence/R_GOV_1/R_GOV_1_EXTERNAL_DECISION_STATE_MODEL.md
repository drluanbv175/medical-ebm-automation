# R-GOV.1 External Decision State Model

**Document:** R_GOV_1_EXTERNAL_DECISION_STATE_MODEL.md  
**Date:** 2026-06-28  
**Role:** R-GOV.1 Ethics, Hospital Authorization and Independent Qualification Readiness Lead  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## 1. Purpose

This document defines the valid state model for external governance decisions required before the Medical Research OS may be used for real research activity. All decisions are made by external parties — not by this system, not by Claude Code.

---

## 2. Valid external decision states

| State | Description |
|-------|-------------|
| `NOT_STARTED` | No work begun toward this decision |
| `PREPARING` | Documentation being assembled for submission |
| `READY_FOR_EXTERNAL_REVIEW` | Dossier complete; awaiting external submission by PI |
| `SUBMITTED_EXTERNALLY` | PI has submitted to external authority; awaiting decision |
| `REVISION_REQUESTED` | External authority has requested revision; PI preparing response |
| `APPROVED_EXTERNALLY` | External authority has issued formal approval (evidence required) |
| `REJECTED_EXTERNALLY` | External authority has formally rejected; amendment or re-submission required |
| `EXPIRED` | Prior approval has passed expiry date; renewal required |
| `AMENDMENT_REQUIRED` | Protocol or system change triggers re-review |

---

## 3. Prohibited states

The following states MUST NOT appear in any register, document, or system record:

| Prohibited state | Reason |
|----------------|--------|
| `AUTO_APPROVED` | External approval requires external human decision |
| `SYSTEM_APPROVED` | No AI system may grant ethics, hospital, or qualification approval |
| `AI_APPROVED` | Prohibited |
| `ETHICS_APPROVED_BY_SYSTEM` | Prohibited |
| `HOSPITAL_APPROVED_BY_SYSTEM` | Prohibited |
| `INDEPENDENTLY_QUALIFIED_BY_SYSTEM` | Prohibited |

---

## 4. State transition rules

```
NOT_STARTED
  → PREPARING (PI begins dossier preparation)
  → READY_FOR_EXTERNAL_REVIEW (dossier complete per phase checklist)
  → SUBMITTED_EXTERNALLY (PI submits to external authority — human action required)
  → REVISION_REQUESTED (external authority responds — human confirmation required)
  → APPROVED_EXTERNALLY (external authority issues decision — evidence required)
  → REJECTED_EXTERNALLY (external authority issues decision — evidence required)
  → EXPIRED (after approval_expiry_date — automatic)
  → AMENDMENT_REQUIRED (triggered by protocol/system change)
```

**Status may not skip to APPROVED_EXTERNALLY without:**
1. External authority decision document
2. Human (PI) confirmation of authenticity
3. Evidence recorded in R_GOV_1_EXTERNAL_DECISION_EVIDENCE_INDEX.csv

---

## 5. Maximum status without external document

If no external decision document has been supplied and human-confirmed:

```
Maximum status: READY_FOR_EXTERNAL_REVIEW
```

---

## 6. Current status of all three decisions

| Decision domain | Decision ID | Status |
|----------------|-------------|--------|
| Ethics review | ETH-GOV-01 | READY_FOR_EXTERNAL_REVIEW |
| Hospital / institutional authorization | HOSP-GOV-01 | READY_FOR_EXTERNAL_REVIEW |
| Independent qualification | IQ-GOV-01 | READY_FOR_EXTERNAL_REVIEW |

---

## 7. Governance invariants

```
This state model does not grant any approval.
No state in this model overrides the global qualification verdict.
Global qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
