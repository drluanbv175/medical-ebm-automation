# Production Blockers

This system is not production-ready and must not be used with real patient data until all blockers are cleared.

Machine-readable readiness is tracked in `lib/production-readiness.ts`, exposed at `/api/admin/production-readiness`, and surfaced in Admin Settings. Automation and CI should consume that manifest instead of parsing this Markdown file.

## Security blockers

- Backend RBAC not wired to every route/action.
- Authentication/session/MFA not implemented for production.
- Password hashing not implemented.
- Rate limiting and CSRF contract added, but not wired to every production write route.
- Secure headers are configured in repo, but deployment header scan/signoff is still missing.
- Environment validation contract added, but production deployment evidence/signoff is still missing.
- Dependency lockfile exists, but vulnerability scan evidence is still missing.
- PHI redaction logger contract added, but de-identified UAT persistence evidence/signoff is still missing.

## Data protection blockers

- Organization/site isolation is modeled but not enforced end-to-end.
- Backup/restore procedure not tested.
- Audit log persistence contract is modeled, but reviewed migration/runtime immutability enforcement is not implemented.
- No formal data retention/archive policy.
- No UAT with de-identified workflow data.

## Clinical safety blockers

- Clinical rules are draft and not formally approved.
- Rule approval workflow not fully executable.
- Clinical content and patient education approval not fully executable.
- A5 PDF output not tested.
- Red flag workflow not tested with real operational users.
- No clinical safety signoff.

## Operations blockers

- Docker one-command run not verified in this environment.
- Prisma migration has schema but no generated migration folder.
- Error logging and monitoring not configured.
- Incident response process documented but not drilled.

## AI blocker

- AI must remain disabled until MVP-01 is stable, privacy controls are verified and human review workflow is implemented. (2026-07-12: `lib/ai-guard.ts::assertAiDraftsEnabled()` added as a code-level circuit breaker — any future AI call site must call it first. Still open: this only enforces the flag once a call site exists; the governance/privacy/review-workflow prerequisites above are unaffected.)
