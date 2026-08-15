# API Spec

## Planned route groups

- `GET /api/patients`
- `POST /api/patients`
- `GET /api/patients/:id`
- `PATCH /api/patients/:id`
- `POST /api/patients/:id/vitals`
- `POST /api/patients/:id/medications/reconcile`
- `POST /api/patients/:id/risk-assessments`
- `POST /api/care-plans`
- `POST /api/care-plans/:id/approve`
- `POST /api/appointments`
- `PATCH /api/appointments/:id/check-in`
- `POST /api/tasks`
- `POST /api/handouts`
- `POST /api/handouts/:id/approve`
- `GET /api/quality/metrics`
- `GET /api/audit-logs`

## Cross-cutting requirements

- Moi write endpoint can RBAC check.
- Moi view/export nhay cam can audit log.
- Moi response loi clinical safety dung ngon ngu ro rang, khong thay the cap cuu.
