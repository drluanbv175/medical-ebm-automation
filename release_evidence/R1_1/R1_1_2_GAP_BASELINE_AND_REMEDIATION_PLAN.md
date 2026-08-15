# R1.1.2 Gap Baseline and Remediation Plan

**Document:** R1_1_2_GAP_BASELINE_AND_REMEDIATION_PLAN.md  
**Date:** 2026-06-28  
**Phase:** R1.1.2 — Design-Gap Remediation and Test Hardening  
**Baseline:** r1.1-frozen (commit 9fdfdff)  
**Branch:** feat/r1-1-2-design-gap-remediation  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Nguồn finding

Tất cả findings trích trực tiếp từ:
- `R1_1_1_VALIDATION_DESIGN_REVIEW.md` §4.4 và §7
- `R1_1_1_NEGATIVE_TEST_AND_ABUSE_CASE_REVIEW.md` AC-05 và AC-11

---

## Gap Baseline Table

| gap_id | exact_original_finding | source_document | risk_level | root_cause | remediation_type | source_change_required | test_change_required | documentation_change_required | acceptance_criteria | residual_risk_after_remediation | validation_lead_reconfirmation_required |
|--------|----------------------|-----------------|------------|------------|-----------------|----------------------|---------------------|-------------------------------|---------------------|---------------------------------|----------------------------------------|
| G-01 | "CLI commands có compile check nhưng không có end-to-end functional test qua subprocess" | R1_1_1_VALIDATION_DESIGN_REVIEW.md §4.4 | LOW | CLI handler functions are tested via module tests only; no test invokes the CLI entrypoint via subprocess | ADD_TEST | No | Yes — add subprocess CLI tests for all 4 commands | Yes — update traceability | Subprocess tests for rbac-simulate, delegation-register, delegation-status, audit-attribution-verify all return exit_code=0 | VERY_LOW — logic tested via module; subprocess verifies entrypoint wire-up | No |
| G-02 | "EXTERNAL_SUBMISSION và CLINICAL_RELEASE được cover qua shared guard path với FINAL_APPROVAL, không có dedicated test" | R1_1_1_VALIDATION_DESIGN_REVIEW.md §4.4 | LOW | Tests T15–T17 use FINAL_APPROVAL and ETHICS_APPROVAL; EXTERNAL_SUBMISSION and CLINICAL_RELEASE share the same pre-RBAC gate but lack independent test evidence | ADD_TEST | No | Yes — add dedicated test per forbidden action | Yes — update traceability | T_G02a: EXTERNAL_SUBMISSION → BLOCK with FORBIDDEN_ACTION_ALL_ROLES; T_G02b: CLINICAL_RELEASE → BLOCK with FORBIDDEN_ACTION_ALL_ROLES; both for METHODS_STATISTICS_REVIEWER as representative non-PI role | LOW — guard path is code-identical; dedicated tests eliminate shared-path concern | No |
| G-03 | "_RESEARCH_CONTENT_APPROVAL_ACTIONS set (SoD-02) không có test cho LOCK_RESEARCH_DATA bị block khi actor là SYSADMIN" | R1_1_1_VALIDATION_DESIGN_REVIEW.md §4.4 | LOW | LOCK_RESEARCH_DATA is in _RESEARCH_CONTENT_APPROVAL_ACTIONS (line 150 of project_rbac_simulation.py) so the guard is implemented; no test exercises this specific action×role combination for SoD-02 | ADD_TEST | No — LOCK_RESEARCH_DATA already in _RESEARCH_CONTENT_APPROVAL_ACTIONS | Yes — add test SYSADMIN cannot LOCK_RESEARCH_DATA | Yes — update traceability | T_G03: SYSADMIN + LOCK_RESEARCH_DATA → BLOCK with ADMIN_RESEARCH_APPROVAL | VERY_LOW — guard already implemented and covered by code path shared with T08 | No |
| G-04 | "Expired role test (T14) chấp nhận cả hai reason_code; Validation Lead cần confirm policy intent" | R1_1_1_VALIDATION_DESIGN_REVIEW.md §4.4; AC-05 in R1_1_1_NEGATIVE_TEST_AND_ABUSE_CASE_REVIEW.md | MEDIUM | T14 asserts `reason_code in (EXPIRED_ROLE, ROLE_NOT_PERMITTED)` making policy intent ambiguous; code at line 424–425 returns EXPIRED_ROLE when active_roles=[] (all roles expired) which is the definitive path | FIX_TEST_ASSERTION | No — code already returns EXPIRED_ROLE for all-roles-expired path | Yes — tighten T14 assertion to EXPIRED_ROLE specifically | Yes — update traceability and VLD-04 resolution | T14 (updated) asserts reason_code==EXPIRED_ROLE; test still passes | LOW — policy intent now unambiguous; ROLE_NOT_PERMITTED remains correct for has-active-role-but-wrong-role scenario (not covered by T14) | No |
| RR-02 / AC-11 | "JSONL ledger không phải WORM; replace-then-rehash possible nếu có write access" (RR-02) + "production requires WORM storage (R1.3) to prevent replace-then-rehash attack; offline JSONL is not WORM" (AC-11) | R1_1_1_VALIDATION_DESIGN_REVIEW.md §7; R1_1_1_NEGATIVE_TEST_AND_ABUSE_CASE_REVIEW.md AC-11 | MEDIUM | Local JSONL is not WORM; description did not explicitly label the local ledger as "simulation" vs "WORM"; replace-then-rehash is an out-of-scope local filesystem attack | TRUTHFULNESS_CORRECTION + ADD_TAMPER_SCENARIOS | Yes — add sequence_number, enhanced tamper detection (sequence discontinuity, duplicate event_id, out-of-order, deleted middle record), ledger_root_hash; fix module label to "tamper-evident local audit ledger simulation"; add PROD_AUD_01 production dependency marker | Yes — add 6 tamper scenario tests; add assertion that ledger output never claims WORM | Yes — WORM boundary document | PROD-AUD-01 remains OPEN/DEFERRED; local tamper scenarios all detect correctly; module never claims WORM | MEDIUM — replace-then-rehash with full-ledger replacement remains out-of-scope for offline simulation; cannot be closed without production WORM (R1.3) | Yes — confirm DEFERRED_TO_PRODUCTION_QUALIFICATION is acceptable |
| DEL-REASON | AC-05 residual: "test allows either reason_code; Validation Lead to confirm whether ROLE_NOT_PERMITTED alone is acceptable or EXPIRED_ROLE specifically required" + missing structured delegation reason codes | R1_1_1_NEGATIVE_TEST_AND_ABUSE_CASE_REVIEW.md AC-05; R1.1.2 spec §Phase C | MEDIUM | Delegation evaluation returns only a status string; no structured decision object with reason_code, policy_reference, delegation_id, effective_until_utc, evaluated_at_utc | ADD_STRUCTURED_RESULT | Yes — add DelegationReasonCode enum + DelegationDecision dataclass + evaluate_delegation_action() to project_delegation_registry.py | Yes — add 4 delegation reason-code tests | Yes — delegation reason-code spec document | All 7 DelegationReasonCode values deterministically returned for their respective scenarios | LOW — offline simulation only; production enforcement deferred to R1.3 | No |

---

## Remediation types legend

| Type | Description |
|------|-------------|
| ADD_TEST | No source change; add test only |
| FIX_TEST_ASSERTION | Tighten existing test to remove ambiguity |
| TRUTHFULNESS_CORRECTION | Update labels/descriptions to be factually accurate without overclaiming |
| ADD_STRUCTURED_RESULT | Add new data class / enum to existing module |

---

## Items that cannot be closed offline

| Item | Status | Reason |
|------|--------|--------|
| PROD-AUD-01: External WORM retention | DEFERRED_TO_PRODUCTION_QUALIFICATION | Requires R1.3 production infrastructure |
| Production RBAC enforcement | DEFERRED_TO_PRODUCTION_QUALIFICATION | Requires R1.3 SSO + RBAC service |
| Independent security pentest (IQ-20) | DEFERRED_TO_PRODUCTION_QUALIFICATION | Requires external tester (R1.5) |

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
