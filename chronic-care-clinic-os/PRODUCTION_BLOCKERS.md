# Production Blockers

This system is not production-ready and must not be used with real patient data until all blockers are cleared.

Machine-readable readiness is tracked in `lib/production-readiness.ts` and surfaced in Admin Settings. Automation and CI should consume that manifest instead of parsing this Markdown file.

## Security blockers

- Backend RBAC not wired to every route/action.
- Authentication/session/MFA not implemented for production.
- Password hashing not implemented.
- Rate limiting and CSRF controls not implemented.
- Secure headers not verified.
- Environment validation not implemented.
- No dependency lockfile or vulnerability scan.
- No PHI redaction logger.

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
