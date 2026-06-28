# V4.3.4 Executive Summary — Human Review Operations

**Version:** 4.3.4  
**Corrected:** 2026-06-28 (V4.3.4.1 — documentation truthfulness pass)  
**Base:** `v4.3.3.2-frozen` (commit `0ce0d47`)  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Tóm tắt một dòng

V4.3.4 bổ sung **Manual Review Attestation Layer** — một lớp yêu cầu ghi nhận thủ công
trước khi dossier chuyển bước nội bộ. Hệ thống **chặn automation tự ghi review record**,
nhưng **không xác thực danh tính, không xác minh tính độc lập của reviewer**.

---

## Những gì được thêm

### 1 source module mới
**`research_project/project_review_operations.py`**:
- `ReviewRole` enum — 4 vai trò (label routing, không xác thực danh tính)
- `ReviewMode` enum — 2 mode hợp lệ; 4 mode bị tường minh cấm
- `HumanDecision` enum — 5 quyết định hợp lệ
- `RiskLevel` enum — CRITICAL/HIGH/MEDIUM/LOW
- `ReviewRecord` dataclass — 13 trường, manual-attestation record
- `ReviewLedger` class — ghi `review_ledger.jsonl`, append-only
- `REVIEW_ROUTING_MATRIX` — ánh xạ 19 ArtifactID → role + focus + risk + gate
- `AutoReviewForbidden` — block automation-originated record
- `ForbiddenReviewMode` — block invalid mode strings
- `record_decision()`, `list_review_queue()`, `get_review_status()`, `build_revision_plan()`

### 4 CLI subcommand mới (trong `project_cli.py`)
| Subcommand | Chức năng |
|------------|-----------|
| `project-review-list` | Liệt kê artifact cần review + role + risk |
| `project-review-record` | Ghi manual attestation record (automation bị block) |
| `project-review-status` | Tổng hợp counters — không có "final/approved" |
| `project-revision-plan` | Kế hoạch revision từ REVISION_REQUIRED |

### 1 test file mới
**`tests/test_v4_3_4_human_review_operations.py`** — 20 test, được kiểm chứng
trong full suite (xem test report để biết count chính xác).

---

## Bất biến kỹ thuật được đảm bảo

| Bất biến | Cơ chế kỹ thuật |
|----------|-----------------|
| Automation không thể ghi review record | `AutoReviewForbidden` khi `automation_caller=True` |
| Các mode bị cấm không thể được lưu | `ForbiddenReviewMode` trong `ReviewLedger.append()` |
| Ledger append-only | Chỉ có `append()` — không có `delete()` hay `update()` |
| Không có artifact final/released/submitted | `final_released_submitted_count` luôn = 0 |
| Không PII | Guard trong `list_review_queue()` và `record_decision()` |
| No-overwrite | Revision plan yêu cầu tạo version mới, không ghi đè |

## Giới hạn hệ thống — KHÔNG được đảm bảo kỹ thuật

| Giới hạn | Lý do |
|----------|-------|
| Danh tính reviewer không được xác thực | Hệ thống không có authentication layer |
| Tính độc lập reviewer không được xác minh | Không có cơ chế kiểm tra xung đột lợi ích |
| Phê duyệt ethics/PI không được xác lập | Record chỉ là manual attestation, không phải approval chính thức |
| Số liệu đếm review không phản ánh chất lượng | Ledger ghi số lần, không đánh giá nội dung |

---

## Test count (V4.3.4.1 reconciled)

Xem `V4_3_4_1_FULL_SUITE_TEST_REPORT.md` để có số liệu chính xác từ fresh archive.
Cách ghi `"Full suite (774 + 20)"` trong draft trước là **sai** — 20 test V4.3.4 là
**tập con** của full suite, không cộng thêm vào.

---

## Phạm vi KHÔNG thay đổi

- Không sửa `project_config.py`, `project_qa_runner.py`, `project_dossier_builder.py`
- Không thay đổi schema 19 artifact
- Không thay đổi 15 quality gates (D-R1..D-R15)
- Không thêm API call, không thêm network dependency
- Không thay đổi MRAQ score hay qualification

---

*Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT tự động — KHÔNG thực thi thật.*  
*Manual review record does not constitute ethics, PI, final, or independent approval.*
