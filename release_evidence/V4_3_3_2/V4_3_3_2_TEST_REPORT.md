---
document: V4_3_3_2_TEST_REPORT
version: V4.3.3.2
generated: 2026-06-28
qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
---

# V4.3.3.2 Test Report

## Environment

| Item | Value |
|------|-------|
| Python | 3.9.6 |
| pytest | 8.4.2 |
| Platform | macOS-26.5.1-arm64-arm-64bit |
| MRAQ_OFFLINE_CI | 1 |
| Commit | `30a27f71159bc0a4b7c59156a77145e9f16d9318` |
| Branch | `feat/v4-3-3-2-repository-rationalization` |

---

## A. Working Tree Run

**Command:** `MRAQ_OFFLINE_CI=1 python3 -m pytest tests/test_v4_3_3_project_dossier.py tests/test_v4_3_3_2_gate_corrections.py -v --noconftest`

**Result: 53 passed, 0 failed, 0 skipped — exit 0**

| # | Test | Result |
|---|------|--------|
| 1 | test_01_study_type_enum_all_7_values | ✅ PASS |
| 2 | test_02_artifact_id_enum_19_artifacts | ✅ PASS |
| 3 | test_03_safety_guards_pii_fabrication | ✅ PASS |
| 4 | test_04_charter_has_downstream | ✅ PASS |
| 5 | test_05_mark_stale_propagates | ✅ PASS |
| 6 | test_06_topological_order_no_missing | ✅ PASS |
| 7 | test_07_registry_register_and_load | ✅ PASS |
| 8 | test_08_registry_duplicate_raises | ✅ PASS |
| 9 | test_09_registry_unknown_raises | ✅ PASS |
| 10 | test_10_registry_list_projects | ✅ PASS |
| 11 | test_11_evidence_intake_add_and_load | ✅ PASS |
| 12 | test_12_evidence_intake_blocks_pii | ✅ PASS |
| 13 | test_13_evidence_intake_blocks_retracted_new_add | ✅ PASS |
| 14a–g | test_14_methodology_planner_7_types[all 7 study types] | ✅ PASS ×7 |
| 15 | test_15_methodology_plan_has_rhi_markers | ✅ PASS |
| 16 | test_16_crf_draft_has_sections | ✅ PASS |
| 17 | test_17_reporting_checklist_items_count | ✅ PASS |
| 18 | test_18_dossier_builder_creates_19_artifacts | ✅ PASS |
| 19 | test_19_dossier_builder_blocks_pii | ✅ PASS |
| 20 | test_20_dossier_artifacts_contain_rhi | ✅ PASS |
| 21 | test_21_change_control_creates_record | ✅ PASS |
| 22 | test_22_change_control_blocks_pii | ✅ PASS |
| 23 | test_23_change_control_audit_log_immutable | ✅ PASS |
| 24 | test_24_qa_runner_pass_on_full_dossier | ✅ PASS |
| 25 | test_25_qa_dr10_fails_on_pii_artifact | ✅ PASS |
| 26 | test_26_qa_dr9_fails_on_fabrication | ✅ PASS |
| 27 | test_27_qa_dr11_fails_when_not_draft | ✅ PASS |
| 28 | test_28_review_pack_generates_decisions | ✅ PASS |
| 29 | test_29_review_pack_markdown_has_disclaimer | ✅ PASS |
| 30 | test_30_cli_project_status_lists_all | ✅ PASS |
| I1 | test_invariant_no_api_import | ✅ PASS |
| I2 | test_invariant_all_artifacts_have_filename | ✅ PASS |
| V1 | test_v4332_inv0_no_api_imports | ✅ PASS |
| V2 | test_v4332_dr13_safety_no_submit | ✅ PASS |
| V3 | test_v4332_dr13_safety_blocked_publish | ✅ PASS |
| V4 | test_v4332_dr13_safety_forbidden_email | ✅ PASS |
| V5 | test_v4332_dr13_safety_do_not_post | ✅ PASS |
| V6 | test_v4332_dr13_real_action_submit | ✅ PASS |
| V7 | test_v4332_dr13_real_action_publish | ✅ PASS |
| V8 | test_v4332_dr13_mixed_lines | ✅ PASS |
| V9 | test_v4332_dr13_empty_content | ✅ PASS |
| V10 | test_v4332_dr8_empty_manifest_state | ✅ PASS |
| V11 | test_v4332_dr8_retracted_state | ✅ PASS |
| V12 | test_v4332_dr8_manual_review_state | ✅ PASS |
| V13 | test_v4332_dr8_verified_state | ✅ PASS |
| V14 | test_v4332_dr8_no_evidence_dir | ✅ PASS |
| V15 | test_v4332_integration_fresh_draft_dr13_no_false_positive | ✅ PASS |

---

## B. Hermetic Archive Run

**Source:** `git archive 30a27f7` → isolated extract (no repo state)

**Command:** `MRAQ_OFFLINE_CI=1 python3 -m pytest tests/test_v4_3_3_project_dossier.py tests/test_v4_3_3_2_gate_corrections.py -v --noconftest`

**Result: 53 passed, 0 failed, 0 skipped — exit 0**

Identical result to working tree run. Raw log: `results/v4_3_3_2_hermetic_test_run.txt`

---

## C. Safety Counters

| Counter | Value |
|---------|-------|
| Network calls | 0 |
| API calls (OpenAI/Anthropic/etc.) | 0 |
| Real PII items | 0 |
| Synthetic PII guard cases | 3 |
| Production connector calls | 0 |

---

## D. Gate Verification Summary

### D-R13 — No External Action (corrected)

Before fix: fresh DRAFT project → D-R13 FAIL (false positive on safety text)
After fix: fresh DRAFT project → D-R13 PASS; real action text → D-R13 FAIL (correct)

Verified by: V2–V9 + V15 (9 tests)

### D-R8 — Evidence Status (corrected)

Before fix: empty manifest → generic `GateStatus.WARN`
After fix: empty manifest → `GateStatus.WARN` + `evidence_gate_state = REQUIRE_HUMAN_EVIDENCE_INPUT`

State matrix verified by: V10–V14 (5 tests covering all 4 states + SKIP)

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
*Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT tự động — KHÔNG thực thi thật.*
