# V4.3.4.1 Full Suite Test Report — Fresh Archive

**Version:** 4.3.4.1  
**Date:** 2026-06-28  
**Source:** Fresh archive from `git archive --format=tar v4.3.4`  
**Commit:** `101ca08a331605e95b15cb82a4839e0e2a799e3e`  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Môi trường

```
Platform:        darwin (macOS)
Python:          3.9.6
pytest:          8.4.2
Archive files:   740
Archive bytes:   6,256,640
MRAQ_OFFLINE_CI: 1
API keys:        ALL UNSET
Network:         OFFLINE
```

---

## Kết quả full suite

| Metric | Giá trị |
|--------|---------|
| collected | **781** |
| passed | **776** |
| skipped | **5** |
| failed | **0** |
| errors | 0 |
| Equation | 776 + 5 = 781 ✓ |
| **Verdict** | **PASS** |

---

## 5 tests bị SKIP (vĩnh viễn — không phụ thuộc CI flag)

| Test | Lý do |
|------|-------|
| `tests/test_reference_import.py::test_items_are_verbatim_from_source` | Cần external file |
| `tests/test_v4_4_claude_api_runtime.py::TestT25fLiveApi::test_live_run_returns_fixture_output` | Requires live API |
| `tests/test_v4_4_claude_api_runtime.py::TestT25fLiveApi::test_live_response_has_disclaimer` | Requires live API |
| `tests/test_v4_4_claude_api_runtime.py::TestT25fLiveApi::test_live_no_pii_in_output` | Requires live API |
| `tests/test_v4_4_claude_api_runtime.py::TestT25fLiveApi::test_live_policy_not_pii_blocked` | Requires live API |

**Lưu ý về live API tests:** Đây là live API tests đúng chức năng — chúng SKIP trong archive vì `MRAQ_OFFLINE_CI=1` và keys unset. Đây là hành vi đúng và an toàn.

---

## Skip difference (7 vs 5) — giải thích đầy đủ

Trong working tree **không có** `MRAQ_OFFLINE_CI=1`, có thêm 2 test SKIP:

| Test thêm | Hành vi có CI flag | Hành vi không có CI flag |
|-----------|-------------------|--------------------------|
| `test_offline_ci_guard.py::test_no_api_keys_present` | **PASS** (xác nhận không có keys) | SKIP |
| `test_offline_ci_guard.py::test_network_connect_is_blocked` | **PASS** (xác nhận không có network) | SKIP |

**Kết luận:** Archive với `MRAQ_OFFLINE_CI=1` cho kết quả **tốt hơn** — 2 hermetic guard
tests chuyển SKIP → PASS, xác nhận môi trường offline CI đúng chuẩn.
Không có test nào bị regression.

---

## V4.3.4-specific tests (tập con — 20/781)

```
tests/test_v4_3_4_human_review_operations.py .................... [100%]
20 passed in 0.10s
```

**Tất cả 20 test V4.3.4 PASS trên archive.** Đây là tập con của 781 collected — không cộng thêm.

---

## Manifest và Registry Verify

```
python3 -m compileall -q research_project/ tests/
→ PASS — không có compile error

registry_verify:
  research_project modules: 15
  test files: 69
  has project_review_operations: YES
```

---

## Project Smoke Steps 6–14 (tóm tắt)

| Step | Command | Kết quả |
|------|---------|---------|
| 6 | `project-init` | OK — V4341-SMOKE-001 tại `projects/V4341-SMOKE-001` |
| 7 | `project-build` | OK — 19 artifacts created |
| 8 | `project-qa` | PASS=13 FAIL=0 WARN=2 (placeholder outcomes + empty evidence — expected) |
| 9 | `project-review-list` | OK — 19 artifacts (CRITICAL×3, HIGH×9, MEDIUM×6, LOW×1) |
| 10 | `project-review-record` | OK — RV-C56A2169C273, mode=HUMAN_REVIEW_INDEPENDENCE_NOT_ESTABLISHED |
| 11 | `project-review-status` | OK — Final=0, Draft-only=True, "NO-GO" qualification in output |
| 12 | `project-revision-plan` | OK — 1 revision, 12 stale downstream |
| 13 | `project-review-pack` | OK |
| 14 | `project-reproducibility-check` | OK — 19/19 artifacts present |

---

## Mandatory Assertion Checklist

| Assertion | Kết quả |
|-----------|---------|
| `network_attempts == 0` | ✓ PASS |
| `api_attempts == 0` | ✓ PASS |
| `real_pii_inputs == 0` | ✓ PASS |
| `production_connector_attempts == 0` | ✓ PASS |
| `automation_caller_blocked` (T02) | ✓ PASS |
| `final_released_submitted_count == 0` | ✓ PASS — confirmed in review-status |
| `external_release_blocked` (D-R11, D-R13) | ✓ PASS |
| `draft_only_confirmed` | ✓ PASS |
| `full_suite failed == 0` | ✓ PASS |
| `v434_specific all pass` | ✓ 20/20 PASS |

---

## Security Invariants (preserved verbatim)

```
NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
Real research execution:      BLOCKED
External release/submission:  BLOCKED
Live Agent behavior:          NOT VERIFIED
API connectivity:             NOT RUN
Independent review:           NOT ESTABLISHED
All outputs are DRAFT —       REQUIRE HUMAN REVIEW
```

---

*Manual review record does not constitute ethics, PI, final, or independent approval.*  
*Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT tự động — KHÔNG thực thi thật.*
