---
_harness_template: "Plans.md.template"
_harness_version: "4.3.3"
---

# medical-ebm-automation — Plans.md

> **Project**: medical-ebm-automation
> **Created**: 2026-06-07
> **Updated by**: Claude Code (harness-plan create)

Sprint mục tiêu: **Rà soát & chốt độ tin cậy của 30 thang điểm lâm sàng `verified`** —
khóa (pin) bằng test các cập nhật guideline 2024–2026 và ghi change log, để nội dung
không bị trôi/sai khi sửa về sau.

---

## Phase 0: Nền kiểm thử (chạy được trước khi sửa nội dung)

| Task | Nội dung | DoD | Depends | Status |
|------|----------|-----|---------|--------|
| 0.1 | Tạo venv **ngoài OneDrive** (`~/.ebm-venv`), cài `requirements.txt`, chạy `pytest` lấy baseline xanh/đỏ. `[tdd:skip:env-setup]` | `pytest` chạy được; ghi lại số test pass/fail hiện tại vào change log | - | cc:done (95 passed) |
| 0.2 | Thêm baseline lint (ruff) nếu repo chưa có cấu hình; chỉ cấu hình, không sửa lỗi hàng loạt. `[tdd:skip:tooling-setup]` | `ruff check` chạy được, có file cấu hình; (hoặc ghi `Spec skip reason` nếu quyết định chưa dùng) | 0.1 | cc:done (ruff.toml, baseline 189) |

---

## Phase 1: Khóa các cập nhật guideline bằng test (chống trôi nội dung)

| Task | Nội dung | DoD | Depends | Status |
|------|----------|-----|---------|--------|
| 1.1 | Test khóa **6 thang đã cập nhật**: CHA2DS2-VA (max 8, ngưỡng ≥2 không phân biệt giới), FIB-4 (<1.3 MASLD/AASLD 2023), qSOFA (SSC 2021 *mạnh chống* sàng lọc đơn lẻ), MELD 3.0 (chuẩn từ 2023), GOLD ABE 2025 (eos ≥300 cho ICS), ASCVD PCE + cảnh báo PREVENT 2023. `[tdd:required]` | `tests/test_clinical_scores_updates.py` PASS; mỗi test FAIL nếu cụm từ/ngưỡng tương ứng bị xóa khỏi `verified.py` | 0.1 | cc:done (12 test, APPROVE) |
| 1.2 | Test khóa **GAD-7 = USPSTF 2023 mức B** (sàng lọc lo âu người lớn ≤64). `[tdd:required]` | Test PASS, FAIL nếu mất tham chiếu USPSTF 2023 | 0.1 | cc:done |
| 1.3 | Đảm bảo `seed_verified_scores()` ghi **ChangeLogEntry** cho mỗi thang được cập nhật. `[tdd:required]` | Test xác nhận có change-log entry sau khi cập nhật score; không trùng lặp khi chạy lại | 0.1 | cc:done |
| 1.4 | Test **liêm chính danh mục**: số `verified` = 32 và `needs_verification` = 16 (theo doc), và không `needs_verification` nào có công thức. `[tdd:required]` | Test PASS phản ánh đúng số liệu doc; nếu lệch → cập nhật doc hoặc code cho khớp (khớp: 32/16) | 0.1 | cc:done |

---

## Phase 2: Nhất quán định danh & hồ sơ (sau khi test xanh)

| Task | Nội dung | DoD | Depends | Status |
|------|----------|-----|---------|--------|
| 2.1 | Quyết định xử lý `score_id` đã đổi tên (`cha2ds2_vasc`, `meld_na`): giữ id + alias hiển thị hay đổi id. Ghi quyết định, **không phá khóa DB**. `[tdd:skip:decision-doc]` | Quyết định ghi vào `docs/RA_SOAT_THANG_DIEM_2026-06.md` (hoặc spec); seed vẫn chạy, không mất dữ liệu cũ | 1.1, 1.4 | cc:done (kỹ thuật: mục E; lâm sàng → mục F chờ chuyên khoa) |
| 2.2 | Cập nhật Change Log + thêm mục **chờ bác sĩ chuyên khoa ký xác nhận** (doc mục D.1) vào tài liệu. `[tdd:skip:docs-only]` | Doc cập nhật, có dòng sign-off; README trỏ tới quy trình cập nhật | 2.1 | cc:done |

---

## In Progress

(none)

## Completed

- [x] Harness initialized for project `pm:approved` (2026-06-07)

## Archive

---

## Status Marker Legend

| Marker | Meaning |
|--------|---------|
| `pm:requested` | PM requested work |
| `cc:todo` | Not started by Claude Code |
| `cc:wip` | Claude Code is working |
| `cc:done` | Claude Code completed, awaiting confirmation |
| `pm:approved` | PM confirmed completion |
| `blocked` | Blocked; include the reason |

TDD tags: `[tdd:required]` = viết test thất bại trước; `[tdd:skip:<lý do>]` = bỏ TDD có lý do.

---

## Last Update

- **Updated at**: 2026-06-07
- **Last session owner**: Claude Code
- **Branch**: main
