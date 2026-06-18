# Phase 3A Operator Guide

## Run focused tests

```bash
pytest tests/test_phase_3a_chronic_care_*.py
```

## Inspect migration dry-run

```python
from app.chronic_care.migration import build_chronic_care_migration_plan
plan = build_chronic_care_migration_plan()
print(plan.destructive, plan.missing_tables)
```

Không chạy production migration khi chưa có owner approval.

## Dashboard

Tab Phase 3A chỉ read-only. Không có nút enable flag, không gửi message, không ghi EMR/HIS.
