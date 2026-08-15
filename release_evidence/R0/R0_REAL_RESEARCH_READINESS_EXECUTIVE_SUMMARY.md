# R0 Real Research Readiness — Executive Summary

**Document:** R0_REAL_RESEARCH_READINESS_EXECUTIVE_SUMMARY.md  
**Date:** 2026-06-28  
**Version:** R0  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## 1. Mục đích

R0 là **blueprint chuyển đổi** — kế hoạch tổng thể để chuyển Medical Research Project
Dossier Automation từ hệ thống offline, draft-only sang nền tảng có thể được đánh giá
độc lập cho nghiên cứu y khoa thật trong tương lai.

R0 **không triển khai** nghiên cứu thật, không mở API, không nhập dữ liệu bệnh nhân,
không thay đổi source code hệ thống, và không cấp bất kỳ qualification nào.

---

## 2. Trạng thái hiện tại

| Thuộc tính | Trạng thái |
|-----------|-----------|
| Hệ thống hiện tại | **PRE-PRODUCTION RESEARCH OS** |
| Môi trường | OFFLINE · DRAFT-ONLY · SYNTHETIC DATA |
| Qualification | NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE |
| Dữ liệu thật | BLOCKED |
| API / network | BLOCKED |
| Kết nối eHospital/HIS/EMR | BLOCKED |
| Ethics approval | NOT ESTABLISHED |
| Independent review | NOT ESTABLISHED |
| Reviewer identity authentication | NOT IMPLEMENTED |

Hệ thống hiện tại đã hoàn thành đến **V4.3.5** với Evidence Intake và Claim Traceability.
Đây là nền tảng offline có kiến trúc DRAFT-only hợp lệ — nhưng chưa đủ điều kiện
cho nghiên cứu y khoa thật ở bất kỳ cấp độ nào.

---

## 3. Lý do cần R0 Blueprint

Hệ thống hiện tại có các gap nghiêm trọng ngăn sử dụng trong nghiên cứu thật:

| Nhóm gap | Ví dụ |
|----------|-------|
| **Quản trị** | Không có ethics approval, không có ủy quyền tổ chức |
| **Danh tính** | Không xác thực danh tính người dùng thật, không có MFA |
| **Dữ liệu** | Không có EDC (electronic data capture) đã kiểm định, không có audit trail đạt chuẩn |
| **An toàn** | Không có workflow biến cố bất lợi, không có monitoring kế hoạch |
| **Kiểm định** | Không có validation package, không có independent security testing |
| **Tích hợp** | Không có ranh giới truy xuất eHospital đã được phê duyệt |

---

## 4. Lộ trình tổng quan

```
V4.3.5 (HIỆN TẠI — DONE)
  Evidence Intake + Claim Traceability
  ↓
R1 — Identity, RBAC, MFA, Delegation, Audit Attribution
R2 — Validated EDC + Research Data Lifecycle
R3 — Ethics, Consent, Monitoring, Safety Operations
R4 — eHospital Read-Only Research Data Mart Sandbox
R5 — Independent Security + Validation + Operational Qualification
R6 — Limited Level-A Pilot + Formal Go/No-Go
R7 — Level-B Prospective Observational Readiness
R8 — Level-C Interventional Trial Readiness
```

Lộ trình là **tuần tự và có cổng** — không được bỏ qua phase, không được mở phase sau
khi phase trước chưa đạt Go/No-Go.

---

## 5. Phân loại rủi ro nghiên cứu

R0 xác định 3 cấp độ nghiên cứu:

| Cấp độ | Loại | Yêu cầu tối thiểu |
|--------|------|-------------------|
| **LEVEL_A** | Retrospective de-identified | IRB waiver hoặc exemption; de-identification protocol |
| **LEVEL_B** | Prospective observational | Full ethics approval; informed consent; monitoring plan |
| **LEVEL_C** | Interventional clinical trial | GCP; DSMB/DMC; safety reporting; prospective registration |

**LEVEL_A là pilot khuyến nghị đầu tiên** — cấp độ rủi ro thấp nhất, phù hợp nhất
cho kiểm thử hệ thống trong điều kiện gần thực tế.

---

## 6. Dependencies với V4.3.5

Trước khi bắt đầu bất kỳ nghiên cứu thật nào, hệ thống V4.3.5 phải được:

- Evidence Source Ledger PASS với evidence thật từ PI
- Claim Traceability Ledger PASS với claims liên kết evidence verified
- D-R8 gate PASS (không có RETRACTED, không có UNVERIFIED claim)
- Reviewer authentication được thiết lập (ngoài phạm vi V4.3.5)

Evidence chưa verified **KHÔNG** đủ điều kiện bắt đầu nghiên cứu thật.

---

## 7. Kết luận bắt buộc

```
Current system status:                    PRE-PRODUCTION RESEARCH OS
Level-A retrospective pilot readiness:    HOLD
Level-B prospective observational:        HOLD
Level-C interventional trial:             HOLD
Evidence governance dependency (V4.3.5):  PASS (offline baseline)
Identity and authentication:              OPEN
Validated EDC:                            OPEN
Ethics and institutional authorization:   OPEN
eHospital research data boundary:         OPEN
Independent qualification:                OPEN
Real research execution:                  BLOCKED
Qualification:                            NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

---

*Applicable institutional, Ministry of Health, ethics committee and legal requirements
must be confirmed by the institution before study activation.*

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
