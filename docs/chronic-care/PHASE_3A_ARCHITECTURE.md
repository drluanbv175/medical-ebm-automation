# Phase 3A Architecture

## Product stance

Phase 3A là synthetic shadow pilot cho Chronic Care Coordination Module, không phải clinical production và không thay thế EMR/HIS.

## Module layout

```text
app/chronic_care/
  constants.py
  models.py
  migration.py
  synthetic_cases.py
  audit.py
  rules.py
  service.py
  dashboard.py
```

## V7 integration

- `RunPacket`: tạo run shadow cho workflow.
- `AuditLogger`: ghi audit event không PII.
- `ApprovalCenter`: risk draft/care-plan draft review.
- `PolicyEngine`: chặn PII, export unsafe, feature flag bypass và release sai.
- `EvidenceRegistry` / `ClaimRegistry`: kiểm tra evidence/claim traceability cho care-plan draft.
- `FeatureFlags`: risky flags giữ `False`.
- `dashboard/v7_readonly.py` pattern: snapshot + render read-only.

## Data flow

Synthetic case pack -> Enrollment -> Review/task/risk draft/care-plan draft -> Timeline -> Quality snapshot -> Read-only dashboard/export aggregate.

Không có patient-facing message, EMR write-back, medication change action, prescription action hoặc auto-apply.
