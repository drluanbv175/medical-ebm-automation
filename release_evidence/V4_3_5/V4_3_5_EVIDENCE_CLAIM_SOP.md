# V4.3.5 Evidence Intake & Claim Traceability — SOP

**Version:** 4.3.5  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## 1. Mục đích

SOP này mô tả quy trình vận hành Evidence Intake và Claim Traceability trong hệ thống
per-project dossier automation V4.3.5. Mọi evidence source phải do PI cung cấp thủ công
(HUMAN_PROVIDED_ONLY). Mọi claim phải liên kết với evidence đã được human verified.

---

## 2. Bất biến cốt lõi

| # | Bất biến | Hành vi khi vi phạm |
|---|----------|---------------------|
| I1 | `retrieval_mode` = HUMAN_PROVIDED_ONLY | `ForbiddenRetrievalMode` — BLOCK |
| I2 | Automation không đặt HUMAN_VERIFIED | `AutoVerificationForbidden` — BLOCK |
| I3 | EvidenceSourceLedger append-only | Không có `delete()` hay `update()` |
| I4 | ClaimTraceabilityLedger append-only | Không có `delete()` hay `update()` |
| I5 | RETRACTED source → block D-R8 + claim | FAIL BLOCK |
| I6 | Claim dùng UNVERIFIED → BLOCK | `BLOCKED_UNVERIFIED_EVIDENCE` |
| I7 | Không PII | Guard trong `add_evidence_source()` + `register_claim()` |
| I8 | Không auto-citation | DOI/PMID phải do PI nhập hoặc → [REQUIRE_HUMAN_INPUT] |
| I9 | Kèm disclaimer | Mọi audit trail và queue output |

---

## 3. RetrievalMode — chỉ HUMAN_PROVIDED_ONLY

| Mode | Trạng thái | Ghi chú |
|------|-----------|---------|
| `HUMAN_PROVIDED_ONLY` | **HỢP LỆ** | PI tự nạp thông tin |
| `AUTO_RETRIEVED` | **CẤM** | `ForbiddenRetrievalMode` |
| `MODEL_GENERATED` | **CẤM** | `ForbiddenRetrievalMode` |
| `WEB_SCRAPED` | **CẤM** | `ForbiddenRetrievalMode` |
| `API_FETCHED` | **CẤM** | `ForbiddenRetrievalMode` |

---

## 4. VerificationState — 5 trạng thái

| State | Khi dùng | claim_use_allowed |
|-------|----------|-------------------|
| `UNVERIFIED` | Mặc định khi mới nạp | `False` |
| `HUMAN_VERIFIED` | PI/reviewer đã kiểm và xác nhận | `True` (nếu không RETRACTED) |
| `REQUIRES_HUMAN_REVIEW` | Cần reviewer xem lại | `False` |
| `RETRACTED` | Bài báo đã bị rút | `False` (block toàn bộ) |
| `EXCLUDED` | Không dùng trong đề tài này | `False` |

---

## 5. ClaimStatus — 6 trạng thái

| Status | Ý nghĩa | D-R8 |
|--------|---------|------|
| `NOT_READY` | Claim chưa được xử lý | WARN |
| `REQUIRE_HUMAN_EVIDENCE_INPUT` | Chưa có source nào | WARN |
| `REQUIRE_HUMAN_REVIEW` | Source chưa được verify | WARN |
| `SUPPORTED_BY_HUMAN_VERIFIED_EVIDENCE` | Tất cả sources HUMAN_VERIFIED | PASS |
| `BLOCKED_RETRACTED_EVIDENCE` | Có source RETRACTED | FAIL/BLOCK |
| `BLOCKED_UNVERIFIED_EVIDENCE` | Source chưa verified | FAIL/BLOCK |

---

## 6. Luồng công việc

```
project-build → project-qa (D-R8 cũ với CSV)
                    ↓
project-evidence-import (PI nạp source + VerificationState)
                    ↓
project-evidence-list --queue-only (xem review queue)
                    ↓
[EVIDENCE_CITATION_REVIEWER xem xét — ngoài hệ thống]
                    ↓
project-evidence-import --verification-state HUMAN_VERIFIED (sau khi review)
                    ↓
project-claim-register (đăng ký claim + liên kết sources)
                    ↓
project-claim-audit (kiểm audit trail)
                    ↓
project-qa (D-R8 mới với evidence_source_ledger.jsonl)
```

---

## 7. Lệnh CLI

```bash
# Nạp evidence source (PI chạy — không phải automation)
researchctl project-evidence-import \
  --project-id <ID> \
  --source-type RCT \
  --title "Tên nghiên cứu đầy đủ" \
  --authors "Tác giả và cộng sự" \
  --year "2024" \
  --journal "Tên tạp chí" \
  --doi "10.xxxx/yyyy" \
  --pmid "12345678" \
  --reference "Tác giả. Tạp chí. 2024;1:1-10." \
  --verification-state UNVERIFIED \
  --verification-reason "Mới nạp, chưa xác minh"

# Xem review queue
researchctl project-evidence-list --project-id <ID> --queue-only

# Đăng ký claim sau khi source đã HUMAN_VERIFIED
researchctl project-claim-register \
  --project-id <ID> \
  --artifact-id 03_EVIDENCE_PLAN \
  --claim-text "Điều trị X giảm kết cục Y theo RCT có chứng cứ." \
  --claim-type BACKGROUND \
  --source-ids ES-XXXXXXXXXX

# Xem audit trail
researchctl project-claim-audit --project-id <ID>
```

---

## 8. Chính sách no-overwrite

- `evidence_source_ledger.jsonl` là append-only — không có lệnh xóa/sửa record
- `claim_traceability_ledger.jsonl` là append-only — tương tự
- Nếu cần thay đổi VerificationState, nạp lại một record mới với trạng thái mới
- Version mới của claim = register_claim() mới — không xóa record cũ

---

## 9. Giới hạn hệ thống

- Hệ thống là OFFLINE, DRAFT-only, synthetic data only.
- **KHÔNG** tự resolve DOI/PMID — không kết nối PubMed, CrossRef, Europe PMC.
- **KHÔNG** tự check retraction — không kết nối Retraction Watch.
- **KHÔNG** xác thực danh tính reviewer — `reviewer_reference` chỉ là string.
- **KHÔNG** thiết lập tính độc lập reviewer.
- Mọi quyết định của AI là ĐỀ XUẤT — PI/reviewer người thật xác nhận.

---

*Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT tự động — KHÔNG thực thi thật.*
