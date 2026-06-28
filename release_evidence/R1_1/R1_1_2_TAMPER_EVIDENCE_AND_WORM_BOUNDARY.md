# R1.1.2 Tamper Evidence and WORM Boundary

**Document:** R1_1_2_TAMPER_EVIDENCE_AND_WORM_BOUNDARY.md  
**Date:** 2026-06-28  
**Phase:** R1.1.2 — Phase F Documentation  
**Baseline finding:** RR-02 / AC-11 in R1.1.1  
**Branch:** feat/r1-1-2-design-gap-remediation  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## 1. Mục đích

Tài liệu này xác lập ranh giới rõ ràng giữa:
- Những gì local tamper-evident ledger **CÓ THỂ** phát hiện (offline, không cần WORM)
- Những gì **KHÔNG THỂ** phát hiện mà không có WORM storage (PROD-AUD-01, deferred R1.3)

Đây là phần sửa chữa tính trung thực (truthfulness correction) cho RR-02/AC-11 từ R1.1.1.

---

## 2. Phân loại chính xác của local ledger

| Thuộc tính | Giá trị |
|-----------|--------|
| Tên chính xác | Tamper-Evident Local Audit Ledger Simulation |
| Hằng số module | `LOCAL_LEDGER_CLASSIFICATION = "TAMPER_EVIDENT_LOCAL_SIMULATION_NOT_WORM"` |
| Hằng số WORM | `PROD_AUD_01_WORM_DEPENDENCY = "NOT_IMPLEMENTED"` |
| Phân loại | KHÔNG phải WORM · KHÔNG phải immutable storage · KHÔNG phải production audit trail |

---

## 3. Những gì local ledger CÓ THỂ phát hiện

Tất cả các kịch bản dưới đây đều có test coverage trong `test_r1_1_2_gap_remediation.py`:

| Kịch bản tamper | Cơ chế phát hiện | Test |
|-----------------|-----------------|------|
| Sửa nội dung event (bất kỳ field) | `audit_event_hash` mismatch với recompute | WORM-05 |
| Xóa/sửa `previous_event_hash` | Chain link break | WORM-06 |
| `sequence_number` có gap | Sequence discontinuity detection | WORM-07 |
| Xóa event ở giữa chuỗi | Chain break + sequence gap | WORM-08 |
| Duplicate `event_id` | `seen_event_ids` set tracking | WORM-09 |
| Event sai thứ tự (out-of-order) | `seq_num <= prev_seq` check | WORM-10 |

---

## 4. Những gì local ledger KHÔNG THỂ phát hiện (PROD-AUD-01)

| Tấn công | Tại sao không thể phát hiện offline |
|---------|-------------------------------------|
| Replace-then-rehash toàn bộ JSONL file | Attacker có write access → viết lại file hoàn toàn với hash chain mới hoàn toàn hợp lệ |
| Truncation từ cuối file | Không có external reference count để so sánh |
| Rollback về snapshot cũ | Không có external timestamp/seal để kiểm tra |
| Deletion của toàn bộ file | Không có off-system backup để detect |

**Kết luận:** Mọi attack model yêu cầu write access vào JSONL file đều NGOÀI PHẠM VI của offline simulation. Production cần WORM storage (không thể overwrite) kết hợp với off-system backup và access control.

---

## 5. PROD-AUD-01 — Production WORM Dependency

| Hạng mục | Nội dung |
|---------|---------|
| Định danh | PROD-AUD-01 |
| Trạng thái | DEFERRED_TO_PRODUCTION_QUALIFICATION |
| Milestone dự kiến | R1.3 |
| Yêu cầu kỹ thuật | Write-Once Read-Many (WORM) storage · off-system backup · retention policy · legal hold capability · access-controlled archive · independent restore verification |
| Không thể close bằng | Local JSONL test · pytest · offline simulation |

---

## 6. Những gì R1.1.2 đã sửa (RR-02/AC-11 remediation)

| Thay đổi | File | Mô tả |
|---------|------|-------|
| Module label | `project_audit_attribution.py` | Đổi tên module từ "R1.1 Offline Audit Attribution" thành "R1.1.2 Tamper-Evident Local Audit Ledger Simulation" |
| WORM marker | `project_audit_attribution.py` | Thêm `PROD_AUD_01_WORM_DEPENDENCY = "NOT_IMPLEMENTED"` và `LOCAL_LEDGER_CLASSIFICATION = "TAMPER_EVIDENT_LOCAL_SIMULATION_NOT_WORM"` |
| `sequence_number` | `SyntheticAuditEvent` | Thêm field monotonic counter (1-based) |
| Enhanced `verify_hash_chain()` | `project_audit_attribution.py` | Phát hiện 6 kịch bản tamper mới |
| `AuditAttributionLedger.record()` | `project_audit_attribution.py` | Tự gán `sequence_number = len(all_events) + 1` |
| `ledger_root_hash()` | `AuditAttributionLedger` | SHA-256 của concatenated event hashes |
| `create_checkpoint()` | `AuditAttributionLedger` | Point-in-time snapshot với `production_worm_dependency=NOT_IMPLEMENTED` |
| `to_dict()` | `SyntheticAuditEvent` | Thêm `sequence_number` và `local_ledger_classification` |

---

## 7. Test coverage cho WORM truthfulness

| Test ID | Assertion |
|--------|-----------|
| WORM-01 | `event.to_dict()` không chứa chuỗi "worm" (case-insensitive); có `local_ledger_classification` |
| WORM-02 | `AuditAttributionLedger` không có method tên `write_worm`, `seal`, `immutable_lock`, `worm_archive` |
| WORM-03 | `PROD_AUD_01_WORM_DEPENDENCY == "NOT_IMPLEMENTED"` |
| WORM-04 | `LOCAL_LEDGER_CLASSIFICATION` chứa `"NOT_WORM"` và `"SIMULATION"` |
| WORM-11 | Checkpoint record có `production_worm_dependency="NOT_IMPLEMENTED"` |

---

## 8. Residual risk sau R1.1.2

| Risk ID | Mô tả | Mức | Lý do còn tồn tại | Kế hoạch xử lý |
|--------|-------|-----|-------------------|----------------|
| RR-02 (updated) | Replace-then-rehash toàn bộ JSONL nếu có write access | MEDIUM | Không thể close offline — cần WORM storage vật lý | R1.3: production WORM-capable retention |
| PROD-AUD-01 | Production WORM storage không implemented | HIGH (deferred) | Ngoài phạm vi offline simulation | R1.3: production infrastructure |

**Validation Lead confirmation required for RR-02:** Xác nhận rằng DEFERRED_TO_PRODUCTION_QUALIFICATION (R1.3) là chấp nhận được cho giai đoạn này.

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
