# R1.1.3 Gate R1.1 Decision Options

**Document:** R1_1_3_GATE_R1_1_DECISION_OPTIONS.md  
**Date:** 2026-06-28  
**Phase:** R1.1.3 — Phase C  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **Recommendation only.**  
> Final decision must be made by the designated human Validation Lead.  
> Claude Code provides analysis to inform — not to substitute — the human decision.

---

## Overview of four valid decision paths

| Decision | One-line meaning |
|---------|-----------------|
| `ACCEPT_TECHNICAL_TEST_DESIGN` | All evidence sufficient; no outstanding actions |
| `ACCEPT_WITH_ACTIONS` | Evidence sufficient; named conditions must be tracked |
| `REVISION_REQUIRED` | Evidence needs specific changes; return to author |
| `REJECT_TECHNICAL_TEST_DESIGN` | Fundamental redesign needed |

---

## Decision 1 — ACCEPT_TECHNICAL_TEST_DESIGN

### When appropriate

Choose this when the Validation Lead is satisfied that:
- All 44 requirements are covered with sufficient evidence
- All 4 adequacy gaps (G-01–G-04) are adequately remediated
- All 16 abuse cases are PASS with no unacceptable residuals
- The tamper-evident ledger is correctly described as local simulation (not WORM)
- Delegation reason codes are sufficient for offline simulation scope
- Residual risks (PROD-AUD-01, replace-then-rehash) are explicitly accepted as deferred
- No open technical actions remain

### Minimum evidence required

All of the following must be reviewed and found satisfactory:
- `R1_1_1_REQUIREMENT_TEST_TRACEABILITY_MATRIX.csv` — 44 requirements, 0 uncovered
- `R1_1_1_NEGATIVE_TEST_AND_ABUSE_CASE_REVIEW.md` — 16 PASS, residuals acceptable
- `R1_1_2_FRESH_ARCHIVE_ACCEPTANCE.json` — 867 passed / 0 failed
- `R1_1_2_GAP_REMEDIATION_TRACEABILITY_MATRIX.csv` — all 31 rows accepted
- VLD-R1, VLD-R2, VLD-R3 all answered in the decision record

### Effect on GATE-R1.1

GATE-R1.1 → **PASS**  
R1.2 entry is authorized for design-scope activities (see `R1_1_3_R1_2_ENTRY_CRITERIA.md`).

### Effect on R1.2 entry

R1.2 may begin. Scope limited to SSO/MFA design review and institutional IT engagement.  
R1.2 must not implement production SSO, enable real user access, or process real data.

### Effect on PROD-AUD-01

PROD-AUD-01 remains **OPEN**. It does not close when GATE-R1.1 passes.  
It is a mandatory prerequisite for R1.3. It cannot be waived by this decision.

### Effect on real research status

**Real research execution remains BLOCKED.**  
GATE-R1.1 PASS is one precondition of many; GATE-R1, GATE-R2, GATE-R3 must also pass.

---

## Decision 2 — ACCEPT_WITH_ACTIONS (Technical Recommendation)

### When appropriate

Choose this when:
- Evidence is substantially sufficient but one or more named actions need tracking
- The Validation Lead wants to proceed to R1.2 design scope while ensuring explicit follow-up on deferred items
- The PROD-AUD-01 residual needs to be explicitly tracked as an open action item
- VLD-R1/R2/R3 answers are acceptable but the reviewer wants confirmations recorded

This is the **technically recommended path** given current evidence state.

### Minimum evidence required

Same as ACCEPT_TECHNICAL_TEST_DESIGN, plus:
- Each named action must have: description, owner, due date
- PROD-AUD-01 must be listed as Action 1 with R1.3 as the milestone
- All named actions must be completed before the gate is considered fully PASS

### Recommended minimum conditions for ACCEPT_WITH_ACTIONS

If this decision is chosen, the following five conditions are the minimum the Validation Lead should record:

```
Condition 1: PROD-AUD-01 (production WORM retention) remains explicitly OPEN.
             It must be addressed before R1.3 claims production audit readiness.
             Owner: PI / R1.3 lead. Target: R1.3 qualification.

Condition 2: The local audit ledger must be described only as
             "tamper-evident local simulation" in all downstream documentation.
             Neither R1.2 nor R1.3 documents may describe it as WORM or immutable
             until PROD-AUD-01 is closed.

Condition 3: No production identity system, real SSO, or real MFA is activated
             in R1.2. R1.2 is design-approval scope only.

Condition 4: R1.3 must not claim production audit readiness until PROD-AUD-01
             is addressed with a verified WORM-capable retention solution.

Condition 5: Independent security pentest (IQ-20) remains scheduled for R1.5
             and must not be claimed as completed or waived without external
             tester engagement.
```

### Effect on GATE-R1.1

GATE-R1.1 → **ACCEPTED_WITH_ACTIONS**  
Gate is not fully PASS until all named actions are completed and re-confirmed by the Validation Lead.

### Effect on R1.2 entry

R1.2 design-scope entry is **authorized** subject to conditions 1–5 above.  
R1.2 must not exceed design-scope activities (see `R1_1_3_R1_2_ENTRY_CRITERIA.md`).

### Effect on PROD-AUD-01

PROD-AUD-01 is recorded as an **explicit tracked open action** targeting R1.3.  
It does not close with GATE-R1.1.

### Effect on real research status

**Real research execution remains BLOCKED.**  
ACCEPTED_WITH_ACTIONS does not authorize research execution.

---

## Decision 3 — REVISION_REQUIRED

### When appropriate

Choose this when:
- One or more specific deficiencies are found that the author must correct
- The evidence is not sufficient as submitted — not a fundamental architecture problem, but needs rework
- VLD-R1, VLD-R2, or VLD-R3 answers reveal a gap that must be closed before proceeding
- The Validation Lead identifies a specific error in test logic, coverage, or documentation

### Minimum evidence required

The Validation Lead must specify:
- Exactly which evidence file(s) are deficient
- What specific correction is needed
- What the acceptance criterion for the revised submission is

### Effect on GATE-R1.1

GATE-R1.1 → **REVISION_REQUIRED (HOLD)**  
Author must address all identified deficiencies and resubmit for VL review.  
No new baseline tag or commit is created until the revision is accepted.

### Effect on R1.2 entry

**R1.2 entry is BLOCKED** until GATE-R1.1 is re-reviewed and reaches ACCEPTED or ACCEPTED_WITH_ACTIONS.

### Effect on PROD-AUD-01

No change. PROD-AUD-01 remains OPEN as before.

### Effect on real research status

**Real research execution remains BLOCKED.**

---

## Decision 4 — REJECT_TECHNICAL_TEST_DESIGN

### When appropriate

Choose this when:
- The test harness design has a fundamental architectural flaw that cannot be corrected by revision
- The policy model (RBAC, SoD, delegation) is structurally incorrect
- The evidence approach is not suitable for verifying the stated requirements
- The Validation Lead determines that R1.1 cannot serve its intended purpose regardless of changes

### Minimum evidence required

The Validation Lead must document:
- The specific architectural or structural reason for rejection
- Why revision cannot address the underlying problem
- What redesign would be needed

### Effect on GATE-R1.1

GATE-R1.1 → **REJECTED**  
R1.1 work must restart from a new design baseline.  
Existing r1.1-frozen tag and evidence remain in the record but the R1.1 track is closed.

### Effect on R1.2 entry

**R1.2 entry is BLOCKED** indefinitely until a new R1.1 baseline is established.

### Effect on PROD-AUD-01

No change. PROD-AUD-01 remains OPEN.

### Effect on real research status

**Real research execution remains BLOCKED.**

---

## Technical recommendation

```
Recommended decision: ACCEPT_WITH_ACTIONS

Rationale (technical, not a governance decision):
  - 867 tests pass with 0 failures; 44 requirements covered; 16 abuse cases PASS
  - G-01 through G-04 all remediated with passing tests
  - WORM boundary is correctly labeled and tested
  - Delegation reason codes are structured and tested
  - PROD-AUD-01 is explicitly marked NOT_IMPLEMENTED with a deferred milestone
  - The remaining MEDIUM residual (replace-then-rehash) is an inherent property
    of local filesystem storage, not a deficiency of the test design
  - ACCEPT_WITH_ACTIONS allows R1.2 design scope to begin while ensuring
    PROD-AUD-01 and the local ledger scope limitation are tracked explicitly

Minimum conditions recommended: see Condition 1–5 above.

Recommendation only.
Final decision must be made by the designated human Validation Lead.
```

---

## Quick reference

| Criterion | ACCEPT | ACCEPT_WITH_ACTIONS | REVISION_REQUIRED | REJECT |
|-----------|--------|--------------------|--------------------|--------|
| GATE-R1.1 | PASS | ACCEPTED_WITH_ACTIONS | REVISION_REQUIRED | REJECTED |
| R1.2 entry | Authorized | Authorized (design only) | BLOCKED | BLOCKED |
| PROD-AUD-01 | Still OPEN | Tracked as action | Still OPEN | Still OPEN |
| Real research | BLOCKED | BLOCKED | BLOCKED | BLOCKED |
| Author action needed | None | Complete named actions | Revise evidence | Redesign R1.1 |

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
