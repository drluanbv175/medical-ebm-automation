# R1.1 Role Policy Reference

**Document:** R1_1_ROLE_POLICY_REFERENCE.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE  
**Source:** `research_project/project_rbac_simulation.py`

---

## 10 Research Roles

| Role | Mô tả |
|------|-------|
| `PI` | Principal Investigator — chịu trách nhiệm toàn bộ đề tài |
| `CO_INVESTIGATOR` | Co-Investigator — tham gia theo ủy quyền |
| `METHODS_STATISTICS_REVIEWER` | Reviewer phương pháp và thống kê |
| `EVIDENCE_CITATION_REVIEWER` | Reviewer trích dẫn và nguồn bằng chứng |
| `DATA_MANAGER` | Quản lý và nhập dữ liệu |
| `DATA_GOVERNANCE_QA_REVIEWER` | Reviewer QA và quản trị dữ liệu |
| `MONITOR` | Giám sát tính tuân thủ đề tài |
| `SYSTEM_ADMINISTRATOR` | Quản trị hệ thống và phân quyền |
| `SECURITY_ADMINISTRATOR` | Quản trị an ninh |
| `READ_ONLY_AUDITOR` | Kiểm toán — chỉ đọc |

---

## RBAC Policy Table

| Action | PI | CO-I | STAT | EVID | DM | QA | MON | SYSADM | SECADM | AUDITOR |
|--------|:--:|:----:|:----:|:----:|:--:|:--:|:---:|:------:|:------:|:-------:|
| CREATE_DRAFT_PROJECT | ✓ | | | | | | | | | |
| EDIT_DRAFT_ARTIFACT | ✓ | ✓ | | | ✓ | | | | | |
| RECORD_REVIEW_ATTESTATION | ✓¹ | | ✓ | | | ✓ | | | | |
| RECORD_EVIDENCE_ATTESTATION | | | | ✓ | | | | | | |
| REQUEST_REVISION | ✓ | ✓ | ✓ | ✓ | | ✓ | ✓ | | | |
| VIEW_AUDIT_LOG | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VIEW_EVIDENCE_LEDGER | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | | | ✓ |
| REGISTER_CLAIM_DRAFT | ✓ | ✓ | | | ✓ | | | | | |
| MANAGE_SYNTHETIC_ROLE_ASSIGNMENT | | | | | | | | ✓ | ✓ | |
| MANAGE_SYNTHETIC_DELEGATION | ✓ | | | | | | | ✓ | | |
| VIEW_SYSTEM_CONFIGURATION | | | | | | | | ✓ | ✓ | |
| MODIFY_SYSTEM_CONFIGURATION | | | | | | | | ✓ | ✓ | |
| REQUEST_EXPORT | ✓ | | | | | | | | | |
| LOCK_RESEARCH_DATA | ✓ | | | | | | | | | |
| UNLOCK_RESEARCH_DATA | | | | | ✓² | | | | | |

¹ PI chỉ được SELF_REVIEW — SoD guard block INDEPENDENT_REVIEW của own artifact (SoD-01)  
² DATA_MANAGER yêu cầu `has_controlled_change_authorization=True` (SoD-04)

---

## Forbidden Actions (mọi role đều bị block)

| Action | Lý do |
|--------|-------|
| `FINAL_APPROVAL` | Không thể được cấp bởi bất kỳ role nào trong harness |
| `ETHICS_APPROVAL` | Thuộc về tổ chức/IRB — không thể mô phỏng |
| `INDEPENDENT_REVIEW_APPROVAL` | Yêu cầu reviewer độc lập thật |
| `EXTERNAL_SUBMISSION` | Không thể submit trong harness offline |
| `CLINICAL_RELEASE` | Chưa qualified cho production |

---

## 8 SoD Guards

| # | Mã | Scenario | Block condition |
|---|-----|----------|-----------------|
| SoD-01 | `PI_SELF_INDEPENDENT_REVIEW` | PI claim independent review của own artifact | role=PI + action=RECORD_REVIEW_ATTESTATION + review_type=INDEPENDENT_REVIEW + is_own_artifact=True |
| SoD-02 | `ADMIN_RESEARCH_APPROVAL` | SYSTEM_ADMINISTRATOR phê duyệt research content | role=SYSADM + action ∈ {RECORD_REVIEW_ATTESTATION, RECORD_EVIDENCE_ATTESTATION, LOCK_RESEARCH_DATA} |
| SoD-03 | `READ_ONLY_WRITE_ATTEMPT` | READ_ONLY_AUDITOR thực hiện write action | role=AUDITOR + action ∈ _WRITE_ACTIONS |
| SoD-04 | `DATA_MANAGER_UNLOCK_NO_AUTH` | DATA_MANAGER unlock không có authorization | role=DM + action=UNLOCK_RESEARCH_DATA + has_controlled_change_authorization=False |
| SoD-05 | `EVIDENCE_REVIEWER_SELF_ATTEST` | EVIDENCE_CITATION_REVIEWER tự attest source họ tạo | role=ECR + action=RECORD_EVIDENCE_ATTESTATION + is_own_source=True |
| SoD-06 | `CONFLICTING_ROLES_SAME_ACTOR` | Cùng actor thực hiện prohibited conflicting actions | Detected per-evaluation via role check |
| SoD-07 | `EXPIRED_ROLE` | Role assignment hết hạn | expires_at_utc trong quá khứ |
| SoD-08 | `DISABLED_ACTOR` | Actor bị disable hoặc hết hạn | status=DISABLED hoặc actor.expires_at_utc quá khứ |

---

## Kết luận bắt buộc

```
RBAC schema:               DEFINED (10 roles, 15 permitted + 5 forbidden)
SoD matrix:                DEFINED (8 guards implemented)
Technical enforcement:     OFFLINE SIMULATION ONLY — not production RBAC service
SSO binding:               NOT IMPLEMENTED
Production deployment:     NOT APPLICABLE
Qualification:             NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
