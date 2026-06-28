# V4.3.5 Evidence State Machine

**Version:** 4.3.5  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## 1. Evidence Source State Machine

```
                 ┌─────────────┐
                 │  (imported) │
                 └──────┬──────┘
                        │ add_evidence_source()
                        ▼
               ┌─────────────────┐
               │   UNVERIFIED    │◄─────────────────────────────┐
               │ (claim_use=No)  │                              │
               └────────┬────────┘                              │
                        │                                       │
           ┌────────────┼────────────────────────┐              │
           │            │                        │              │
    PI flags│     PI or  │reviewer     PI marks   │              │
    retracted│    flags   │flags       excluded   │              │
           ▼    needs    ▼            ▼           │              │
   ┌──────────┐  review ┌──────────────────────┐ │   Re-import  │
   │RETRACTED │◄────────│ REQUIRES_HUMAN_REVIEW │─┘   with new  │
   │(claim=No)│         │    (claim_use=No)     │  verification  │
   └──────────┘         └──────────┬────────────┘              │
         │                         │                            │
         │                  Reviewer attests                    │
         │                  (automation blocked)                │
         │                         ▼                            │
         │              ┌──────────────────────┐                │
         │              │   HUMAN_VERIFIED     │                │
         │              │ (claim_use=Yes/DRAFT)│                │
         │              └──────────────────────┘                │
         │                         │                            │
         │               Later retraction found                 │
         └─────────────────────────┘                            │
                                                                │
                   ┌──────────┐                                 │
                   │ EXCLUDED │─────────────────────────────────┘
                   │(claim=No)│  (PI can re-evaluate → UNVERIFIED)
                   └──────────┘
```

### Chú thích

| Transition | Điều kiện | Actor |
|-----------|-----------|-------|
| `UNVERIFIED → HUMAN_VERIFIED` | Reviewer xem xét và xác nhận | PI/reviewer người thật (không phải automation) |
| `UNVERIFIED → REQUIRES_HUMAN_REVIEW` | PI gắn cờ cần xem thêm | PI |
| `UNVERIFIED → RETRACTED` | PI ghi nhận retraction | PI |
| `UNVERIFIED → EXCLUDED` | PI loại ra khỏi đề tài | PI |
| `HUMAN_VERIFIED → RETRACTED` | Phát hiện retraction sau verify | PI |
| `REQUIRES_HUMAN_REVIEW → HUMAN_VERIFIED` | Reviewer hoàn thành review | PI/reviewer người thật |
| `REQUIRES_HUMAN_REVIEW → EXCLUDED` | PI quyết định loại | PI |
| `ANY → UNVERIFIED` | Re-import với metadata cập nhật | PI |

### Transition bị cấm

- Automation KHÔNG được thực hiện `→ HUMAN_VERIFIED` (`AutoVerificationForbidden`)
- `RETRACTED` KHÔNG thể trở thành `HUMAN_VERIFIED` (phải qua `EXCLUDED` hoặc nộp lại thông tin mới)

---

## 2. Claim Status State Machine

```
   register_claim() gọi compute_claim_status() ngay lập tức

   linked_source_ids = []
         ▼
   ┌──────────────────────────────┐
   │ REQUIRE_HUMAN_EVIDENCE_INPUT │  (không có source)
   └──────────────────────────────┘

   linked_source_ids ≠ []
         ▼
   Có RETRACTED source?
   ├── Có → ┌──────────────────────────────┐
   │         │  BLOCKED_RETRACTED_EVIDENCE   │  (ưu tiên cao nhất)
   │         └──────────────────────────────┘
   └── Không ▼
   Có UNVERIFIED / REQUIRES_HUMAN_REVIEW / NOT_FOUND?
   ├── Có → ┌──────────────────────────────┐
   │         │  BLOCKED_UNVERIFIED_EVIDENCE  │
   │         └──────────────────────────────┘
   └── Không → tất cả HUMAN_VERIFIED?
             ├── Có → ┌─────────────────────────────────────────────┐
             │         │ SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE (DRAFT) │
             │         └─────────────────────────────────────────────┘
             └── Không → REQUIRE_HUMAN_REVIEW
```

### Quy tắc ưu tiên `compute_claim_status()`

1. `linked_source_ids` rỗng → `REQUIRE_HUMAN_EVIDENCE_INPUT`
2. Bất kỳ source nào `RETRACTED` → `BLOCKED_RETRACTED_EVIDENCE` (không kiểm tiếp)
3. Bất kỳ source nào `UNVERIFIED` hoặc `REQUIRES_HUMAN_REVIEW` hoặc không tìm thấy → `BLOCKED_UNVERIFIED_EVIDENCE`
4. Tất cả sources `HUMAN_VERIFIED` → `SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE`

**Lưu ý:** `SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE` vẫn chỉ là **DRAFT** — không phải "approved", "final", hay "clinically validated".

---

## 3. D-R8 Evidence Gate — Transition Map

| Trạng thái evidence | D-R8 status | D-R8 gate_state |
|--------------------|-------------|-----------------|
| Không có ledger | WARN | REQUIRE_HUMAN_EVIDENCE_INPUT |
| Ledger rỗng | WARN | REQUIRE_HUMAN_EVIDENCE_INPUT |
| Chỉ UNVERIFIED sources, không có blocked claim | WARN | REQUIRE_HUMAN_REVIEW |
| Claim dùng UNVERIFIED source | FAIL | BLOCK |
| Có RETRACTED source (dù có claim hay không) | FAIL | BLOCK |
| Tất cả sources HUMAN_VERIFIED, không có blocked claim | PASS | PASS |

---

## 4. Forbidden Status Labels

Claim KHÔNG được gắn các nhãn sau:

| Nhãn bị cấm | Lý do |
|-------------|-------|
| `FINAL` | Ngụ ý đã hoàn thành xem xét — chưa có |
| `APPROVED` | Ngụ ý có thẩm quyền chính thức — chưa có |
| `CLINICALLY_VALIDATED` | Ngụ ý kiểm định lâm sàng — chưa thực hiện |
| `PUBLISHED` | Ngụ ý đã công bố — không có |

---

## 5. Giới hạn state machine

- Mỗi lần gọi `add_evidence_source()` tạo ra **record mới** trong ledger JSONL — không sửa record cũ.
- Mỗi lần gọi `register_claim()` tạo ra **record mới** — không sửa record cũ.
- `EvidenceSourceLedger` và `ClaimTraceabilityLedger` là **append-only**: chỉ có `add()`, không có `delete()` hay `update()`.
- Trạng thái "hiện tại" của một source là **record cuối cùng** có cùng `source_id` (trường hợp nộp lại).
- Trạng thái "hiện tại" của một claim là **record cuối cùng** có cùng `claim_id` (trường hợp đăng ký lại).

---

*Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT tự động — KHÔNG thực thi thật.*
