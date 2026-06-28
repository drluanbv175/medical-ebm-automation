# R1.1.3 Validation Lead Decision Record Template

**Document:** R1_1_3_VALIDATION_LEAD_DECISION_RECORD_TEMPLATE.md  
**Date:** 2026-06-28  
**Phase:** R1.1.3 — Phase B  
**Status:** DRAFT — AWAITING HUMAN COMPLETION  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **MANDATORY NOTICE:**  
> This record documents a human governance decision.  
> It does not constitute production authorization, ethics approval,  
> independent validation, or permission to use real research data.

---

## Instructions

This template must be completed by a human Validation Lead.  
Claude Code must not fill, pre-fill, or simulate any field in this record.  
Leave a field blank if the value is not yet determined — do not guess.

All fields marked **(required)** must be completed before this record is considered signed.

---

## Decision Record

---

**decision_id** *(required)*

```
[Validation Lead assigns a unique identifier, e.g. VL-GATE-R1.1-2026-001]

```

---

**decision_date_utc** *(required)*

```
[ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ]

```

---

**reviewer_reference** *(required)*

```
[Full name or institutional role reference of the human Validation Lead]
[Do NOT enter: "Claude Code", "AI", "automated", or any non-human identifier]

```

---

**review_mode** *(required — choose exactly one)*

```
[ ] SELF_REVIEW
    Definition: The Validation Lead is also the PI, developer, or author of the
    evidence being reviewed. Independence has not been established. This is the
    expected mode for initial iterations where a separate reviewer is not available.

[ ] HUMAN_REVIEW_INDEPENDENCE_NOT_ESTABLISHED
    Definition: A human other than the author reviewed the evidence, but formal
    independence (e.g. institutional separation, declared conflict-of-interest check)
    has not been verified or documented.
```

> Note: No mode other than the two above is valid for R1.1.  
> Modes such as `INDEPENDENT_EXPERT_REVIEW` or `EXTERNAL_AUDIT` must not be claimed  
> unless institutional independence has been formally established and documented.

---

**reviewer_role** *(required)*

```
[Actual role of the reviewer, e.g. "Principal Investigator", "Research Coordinator",
"Department Head". Do not enter "Independent Auditor" unless formal independence is documented.]

```

---

**baseline_commit** *(required — do not modify)*

```
e806e0e (feat/r1-1-2-design-gap-remediation)
Branch: feat/r1-1-2-design-gap-remediation
Full SHA: e806e0ea5f553e3f1279af863fa908accc3606e9
Baseline frozen tag: r1.1-frozen at 9fdfdffed90cb38d2dc56f6cf8604223c4e6d70e
Suite result at commit: 867 passed / 0 failed
```

---

**evidence_pack_reference** *(required)*

```
Primary evidence pack: release_evidence/R1_1/
R1.1.1 evidence: R1_1_1_* (7 files)
R1.1.2 evidence: R1_1_2_* (10 files)
R1.1.3 decision support: R1_1_3_* (this file + 5 supporting files)
```

---

**vld_r1_response** *(required — choose one)*

VLD-R1: PROD-AUD-01 WORM dependency acceptance

```
Question: PROD-AUD-01 (production WORM storage) is NOT IMPLEMENTED and DEFERRED to R1.3.
The replace-then-rehash residual risk is MEDIUM and cannot be closed offline.
Is this acceptable for the offline simulation scope of R1.1?

[ ] ACCEPTED — DEFERRED_TO_PRODUCTION_QUALIFICATION (R1.3) is acceptable for offline simulation.
    R1.3 must address WORM retention before production audit attribution is claimed.

[ ] NOT_ACCEPTED — Specify requirement before proceeding:
    [Validation Lead enters requirement here]

```

---

**vld_r2_response** *(required — choose one)*

VLD-R2: G-04 policy intent — EXPIRED_ROLE vs ROLE_NOT_PERMITTED

```
Question: T14 now asserts reason_code == EXPIRED_ROLE (all-roles-expired path).
ROLE_NOT_PERMITTED is reserved for has-active-role-but-wrong-role scenarios.
Is this the intended policy distinction?

[ ] CONFIRMED — EXPIRED_ROLE for all-roles-expired; ROLE_NOT_PERMITTED for wrong-active-role.

[ ] DIFFERENT_INTENT — Specify intended policy:
    [Validation Lead enters intended policy here]

```

---

**vld_r3_response** *(required — choose one)*

VLD-R3: DelegationReasonCode completeness

```
Question: 9 DelegationReasonCode values were added for offline simulation.
Production-specific codes (e.g., account suspension, disabled actor) are reserved for R1.3.
Are 9 values sufficient for the R1.1 offline simulation scope?

[ ] SUFFICIENT — 9 values are sufficient for R1.1 scope.

[ ] INSUFFICIENT — Specify missing values:
    [Validation Lead enters missing values here]

```

---

**decision** *(required — choose exactly one)*

```
[ ] ACCEPT_TECHNICAL_TEST_DESIGN
    Meaning: All evidence is sufficient. No outstanding actions. GATE-R1.1 → PASS.

[ ] ACCEPT_WITH_ACTIONS
    Meaning: Evidence is sufficient but named actions must be tracked and completed
    before R1.1 is considered fully closed. GATE-R1.1 → ACCEPTED_WITH_ACTIONS.
    Actions must be specified in the conditions_or_actions field below.

[ ] REVISION_REQUIRED
    Meaning: Evidence needs specific changes. Return to author for rework.
    GATE-R1.1 → REVISION_REQUIRED (HOLD). R1.2 entry is blocked.

[ ] REJECT_TECHNICAL_TEST_DESIGN
    Meaning: Fundamental redesign needed. GATE-R1.1 → REJECTED.
    R1.1 work must restart from a new baseline.
```

> **NOT VALID:** `PRODUCTION_APPROVED` · `RESEARCH_APPROVED` · `ETHICS_APPROVED` ·  
> `INDEPENDENT_VALIDATION_APPROVED` · `WORM_COMPLIANT` · `RESEARCH_READY` · any equivalent.

---

**decision_rationale** *(required)*

```
[Validation Lead provides rationale for the chosen decision in their own words.
Minimum: one sentence. State what was reviewed and what led to this decision.
Do not copy-paste AI-generated text here — this must reflect the human reviewer's judgment.]

```

---

**conditions_or_actions** *(required if decision = ACCEPT_WITH_ACTIONS or REVISION_REQUIRED)*

```
[If ACCEPT_WITH_ACTIONS: list each action, owner, and due date.
If REVISION_REQUIRED: specify exactly what must be changed.
If ACCEPT_TECHNICAL_TEST_DESIGN or REJECT: enter "N/A"]

Action 1: [Description] — Owner: [Name] — Due: [YYYY-MM-DD]
Action 2: [Description] — Owner: [Name] — Due: [YYYY-MM-DD]
...

```

---

**residual_risks_accepted** *(required)*

```
[List the residual risks the Validation Lead explicitly accepts with this decision.
At minimum, address:
  - RR-02: replace-then-rehash (MEDIUM; PROD-AUD-01 deferred to R1.3)
  - PROD-AUD-01: production WORM retention (NOT IMPLEMENTED)
  - Production RBAC enforcement (NOT IMPLEMENTED)
  - Independent pentest IQ-20 (DEFERRED to R1.5)]

Accepted residual risks:

```

---

**follow_up_owner** *(required if decision = ACCEPT_WITH_ACTIONS)*

```
[Name or role of the person responsible for tracking outstanding actions.
Enter "N/A" if decision is ACCEPT_TECHNICAL_TEST_DESIGN or REJECT.]

```

---

**follow_up_due_date** *(required if decision = ACCEPT_WITH_ACTIONS)*

```
[ISO 8601 date by which all actions must be completed and re-verified.
Enter "N/A" if decision is ACCEPT_TECHNICAL_TEST_DESIGN or REJECT.]

```

---

**signature_or_external_attestation_reference** *(required)*

```
[One of the following:
  a) Physical/wet signature: "Signed — [Name], [Date]"
  b) Electronic signature reference: "[System], [Signature ID], [Date]"
  c) External document reference: "[Document title/number], [Date]"
  d) Institutional acknowledgement: "[Institution], [Process], [Date]"

The signature attests that the human identified in reviewer_reference
read the evidence pack and made this decision personally.
AI tools must not sign this field.]

```

---

## Mandatory limitation acknowledgement

By signing this record, the Validation Lead acknowledges:

☐ R1.1 is an offline Python simulation. It does not enforce access control in any production system.  
☐ GATE-R1.1 PASS does not authorize real research execution, real data access, or clinical use.  
☐ SSO, MFA, authenticated identity, and production audit attribution remain NOT IMPLEMENTED.  
☐ PROD-AUD-01 (WORM storage) remains OPEN and deferred to R1.3.  
☐ Independent security pentest (IQ-20) has not been conducted.  
☐ This record does not constitute ethics or IRB approval.

---

*This template is DRAFT. It must be completed by a human Validation Lead.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
