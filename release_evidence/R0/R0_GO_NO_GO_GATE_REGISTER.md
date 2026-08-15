# R0 Go/No-Go Gate Register

**Document:** R0_GO_NO_GO_GATE_REGISTER.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Nguyên tắc

Mỗi Gate phải được đánh giá và sign-off bởi **người thật có thẩm quyền** —
không phải AI. Gate PASS chỉ được tuyên bố sau khi tất cả điều kiện bắt buộc
được kiểm chứng độc lập.

AI system có thể hỗ trợ chuẩn bị checklist và tổng hợp evidence —
nhưng quyết định Go/No-Go thuộc về PI và tổ chức.

---

## GATE-V435 — V4.3.5 Baseline Freeze

| Thuộc tính | Nội dung |
|-----------|---------|
| **Gate ID** | GATE-V435 |
| **Phase** | V4.3.5 |
| **Decision** | Freeze baseline cho R0 blueprint |
| **Reviewer** | PI (offline review) |
| **Status** | **PASS** — `v4.3.5-frozen` tại `d041ecd` |

### Điều kiện PASS

| # | Điều kiện | Kết quả |
|---|----------|---------|
| G1 | `MRAQ_OFFLINE_CI=1 pytest` → 0 failed | ✓ 797 PASS |
| G2 | V4.3.5 suite 21 tests PASS | ✓ 21 PASS |
| G3 | `verify_manifest_registry.py` → PASS | ✓ PASS |
| G4 | Fresh archive SHA256 verified | ✓ `78d34ff3...` |
| G5 | No network calls in suite | ✓ CONFIRMED |
| G6 | No PII in test data | ✓ CONFIRMED |
| G7 | Evidence Source Ledger append-only | ✓ CONFIRMED |
| G8 | Claim Traceability Ledger append-only | ✓ CONFIRMED |
| G9 | AutoVerificationForbidden enforced | ✓ CONFIRMED |
| G10 | RETRACTED source blocks D-R8 | ✓ CONFIRMED |

### Blocking conditions (nếu bất kỳ điều nào FAIL)

- Test failure → HOLD (tìm root cause, không bỏ qua)
- PII leak → BLOCKED (không được tiếp tục)
- Network call → BLOCKED (vi phạm bất biến cốt lõi)

---

## GATE-R1 — Identity and Governance Service Ready

| Thuộc tính | Nội dung |
|-----------|---------|
| **Gate ID** | GATE-R1 |
| **Phase** | R1 |
| **Decision** | Identity infrastructure đủ điều kiện cho production access |
| **Reviewer** | PI + IT Lead + Validation Lead |
| **Status** | **OPEN** — chưa thực hiện |

### Điều kiện PASS (tất cả bắt buộc)

| # | Điều kiện | Evidence required |
|---|----------|-------------------|
| R1-G1 | Institutional SSO/identity provider integrated và tested | Integration test report |
| R1-G2 | MFA bắt buộc cho 100% production users — không có bypass | MFA enforcement test |
| R1-G3 | Access revocation tested (deactivate account → access denied trong 1h) | Revocation test report |
| R1-G4 | RBAC roles defined, configured, tested cho mọi study role | RBAC audit report |
| R1-G5 | Delegation log functional — task-specific, expiry, signed | Delegation log test |
| R1-G6 | COI declarations collected từ mọi nhân sự nghiên cứu | Signed COI forms |
| R1-G7 | Audit trail tamper-resistant — penetration test TP-SEC-02 PASS | Pentest report |
| R1-G8 | E-signature policy signed và implemented | Policy document + technical test |
| R1-G9 | Separation of duties: author ≠ reviewer enforced | RBAC separation test |
| R1-G10 | Access control review procedure documented | Review procedure |

### Blocking conditions

- Anonymous access possible → BLOCKED
- MFA bypassable → BLOCKED
- Audit log tamperable → BLOCKED
- No COI declarations → HOLD

---

## GATE-R2 — Validated EDC Ready

| Thuộc tính | Nội dung |
|-----------|---------|
| **Gate ID** | GATE-R2 |
| **Phase** | R2 |
| **Decision** | EDC production đủ điều kiện cho data entry |
| **Reviewer** | PI + Validation Lead + Data Manager |
| **Status** | **OPEN** — chưa thực hiện |

### Điều kiện PASS (tất cả bắt buộc)

| # | Điều kiện | Evidence required |
|---|----------|-------------------|
| R2-G1 | Validation package (IQ/OQ/PQ) complete và signed | Validation package |
| R2-G2 | CRF design approved by PI | CRF specification signed |
| R2-G3 | Edit checks validated (TP-09) | Validation test results |
| R2-G4 | Database lock procedure tested | Lock/unlock test report |
| R2-G5 | Controlled export với hash verified | Export test report |
| R2-G6 | Pseudonymization verified (no PII in Zone 1) | Pseudonymization test |
| R2-G7 | Backup restore tested trong RTO | Restore test report |
| R2-G8 | DR test documented | DR test report |
| R2-G9 | Change control procedure in place | Change control SOP |
| R2-G10 | 0 open critical/major validation defects | Defect log |

### Blocking conditions

- Open critical validation defect → BLOCKED
- Backup not tested → HOLD
- Pseudonymization not verified → BLOCKED
- Database lock not functional → HOLD

---

## GATE-R3 — Ethics and Safety Operations Ready

| Thuộc tính | Nội dung |
|-----------|---------|
| **Gate ID** | GATE-R3 |
| **Phase** | R3 |
| **Decision** | Ethics approval và safety operations đủ điều kiện cho LEVEL_A pilot |
| **Reviewer** | PI + Ethics Committee + Institution |
| **Status** | **OPEN** — chưa thực hiện |

### Điều kiện PASS (tất cả bắt buộc)

| # | Điều kiện | Evidence required |
|---|----------|-------------------|
| R3-G1 | Ethics waiver/exemption received từ IRB/IEC | Ethics approval letter |
| R3-G2 | De-identification protocol approved | DI SOP signed |
| R3-G3 | Data access agreement executed với data custodian | Signed agreement |
| R3-G4 | Data minimization policy signed | Policy document |
| R3-G5 | Permitted-use policy signed | Policy document |
| R3-G6 | Monitoring plan approved (LEVEL_A minimal) | Monitoring plan |
| R3-G7 | AE/SAE workflow tested (nếu chuẩn bị LEVEL_B) | Workflow test |
| R3-G8 | Institutional authorization confirmed | Authorization letter |

### Blocking conditions

- Ethics approval absent → BLOCKED (không thể proceed với bất kỳ real data)
- De-identification protocol not approved → BLOCKED
- Data access agreement not signed → BLOCKED

---

## GATE-R4 — eHospital Data Mart Boundary Ready

| Thuộc tính | Nội dung |
|-----------|---------|
| **Gate ID** | GATE-R4 |
| **Phase** | R4 |
| **Decision** | Read-only eHospital extraction boundary đủ điều kiện |
| **Reviewer** | PI + Hospital IT + Institution |
| **Status** | **OPEN** — chưa thực hiện |

### Điều kiện PASS (tất cả bắt buộc)

| # | Điều kiện | Evidence required |
|---|----------|-------------------|
| R4-G1 | Data access agreement (HIS-01) signed | Signed agreement |
| R4-G2 | Approved field list from data custodian (in writing) | Field list document |
| R4-G3 | Technical read-only verified — no write-back | Architecture review + TP-SEC-04 PASS |
| R4-G4 | Data dictionary mapping approved (HIS-02) | Data dictionary |
| R4-G5 | Reconciliation procedure tested (synthetic extraction) | Reconciliation test report |
| R4-G6 | Institutional authorization for eHospital access | Authorization |

### Blocking conditions

- Write-back possible → BLOCKED (kiến trúc phải đảm bảo)
- No data access agreement → BLOCKED
- No approved field list → HOLD

---

## GATE-R5 — Independent Qualification Complete

| Thuộc tính | Nội dung |
|-----------|---------|
| **Gate ID** | GATE-R5 |
| **Phase** | R5 |
| **Decision** | Independent validation và security qualification đủ điều kiện cho pilot |
| **Reviewer** | Independent Validator + Independent Security Tester + PI |
| **Status** | **OPEN** — chưa thực hiện |

### Điều kiện PASS (tất cả bắt buộc)

| # | Điều kiện | Evidence required |
|---|----------|-------------------|
| R5-G1 | Independent penetration test complete | Pentest report (signed by independent tester) |
| R5-G2 | 0 open critical security findings | CAPA log |
| R5-G3 | 100% high security findings CAPA closed | CAPA log |
| R5-G4 | Independent validation review complete | Validation review report (signed by independent validator) |
| R5-G5 | 0 open critical/major validation defects | Defect log |
| R5-G6 | 100% training completion với records | Training records |
| R5-G7 | Backup restore test PASS trong RTO | Restore test |
| R5-G8 | DR test PASS | DR test report |
| R5-G9 | Operational qualification signed | OQ sign-off |

### Blocking conditions

- Open critical security finding → BLOCKED (không Go mà không CAPA closed)
- Independent validation not performed → BLOCKED
- Training incomplete → HOLD

---

## GATE-R6 — Level-A Pilot Go/No-Go

| Thuộc tính | Nội dung |
|-----------|---------|
| **Gate ID** | GATE-R6 |
| **Phase** | R6 |
| **Decision** | LEVEL_A pilot hoàn thành thành công; có thể mở LEVEL_B |
| **Reviewer** | PI + Independent Reviewer + Institution |
| **Status** | **OPEN** — chưa thực hiện |

### Điều kiện PASS (tất cả bắt buộc)

| # | Điều kiện | Evidence required |
|---|----------|-------------------|
| R6-G1 | LEVEL_A pilot complete với 0 critical incidents | Pilot completion report |
| R6-G2 | Audit trail complete — no gaps | Audit trail review |
| R6-G3 | Data quality acceptable per PI | Data quality report |
| R6-G4 | No PII leak trong pilot | PII audit |
| R6-G5 | No unauthorized access | Security incident log |
| R6-G6 | Independent Reviewer sign-off | Independent review report |
| R6-G7 | Ethics waiver still valid | Confirmation |
| R6-G8 | Institutional authorization for LEVEL_B confirmed | Authorization letter |
| R6-G9 | Incident log reviewed và all incidents closed | Incident log |

### Blocking conditions

- Any critical incident → BLOCKED (investigate, CAPA, re-pilot)
- PII leak → BLOCKED
- Independent Reviewer HOLD → HOLD
- Ethics expired → BLOCKED

---

## GATE-R7 — Level-B Prospective Readiness

| Thuộc tính | Nội dung |
|-----------|---------|
| **Gate ID** | GATE-R7 |
| **Phase** | R7 |
| **Decision** | Đủ điều kiện tuyển dụng người tham gia cho prospective observational study |
| **Reviewer** | PI + Ethics Committee + Monitor |
| **Status** | **OPEN** — chưa thực hiện |

### Điều kiện PASS (tất cả bắt buộc)

| # | Điều kiện | Evidence required |
|---|----------|-------------------|
| R7-G1 | Full ethics approval (not waiver) | Ethics approval letter |
| R7-G2 | ICF version approved và available at site | ICF version + approval |
| R7-G3 | Protocol registered trước tuyển dụng đầu tiên | Registration number |
| R7-G4 | AE/SAE workflow active và tested | Workflow test + timeline test |
| R7-G5 | Monitoring plan approved và activated | Monitoring plan + activation |
| R7-G6 | Site monitoring visit 1 scheduled/completed | Monitoring visit report |
| R7-G7 | LEVEL_A pilot (R6) PASS | R6 sign-off |

### Blocking conditions

- Full ethics approval absent → BLOCKED
- No ICF approval → BLOCKED
- No protocol registration → BLOCKED
- AE/SAE workflow not active → BLOCKED

---

## GATE-R8 — Level-C Interventional Readiness

| Thuộc tính | Nội dung |
|-----------|---------|
| **Gate ID** | GATE-R8 |
| **Phase** | R8 |
| **Decision** | Đủ điều kiện bắt đầu thử nghiệm lâm sàng can thiệp |
| **Reviewer** | PI + Sponsor + DSMB + Regulatory Affairs + Independent Auditor |
| **Status** | **OPEN** — chưa thực hiện |

### Điều kiện PASS (tất cả bắt buộc)

| # | Điều kiện | Evidence required |
|---|----------|-------------------|
| R8-G1 | GCP certification — 100% study personnel | GCP certificates |
| R8-G2 | DSMB constituted và charter signed | DSMB charter + member list |
| R8-G3 | SUSAR reporting pipeline tested trong timeline | SUSAR timeline test |
| R8-G4 | Regulatory notification acknowledged (nếu áp dụng) | Regulatory correspondence |
| R8-G5 | Full ethics approval cho LEVEL_C protocol | Ethics approval |
| R8-G6 | Pharmacovigilance SOP signed | PV SOP |
| R8-G7 | Computerised system validation (CSV) complete | CSV package |
| R8-G8 | Institutional sponsor authorization | Sponsor authorization |
| R8-G9 | LEVEL_B (R7) PASS | R7 sign-off |

### Blocking conditions

- GCP not certified → BLOCKED
- No DSMB → BLOCKED
- No SUSAR pathway → BLOCKED
- Ethics not approved for LEVEL_C → BLOCKED
- No sponsor authorization → BLOCKED

---

## Tóm tắt trạng thái hiện tại

| Gate | Phase | Status |
|------|-------|--------|
| GATE-V435 | V4.3.5 | **PASS** |
| GATE-R1 | R1 Identity | **OPEN** |
| GATE-R2 | R2 Validated EDC | **OPEN** |
| GATE-R3 | R3 Ethics + Safety | **OPEN** |
| GATE-R4 | R4 eHospital Boundary | **OPEN** |
| GATE-R5 | R5 Independent Qualification | **OPEN** |
| GATE-R6 | R6 Level-A Pilot | **OPEN** |
| GATE-R7 | R7 Level-B Readiness | **OPEN** |
| GATE-R8 | R8 Level-C Readiness | **OPEN** |

**7 / 8 gates OPEN → Real research execution: BLOCKED**

---

*Applicable institutional, Ministry of Health, ethics committee and legal requirements
must be confirmed by the institution before study activation.*

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
