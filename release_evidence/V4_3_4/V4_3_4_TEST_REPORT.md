# V4.3.4 Test Report

**Version:** 4.3.4  
**Corrected:** 2026-06-28 (V4.3.4.1 — test count reconciliation + attestation boundary)  
**Status:** DRAFT — REQUIRE HUMAN REVIEW

> **Lưu ý:** Bản V4.3.4 gốc có cách ghi `"Full suite (774 + 20)"` — đây là **SAI**.
> 20 test V4.3.4 là **tập con** của full suite, không phải cộng thêm vào.
> Số đúng từ fresh archive V4.3.4.1: xem bảng bên dưới.

---

## Số liệu từ fresh archive (MRAQ_OFFLINE_CI=1)

| Metric | Working tree (no CI flag) | Fresh archive (MRAQ_OFFLINE_CI=1) |
|--------|--------------------------|-----------------------------------|
| Collected | 781 | 781 |
| Passed | 774 | **776** |
| Skipped | 7 | **5** |
| Failed | 0 | 0 |
| Equation check | 774+7=781 ✓ | 776+5=781 ✓ |

**V4.3.4-specific tests:** 20 (tập con của 781 collected)

### Giải thích skip difference (7 vs 5)

| Test | Không có CI flag | MRAQ_OFFLINE_CI=1 |
|------|-----------------|-------------------|
| `test_offline_ci_guard.py::test_no_api_keys_present` | SKIP | **PASS** |
| `test_offline_ci_guard.py::test_network_connect_is_blocked` | SKIP | **PASS** |
| 5 tests còn lại (live API, reference import) | SKIP | SKIP |

**Lý do:** Hai test trong `test_offline_ci_guard.py` chỉ chạy khi `MRAQ_OFFLINE_CI=1`.
Trong archive, chúng PASS vì API keys unset và network bị chặn.
**Sự khác biệt là có lợi về an toàn** — archive xác nhận hermetic offline CI guard ACTIVE.

---

## 20 test V4.3.4 (tập con — đều PASS trên archive)

| ID | Test name | Kết quả |
|----|-----------|---------|
| T01 | `test_t01_review_role_has_4_values` | PASS |
| T02 | `test_t02_automation_caller_blocked` | PASS |
| T03 | `test_t03_ledger_append_only` | PASS |
| T04 | `test_t04_review_record_13_fields` | PASS |
| T05 | `test_t05_forbidden_review_mode_rejected` | PASS |
| T06 | `test_t06_human_decision_5_values` | PASS |
| T07 | `test_t07_review_mode_2_allowed_values` | PASS |
| T08 | `test_t08_routing_matrix_covers_all_artifacts` | PASS |
| T09 | `test_t09_protocol_draft_critical_risk` | PASS |
| T10 | `test_t10_sap_draft_routed_to_methods_reviewer` | PASS |
| T11 | `test_t11_ledger_empty_when_no_file` | PASS |
| T12 | `test_t12_review_status_counters` | PASS |
| T13 | `test_t13_review_status_has_no_go_qualification` | PASS |
| T14 | `test_t14_revision_plan_empty_when_no_revisions` | PASS |
| T15 | `test_t15_revision_plan_marks_downstream_stale` | PASS |
| T16 | `test_t16_ledger_roundtrip_json` | PASS |
| T17 | `test_t17_review_queue_no_pii` | PASS |
| T18 | `test_t18_make_review_queue_item_structure` | PASS |
| T19 | `test_t19_id_prefixes` | PASS |
| T20 | `test_t20_cli_has_4_new_subcommands` | PASS |

---

## Giới hạn kiểm thử

| Test kiểm | Test không kiểm |
|-----------|----------------|
| `AutoReviewForbidden` khi `automation_caller=True` | Danh tính reviewer thật |
| `ForbiddenReviewMode` khi mode bị cấm | Tính độc lập reviewer |
| Ledger append-only (không delete/update) | Chuyên môn người ghi record |
| `final_released_submitted_count` = 0 | Nội dung `reason` có hợp lý không |
| Không PII trong review queue | Reviewer có thực sự đọc artifact không |
| 4 CLI subcommand có trong parser | Authentication bên ngoài |

---

## Môi trường (fresh archive)

```
Platform:  darwin (macOS)
Python:    3.9.6
pytest:    8.4.2
MRAQ_OFFLINE_CI: 1
ANTHROPIC_API_KEY: unset
OPENAI_API_KEY: unset
EHOSPITAL_ENABLED: unset
Network: OFFLINE
```

---

*Manual review record does not constitute ethics, PI, final, or independent approval.*  
*Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT tự động — KHÔNG thực thi thật.*
