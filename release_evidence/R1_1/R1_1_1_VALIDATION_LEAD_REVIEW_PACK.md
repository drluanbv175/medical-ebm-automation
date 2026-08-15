# R1.1.1 Validation Lead Review Pack

**Document:** R1_1_1_VALIDATION_LEAD_REVIEW_PACK.md  
**Date:** 2026-06-28  
**Phase:** R1.1.1 — Validation Evidence Pack  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **Bắt buộc:**
> This review pack is prepared for a human Validation Lead.
> Claude Code must not make or simulate the Validation Lead decision.

---

## Mục đích tài liệu

Gói này cung cấp toàn bộ bằng chứng kỹ thuật cần thiết để Validation Lead tiến hành đánh giá độc lập thiết kế kiểm định của R1.1 — Offline RBAC and Synthetic Identity Test Harness. Đây là tài liệu trình bày; quyết định và chữ ký phải đến từ con người.

---

## 1. Tóm tắt phạm vi R1.1

R1.1 là **offline test harness** — không phải production system. Nó chứa:

| Thành phần | Mô tả |
|-----------|-------|
| `project_rbac_simulation.py` | SyntheticActor model + RBAC policy engine (10 roles, 20 actions, 8 SoD guards) |
| `project_delegation_registry.py` | Append-only JSONL delegation lifecycle (5 states) |
| `project_audit_attribution.py` | SHA-256 hash chain audit ledger + tamper detection |
| `project_cli.py` | +4 CLI commands |
| `test_r1_1_offline_rbac_synthetic_identity.py` | 39 tests |

**R1.1 KHÔNG CÓ:**
- SSO, LDAP, OAuth, MFA, authenticated identity
- Production RBAC service
- Electronic signature
- Ethics/IRB approval mechanism
- EDC hoặc eHospital integration
- Real user data hay PII

---

## 2. Inventory tài liệu bằng chứng

| # | File | Nội dung | Phase |
|---|------|---------|-------|
| 1 | `R1_1_1_REQUIREMENT_TEST_TRACEABILITY_MATRIX.csv` | 44 requirements × 12 cột traceability | A |
| 2 | `R1_1_1_NEGATIVE_TEST_AND_ABUSE_CASE_REVIEW.md` | 16 abuse cases với expected/observed/residual | B |
| 3 | `R1_1_1_VALIDATION_DESIGN_REVIEW.md` | 11 sections: intended use, coverage, adequacy, residual risk | C |
| 4 | `R1_1_1_FRESH_ARCHIVE_EVIDENCE_CONFIRMATION.json` | Fresh archive re-verify: 836 passed, 0 failed, 0 network | D |
| 5 | `R1_1_1_VALIDATION_LEAD_REVIEW_PACK.md` | File này | E |
| 6 | `R1_1_1_GATE_R1_1_DECISION_PREPARATION.md` | Gate register state | F |
| 7 | `R1_1_1_EXECUTIVE_SUMMARY.md` | Tóm tắt điều hành | — |
| 8 | `R1_1_FREEZE_SUMMARY.md` | Freeze summary (frozen context) | R1.1 |
| 9 | `R1_1_FRESH_ARCHIVE_ACCEPTANCE.json` | R1.1 phase acceptance (frozen context) | R1.1 |

---

## 3. Bằng chứng kỹ thuật tóm tắt

### 3.1 Fresh archive hermetic reproducibility

| Item | Value |
|------|-------|
| git_tag | `r1.1-frozen` |
| git_commit | `9fdfdffed90cb38d2dc56f6cf8604223c4e6d70e` |
| archive_sha256 | `0523a9667c439628b6b5d223a3b7c5984a0e7d383831c2cbebf0c0fa11853007` |
| archive_size_bytes | 1,504,708 |
| passed | 836 |
| failed | **0** |
| skipped | 5 |
| network_attempts | **0** |
| api_attempts | **0** |
| real_pii_inputs | **0** |
| manifest agents | 48 |
| all_hash_verified | **True** |

### 3.2 Requirement coverage

| Nhóm | CRITICAL | HIGH | LOW | Tổng |
|------|---------|------|-----|------|
| Synthetic identity | 4 | 3 | 1 | 8 |
| RBAC allow/deny | 3 | 4 | 1 | 8 |
| SoD guards | 8 | 0 | 0 | 8 |
| Delegation lifecycle | 2 | 3 | 0 | 5 |
| Audit schema | 4 | 1 | 0 | 5 |
| Append-only / hash chain | 3 | 0 | 0 | 3 |
| CLI / hermetic | 0 | 1 | 1 | 2 |
| Misc | 1 | 2 | 2 | 5 |
| **Tổng** | **25** | **14** | **5** | **44** |
| **Uncovered** | **0** | **0** | **0** | **0** |

### 3.3 Abuse case summary

| Danh mục | Tổng | PASS | MEDIUM risk | VL Review cần |
|---------|------|------|-------------|--------------|
| SoD violations | 5 | 5 | 1 | 3 |
| Delegation abuse | 5 | 5 | 0 | 2 |
| Audit tampering | 2 | 2 | 1 | 1 |
| Identity overclaim | 2 | 2 | 0 | 0 |
| Forbidden action | 3 | 3 | 0 | 1 |
| **Tổng** | **16** | **16** | **2** | **7** |

---

## 4. Điểm mở cần Validation Lead quyết định

Các điểm sau **không thể tự quyết định bởi Claude Code** — cần Validation Lead:

| VLD-ID | Câu hỏi | Nguồn | Risk nếu bỏ qua |
|--------|---------|-------|----------------|
| VLD-01 | Shared guard path (T15) có đủ làm evidence cho EXTERNAL_SUBMISSION và CLINICAL_RELEASE không? | AC-16, R-FAC-04/05 | LOW — nếu chấp nhận shared path |
| VLD-02 | _WRITE_ACTIONS set (SoD-03) có đủ đầy đủ không? | AC-03 | LOW |
| VLD-03 | _RESEARCH_CONTENT_APPROVAL_ACTIONS set (SoD-02) — cần test LOCK_RESEARCH_DATA không? | G-03, AC-02 | LOW |
| VLD-04 | T14 chấp nhận cả EXPIRED_ROLE và ROLE_NOT_PERMITTED — có ok không? | AC-05 | MEDIUM |
| VLD-05 | Residual risk RR-02 (WORM gap) — acceptable cho offline harness không? | AC-11 | MEDIUM |
| VLD-06 | CLI gap (G-01) — compile check đủ không? | G-01 | LOW |
| VLD-07 | SoD-02 test cần mở rộng thêm không? | G-03 | LOW |

---

## 5. Giới hạn cứng phải ghi nhận

Validation Lead phải xác nhận đã đọc và hiểu các giới hạn này:

| # | Giới hạn | Phạm vi xử lý |
|---|---------|--------------|
| GL-01 | SoD guards là offline Python evaluation — KHÔNG được enforce tại network/API layer | R1.3 |
| GL-02 | Không có SSO — synthetic_actor_id không được verify bởi identity provider | R1.3 |
| GL-03 | JSONL ledger không phải WORM — replace-then-rehash possible | R1.3 |
| GL-04 | Delegation không có PI authenticated signature | R1.3/manual |
| GL-05 | CLI không có E2E functional test qua subprocess | Ghi nhận |
| GL-06 | Independent security pentest (IQ-20) chưa được thực hiện | R1.5 |
| GL-07 | 5 tests skipped — không liên quan R1.1 modules | Carryover |

---

## 6. Gate status trước khi Validation Lead review

| Gate | Status hiện tại | Điều kiện để chuyển trạng thái |
|------|----------------|-------------------------------|
| GATE-R1.1 | **OPEN** | Validation Lead ký ACCEPT → PASS; ký REVISION_REQUIRED → HOLD |
| GATE-R1.2 | OPEN | Phụ thuộc GATE-R1.1 PASS + IT Lead engagement |
| GATE-R1 | OPEN | Phụ thuộc tất cả GATE-R1.x |

---

## 7. Form quyết định Validation Lead

**Hướng dẫn:** Validation Lead đọc toàn bộ gói bằng chứng, trả lời các câu hỏi VLD-01 đến VLD-07, và chọn MỘT trong 4 quyết định sau. Ký tên và ghi ngày. Claude Code không được điền vào form này.

---

### 7.1 Điều khoản bắt buộc xác nhận

Trước khi quyết định, Validation Lead xác nhận:

☐ Tôi đã đọc `R1_1_1_REQUIREMENT_TEST_TRACEABILITY_MATRIX.csv`  
☐ Tôi đã đọc `R1_1_1_NEGATIVE_TEST_AND_ABUSE_CASE_REVIEW.md`  
☐ Tôi đã đọc `R1_1_1_VALIDATION_DESIGN_REVIEW.md`  
☐ Tôi đã đọc `R1_1_1_FRESH_ARCHIVE_EVIDENCE_CONFIRMATION.json`  
☐ Tôi hiểu R1.1 là offline simulation, KHÔNG phải production identity system  
☐ Tôi hiểu GATE-R1.1 PASS không có nghĩa là hệ thống đủ điều kiện cho nghiên cứu thật  
☐ Tôi đã trả lời các câu hỏi VLD-01 đến VLD-07  

---

### 7.2 Câu trả lời VLD-01 đến VLD-07

| VLD-ID | Quyết định Validation Lead |
|--------|--------------------------|
| VLD-01 | [ ] Shared path đủ / [ ] Cần dedicated test |
| VLD-02 | [ ] _WRITE_ACTIONS đủ đầy đủ / [ ] Cần bổ sung action |
| VLD-03 | [ ] Không cần test LOCK_RESEARCH_DATA / [ ] Cần test |
| VLD-04 | [ ] Cả hai reason_code đều OK / [ ] Yêu cầu EXPIRED_ROLE cụ thể |
| VLD-05 | [ ] WORM gap acceptable cho offline harness / [ ] Cần note đặc biệt |
| VLD-06 | [ ] Compile check đủ / [ ] Cần subprocess E2E test |
| VLD-07 | [ ] SoD-02 test đủ / [ ] Cần mở rộng |

---

### 7.3 Quyết định

*(Chọn đúng một)*

| Lựa chọn | Mô tả |
|---------|-------|
| ☐ **ACCEPT_TECHNICAL_TEST_DESIGN** | Chấp nhận toàn bộ thiết kế kiểm định. GATE-R1.1 kỹ thuật PASS. |
| ☐ **ACCEPT_WITH_ACTIONS** | Chấp nhận cơ bản, yêu cầu các action cụ thể phải hoàn thành trước khi GATE-R1.1 PASS. |
| ☐ **REVISION_REQUIRED** | Yêu cầu sửa đổi đáng kể thiết kế kiểm định. Trả về tác giả để rework. |
| ☐ **REJECT_TECHNICAL_TEST_DESIGN** | Từ chối thiết kế kiểm định. Cần tái thiết kế căn bản. |

**KHÔNG được chọn:** PRODUCTION_APPROVED · RESEARCH_APPROVED · ETHICS_APPROVED · INDEPENDENT_REVIEW_ESTABLISHED

---

### 7.4 Chi tiết quyết định

**Lý do / Actions required (nếu có):**

```
[Validation Lead điền tại đây]
```

---

### 7.5 Chữ ký

| Trường | Nội dung |
|--------|---------|
| Họ tên Validation Lead | |
| Chức danh | |
| Ngày ký | |
| Chữ ký | |

---

## 8. Tuyên bố giới hạn Claude Code

R1.1 validates offline policy logic only. R1.1 does not validate production authentication. R1.1 does not validate SSO, MFA, real user identity, electronic signature, institutional delegation, or production audit attribution.

Claude Code đã chuẩn bị gói bằng chứng này để hỗ trợ đánh giá của Validation Lead. Claude Code không tự gán nhãn ACCEPTED, APPROVED, hoặc bất kỳ trạng thái tương đương nào. Mọi quyết định cổng phải đến từ con người có thẩm quyền.

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
