# V4.3.4 Human Review Operations — SOP

**Version:** 4.3.4  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## 1. Mục đích

SOP này mô tả quy trình vận hành Human Review trong hệ thống per-project dossier automation V4.3.4.
Mọi review decision chỉ được ghi bởi người thật (PI/reviewer). Automation **không được** tạo review decision.

---

## 2. Bất biến cốt lõi

| # | Bất biến | Hành vi khi vi phạm |
|---|----------|---------------------|
| I1 | Automation không được ghi ReviewRecord | `AutoReviewForbidden` — BLOCK |
| I2 | Mọi artifact vẫn là DRAFT sau review | Không có trạng thái "final/released/submitted" |
| I3 | ReviewLedger là append-only | Không xóa/sửa record đã ghi |
| I4 | INDEPENDENT_REVIEW_APPROVED/ETHICS_APPROVED/PI_APPROVED/FINAL_APPROVED bị cấm | `ForbiddenReviewMode` — BLOCK |
| I5 | Mọi output kèm disclaimer | "Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT" |
| I6 | Không PII trong ledger | Guard trong `record_decision()` |

---

## 3. Vai trò reviewer (4 roles)

| Role | Trách nhiệm chính |
|------|-------------------|
| `PI_PROJECT_OWNER` | Mục tiêu, outcomes, feasibility, charter, revision sign-off |
| `METHODS_STATISTICS_REVIEWER` | Design, cỡ mẫu, SAP, table shells, synthetic readiness |
| `EVIDENCE_CITATION_REVIEWER` | Evidence status, verification, retraction, citation |
| `DATA_GOVERNANCE_QA_REVIEWER` | CRF, data dictionary, governance pack, version register |

---

## 4. Review mode (2 mode)

| Mode | Ý nghĩa |
|------|---------|
| `HUMAN_REVIEW_INDEPENDENCE_NOT_ESTABLISHED` | **Mặc định.** Reviewer độc lập chưa được thiết lập chính thức |
| `SELF_REVIEW` | PI tự review draft của mình — ghi rõ để audit |

**Cấm dùng:** `INDEPENDENT_REVIEW_APPROVED`, `ETHICS_APPROVED`, `PI_APPROVED`, `FINAL_APPROVED`.

---

## 5. Quyết định hợp lệ (5 decisions)

| Decision | Khi dùng | Bước tiếp theo |
|----------|----------|----------------|
| `ACCEPT_DRAFT_FOR_NEXT_INTERNAL_STAGE` | Artifact đủ chất lượng để chuyển bước nội bộ | Ghi nhận; artifact vẫn là DRAFT |
| `REVISION_REQUIRED` | Artifact cần sửa trước khi tiếp tục | `project-revision-plan` → PI sửa → version mới |
| `REQUEST_HUMAN_INPUT` | Artifact thiếu dữ liệu PI phải cung cấp | PI điền `[REQUIRE_HUMAN_INPUT]` → review lại |
| `REJECT_DRAFT` | Artifact không đạt yêu cầu cơ bản | Dossier build lại từ đầu |
| `ARCHIVE_DRAFT` | Artifact không còn dùng | Chuyển sang trạng thái archived |

---

## 6. Luồng công việc

```
project-build → project-qa → project-review-list
                                   ↓
                        project-review-record (PI/reviewer)
                                   ↓
                        project-review-status → kiểm tra counters
                                   ↓ (nếu REVISION_REQUIRED)
                        project-revision-plan → PI sửa artifact
                                   ↓
                        project-qa lại → project-review-record
```

---

## 7. Chính sách no-overwrite

- Khi `REVISION_REQUIRED`, PI **tạo version mới** của artifact (không ghi đè version cũ).
- `18_VERSION_REGISTER.csv` ghi thêm dòng mới; không xóa dòng cũ.
- `review_ledger.jsonl` là append-only — không có lệnh `delete` hoặc `update`.
- Downstream artifacts bị đánh dấu `STALE_REQUIRES_REVISION` trong `CHANGE_IMPACT_REPORT`.

---

## 8. Lệnh CLI

```bash
# Liệt kê artifact cần review
researchctl project-review-list --project-id <ID>

# Ghi quyết định review (người thật — không phải automation)
researchctl project-review-record \
  --project-id <ID> \
  --artifact-id 07_STATISTICAL_ANALYSIS_PLAN_DRAFT \
  --decision REVISION_REQUIRED \
  --role METHODS_STATISTICS_REVIEWER \
  --reason "SAP thiếu assumptions effect size." \
  --required-actions "Điền effect size δ;Xác nhận alpha=0.05"

# Xem tổng hợp trạng thái
researchctl project-review-status --project-id <ID>

# Xem kế hoạch revision
researchctl project-revision-plan --project-id <ID>
```

---

## 9. Giới hạn hệ thống

- Hệ thống này là OFFLINE, DRAFT-only, synthetic data only.
- **KHÔNG** kết nối HIS, EMR, eHospital, PubMed, API nào.
- **KHÔNG** gửi ethics, protocol, manuscript.
- **KHÔNG** tự công bố artifact là final/released/submitted.
- Mọi quyết định của AI là ĐỀ XUẤT — PI/reviewer người thật xác nhận.

---

*Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT tự động — KHÔNG thực thi thật.*
