# MVP-01 Limitations

- UI uses static fake seed data until Prisma runtime is wired.
- Demo role selector is not production authentication.
- Backend RBAC guard exists as domain code but is not applied to all API/server actions.
- Audit log viewer is demo data; append-only persistent audit store is not wired.
- A5 handout is printable HTML, not tested PDF output.
- Rule approval workflow is modeled but not fully executable.
- Docker configuration exists but was not verified in this environment.
- No lockfile has been generated because dependencies were not installed here.
- No real EMR/HIS/FHIR integration.
- No patient communication gateway.
- AI remains disabled and unimplemented.
