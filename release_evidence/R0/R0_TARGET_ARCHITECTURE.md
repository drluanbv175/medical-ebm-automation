# R0 Target Architecture

**Document:** R0_TARGET_ARCHITECTURE.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Nguyên tắc kiến trúc

```
No direct AI write-back to eHospital.
No direct AI access to identifiable data by default.
No production deployment without documented validation.
No study activation without ethics and institutional authorization.
```

Kiến trúc mục tiêu tách biệt 5 vùng (zone) với ranh giới kiểm soát rõ ràng.
Không có vùng nào được kết nối trực tiếp với vùng khác mà không qua access control.

---

## Sơ đồ tổng quan

```
┌─────────────────────────────────────────────────────────────────┐
│  ZONE 5: Qualification and Monitoring Layer                      │
│  (Validation Evidence · Security Evidence · CAPA · Audit)       │
└────────────────────────────┬────────────────────────────────────┘
                             │ Read-only oversight
┌────────────────────────────▼────────────────────────────────────┐
│  ZONE 1: Research OS                                             │
│  (Dossier · Review · Evidence Governance · Change Control)      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ research_project/ package · project_* modules · CLI     │    │
│  │ Evidence Source Ledger (V4.3.5) · Claim Traceability    │    │
│  │ Human Review Operations (V4.3.4) · QA Gates D-R1..D-R15│    │
│  └─────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │ Authenticated API (R1 onwards)
┌────────────────────────────▼────────────────────────────────────┐
│  ZONE 2: Identity and Governance Service                         │
│  (Real Accounts · RBAC · MFA · Delegation · Audit · Revocation) │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Institutional SSO / LDAP / SAML                         │    │
│  │ Role: PI · Co-I · Data Manager · Reviewer · Monitor     │    │
│  │ MFA enforcement · Access revocation workflow            │    │
│  │ COI declaration · Delegation log                        │    │
│  │ Tamper-evident audit log (hash chain / write-once)      │    │
│  └─────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │ Validated data entry
┌────────────────────────────▼────────────────────────────────────┐
│  ZONE 3: Validated Research Data Platform                        │
│  (CRF · Data Entry · Edit Checks · Queries · Lock · Export)     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Production CRF (validated per EDC-01..EDC-04)           │    │
│  │ Edit checks · Query management · Data reconciliation    │    │
│  │ Database lock procedure · Controlled export             │    │
│  │ Pseudonymization before ZONE 1 access                   │    │
│  │ AE/SAE workflow (LEVEL_B/C) · Deviation log             │    │
│  └─────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │ Read-only approved extract
┌────────────────────────────▼────────────────────────────────────┐
│  ZONE 4: Research Data Mart                                      │
│  (Pseudonymized · Minimum-necessary · Read-only from eHospital)  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Approved extraction boundary (HIS-01)                   │    │
│  │ Data dictionary mapping (HIS-02)                        │    │
│  │ De-identified / pseudonymized only                      │    │
│  │ No write-back to eHospital                              │    │
│  │ Field list approved by institution + ethics committee   │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘

                    ─── eHospital / HIS / EMR ───
                    (External — not part of system)
                    (Read-only extract only — no write)
```

---

## ZONE 1: Research OS

**Phạm vi:** Hệ thống hiện tại (`research_project/` package + CLI).

**Chức năng:**
- Project dossier automation (19 artifacts, 15 QA gates)
- Evidence Source Ledger (V4.3.5) — append-only, HUMAN_PROVIDED_ONLY
- Claim Traceability Ledger (V4.3.5) — append-only
- Human Review Operations (V4.3.4) — 4 roles, 5 decisions
- D-R8 evidence readiness gate

**Trạng thái hiện tại:** OFFLINE · DRAFT-ONLY · SYNTHETIC DATA

**Yêu cầu để vào production:**
- Zone 2 (Identity) phải sẵn sàng trước
- Validated deployment (EDC-04)
- Audit trail tamper-evident

**Ranh giới cứng:**
- KHÔNG write-back sang eHospital
- KHÔNG truy cập trực tiếp dữ liệu định danh
- KHÔNG tự generate DOI/PMID/citation
- KHÔNG tự verify evidence

---

## ZONE 2: Identity and Governance Service

**Phạm vi:** Dịch vụ quản lý danh tính và quản trị — nằm ngoài Research OS hiện tại.

**Chức năng:**
- Xác thực danh tính thật với institutional SSO (LDAP/SAML/OAuth)
- MFA bắt buộc cho mọi truy cập production
- RBAC: PI · Co-Investigator · Data Manager · Evidence Reviewer · Monitor · Auditor
- Delegation log với expiry và traceability
- COI declaration management
- Access revocation workflow (on departure/role change)
- Tamper-evident audit log (hash chain hoặc write-once sink)
- Electronic signature capture (với policy per ID-03)

**Dependencies:** R1 implementation phase

**Ranh giới cứng:**
- KHÔNG có anonymous access
- KHÔNG tự grant PI approval
- KHÔNG bypass MFA

---

## ZONE 3: Validated Research Data Platform

**Phạm vi:** EDC (Electronic Data Capture) production — nằm ngoài Research OS hiện tại.

**Chức năng:**
- Production CRF (validated, based on approved protocol)
- Edit checks với range/logic validation
- Query management workflow (data manager ↔ site)
- Pseudonymization trước khi data vào Zone 1
- Database lock với PI authorization
- Controlled export với audit trail
- AE/SAE reporting workflow (LEVEL_B và LEVEL_C)
- Protocol deviation log

**Dependencies:** R2 implementation phase; Zone 2 sẵn sàng

**Ranh giới cứng:**
- KHÔNG cho phép data entry không qua edit checks
- KHÔNG export sau database lock mà không có PI authorization
- AE/SAE workflow phải active trước LEVEL_B

---

## ZONE 4: Research Data Mart

**Phạm vi:** Lớp trích xuất read-only từ eHospital — được phê duyệt và giám sát bởi institution.

**Chức năng:**
- Approved read-only extract từ eHospital/HIS/LIS/PACS (per HIS-01)
- Data dictionary mapping (per HIS-02)
- De-identification / pseudonymization trước khi vào Zone 3
- Minimum-necessary field list (approved by ethics + institution)
- Quality reconciliation procedure

**Dependencies:** R4 implementation phase; HIS-01 và HIS-02 approved; Zone 2 và 3 sẵn sàng

**Ranh giới cứng:**
- KHÔNG write-back về eHospital
- KHÔNG AI truy cập trực tiếp dữ liệu định danh
- KHÔNG extract field ngoài approved list
- KHÔNG kết nối PACS/LIS mà không có thêm approval

---

## ZONE 5: Qualification and Monitoring Layer

**Phạm vi:** Lớp giám sát, kiểm định và bằng chứng — overlay trên tất cả zones.

**Chức năng:**
- Validation evidence (IQ/OQ/PQ) cho mọi production component
- Security testing evidence (penetration test, vulnerability assessment)
- CAPA (Corrective and Preventive Action) tracking
- Monitoring reports (central statistical + site monitoring)
- Backup/restore test evidence
- DR test evidence
- Audit log review
- Periodic review schedule

**Dependencies:** R5 implementation phase; tất cả zones khác sẵn sàng

**Ranh giới cứng:**
- KHÔNG phát hành production mà không có validation evidence
- KHÔNG bắt đầu nghiên cứu thật mà không có Go/No-Go sign-off từ Zone 5

---

## Luồng dữ liệu an toàn

```
eHospital (external)
    │
    │ Read-only approved extract ONLY
    ▼
ZONE 4: Research Data Mart
    │ De-identified / pseudonymized
    │
    ▼
ZONE 3: Validated EDC
    │ Pseudonymized data entry + edit checks
    │ AE/SAE workflow
    │
    ▼
ZONE 1: Research OS
    │ DRAFT dossier + evidence governance
    │ HUMAN_PROVIDED_ONLY evidence metadata
    │
    ▼ (read-only oversight)
ZONE 5: Qualification Layer
    │
    ▼ (all zones)
ZONE 2: Identity + Governance
    (overlays all zones — authentication + audit)
```

**Không có luồng ngược** từ Zone 1 → Zone 4 → eHospital.  
**Không có AI write-back** vào bất kỳ system lâm sàng nào.

---

*Applicable institutional, Ministry of Health, ethics committee and legal requirements
must be confirmed by the institution before study activation.*

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
