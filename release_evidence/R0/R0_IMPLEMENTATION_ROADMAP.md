# R0 Implementation Roadmap

**Document:** R0_IMPLEMENTATION_ROADMAP.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Nguyên tắc lộ trình

- Mỗi phase là **tuần tự có cổng** — không được bắt đầu phase N+1 khi phase N chưa đạt Go/No-Go
- Mỗi phase có acceptance tests và blocking conditions rõ ràng
- Không phase nào được tạo chức năng mới ngoài scope
- Mọi thay đổi production phải qua change control (QUAL-02, EDC-04)
- AI outputs vẫn là DRAFT trong mọi phase — chỉ PI có thể quyết định áp dụng

---

## V4.3.5 — Evidence Intake and Claim Traceability (COMPLETED)

| Thuộc tính | Nội dung |
|-----------|---------|
| **purpose** | Xây dựng lớp Evidence Governance offline: Evidence Source Ledger, Claim Traceability Ledger, D-R8 evidence gate |
| **scope** | `project_evidence_intake.py`, `project_claim_traceability.py`, `project_qa_runner.py`, `project_cli.py`; 21 tests |
| **out_of_scope** | Xác thực danh tính reviewer, production deployment, real data, API |
| **required_roles** | AI implementation (current); PI review của design |
| **required_evidence** | 21 tests PASS; fresh archive 797 passed; manifest PASS; dry run PASS |
| **acceptance_tests** | `MRAQ_OFFLINE_CI=1 pytest` → 0 failed; `verify_manifest_registry.py` → PASS |
| **go_no_go_conditions** | Tất cả tests PASS; freeze tag `v4.3.5-frozen` tạo; release evidence complete |
| **blocking_conditions** | Tests failed; PII leak; network call; fabricated citation |
| **status** | **COMPLETED** — `v4.3.5-frozen` tại `d041ecd` |

---

## R1 — Identity, RBAC, MFA, Delegation and Audit Attribution

| Thuộc tính | Nội dung |
|-----------|---------|
| **purpose** | Thiết lập cơ sở hạ tầng danh tính thật cho mọi người dùng production: xác thực, phân quyền, MFA, ủy quyền có thể kiểm chứng, audit log có danh tính |
| **scope** | Zone 2 (Identity and Governance Service): SSO integration; RBAC schema; MFA enforcement; delegation log module; access revocation workflow; tamper-evident audit trail; COI declaration management; e-signature policy |
| **out_of_scope** | EDC; eHospital integration; real data; AE/SAE workflow; code thay đổi Zone 1 Research OS ngoài integration points |
| **required_roles** | IT / Identity Architect; PI; Institution; Validation Lead |
| **required_evidence** | Identity provider integration test; MFA enforcement test; access revocation test; RBAC audit; delegation log test; audit trail integrity test; e-signature policy signed; COI procedure document |
| **acceptance_tests** | TP-03 (MFA), TP-06 (revocation), TP-05 (audit trail), TP-SEC-02 (audit tamper) — per Validation Master Plan |
| **go_no_go_conditions** | MFA 100% enforced; audit trail tamper-resistant; delegation log functional; COI declaration collected from all personnel; identity verification complete; RBAC mapped and tested; access revocation procedure tested |
| **blocking_conditions** | Anonymous access possible; audit trail tamperable; no MFA; delegation log absent; identity provider not integrated |
| **prerequisite** | V4.3.5 COMPLETED |
| **gaps_addressed** | GOV-02, GOV-03, ID-01, ID-02, ID-03 |

---

## R2 — Validated EDC and Research Data Lifecycle

| Thuộc tính | Nội dung |
|-----------|---------|
| **purpose** | Xây dựng và kiểm định EDC production với CRF, edit checks, query management, database lock và controlled export theo tiêu chuẩn kiểm định |
| **scope** | Zone 3 (Validated EDC): production CRF design; edit check specification; query management workflow; pseudonymization layer; database lock procedure; controlled export; backup/restore configuration; DR plan |
| **out_of_scope** | AE/SAE workflow (R3); eHospital integration (R4); independent security test (R5); real patient data |
| **required_roles** | EDC Vendor / Developer; Validation Lead; Data Manager; PI; IT |
| **required_evidence** | Validation package (IQ/OQ/PQ): TP-01 through TP-10; backup restore test TP-12; DR test TP-13; change control log; CRF specification signed by PI |
| **acceptance_tests** | 100% OQ/PQ tests PASS; backup restore successful; DR test documented; database lock test successful; controlled export with hash verification |
| **go_no_go_conditions** | Validation package complete and signed; backup restore tested; DR plan tested; database lock procedure tested; pseudonymization verified; no open critical defects |
| **blocking_conditions** | Open critical validation defects; backup not tested; database lock not functional; pseudonymization not verified; CRF not approved by PI |
| **prerequisite** | R1 Go/No-Go PASS |
| **gaps_addressed** | DATA-03, DATA-04, EDC-01, EDC-02, EDC-03, EDC-04 |

---

## R3 — Ethics, Consent, Monitoring and Safety Operations

| Thuộc tính | Nội dung |
|-----------|---------|
| **purpose** | Thiết lập khung vận hành đạo đức và an toàn: ethics approval cho LEVEL_A pilot; consent/waiver procedure; de-identification protocol; AE/SAE workflow (cho LEVEL_B/C); monitoring plan |
| **scope** | Ethics committee submission cho LEVEL_A (waiver/exemption); de-identification SOP; data access agreement; monitoring SOP; AE/SAE reporting workflow (Zone 3); escalation matrix; permitted-use policy |
| **out_of_scope** | eHospital integration (R4); GCP certification (R3 chỉ chuẩn bị foundation — GCP bắt buộc cho LEVEL_C); independent validation (R5) |
| **required_roles** | PI; Ethics Committee; Data Privacy Officer; Monitor; Institution |
| **required_evidence** | Ethics approval (waiver/exemption) từ hội đồng đạo đức; de-identification SOP signed; data access agreement signed; monitoring plan approved; AE/SAE workflow validation test (nếu chuẩn bị LEVEL_B); permitted-use policy signed |
| **acceptance_tests** | Ethics waiver document received; de-identification protocol approved by ethics or DPO; data access agreement executed; monitoring plan signed; AE workflow test (SAFE-01) if targeting LEVEL_B |
| **go_no_go_conditions** | Ethics approval (waiver/exemption) in hand; de-identification protocol approved; data access agreement executed; data minimization policy signed; monitoring plan approved; permitted-use policy signed |
| **blocking_conditions** | Ethics approval absent; de-identification protocol not approved; data access agreement not signed; no monitoring plan |
| **prerequisite** | R2 Go/No-Go PASS |
| **gaps_addressed** | GOV-01, DATA-01, DATA-02, SAFE-01, SAFE-02 |

---

## R4 — eHospital Read-Only Research Data Mart Sandbox

| Thuộc tính | Nội dung |
|-----------|---------|
| **purpose** | Thiết lập ranh giới trích xuất dữ liệu read-only đã được phê duyệt từ eHospital vào Research Data Mart; không write-back; data dictionary mapping và quality reconciliation |
| **scope** | Zone 4 (Research Data Mart): approved extraction boundary document; technical read-only controls; data dictionary mapping; quality reconciliation procedure; test extraction (synthetic/anonymized data only) |
| **out_of_scope** | Real patient data (chỉ test extraction với synthetic); PACS/LIS integration (cần approval riêng); write-back (bị cấm); AI direct access to identifiable data |
| **required_roles** | Hospital IT; PI; Institution; Data Manager; Network/Security team |
| **required_evidence** | Data access agreement (HIS-01); approved field list; technical architecture review showing read-only; no write-back penetration test; data dictionary document (HIS-02); reconciliation procedure; test extraction quality report |
| **acceptance_tests** | TP-SEC-04 (write-back prevention); approved field list signed; data dictionary verified; test extraction reconciliation report; institutional authorization for eHospital access |
| **go_no_go_conditions** | Data access agreement signed; approved field list in writing from data custodian; technical read-only verified (no write-back); data dictionary approved; reconciliation procedure tested with synthetic extraction; institutional authorization confirmed |
| **blocking_conditions** | Write-back possible; no data access agreement; no approved field list; eHospital IT not engaged; no reconciliation procedure |
| **prerequisite** | R3 Go/No-Go PASS |
| **gaps_addressed** | HIS-01, HIS-02 |

---

## R5 — Independent Security, Validation and Operational Qualification

| Thuộc tính | Nội dung |
|-----------|---------|
| **purpose** | Kiểm định độc lập toàn diện: penetration test bởi independent security tester; validation review bởi independent validator; CAPA closed; operational qualification |
| **scope** | Independent penetration test (TP-SEC-01..04); independent validation review (EDC-04); CAPA management; operational qualification of all zones; training completion verification |
| **out_of_scope** | Pilot execution (R6); real patient data; ethics re-submission |
| **required_roles** | Independent Security Tester (không thuộc team phát triển); Independent Validator; CAPA owner; Training Lead |
| **required_evidence** | Penetration test report signed by independent tester; validation review report signed by independent validator; CAPA log với mọi critical/high finding CLOSED; training completion records; final qualification sign-off |
| **acceptance_tests** | 0 open critical security findings; 0 open major validation defects; 100% training completion; backup/restore test PASS; DR test PASS |
| **go_no_go_conditions** | Independent penetration test complete; all critical and high findings CLOSED (CAPA); independent validation review complete and signed; all training complete with records; operational qualification signed |
| **blocking_conditions** | Open critical security findings; open major validation defects; training incomplete; independent validation not performed; CAPA not closed |
| **prerequisite** | R4 Go/No-Go PASS |
| **gaps_addressed** | QUAL-01, EDC-04 (final sign-off) |

---

## R6 — Limited Level-A Pilot With Formal Go/No-Go

| Thuộc tính | Nội dung |
|-----------|---------|
| **purpose** | Thực hiện nghiên cứu hồi cứu khử định danh thật đầu tiên (LEVEL_A) ở quy mô hạn chế có kiểm soát; formal Go/No-Go review trước khi mở rộng |
| **scope** | Một nghiên cứu hồi cứu LEVEL_A duy nhất; de-identified data only; full audit trail; monitoring; incident log; pilot completion report; formal Go/No-Go review |
| **out_of_scope** | Mọi nghiên cứu tiến cứu; mọi can thiệp; PII; LEVEL_B/C |
| **required_roles** | PI; Data Manager; Evidence Reviewer (authenticated); Monitor; Independent Reviewer (for Go/No-Go) |
| **required_evidence** | Pilot completion report; incident log; audit trail review; data quality report; Independent Reviewer sign-off; ethics waiver confirmed; no PII leak; no unauthorized access |
| **acceptance_tests** | Pilot complete with 0 major incidents; audit trail complete; data quality acceptable per PI; Independent Reviewer PASS; no security incidents |
| **go_no_go_conditions** | Ethics waiver valid; all R1-R5 gaps closed; pilot complete; 0 critical incidents; audit review PASS; Independent Reviewer sign-off; institutional authorization confirmed for next phase |
| **blocking_conditions** | Ethics waiver absent; any critical incident; PII leak; security breach; data integrity failure; audit trail gap |
| **prerequisite** | R5 Go/No-Go PASS |
| **gaps_addressed** | QUAL-02 (LEVEL_A pilot) |

---

## R7 — Level-B Prospective Observational Readiness

| Thuộc tính | Nội dung |
|-----------|---------|
| **purpose** | Mở rộng hệ thống cho nghiên cứu tiến cứu quan sát với người tham gia thật; consent management; prospective protocol registration; full safety reporting |
| **scope** | Full ethics approval submission (LEVEL_B); ICF approval; protocol registration; AE/SAE workflow activation; monitoring plan execution; site monitoring; participant enrollment |
| **out_of_scope** | Can thiệp điều trị; LEVEL_C; DSMB (khuyến nghị nhưng không bắt buộc cho thuần observational) |
| **required_roles** | PI; Ethics Committee; Monitor; Participants; Data Manager; AE Coordinator |
| **required_evidence** | Full ethics approval; ICF approved; protocol registered; AE/SAE workflow tested; monitoring plan activated; site monitoring visit 1 complete |
| **acceptance_tests** | Ethics approval in hand; ICF version approved; protocol registration number received; AE timeline compliance tested; first monitoring visit complete with report |
| **go_no_go_conditions** | LEVEL_A pilot (R6) PASS; full ethics approval; ICF approved; protocol registered; AE/SAE workflow active; monitoring plan approved and activated; institutional authorization for LEVEL_B |
| **blocking_conditions** | No full ethics approval; no ICF approval; no protocol registration; AE workflow not tested; no monitoring plan |
| **prerequisite** | R6 Go/No-Go PASS |

---

## R8 — Level-C Interventional Trial Readiness

| Thuộc tính | Nội dung |
|-----------|---------|
| **purpose** | Mở rộng hệ thống cho thử nghiệm lâm sàng can thiệp có đầy đủ GCP, DSMB, SUSAR reporting, computerised system validation và regulatory notification |
| **scope** | GCP certification toàn bộ team; DSMB charter và activation; SUSAR reporting pipeline; regulatory notification; pharmacovigilance procedures; investigational product management (nếu áp dụng); IB; randomization system |
| **out_of_scope** | Giai đoạn sau (NDA/marketing authorization) |
| **required_roles** | PI (GCP certified); Co-I (GCP certified); Sponsor; DSMB; Regulatory Affairs; Pharmacovigilance Officer; Independent CRO (nếu áp dụng) |
| **required_evidence** | GCP certificates (all personnel); DSMB charter signed and DSMB constituted; SUSAR reporting procedure tested; regulatory notification (if applicable); IB approved; randomization system validated; pharmacovigilance SOP; final CSV package |
| **acceptance_tests** | GCP training 100% complete; DSMB constituted and first meeting scheduled; SUSAR timeline test PASS; regulatory notification acknowledged (if applicable); computerised system validation complete |
| **go_no_go_conditions** | LEVEL_B (R7) PASS; GCP certification complete; DSMB active; SUSAR pipeline validated; regulatory notification; full ethics approval for LEVEL_C protocol; pharmacovigilance SOP; institutional sponsor authorization |
| **blocking_conditions** | GCP not certified; no DSMB; no SUSAR pathway; regulatory notification absent (if required); ethics not approved for LEVEL_C; no sponsor authorization |
| **prerequisite** | R7 Go/No-Go PASS |

---

## Tóm tắt lộ trình

```
V4.3.5  COMPLETED ──► R1 ──► R2 ──► R3 ──► R4 ──► R5 ──► R6 ──► R7 ──► R8
        (offline    Identity  EDC   Ethics eHospital  Qual  Pilot Level-B Level-C
         baseline)  +RBAC    valid  +Consent Data    Audit  Go/  prosp  interv
                    +MFA            +Safety  Mart     +Pen  NoGo  obs    trial
```

**Mỗi mũi tên là một Go/No-Go gate.** Không có shortcut.

---

*Applicable institutional, Ministry of Health, ethics committee and legal requirements
must be confirmed by the institution before study activation.*

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
