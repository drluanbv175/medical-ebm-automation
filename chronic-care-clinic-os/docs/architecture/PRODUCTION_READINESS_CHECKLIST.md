# Production Readiness Checklist

Khong duoc goi production-ready neu chua dat tat ca muc sau.

## Security

- [ ] Password hashing.
- [ ] Session expiration.
- [ ] MFA-ready.
- [ ] Backend RBAC.
- [ ] Rate limiting.
- [ ] CSRF protection where applicable.
- [ ] Input validation.
- [ ] Secure headers.
- [ ] Encrypted secrets.
- [ ] Environment validation.
- [ ] No sensitive PHI in logs.
- [ ] Evidence dossier generated with all required runtime control IDs before final go-live.

## Data

- [ ] Organization/site isolation.
- [ ] Backup schedule.
- [ ] Restore procedure tested.
- [ ] No real data in test/demo.
- [ ] No PHI in analytics events.

## Clinical safety

- [ ] Clinical rule approval workflow.
- [ ] Clinical content approval workflow.
- [ ] Red flag workflow tested.
- [ ] Care plan version history.
- [ ] Incident response workflow.
- [ ] Clinical safety signoff.

## Operations

- [ ] Docker one-command local run verified.
- [ ] Migration versioned.
- [ ] Audit log immutable by normal UI.
- [ ] User acceptance testing.
- [ ] Quality dashboard de-identified.
