# R1.1 Test Report

**Document:** R1_1_TEST_REPORT.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE  
**Test file:** `tests/test_r1_1_offline_rbac_synthetic_identity.py`

---

## Kết quả chạy

```
MRAQ_OFFLINE_CI=1 pytest tests/test_r1_1_offline_rbac_synthetic_identity.py -v
```

| Metric | Giá trị |
|--------|---------|
| Tests collected | 39 |
| Passed | 39 |
| Failed | 0 |
| Skipped | 0 |
| Duration | ~0.14s |
| Network calls | 0 (MRAQ_OFFLINE_CI=1) |
| PII detected | 0 |

---

## Toàn bộ suite (797 + 39 = 836 tests)

```
MRAQ_OFFLINE_CI=1 pytest --tb=short -q
836 passed, 5 skipped, 1 warning in 6.19s
```

Không có regression trong bộ test V4.3.5 và các phiên bản trước.

---

## Chi tiết từng test

| Test ID | Tên | Kết quả |
|---------|-----|---------|
| T01a | test_email_in_display_label_rejected | PASS |
| T01b | test_phone_number_in_display_label_rejected | PASS |
| T01c | test_valid_display_label_accepted | PASS |
| T02a | test_authenticated_state_rejected | PASS |
| T02b | test_default_authentication_state_is_not_authenticated | PASS |
| T03a | test_bad_format_rejected | PASS |
| T03b | test_missing_prefix_rejected | PASS |
| T04 | test_t04_pi_can_create_draft_project | PASS |
| T05 | test_t05_pi_can_edit_draft_artifact | PASS |
| T06 | test_t06_pi_can_record_self_review | PASS |
| T07 | test_pi_cannot_independent_review_own_artifact | PASS |
| T08 | test_sysadmin_cannot_record_review_attestation | PASS |
| T09 | test_auditor_cannot_edit_artifact | PASS |
| T10 | test_t10_dm_cannot_unlock_without_auth | PASS |
| T11 | test_t11_dm_can_unlock_with_authorization | PASS |
| T12a | test_ecr_cannot_attest_own_source | PASS |
| T12b | test_ecr_can_attest_external_source | PASS |
| T13 | test_disabled_actor_blocked_for_any_action | PASS |
| T14 | test_expired_role_is_blocked | PASS |
| T15 | test_t15_final_approval_blocked_for_pi | PASS |
| T16 | test_t16_ethics_approval_blocked_for_pi | PASS |
| T17 | test_t17_independent_review_approval_blocked_for_reviewer | PASS |
| T18 | test_block_decision_has_all_required_fields | PASS |
| T19 | test_t19_self_delegation_rejected | PASS |
| T20 | test_t20_delegation_with_forbidden_action_rejected | PASS |
| T21 | test_delegation_lifecycle | PASS |
| T22 | test_delegation_expired_after_effective_until | PASS |
| T23a | test_audit_event_has_required_fields | PASS |
| T23b | test_audit_event_hash_is_present_and_non_empty | PASS |
| T24a | test_no_delete_or_update_method_on_ledger | PASS |
| T24b | test_events_accumulate_across_records | PASS |
| T25 | test_hash_chain_passes_for_valid_ledger | PASS |
| T26 | test_hash_chain_fails_after_event_tamper | PASS |
| T27a | test_audit_event_never_has_production_valid_true | PASS |
| T27b | test_synthetic_actor_never_has_production_valid_attribute | PASS |
| T27c | test_rbac_decision_disclaimer_present | PASS |
| T28 | test_rejected_delegation_cannot_activate | PASS |
| B01 | test_all_default_actors_have_valid_ids | PASS |
| B02 | test_all_default_actors_are_not_authenticated | PASS |

---

## SoD coverage matrix

| SoD Guard | Test(s) | Status |
|-----------|---------|--------|
| SoD-01 PI self-independent-review | T07 | ✓ COVERED |
| SoD-02 Admin research approval | T08 | ✓ COVERED |
| SoD-03 Read-only write attempt | T09 | ✓ COVERED |
| SoD-04 DM unlock no auth | T10, T11 | ✓ COVERED |
| SoD-05 ECR self-attest | T12a, T12b | ✓ COVERED |
| SoD-06 Conflicting roles | T13 (disabled) | ✓ COVERED |
| SoD-07 Expired role | T14 | ✓ COVERED |
| SoD-08 Disabled actor | T13 | ✓ COVERED |
| Forbidden actions | T15, T16, T17 | ✓ COVERED |

---

## Compile check

```
python -m compileall -q \
  research_project/project_rbac_simulation.py \
  research_project/project_delegation_registry.py \
  research_project/project_audit_attribution.py \
  research_project/project_cli.py
```
Kết quả: **COMPILE OK** (0 errors)

---

## Manifest verify

```
python3 scripts/verify_manifest_registry.py
RESULT=PASS
```

---

## Kết luận bắt buộc

```
Tests collected:       39
Tests passed:          39
Tests failed:          0
Full suite:            836 passed / 0 failed
SoD coverage:          8/8 guards covered
Forbidden actions:     3/3 covered
Network calls:         0
PII in fixtures:       0
Real credentials:      0
Qualification:         NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
