# V4.3.4 Controlled Topic Dry Run — Spec & Results

**Version:** 4.3.4  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## 1. Mục tiêu Dry Run

Xác nhận toàn bộ V4.3.4 pipeline hoạt động end-to-end với dữ liệu tổng hợp (synthetic),
không PII, không API, không network.

---

## 2. Thông tin đề tài tổng hợp

| Field | Giá trị |
|-------|---------|
| Project ID | `DRY-V434-001` |
| Title | Synthetic Cohort Study — HbA1c intervention (DRY RUN) |
| Study Type | `cohort` |
| Primary Objective | Đánh giá ảnh hưởng của tư vấn dinh dưỡng đến HbA1c |
| Primary Outcome | Thay đổi HbA1c sau 12 tuần |
| Data Mode | `NO_REAL_DATA` |
| Human Owner | `PI-SYNTH` |
| PII | KHÔNG — synthetic only |
| API calls | KHÔNG — offline |

---

## 3. Kịch bản thực hiện

### Bước 1: Build dossier
```
builder.build(config, overwrite=True)
→ +19 artifacts, blocked=False
```

### Bước 2: QA
```
run_project_qa(project_dir, config)
→ PASS=14 FAIL=0 WARN=1 SKIP=0 → PASS
```
*(WARN dự kiến: evidence chưa xác minh — synthetic project không có PMID thật)*

### Bước 3: Review list
```
list_review_queue(project_dir, config)
→ 19 artifacts in queue
```

### Bước 4: Record decisions (PI/reviewer — không phải automation)
```
record_decision(..., RESEARCH_CHARTER, ACCEPT_DRAFT_FOR_NEXT_INTERNAL_STAGE, PI_PROJECT_OWNER)
→ RV-XXXXXXXX... ✓

record_decision(..., SAP_DRAFT, REVISION_REQUIRED, METHODS_STATISTICS_REVIEWER,
    required_actions=["Điền effect size δ=0.5", "Xác nhận alpha=0.05"])
→ RV-XXXXXXXX... ✓

record_decision(..., EVIDENCE_PLAN, REQUEST_HUMAN_INPUT, EVIDENCE_CITATION_REVIEWER)
→ RV-XXXXXXXX... ✓
```

### Bước 5: Review status
```
get_review_status(project_dir)
→ total_review_records=3
  revision_required=1
  human_input_required=1
  final_released_submitted_count=0 ✓
  draft_only_status=True ✓
  qualification: "NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE"
```

### Bước 6: Revision plan
```
build_revision_plan(project_dir, config)
→ 1 revision (SAP_DRAFT)
  8 downstream stale artifacts marked
  no_overwrite_policy: ghi rõ
```

### Bước 7: PII check
```
Tất cả record trong ledger: không có "patient_id", "mã bệnh nhân", "date_of_birth" → PASS
```

---

## 4. Kết quả

| Kiểm tra | Kết quả |
|----------|---------|
| Build dossier | PASS |
| QA 15 gates | PASS (14 PASS, 1 WARN dự kiến) |
| Review list trả 19 items | PASS |
| 3 review decisions ghi thành công | PASS |
| `final_released_submitted_count = 0` | PASS |
| `draft_only_status = True` | PASS |
| Revision plan đúng 1 item | PASS |
| Downstream stale đúng | PASS |
| Không PII trong ledger | PASS |
| Không gọi API/network | PASS |
| `AutoReviewForbidden` khi automation_caller=True | PASS (T02 test) |
| `ForbiddenReviewMode` với mode cấm | PASS (T05 test) |

**Kết luận: DRY RUN PASS — Tất cả kiểm tra đều đạt.**

---

## 5. Giới hạn dry run

- Đây là dry run với dữ liệu tổng hợp — **không phải nghiên cứu thật**.
- Mọi output là DRAFT, không có giá trị pháp lý hay lâm sàng.
- Reviewer trong dry run là lập trình viên test, không phải PI/reviewer y tế thật.

---

*Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT tự động — KHÔNG thực thi thật.*
