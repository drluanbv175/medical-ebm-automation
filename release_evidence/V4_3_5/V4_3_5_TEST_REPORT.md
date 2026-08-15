# V4.3.5 Test Report — Evidence Intake & Claim Traceability

**Version:** 4.3.5  
**Date:** 2026-06-28  
**Test file:** `tests/test_v4_3_5_evidence_claim_traceability.py`  
**Status:** DRAFT — REQUIRE HUMAN REVIEW

---

## Tóm tắt

| Metric | Giá trị |
|--------|---------|
| Test mới V4.3.5 | **20 passed** |
| Regression (full suite) | **794 passed, 7 skipped** |
| Test thu thập tổng | **801** |
| FAIL | 0 |
| ERROR | 0 |
| API call trong test | 0 |
| PII trong test data | 0 |

> **Lưu ý:** 20 V4.3.5 test là SUBSET của 801 collected (794 + 7 skip).
> Baseline V4.3.4 có 774 passed + 7 skipped = 781. V4.3.5 thêm 20 test → 794 = 774 + 20.

---

## Danh sách 20 test V4.3.5

| ID | Test name | Mô tả | Kết quả |
|----|-----------|-------|---------|
| T01 | `test_t01_human_provided_only_accepted` | HUMAN_PROVIDED_ONLY được chấp nhận | PASS |
| T02 | `test_t02_auto_retrieved_blocked` | AUTO_RETRIEVED bị block tại ledger | PASS |
| T03 | `test_t03_model_generated_blocked` | MODEL_GENERATED bị block tại ledger | PASS |
| T04 | `test_t04_api_fetched_blocked` | API_FETCHED bị block tại ledger | PASS |
| T05 | `test_t05_unverified_source_cannot_support_claim` | UNVERIFIED → BLOCKED_UNVERIFIED_EVIDENCE | PASS |
| T06 | `test_t06_retracted_source_blocks_claim` | RETRACTED → BLOCKED_RETRACTED_EVIDENCE | PASS |
| T07 | `test_t07_human_verified_source_supports_claim` | HUMAN_VERIFIED → SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE | PASS |
| T08 | `test_t08_no_source_require_human_input` | Không có source → REQUIRE_HUMAN_EVIDENCE_INPUT | PASS |
| T09 | `test_t09_mixed_verified_unverified_blocked` | Hỗn hợp → BLOCKED_UNVERIFIED_EVIDENCE | PASS |
| T10 | `test_t10_ledger_append_only` | Ledger ghi thêm, không ghi đè | PASS |
| T11 | `test_t11_evidence_source_no_pii` | PII trong title → PIIInEvidenceError | PASS |
| T12 | `test_t12_claim_no_pii` | PII trong claim_text → PIIInEvidenceError | PASS |
| T13 | `test_t13_dr8_empty_ledger_require_human_evidence_input` | D-R8 ledger rỗng = WARN + REQUIRE_HUMAN_EVIDENCE_INPUT | PASS |
| T14 | `test_t14_dr8_blocked_unverified_claim_fail` | D-R8 UNVERIFIED claim = FAIL + BLOCK | PASS |
| T15 | `test_t15_dr8_retracted_source_fail` | D-R8 RETRACTED source = FAIL + BLOCK | PASS |
| T16 | `test_t16_dr8_pass_all_verified_no_blocked_claims` | D-R8 tất cả HUMAN_VERIFIED = PASS | PASS |
| T17 | `test_t17_review_queue_routes_to_evidence_citation_reviewer` | Queue → EVIDENCE_CITATION_REVIEWER | PASS |
| T18 | `test_t18_automation_cannot_set_human_verified` | Automation không thể đặt HUMAN_VERIFIED | PASS |
| T19 | `test_t19_cli_has_4_new_subcommands` | CLI có 4 subcommand mới; không import network | PASS |
| T20 | `test_t20_reproducibility_check_still_passes` | Import sạch, FORBIDDEN sets đúng | PASS |

---

## Điều kiện bất biến được kiểm chứng

| Bất biến | Test kiểm | Kết quả |
|----------|-----------|---------|
| Chỉ HUMAN_PROVIDED_ONLY | T01, T02, T03, T04 | PASS |
| UNVERIFIED không support claim | T05, T09 | PASS |
| RETRACTED block claim và D-R8 | T06, T15 | PASS |
| HUMAN_VERIFIED → SUPPORTED | T07 | PASS |
| Không có source → REQUIRE_HUMAN_EVIDENCE_INPUT | T08 | PASS |
| Ledger append-only | T10 | PASS |
| Không PII | T11, T12 | PASS |
| D-R8 V4.3.5 semantics | T13, T14, T15, T16 | PASS |
| Review routing về EVIDENCE_CITATION_REVIEWER | T17 | PASS |
| AutoVerificationForbidden | T18 | PASS |
| Không import network/requests | T19 | PASS |
| Import sạch, không phá backward compat | T20 | PASS |

---

## Skip difference

| Môi trường | Passed | Skipped | Lý do |
|------------|--------|---------|-------|
| Working tree (MRAQ_OFFLINE_CI không set) | 794 | 7 | 5 permanent + 2 hermetic guards skip |
| Fresh archive (MRAQ_OFFLINE_CI=1) | dự kiến 801 | dự kiến 5 | 2 hermetic guards chuyển thành PASS |

_Khác biệt 7→5 skip trong archive là **FAVORABLE** (hermetic guards kích hoạt = an toàn hơn)._

---

## Môi trường

```
Platform:  darwin (macOS)
Python:    3.9.6
pytest:    8.4.2
MRAQ_OFFLINE_CI: not set (deterministic offline tests)
Network:   NONE (OFFLINE)
API calls: NONE
```

---

## Regression check

```
pytest --tb=short -q
794 passed, 7 skipped, 1 warning in 8.23s
```

Không có test nào fail sau khi thêm V4.3.5. Backward compat D-R8 (CSV manifest) được giữ nguyên.

---

*Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT tự động — KHÔNG thực thi thật.*
