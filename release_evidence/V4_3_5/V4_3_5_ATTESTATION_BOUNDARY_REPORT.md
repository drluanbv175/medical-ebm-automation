# V4.3.5 Attestation Boundary Report — Evidence & Claim Traceability

**Version:** 4.3.5  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## 1. Những gì hệ thống ĐẢM BẢO kỹ thuật

| # | Bất biến kỹ thuật | Cơ chế |
|---|-------------------|--------|
| E1 | Chỉ chấp nhận `HUMAN_PROVIDED_ONLY` | `EvidenceSourceLedger.add()` raise `ForbiddenRetrievalMode` với AUTO_RETRIEVED/MODEL_GENERATED/WEB_SCRAPED/API_FETCHED |
| E2 | Automation không thể tự đặt `HUMAN_VERIFIED` | `AutoVerificationForbidden` khi `automation_caller=True` + `verification_state=HUMAN_VERIFIED` |
| E3 | `EvidenceSourceLedger` append-only | Không có `delete()` hay `update()` — chỉ `add()` |
| E4 | `ClaimTraceabilityLedger` append-only | Không có `delete()` hay `update()` — chỉ `add()` |
| E5 | RETRACTED source → BLOCK tất cả | D-R8 FAIL + BLOCK; `ClaimStatus.BLOCKED_RETRACTED_EVIDENCE` |
| E6 | Claim dùng UNVERIFIED → BLOCK | `compute_claim_status()` trả `BLOCKED_UNVERIFIED_EVIDENCE` |
| E7 | Không PII | Guard trong `add_evidence_source()` và `register_claim()` |
| E8 | Không tự tạo DOI/PMID/citation | Tất cả fields nhận từ PI; thiếu → `[REQUIRE_HUMAN_INPUT]` |
| E9 | Định tuyến review về EVIDENCE_CITATION_REVIEWER | `reviewer_reference` mặc định trong `add_evidence_source()` |
| E10 | DRAFT-only output | `_CLAIM_DISCLAIMER` kèm mọi audit trail |

---

## 2. Những gì hệ thống KHÔNG đảm bảo

| # | Giới hạn | Lý do |
|---|----------|-------|
| L1 | **Không xác thực danh tính reviewer** | Hệ thống ghi `reviewer_reference` là string — không có authentication, không có digital signature |
| L2 | **Không thiết lập tính độc lập reviewer** | `review_mode = HUMAN_REVIEW_INDEPENDENCE_NOT_ESTABLISHED` là label mặc định — không phải xác nhận thật |
| L3 | **Không xác minh nội dung evidence** | Hệ thống ghi DOI/PMID do PI cung cấp nhưng không resolve, không full-text check |
| L4 | **Không kiểm tra retraction status thật** | `retraction_status` là string do PI nhập — không kết nối Retraction Watch hay CrossRef |
| L5 | **Không ngăn PI nhập thông tin sai** | PII guard và fabrication check không thể phát hiện mọi loại dữ liệu sai |
| L6 | **Không có external peer review** | Mọi verification là nội bộ, không có journal/IRB review |
| L7 | **Không có ethics approval** | Không tự tạo, không kết nối với cơ quan đạo đức |

---

## 3. Tại sao KHÔNG được dùng cho research thật

> **BLOCKED: Real Research Execution**

Hệ thống V4.3.5 là **offline DRAFT automation** — thiết kế để:
1. Cấu trúc workflow tư duy nghiên cứu
2. Buộc PI nghĩ về evidence traceability
3. Block claim khi evidence rõ ràng chưa sẵn sàng

Hệ thống KHÔNG đủ tiêu chuẩn cho nghiên cứu thật vì:
- `HUMAN_VERIFIED` chỉ là label — không phải xác thực danh tính hay năng lực
- Không có DOI/PMID resolution thật
- Không có independent peer review
- Toàn bộ data là synthetic — không có real patient data

---

## 4. Yêu cầu quản trị bên ngoài

Để dùng trong nghiên cứu thật, cần BỔ SUNG:
- Hệ thống xác thực danh tính reviewer (PKI, institutional SSO)
- DOI resolver và retraction checker thật (CrossRef, Retraction Watch API)
- Quy trình đạo đức (IRB/IEC approval)
- Independent peer review bên ngoài tổ chức
- Audit log có chữ ký số

---

## 5. Bảng tóm tắt

| Thuộc tính | Hệ thống ĐẢM BẢO | Hệ thống KHÔNG đảm bảo |
|------------|-------------------|------------------------|
| Retrieval mode | HUMAN_PROVIDED_ONLY | Nội dung evidence đúng |
| Automation guard | Không tự verify | Danh tính reviewer |
| Ledger integrity | Append-only | Độc lập reviewer |
| PII guard | Marker-based | Mọi loại PII |
| Claim traceability | Liên kết source | Source thật/đúng |
| RETRACTED guard | Block nếu PI đánh dấu | Retraction tự động |
| Disclaimer | Kèm mọi output | Thay thế reviewer thật |

---

*Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT tự động — KHÔNG thực thi thật.*
