# V4.3.4 Human Review Operations — SOP

**Version:** 4.3.4  
**Corrected:** 2026-06-28 (V4.3.4.1 — attestation boundary clarification)  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## 1. Mục đích

SOP này mô tả quy trình ghi nhận **manual review attestation** trong hệ thống
per-project dossier automation V4.3.4.

**Lưu ý quan trọng về phạm vi kỹ thuật:**

> Hệ thống **chặn automation-originated review record** nhưng **không xác thực danh tính**
> và **không xác minh tính độc lập** của reviewer. Mọi review record là
> **manual attestation record** — không phải ethics approval, PI approval,
> hay independent review xác nhận.

---

## 2. Bất biến kỹ thuật

| # | Bất biến | Cơ chế | Ghi chú |
|---|----------|--------|---------|
| I1 | Automation-originated record bị block | `AutoReviewForbidden` khi `automation_caller=True` | Chặn nguồn gốc call, không xác thực danh tính |
| I2 | Mọi artifact vẫn là DRAFT sau review | Không có trạng thái final/released/submitted | `final_released_submitted_count` = 0 |
| I3 | ReviewLedger là append-only | Chỉ `append()` — không có `delete()`/`update()` | Bảo toàn lịch sử ghi |
| I4 | Một số ReviewMode bị cấm | `ForbiddenReviewMode` khi mode nằm trong danh sách cấm | Mode string bị check trước khi ghi |
| I5 | Mọi output kèm disclaimer | Text disclaimer bắt buộc | Không thay thế governance thật |
| I6 | Không PII trong ledger | Guard trong `record_decision()` | Pattern matching, không semantic check |

## 3. Giới hạn — KHÔNG được đảm bảo kỹ thuật

| Giới hạn | Tình trạng |
|----------|-----------|
| Xác thực danh tính reviewer | **KHÔNG** — hệ thống không có authentication layer |
| Xác minh tính độc lập reviewer | **KHÔNG** — không có conflict-of-interest check |
| Xác nhận ethics approval | **KHÔNG** — record không phải ethics document |
| Xác nhận PI approval chính thức | **KHÔNG** — record không có chữ ký điện tử hay pháp lý |
| Kiểm tra nội dung reason hợp lý | **KHÔNG** — `reason` là free-text string |
| Đảm bảo reviewer đọc artifact | **KHÔNG** — hệ thống không track artifact access |

---

## 4. Vai trò reviewer (4 roles — label routing, không xác thực danh tính)

| Role value | Mục đích routing | Cảnh báo |
|------------|-----------------|---------|
| `PI_PROJECT_OWNER` | Artifact mục tiêu, outcomes, charter | Chỉ là label — hệ thống không xác thực |
| `METHODS_STATISTICS_REVIEWER` | Design, cỡ mẫu, SAP | Chỉ là label — không verify chuyên môn |
| `EVIDENCE_CITATION_REVIEWER` | Evidence status, citations | Chỉ là label — không verify citations |
| `DATA_GOVERNANCE_QA_REVIEWER` | CRF, data dictionary, governance | Chỉ là label — không verify authority |

---

## 5. Review mode (2 mode hợp lệ)

| Mode | Ý nghĩa kỹ thuật | Giới hạn |
|------|-----------------|---------|
| `HUMAN_REVIEW_INDEPENDENCE_NOT_ESTABLISHED` | **Mặc định.** Ghi nhận rằng independence chưa được xác lập | Independence THỰC SỰ chưa được xác minh |
| `SELF_REVIEW` | Ghi nhận PI tự review draft của mình | Tính độc lập = không có |

**Mode bị cấm (gây `ForbiddenReviewMode`):**
`INDEPENDENT_REVIEW_APPROVED` · `ETHICS_APPROVED` · `PI_APPROVED` · `FINAL_APPROVED`

*Lý do cấm: các mode này ám chỉ sự xác nhận mà hệ thống không thể kỹ thuật đảm bảo.*

---

## 6. Quyết định hợp lệ (5 decisions)

| Decision | Ý nghĩa | Không có nghĩa là |
|----------|---------|------------------|
| `ACCEPT_DRAFT_FOR_NEXT_INTERNAL_STAGE` | Ghi nhận chấp nhận cho bước nội bộ tiếp theo | Approved, final, released, ethics-cleared |
| `REVISION_REQUIRED` | Ghi nhận artifact cần sửa | Tự động trigger revision |
| `REQUEST_HUMAN_INPUT` | Ghi nhận thiếu đầu vào từ người thật | Xác minh đầu vào được cung cấp |
| `REJECT_DRAFT` | Ghi nhận artifact không đạt yêu cầu cơ bản | Tự động xóa hay rebuild |
| `ARCHIVE_DRAFT` | Ghi nhận artifact không còn dùng | Xóa artifact |

---

## 7. Luồng công việc (manual attestation flow)

```
project-build → project-qa → project-review-list
                                   ↓
                     project-review-record
                     (ghi manual attestation record;
                      automation-originated call bị block;
                      danh tính người ghi không được xác thực)
                                   ↓
                     project-review-status
                     (đếm records — không đánh giá chất lượng nội dung)
                                   ↓ (nếu REVISION_REQUIRED)
                     project-revision-plan
                     (hướng dẫn PI sửa — không tự sửa artifact)
```

---

## 8. Yêu cầu governance bên ngoài hệ thống

Để có independent review thực sự, ethics approval, hay PI sign-off chính thức,
tổ chức phải triển khai **ngoài hệ thống này**:

- Authentication layer (xác thực danh tính reviewer)
- Role-based access control (ngăn PI tự review artifact của mình)
- Digital signature / e-consent system
- IRB/ethics board integration
- Conflict-of-interest declaration workflow

Hệ thống này không cung cấp và không thay thế các cơ chế trên.

---

## 9. Giới hạn hệ thống tổng thể

```
NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
Real research execution: BLOCKED
External release/submission: BLOCKED
Live Agent behavior: NOT VERIFIED
API connectivity: NOT RUN
Independent review: NOT ESTABLISHED
All outputs are DRAFT — REQUIRE HUMAN REVIEW
```

---

*Manual review record does not constitute ethics, PI, final, or independent approval.*  
*Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT tự động — KHÔNG thực thi thật.*
