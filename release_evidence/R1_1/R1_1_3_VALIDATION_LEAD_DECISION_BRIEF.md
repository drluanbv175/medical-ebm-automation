# R1.1.3 Validation Lead Decision Brief

**Document:** R1_1_3_VALIDATION_LEAD_DECISION_BRIEF.md  
**Date:** 2026-06-28  
**Phase:** R1.1.3 — Human Validation Decision Recording  
**Commit verified:** e806e0e (feat/r1-1-2-design-gap-remediation)  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **To the Validation Lead:**  
> This brief is prepared by Claude Code solely to support your independent review.  
> Claude Code has not made and must not make the validation decision.  
> All blanks in the decision record must be filled by a human.

---

## Point 1 — Intended use of R1.1

R1.1 is an **offline test harness** for verifying research workflow policy logic before any production system is built. Its intended use is:

- Validate that RBAC policy engine correctly allows/blocks 20 research actions across 10 synthetic roles
- Validate that 8 Separation-of-Duties (SoD) guards fire at the correct policy boundaries
- Validate that delegation lifecycle (PROPOSED → ACTIVE → EXPIRED/REVOKED) behaves as specified
- Validate that a SHA-256 hash chain audit ledger detects local tamper scenarios
- Serve as a design-time reference for R1.2 (SSO/MFA design review) and R1.3 (production RBAC service)

R1.1 runs entirely in Python with no network, no authentication, and no real data. All actors, events, and identities are synthetic.

---

## Point 2 — Non-intended use of R1.1

R1.1 **is not** and **must not be used as**:

| Prohibited use | Why not |
|---------------|---------|
| Production access control enforcement | No SSO, no token verification, no network layer |
| Authenticated identity management | All actor IDs are synthetic strings, not verified identities |
| Electronic signature or delegation approval | No cryptographic signing, no real-person attestation |
| Production audit trail | Local JSONL is not WORM; replace-then-rehash is possible with filesystem write access |
| Ethics/IRB approval mechanism | No ethics board, no protocol submission, no regulatory filing |
| Evidence for research activation | GATE-R1 (full identity readiness) has not been reached |
| Independent security validation | No external pentest (IQ-20 deferred to R1.5) |

**R1.1 PASS does not authorize real research execution. Qualification remains NO-GO.**

---

## Point 3 — Baseline commit and full-suite evidence

| Item | Value |
|------|-------|
| Candidate commit | `e806e0e` on `feat/r1-1-2-design-gap-remediation` |
| Baseline frozen tag | `r1.1-frozen` at `9fdfdffed90cb38d2dc56f6cf8604223c4e6d70e` |
| Suite command | `MRAQ_OFFLINE_CI=1 pytest --tb=short -q` |
| Total passed | **867** |
| Total failed | **0** |
| Skipped | 5 (pre-existing, unrelated to R1.1) |
| Network calls | 0 |
| PII in fixtures | 0 |
| Production connectors | 0 |
| Manifest verification | PASS (48 agents, all_hash_verified=True) |
| Working tree at evidence creation | CLEAN |

Fresh archive machine-readable evidence: `R1_1_2_FRESH_ARCHIVE_ACCEPTANCE.json`

---

## Point 4 — Requirement coverage

| Priority | Total requirements | Covered | Uncovered |
|---------|-------------------|---------|-----------|
| CRITICAL | 25 | 25 | **0** |
| HIGH | 14 | 14 | **0** |
| LOW | 5 | 5 | 0 |
| **Total** | **44** | **44** | **0** |

Full traceability: `R1_1_1_REQUIREMENT_TEST_TRACEABILITY_MATRIX.csv` (44 rows × 12 columns).  
No CRITICAL or HIGH requirement is uncovered.

---

## Point 5 — Negative and abuse-case coverage

| Category | Cases | Result | Residual risk |
|---------|-------|--------|---------------|
| SoD violations | 5 | 5 PASS | 1 MEDIUM |
| Delegation abuse | 5 | 5 PASS | 0 |
| Audit tampering | 2 | 2 PASS | 1 MEDIUM |
| Identity overclaim | 2 | 2 PASS | 0 |
| Forbidden action | 3 | 3 PASS | 0 |
| **Total** | **16** | **16 PASS** | **2 MEDIUM** |

Details: `R1_1_1_NEGATIVE_TEST_AND_ABUSE_CASE_REVIEW.md`.  
The 2 MEDIUM residuals are: (a) SoD-07 policy ambiguity (resolved in R1.1.2 / G-04) and (b) replace-then-rehash WORM gap (PROD-AUD-01 deferred).

---

## Point 6 — G-01 to G-04: how each gap was addressed

All four adequacy gaps identified in R1.1.1 were remediated in R1.1.2 (commit `e806e0e`):

| Gap | Finding | Remediation | Test evidence |
|-----|---------|-------------|---------------|
| G-01 | CLI subprocess had no E2E functional tests | Added 4 subprocess tests (`-m research_project.project_cli`) | `TestG01_CLI_Subprocess` — 4 tests pass |
| G-02 | `EXTERNAL_SUBMISSION` and `CLINICAL_RELEASE` had no dedicated tests | Added 3 dedicated tests for exact reason_code | `TestG02_ForbiddenActionDedicated` — 3 tests pass |
| G-03 | `SYSADMIN × LOCK_RESEARCH_DATA` (SoD-02) had no test | Added 2 tests; confirmed `LOCK_RESEARCH_DATA` already in `_RESEARCH_CONTENT_APPROVAL_ACTIONS` | `TestG03_SysAdminLockResearchData` — 2 tests pass |
| G-04 | T14 asserted `reason_code in (EXPIRED_ROLE, ROLE_NOT_PERMITTED)` — policy intent ambiguous | Tightened to `reason_code == EXPIRED_ROLE`; basis: code at line 424–425 definitively returns `EXPIRED_ROLE` when `active_roles=[]` | T14 passes with tightened assertion |

Full traceability: `R1_1_2_GAP_REMEDIATION_TRACEABILITY_MATRIX.csv` (31 rows).

---

## Point 7 — Delegation reason-code remediation

**Before R1.1.2:** `DelegationRegistry.get_status()` returned a plain string; no structured result object; evaluation was binary (status only, no reason).

**After R1.1.2 (commit `e806e0e`):**
- `DelegationReasonCode` enum: 9 values covering all blocking and allowing outcomes
- `DelegationDecision` dataclass: 11 fields including `decision`, `reason_code`, `policy_reference`, `delegation_id`, `effective_until_utc`, `evaluated_at_utc`
- `evaluate_delegation_action()` function: 8-step evaluation order (lookup → revoked → rejected → proposed → expired → forbidden authority → scope exceeded → permit)

Evaluation order ensures: terminal states (REVOKED/REJECTED) checked before expiry; forbidden actions (system-wide pre-RBAC gate) checked before scope; scope checked last before ALLOW.

Test coverage: `TestDEL_ReasonCodes` — 8 tests covering all 9 reason codes and all fields.  
Specification: `R1_1_2_DELEGATION_REASON_CODE_SPEC.md`.

---

## Point 8 — Tamper-evident local ledger boundary

**Classification (as of R1.1.2):**  
`LOCAL_LEDGER_CLASSIFICATION = "TAMPER_EVIDENT_LOCAL_SIMULATION_NOT_WORM"`

**What the local ledger CAN detect** (all 8 scenarios have passing tests):

| Scenario | Test |
|---------|------|
| Modified event content (any field) | WORM-05 |
| Broken previous_event_hash chain link | WORM-06 |
| Sequence number discontinuity | WORM-07 |
| Deleted middle event | WORM-08 |
| Duplicate event_id | WORM-09 |
| Out-of-order sequence_number | WORM-10 |
| Checkpoint WORM boundary declared | WORM-11 |
| Root hash changes on content modification | WORM-12 |

**What the local ledger CANNOT detect** (fundamental limitation):  
An attacker with filesystem write access can replace the entire JSONL file with a new file containing a fresh, internally consistent hash chain. This is the "replace-then-rehash" attack. It is out of scope for offline simulation.

**Truthfulness markers added:**
- `PROD_AUD_01_WORM_DEPENDENCY = "NOT_IMPLEMENTED"` — exported constant
- `checkpoint.production_worm_dependency = "NOT_IMPLEMENTED"` — in every checkpoint record
- No method named `write_worm`, `seal`, `immutable_lock`, or `worm_archive` exists on the ledger

Full specification: `R1_1_2_TAMPER_EVIDENCE_AND_WORM_BOUNDARY.md`.

---

## Point 9 — PROD-AUD-01 WORM dependency

| Item | Value |
|------|-------|
| Identifier | PROD-AUD-01 |
| Status | **OPEN — DEFERRED_TO_PRODUCTION_QUALIFICATION** |
| Target milestone | R1.3 |
| Cannot be closed by | Local pytest, offline simulation, hash chain tests |
| Requires | Write-Once Read-Many (WORM) storage, off-system backup, retention policy, legal hold, access-controlled archive, independent restore verification |
| Current constant in code | `PROD_AUD_01_WORM_DEPENDENCY = "NOT_IMPLEMENTED"` |

PROD-AUD-01 will remain OPEN throughout R1.2. It is a **mandatory prerequisite** for R1.3 and cannot be waived by any R1.1.x decision.

---

## Point 10 — Residual risk MEDIUM: replace-then-rehash

**Risk ID:** RR-02 (from R1.1.1) / AC-11  
**Level:** MEDIUM (unchanged — cannot be lowered without WORM storage)

**Attack scenario:**  
An actor with local filesystem write access to the JSONL audit log file can:
1. Delete or replace the file with a freshly generated file
2. Recompute a valid SHA-256 hash chain over the new content
3. Pass `verify_hash_chain()` because the new chain is internally consistent

**Why this cannot be detected offline:** The local ledger has no external reference (no off-system timestamp, no sealed root hash stored elsewhere, no WORM property preventing overwrite).

**Why this is acceptable for R1.1 scope:**  
R1.1 is an offline design-time simulation. File-level write access to the local simulation environment is not in scope of the offline test model. Production filesystem access control is an infrastructure concern addressed in R1.3.

**Validation Lead must confirm** this residual risk is acceptable for the offline simulation scope (VLD-R1).

---

## Point 11 — Questions requiring Validation Lead response

Three open questions were documented in `R1_1_2_VALIDATION_LEAD_REVIEW_DELTA_PACK.md` and remain pending:

### VLD-R1 — WORM residual risk acceptance

> PROD-AUD-01 (production WORM storage) is NOT IMPLEMENTED and DEFERRED to R1.3. The replace-then-rehash residual risk is MEDIUM and cannot be closed with offline tests. Does the Validation Lead accept this as appropriate for the offline simulation scope of R1.1?

Options: `ACCEPTED` (R1.3 is the right milestone) / `NOT_ACCEPTED` (specify requirement)

### VLD-R2 — G-04 policy intent confirmation

> T14 now asserts `reason_code == EXPIRED_ROLE`. Code reading confirms `evaluate_rbac()` returns `EXPIRED_ROLE` when `active_roles=[]` (all roles expired). `ROLE_NOT_PERMITTED` is reserved for actors with an active role that lacks permission for the requested action. Does the Validation Lead confirm this is the intended policy distinction?

Options: `CONFIRMED` / `DIFFERENT_INTENT` (specify)

### VLD-R3 — DelegationReasonCode completeness

> 9 DelegationReasonCode values were added. Does the Validation Lead confirm these are sufficient for the R1.1 offline simulation scope, with the understanding that production-specific codes (e.g., `DELEGATION_DISABLED_ACTOR` for account suspension) are reserved for R1.3?

Options: `SUFFICIENT` / `INSUFFICIENT` (specify missing values)

---

## Point 12 — Valid decision options

The Validation Lead must choose exactly one of the following four decisions.  
No other decision is valid for this gate.

| Decision | Meaning | Effect on GATE-R1.1 |
|---------|---------|---------------------|
| `ACCEPT_TECHNICAL_TEST_DESIGN` | All evidence is sufficient; no outstanding actions | GATE-R1.1 → PASS |
| `ACCEPT_WITH_ACTIONS` | Evidence is sufficient; named actions must be tracked and completed | GATE-R1.1 → ACCEPTED_WITH_ACTIONS; actions tracked; gate closes when actions done |
| `REVISION_REQUIRED` | Evidence needs specific changes; return to author | GATE-R1.1 → REVISION_REQUIRED (HOLD); R1.2 entry blocked |
| `REJECT_TECHNICAL_TEST_DESIGN` | Fundamental redesign needed | GATE-R1.1 → REJECTED; R1.1 work must restart |

**NOT valid:**  
`PRODUCTION_APPROVED` · `RESEARCH_APPROVED` · `ETHICS_APPROVED` · `INDEPENDENT_VALIDATION_APPROVED` · `WORM_COMPLIANT` · any equivalent

A GATE-R1.1 decision does **not** authorize production use, real research, real data access, or SSO/MFA.

---

## Checklist for Validation Lead before signing

☐ Read `R1_1_1_REQUIREMENT_TEST_TRACEABILITY_MATRIX.csv`  
☐ Read `R1_1_1_NEGATIVE_TEST_AND_ABUSE_CASE_REVIEW.md`  
☐ Read `R1_1_1_VALIDATION_DESIGN_REVIEW.md`  
☐ Read `R1_1_2_VALIDATION_LEAD_REVIEW_DELTA_PACK.md` (R1.1.2 delta)  
☐ Read `R1_1_2_TAMPER_EVIDENCE_AND_WORM_BOUNDARY.md`  
☐ Read `R1_1_2_DELEGATION_REASON_CODE_SPEC.md`  
☐ Answered VLD-R1, VLD-R2, VLD-R3  
☐ Understood that R1.1 is offline simulation only  
☐ Understood that GATE-R1.1 PASS does not authorize research execution  
☐ Selected exactly one of the four valid decisions  
☐ Signed and dated `R1_1_3_VALIDATION_LEAD_DECISION_RECORD_TEMPLATE.md`

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
