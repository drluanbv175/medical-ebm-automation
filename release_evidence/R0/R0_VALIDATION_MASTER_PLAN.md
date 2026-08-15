# R0 Validation Master Plan

**Document:** R0_VALIDATION_MASTER_PLAN.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Phân biệt bắt buộc

```
Technical test pass
≠
Research authorization
≠
Ethics approval
≠
Clinical validity
```

Một hệ thống vượt qua tất cả technical tests vẫn KHÔNG đủ điều kiện cho
nghiên cứu y khoa thật nếu thiếu ethics approval và institutional authorization.
Một hệ thống có ethics approval vẫn KHÔNG được triển khai nếu chưa có
validated computerised system per applicable regulatory requirements.

---

## 1. Intended Use

| Thuộc tính | Mô tả |
|-----------|-------|
| **Intended use** | Medical Research Project Dossier Automation — hỗ trợ tổ chức và truy vết hồ sơ nghiên cứu y khoa theo chuẩn GCP |
| **User population** | PI, Co-Investigator, Data Manager, Evidence Reviewer, Monitor tại cơ sở y tế hoặc trường đại học |
| **Environment** | Institutional network với authentication; không phải consumer internet |
| **NOT intended for** | Clinical decision support · Prescription · Patient diagnosis · Real-time clinical monitoring · AI autonomous research execution |
| **Limitations** | AI outputs là DRAFT — yêu cầu human review trước mọi quyết định nghiên cứu |

---

## 2. User Requirements (URS)

| UR-ID | Yêu cầu |
|-------|---------|
| UR-01 | Hệ thống chỉ chấp nhận evidence metadata do con người cung cấp (HUMAN_PROVIDED_ONLY) |
| UR-02 | Evidence RETRACTED hoặc UNVERIFIED phải block claim — không cho phép dùng |
| UR-03 | Mọi reviewer phải được xác thực danh tính trước khi ghi attestation |
| UR-04 | Audit trail phải ghi lại mọi thao tác với user identity + timestamp |
| UR-05 | Hệ thống không được tự gọi API, network hoặc model runtime trong production |
| UR-06 | Dữ liệu bệnh nhân (PII) không được xuất hiện trong bất kỳ artifact nào |
| UR-07 | Mọi output phải kèm disclaimer "DRAFT — REQUIRE HUMAN REVIEW" |
| UR-08 | Backup phải được kiểm tra khả năng phục hồi định kỳ |
| UR-09 | Truy cập phải bị thu hồi ngay khi người dùng rời đề tài |
| UR-10 | Hệ thống phải cho phép database lock và controlled export |

---

## 3. Functional Requirements (FRS)

| FR-ID | Yêu cầu | Mapping URS |
|-------|---------|-------------|
| FR-01 | `EvidenceSourceLedger.add()` raise `ForbiddenRetrievalMode` cho mọi mode không phải HUMAN_PROVIDED_ONLY | UR-01 |
| FR-02 | `compute_claim_status()` trả BLOCKED khi source RETRACTED hoặc UNVERIFIED | UR-02 |
| FR-03 | Identity provider integration — authenticated user ID trên mọi write operation | UR-03 UR-04 |
| FR-04 | Audit log append-only với cryptographic integrity | UR-04 |
| FR-05 | No outbound network call từ production runtime | UR-05 |
| FR-06 | PII guard block mọi content chứa PII markers trước khi lưu | UR-06 |
| FR-07 | Disclaimer header xuất hiện trong mọi output | UR-07 |
| FR-08 | Backup automated với restore test procedure | UR-08 |
| FR-09 | Access revocation API / provisioning integration | UR-09 |
| FR-10 | Database lock command với PI authorization và post-lock export | UR-10 |

---

## 4. Risk Assessment (FMEA summary)

| Risk-ID | Mô tả rủi ro | Xác suất | Nghiêm trọng | Kiểm soát |
|---------|-------------|----------|--------------|-----------|
| RISK-01 | AI tự verify evidence → claim sai được chấp nhận | Thấp (guard hiện có) | Cao | AutoVerificationForbidden; ID verification |
| RISK-02 | PII rò rỉ vào artifact | Trung bình | Rất cao | PII guard + audit; de-identification protocol |
| RISK-03 | Reviewer identity giả mạo | Cao (hiện tại) | Rất cao | R1: MFA + institutional SSO |
| RISK-04 | Evidence retracted nhưng không được đánh dấu | Trung bình | Cao | SOP cho PI cập nhật retraction; D-R8 gate |
| RISK-05 | Audit log bị xóa hoặc giả mạo | Thấp | Rất cao | Tamper-evident storage; write-once sink |
| RISK-06 | Unauthorized data export | Thấp | Cao | RBAC; controlled export workflow |
| RISK-07 | Backup thất bại không phát hiện | Trung bình | Cao | Backup monitoring; periodic restore test |

---

## 5. Validation Strategy

### Approach
Kiểm định theo vòng đời hệ thống (Software Development Lifecycle validation):
- **IQ (Installation Qualification):** Hệ thống được cài đặt đúng môi trường, đúng version, cấu hình đúng
- **OQ (Operational Qualification):** Mỗi chức năng hoạt động đúng theo FRS
- **PQ (Performance Qualification):** Hệ thống hoạt động ổn định trong điều kiện sử dụng thực tế

### Scope
Toàn bộ production components: Research OS (Zone 1) + Identity Service (Zone 2) + EDC (Zone 3) + Data Mart interface (Zone 4).

### Exclusions
- Phần mềm thương mại có vendor validation — yêu cầu vendor validation package
- eHospital system — nằm ngoài scope

---

## 6. Test Protocols

| Protocol | Phase | Mô tả |
|---------|-------|-------|
| TP-01 | IQ | Installation và configuration verification |
| TP-02 | OQ | HUMAN_PROVIDED_ONLY enforcement test |
| TP-03 | OQ | Evidence blocking (RETRACTED/UNVERIFIED) |
| TP-04 | OQ | PII guard test với positive/negative cases |
| TP-05 | OQ | Audit trail integrity test |
| TP-06 | OQ | MFA enforcement test |
| TP-07 | OQ | Access revocation test |
| TP-08 | OQ | Database lock và controlled export test |
| TP-09 | OQ | Edit check validation |
| TP-10 | OQ | AE/SAE workflow test (LEVEL_B/C) |
| TP-11 | PQ | Multi-user concurrent access |
| TP-12 | PQ | Backup restore test |
| TP-13 | PQ | DR failover test |
| TP-SEC-01 | Security | Penetration test — authentication bypass |
| TP-SEC-02 | Security | Penetration test — audit log tampering |
| TP-SEC-03 | Security | Penetration test — data exfiltration |
| TP-SEC-04 | Security | Penetration test — write-back to eHospital |

---

## 7. Acceptance Criteria

| Criteria | Threshold |
|---------|-----------|
| OQ test pass rate | 100% — không có critical/major open defect |
| PQ test pass rate | 100% — không có critical/major open defect |
| Security critical findings | 0 open tại thời điểm Go/No-Go |
| Security high findings | 100% CAPA closed trước Go/No-Go |
| Backup restore test | Successful full restore trong RTO/RPO target |
| DR test | Successful failover và recovery documented |
| Audit trail integrity | 0 tampering detected trong pentest |
| PII guard | 0 PII leak trong test với boundary cases |

---

## 8. Traceability Matrix

| URS | FRS | Test Protocol | Acceptance Criteria |
|-----|-----|---------------|---------------------|
| UR-01 | FR-01 | TP-02 | PASS |
| UR-02 | FR-02 | TP-03 | PASS |
| UR-03 | FR-03 | TP-06 TP-07 | PASS |
| UR-04 | FR-04 | TP-05 TP-SEC-02 | PASS |
| UR-05 | FR-05 | TP-02 (no-network assertion) | PASS |
| UR-06 | FR-06 | TP-04 TP-SEC-03 | PASS |
| UR-07 | FR-07 | TP-02 (output check) | PASS |
| UR-08 | FR-08 | TP-12 TP-13 | PASS |
| UR-09 | FR-09 | TP-07 | PASS |
| UR-10 | FR-10 | TP-08 | PASS |

---

## 9. Change Control

Mọi thay đổi production system sau validation phải tuân theo:

1. **Change request** — mô tả thay đổi, lý do, impact assessment
2. **Impact assessment** — xác định test nào cần re-run
3. **Re-validation** — chạy lại test bị ảnh hưởng; cập nhật traceability matrix
4. **Review và approval** — PI và Validation Lead sign off
5. **Change log** — ghi nhận vào change control log

Không được deploy bất kỳ thay đổi nào lên production mà không qua change control.

---

## 10. Security Testing

| Test | Performer | Frequency |
|------|-----------|-----------|
| Penetration test | Independent security tester | Trước Go/No-Go mỗi level |
| Vulnerability scan | IT / Security team | Quarterly |
| Access control audit | IT / Auditor | Quarterly |
| Audit log integrity check | Auditor | Monthly |

---

## 11. Backup and Restore Testing

| Thành phần | Backup frequency | RPO target | RTO target | Restore test frequency |
|-----------|-----------------|------------|------------|----------------------|
| Research OS data | Daily | 24h | 4h | Monthly |
| EDC database | Continuous | 1h | 2h | Monthly |
| Audit log | Continuous | 1h | 1h | Monthly |
| Identity service | Daily | 24h | 4h | Quarterly |

---

## 12. Disaster Recovery Testing

DR test phải:
- Mô phỏng mất toàn bộ primary environment
- Verify backup data có thể restore thành công
- Verify system hoạt động đúng sau restore
- Verify audit trail liên tục (không có gap)
- Document kết quả với timestamp và sign-off

Frequency: ít nhất annual, trước Go/No-Go mỗi level.

---

## 13. Training Requirements

| Vai trò | Training bắt buộc trước truy cập |
|---------|----------------------------------|
| PI | System overview; data governance; ethics obligations; audit trail |
| Co-Investigator | Protocol adherence; data entry; AE reporting |
| Data Manager | EDC operation; edit check review; query management; lock procedure |
| Evidence Reviewer | Evidence governance; attestation policy; independence requirements |
| Monitor | Monitoring plan; central monitoring tool; escalation |

Training phải được document với date, content, sign-off.

---

## 14. Periodic Review

| Review | Frequency | Owner |
|--------|-----------|-------|
| Validation status review | Annual | Validation Lead + PI |
| Access control review | Quarterly | IT + PI |
| Audit log review | Monthly | Auditor / Data Manager |
| Backup/restore test review | Monthly | IT |
| Security scan review | Quarterly | IT |
| Monitoring report review | Per protocol schedule | Monitor + PI |

---

## 15. Decommissioning and Retention

- Dữ liệu nghiên cứu phải được retain per applicable regulations (tối thiểu 15 năm cho thử nghiệm lâm sàng GCP — xác nhận với institution)
- Decommissioning phải bao gồm: final export → verification → archive → destroy procedure
- Dữ liệu không được xóa đơn phương mà không có PI và institutional authorization
- Audit log phải được retain cùng với hoặc dài hơn dữ liệu nghiên cứu

---

*Applicable institutional, Ministry of Health, ethics committee and legal requirements
must be confirmed by the institution before study activation.*

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
