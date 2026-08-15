# Target Architecture

## Product boundary

Chronic Care Clinic OS la Clinical Coordination Platform. He thong nam ben duoi Clinical Record/EMR phap ly va khong thay the EMR.

```text
Clinical Record / EMR hop phap
        ↓
Chronic Care Coordination OS
        ↓
Registry benh man
+ Care plan
+ Follow-up automation
+ Care coordinator tasks
+ Quality dashboard
+ Patient education
```

## Layer 1: Identity & Access

Thanh phan bat buoc:

- Organization.
- ClinicSite.
- User.
- Role.
- Permission.
- Session.
- MFA-ready architecture.
- User status.
- Audit event.

Moi user thuoc `Organization -> ClinicSite -> Role -> Permission Set`. Khong cho phep truy cap cheo organization.

## Layer 2: Clinical Coordination Data

Tach patient identity data khoi clinical coordination data.

- Identity: ho ten, so dien thoai, dia chi, ngay sinh, lien he khan cap.
- Coordination: chronic conditions, medications, goals, care plan, follow-up status, risk status, lab summary, appointment status, tasks, communication logs, referrals.

Registry mac dinh chi hien ma nguoi benh, nam sinh, gioi, nhom benh, nguy co, ngay kham gan nhat, ngay can tai kham va muc tieu chua dat.

## Layer 3: Workflow & Automation Engine

Moi automation rule co:

- Rule.
- Trigger.
- Eligibility criteria.
- Excluded conditions.
- Priority.
- Owner role.
- Required approval.
- Action type.
- Escalation path.
- Audit record.

Automation tao task/queue/draft. Khong tu gui noi dung dieu tri ca the hoa.

## Layer 4: Clinical Safety & Governance

Can cac bang:

- ClinicalRule.
- ClinicalRuleVersion.
- ClinicalRuleApproval.
- SafetyAlert.
- SafetyAlertReview.
- IncidentReport.
- IncidentReview.
- ClinicalContent.
- ClinicalContentVersion.
- ClinicalContentApproval.

Rule khong co nguoi phe duyet khong duoc chay production.

## Layer 5: Reporting & Quality Improvement

Dashboard tach thanh:

- Operational Dashboard.
- Clinical Coordination Dashboard.
- Quality Improvement Dashboard.
- Governance Dashboard.

Khong tron du lieu van hanh, PII va du lieu quan ly da tong hop trong cung mot view mac dinh.
