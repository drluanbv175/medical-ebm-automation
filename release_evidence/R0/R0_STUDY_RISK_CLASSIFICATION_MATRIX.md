# R0 Study Risk Classification Matrix

**Document:** R0_STUDY_RISK_CLASSIFICATION_MATRIX.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Nguyên tắc

Ma trận này phân loại nghiên cứu y khoa theo 3 cấp rủi ro tăng dần.
Mỗi cấp có yêu cầu quản trị, đạo đức và kỹ thuật riêng phải được
xác minh bởi tổ chức trước khi kích hoạt nghiên cứu.

**Không được coi ma trận này là quyết định đạo đức hay pháp lý.**
Tổ chức phải tự xác nhận với hội đồng đạo đức và cơ quan có thẩm quyền.

---

## LEVEL_A — Retrospective De-identified Study

### Mô tả
Nghiên cứu hồi cứu trên dữ liệu đã được khử định danh hoàn toàn trước khi nhập vào hệ thống.
Không tiếp xúc trực tiếp với người tham gia. Không can thiệp điều trị.

### Bảng yêu cầu

| Thuộc tính | LEVEL_A |
|-----------|---------|
| **study_risk** | MINIMAL — không can thiệp, không tiếp xúc người tham gia |
| **participant_contact** | NONE — dữ liệu đã tách định danh trước khi nhập |
| **real_data_requirement** | Dữ liệu khử định danh (de-identified); không được nhập PII |
| **ethics_requirement** | IRB/IEC exemption hoặc waiver — phải được xác nhận bởi hội đồng đạo đức |
| **consent_or_waiver_requirement** | Waiver thường phù hợp; phải do hội đồng đạo đức xác nhận |
| **data_platform_requirement** | EDC kiểm định tối thiểu; audit trail; access control; encryption at rest |
| **monitoring_requirement** | Periodic data quality review; không cần site monitoring |
| **safety_reporting_requirement** | Không áp dụng (không can thiệp) |
| **registration_requirement** | Thường không bắt buộc — xác nhận với tạp chí đích |
| **eHospital_integration_requirement** | Read-only extract đã được phê duyệt; không write-back |
| **independent_review_requirement** | Data access authorization review; không cần DSMB |
| **minimum_go_no_go_conditions** | Ethics waiver/exemption; de-identification protocol approved; validated EDC; real user identity; MFA; audit trail; institutional authorization |

### Khuyến nghị
> **LEVEL_A là pilot đầu tiên được khuyến nghị.**  
> Rủi ro thấp nhất, phù hợp nhất để kiểm thử hệ thống và quy trình trong điều kiện gần thực tế trước khi mở cấp độ cao hơn.

---

## LEVEL_B — Prospective Observational Study

### Mô tả
Nghiên cứu tiến cứu quan sát — thu thập dữ liệu từ người tham gia theo thời gian thực.
Có tiếp xúc người tham gia để thu thập dữ liệu, nhưng không can thiệp điều trị.

### Bảng yêu cầu

| Thuộc tính | LEVEL_B |
|-----------|---------|
| **study_risk** | LOW-MODERATE — tiếp xúc người tham gia; thu thập dữ liệu trực tiếp |
| **participant_contact** | YES — consent, enrollment, follow-up |
| **real_data_requirement** | Dữ liệu định danh (pseudonymized minimum) + consent trước khi thu thập |
| **ethics_requirement** | Full ethics approval từ IRB/IEC — không được waiver |
| **consent_or_waiver_requirement** | Informed consent bắt buộc; ICF phải được phê duyệt |
| **data_platform_requirement** | Validated EDC (21 CFR Part 11 equivalent hoặc tương đương cục bộ); real-time audit trail; pseudonymization; change control |
| **monitoring_requirement** | Monitoring plan; periodic site visits hoặc central monitoring; data quality checks |
| **safety_reporting_requirement** | SAE reporting (theo timeline); protocol deviation log |
| **registration_requirement** | Đăng ký trước thu thập (ClinicalTrials.gov hoặc ICTRP hoặc registry trong nước) |
| **eHospital_integration_requirement** | Read-only với mapping và reconciliation protocol; không write-back; data dictionary approved |
| **independent_review_requirement** | Monitoring committee; không bắt buộc DSMB nhưng khuyến nghị nếu có endpoint lâm sàng |
| **minimum_go_no_go_conditions** | LEVEL_A đã đạt qualification; full ethics approval; registered protocol; validated EDC; full identity management (MFA, RBAC, audit); monitoring plan approved; SAE workflow active; institutional authorization |

### Ràng buộc
> **LEVEL_B chỉ được mở sau khi LEVEL_A đạt qualification.**  
> Tổ chức phải chứng minh hệ thống hoạt động an toàn trong nghiên cứu thật cấp A trước.

---

## LEVEL_C — Interventional Clinical Trial

### Mô tả
Thử nghiệm lâm sàng can thiệp — phân ngẫu nhiên hoặc có nhóm chứng; có thể thay đổi điều trị.
Yêu cầu cao nhất về đạo đức, an toàn, quản trị và kiểm định.

### Bảng yêu cầu

| Thuộc tính | LEVEL_C |
|-----------|---------|
| **study_risk** | HIGH — can thiệp điều trị; nguy cơ biến cố bất lợi nghiêm trọng |
| **participant_contact** | YES — tuyển dụng, can thiệp, theo dõi an toàn, báo cáo biến cố |
| **real_data_requirement** | Dữ liệu định danh đầy đủ; audit trail toàn bộ; không thể waiver PII |
| **ethics_requirement** | Full IEC/IRB approval; cập nhật khi sửa protocol |
| **consent_or_waiver_requirement** | Informed consent bắt buộc; không được waiver; tái consent khi có thay đổi quan trọng |
| **data_platform_requirement** | GCP-compliant EDC; 21 CFR Part 11 hoặc tương đương; computerised system validation (CSV); change control chính thức; backup/DR tested |
| **monitoring_requirement** | Site monitoring per protocol; central statistical monitoring; DSMB/DMC nếu có interim analysis |
| **safety_reporting_requirement** | SAE/SUSAR reporting theo timeline GCP; stopping rules; DSMB oversight |
| **registration_requirement** | Bắt buộc đăng ký TRƯỚC tuyển dụng người tham gia đầu tiên |
| **eHospital_integration_requirement** | Approved extraction boundary; pharmacovigilance integration; không write-back; real-time safety data |
| **independent_review_requirement** | DSMB/DMC; independent data monitor; security audit; regulatory inspection readiness |
| **minimum_go_no_go_conditions** | LEVEL_B đã đạt qualification; GCP certification; full ethics approval; DSMB active; SAE pipeline validated; computerised system validation complete; pharmacovigilance procedures; regulatory notification (nếu áp dụng); institutional sponsor authorization |

### Ràng buộc
> **LEVEL_C chỉ được mở sau khi có đầy đủ GCP, ethics, safety workflow, validated computerised system và institutional authorization.**  
> Không được dùng hệ thống chưa kiểm định cho thử nghiệm can thiệp có người tham gia.

---

## Tóm tắt so sánh

| Yêu cầu | LEVEL_A | LEVEL_B | LEVEL_C |
|---------|---------|---------|---------|
| Participant contact | Không | Có | Có |
| Ethics approval | Waiver/Exemption | Full approval | Full approval + updates |
| Informed consent | Không bắt buộc | Bắt buộc | Bắt buộc |
| Registration | Thường không | Bắt buộc | Bắt buộc (pre-enrollment) |
| Validated EDC | Minimal | Full | GCP-compliant |
| Safety reporting | N/A | SAE | SAE/SUSAR + DSMB |
| eHospital integration | Read-only extract | Read-only + mapping | Read-only + pharmacovigilance |
| Independent review | Data access review | Monitoring committee | DSMB + security audit |
| Requires prior level | Không | LEVEL_A PASS | LEVEL_B PASS |

---

*Applicable institutional, Ministry of Health, ethics committee and legal requirements
must be confirmed by the institution before study activation.*

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
