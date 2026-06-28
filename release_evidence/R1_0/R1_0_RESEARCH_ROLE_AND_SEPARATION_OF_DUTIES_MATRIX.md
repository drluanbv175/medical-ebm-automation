# R1.0 Research Role and Separation-of-Duties Matrix

**Document:** R1_0_RESEARCH_ROLE_AND_SEPARATION_OF_DUTIES_MATRIX.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Nguyên tắc SoD bắt buộc

```
PI cannot claim independent review of own protocol.
SYSTEM_ADMINISTRATOR cannot approve research content.
DATA_MANAGER cannot alter locked data without controlled change process.
METHODS_STATISTICS_REVIEWER cannot be sole final approver.
READ_ONLY_AUDITOR cannot modify research artifacts.
```

---

## PI — Principal Investigator

| Thuộc tính | Nội dung |
|-----------|---------|
| **permitted_actions** | Approve protocol; sign delegation; lock database; authorize export; approve evidence plan; final sign-off |
| **forbidden_actions** | Claim independent review of own protocol; bypass ethics gate; self-assign METHODS_STATISTICS_REVIEWER role |
| **data_access_scope** | Full study data — pseudonymized in Zones 3/4; identifiable only per ethics approval |
| **review_scope** | Final approval authority — not independent reviewer for own artifacts |
| **approval_limitations** | Cannot approve own protocol without independent reviewer sign-off |
| **delegation_requirements** | Must create signed delegation record BEFORE Co-I acts |
| **independence_constraints** | Cannot serve as Methods/Statistics Reviewer for own protocol |
| **audit_requirements** | All PI actions create attributed audit event with authenticated actor ID |
| **revocation_requirements** | Role persists for study duration; revoked on PI change or study closure |

---

## CO_INVESTIGATOR

| Thuộc tính | Nội dung |
|-----------|---------|
| **permitted_actions** | Data entry; protocol execution per delegation; evidence submission; AE reporting per delegation |
| **forbidden_actions** | Act outside delegation scope; sub-delegate without PI permission; access data outside assigned study |
| **data_access_scope** | Study data within delegation scope only |
| **review_scope** | Per delegation — cannot exceed PI-assigned scope |
| **approval_limitations** | Cannot independently approve protocol or evidence plan |
| **delegation_requirements** | Active delegation record from PI required for every delegated task |
| **independence_constraints** | Cannot independently review own contributions |
| **audit_requirements** | All actions include delegation_id reference in audit event |
| **revocation_requirements** | Role revoked when delegation expires or PI revokes |

---

## METHODS_STATISTICS_REVIEWER

| Thuộc tính | Nội dung |
|-----------|---------|
| **permitted_actions** | Review study design; review SAP; review statistical analysis; annotate methodology concerns; attest methods |
| **forbidden_actions** | Approve own methods contributions; serve as sole final approver; modify data or protocol |
| **data_access_scope** | Aggregate/summary data for review; NOT identifiable patient data |
| **review_scope** | Methodology and statistics only — not clinical validity |
| **approval_limitations** | Cannot be sole approver; second reviewer or PI required for final approval |
| **delegation_requirements** | Must be independent from PI and primary authors |
| **independence_constraints** | Cannot have COI with study; cannot have co-authored the artifact being reviewed |
| **audit_requirements** | Review attestation includes role, independence statement, COI declaration |
| **revocation_requirements** | Role revoked if COI discovered post-assignment |

---

## EVIDENCE_CITATION_REVIEWER

| Thuộc tính | Nội dung |
|-----------|---------|
| **permitted_actions** | Review evidence source metadata; verify citation accuracy; flag unverified/retracted sources; attest evidence plan |
| **forbidden_actions** | Self-generate DOI/PMID; auto-verify evidence without human check; approve own evidence submissions |
| **data_access_scope** | Evidence ledger and citation metadata only; NOT patient data |
| **review_scope** | Evidence source integrity and citation accuracy |
| **approval_limitations** | Cannot approve evidence submitted by self |
| **delegation_requirements** | Independence from evidence submitter required |
| **independence_constraints** | Cannot review evidence they personally retrieved or selected |
| **audit_requirements** | Review attestation includes source IDs reviewed, verification method, timestamp |
| **revocation_requirements** | Role revoked if COI with evidence source discovered |

---

## DATA_MANAGER

| Thuộc tính | Nội dung |
|-----------|---------|
| **permitted_actions** | Data entry; query resolution; edit checks; data cleaning per protocol; pre-lock reconciliation |
| **forbidden_actions** | Alter locked data without controlled change process; approve own data entries; access data outside assigned study |
| **data_access_scope** | Study CRF data — pseudonymized; NOT identifiable data |
| **review_scope** | Data quality review only |
| **approval_limitations** | Cannot approve own data entries; cannot lock database (PI only) |
| **delegation_requirements** | Must be trained per protocol before accessing EDC |
| **independence_constraints** | Cannot review data they entered |
| **audit_requirements** | All data modifications create before/after audit event with actor attribution |
| **revocation_requirements** | Role revoked on study closure or departure |

---

## DATA_GOVERNANCE_QA_REVIEWER

| Thuộc tính | Nội dung |
|-----------|---------|
| **permitted_actions** | Review data governance compliance; review audit trail completeness; flag data anomalies; QA gate decisions |
| **forbidden_actions** | Modify data; approve protocol; claim ethics approval |
| **data_access_scope** | Audit trail and governance artifacts; summary data only |
| **review_scope** | Data governance and quality — not clinical content |
| **approval_limitations** | Cannot approve research content; only governance compliance |
| **delegation_requirements** | Must be independent from PI and data entry team |
| **independence_constraints** | Cannot review governance of studies where they contributed data |
| **audit_requirements** | QA review records include gate ID, checklist result, reviewer attribution |
| **revocation_requirements** | Role revoked on departure or COI discovery |

---

## MONITOR

| Thuộc tính | Nội dung |
|-----------|---------|
| **permitted_actions** | Access source data per monitoring plan; review CRF vs source; flag discrepancies; issue monitoring reports |
| **forbidden_actions** | Modify data; override PI decisions; access data beyond monitoring scope |
| **data_access_scope** | Source data per monitoring plan — may include pseudonymized patient data per ethics approval |
| **review_scope** | Protocol adherence, data integrity, safety reporting compliance |
| **approval_limitations** | Cannot approve protocol or evidence plan |
| **delegation_requirements** | Authorized per monitoring plan signed by PI and ethics |
| **independence_constraints** | Must be independent from research team (sponsor or CRO) |
| **audit_requirements** | Monitoring visit reports with authenticated attribution |
| **revocation_requirements** | Role revoked when monitoring plan ends or monitor changes |

---

## SYSTEM_ADMINISTRATOR

| Thuộc tính | Nội dung |
|-----------|---------|
| **permitted_actions** | System configuration; user provisioning per approved request; backup management; incident response |
| **forbidden_actions** | Approve research content; modify research data; read patient data; approve role assignments without PI approval; delete audit logs |
| **data_access_scope** | System configuration only — NO access to research data or patient data |
| **review_scope** | Technical system operation — NOT research content |
| **approval_limitations** | Cannot approve any research decision |
| **delegation_requirements** | Privileged actions require second approval or PAM just-in-time elevation |
| **independence_constraints** | Must maintain separation from research content decisions |
| **audit_requirements** | All admin actions logged to separate tamper-evident admin audit trail |
| **revocation_requirements** | Role revoked on departure; emergency revocation within 1h |

---

## SECURITY_ADMINISTRATOR

| Thuộc tính | Nội dung |
|-----------|---------|
| **permitted_actions** | Security configuration; penetration test coordination; vulnerability management; security incident response; access policy enforcement |
| **forbidden_actions** | Approve research content; modify research data; read patient data without incident authorization |
| **data_access_scope** | Security logs and system configuration only |
| **review_scope** | Security posture — NOT research content |
| **approval_limitations** | Cannot approve research decisions |
| **delegation_requirements** | Security actions under change control |
| **independence_constraints** | Must be independent from research team |
| **audit_requirements** | Security actions create audit events in tamper-evident log |
| **revocation_requirements** | Role revoked on departure; emergency revocation within 1h |

---

## READ_ONLY_AUDITOR

| Thuộc tính | Nội dung |
|-----------|---------|
| **permitted_actions** | Read audit logs; read governance artifacts; read validation evidence; generate audit reports |
| **forbidden_actions** | Modify any artifact; delete any record; approve any decision; access patient identifiable data |
| **data_access_scope** | Audit trail, governance records, validation evidence — NOT patient data, NOT research data |
| **review_scope** | Audit and governance record review only |
| **approval_limitations** | Cannot approve anything |
| **delegation_requirements** | Authorization from PI or institution for audit engagement |
| **independence_constraints** | Must be independent from research team being audited |
| **audit_requirements** | Auditor access itself is logged |
| **revocation_requirements** | Role time-limited to audit engagement period |

---

## Separation-of-Duties Matrix

| Action | PI | CO-I | MR | ECR | DM | DGQ | MON | SA | SEC | AUD |
|--------|----|----|----|----|----|----|----|----|----|----|
| Write protocol | ✓ | (del) | — | — | — | — | — | — | — | — |
| Independent protocol review | ✗ | ✗ | ✓ | — | — | ✓ | — | — | — | — |
| Approve protocol (final) | ✓ | — | — | — | — | — | — | — | — | — |
| Submit evidence | ✓ | (del) | — | — | — | — | — | — | — | — |
| Attest evidence | — | — | — | ✓ | — | ✓ | — | — | — | — |
| Enter CRF data | — | (del) | — | — | ✓ | — | — | — | — | — |
| Lock database | ✓ | — | — | — | — | — | — | — | — | — |
| Authorize export | ✓ | — | — | — | — | — | — | — | — | — |
| Monitor source data | — | — | — | — | — | — | ✓ | — | — | — |
| Provision user accounts | — | — | — | — | — | — | — | ✓ | — | — |
| Delete audit log | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Read audit log | — | — | — | — | — | ✓ | — | ✓ | ✓ | ✓ |

Legend: ✓ permitted · ✗ explicitly forbidden · — not in role scope · (del) requires active delegation

---

*Required for future production qualification.*  
*Not implemented in current Research OS baseline.*

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
