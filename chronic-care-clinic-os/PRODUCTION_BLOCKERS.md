# Production Blockers

This system is not production-ready and must not be used with real patient data until all blockers are cleared.

Machine-readable readiness is tracked in `lib/production-readiness.ts`, exposed at `/api/admin/production-readiness`, and surfaced in Admin Settings. Automation and CI should consume that manifest instead of parsing this Markdown file.

Production can be declared only by a valid evidence package loaded through `PRODUCTION_READINESS_EVIDENCE_PATH`. The package must clear all 24 blockers and include all five signoffs. See `PRODUCTION_GO_LIVE_RUNBOOK.md`.

## Security blockers

- Backend RBAC not wired to every route/action.
- Authentication/session/MFA not implemented for production.
- Password hashing contract added, but production auth/session/MFA wiring and review evidence are still missing.
- Rate limiting and CSRF contract added, but not wired to every production write route.
- Secure headers are configured in repo, but deployment header scan/signoff is still missing.
- Environment validation contract added, but production deployment evidence/signoff is still missing.
- Dependency lockfile exists, but reviewed vulnerability scan evidence is still missing.
- PHI redaction logger contract added, but de-identified UAT persistence evidence/signoff is still missing.

## Data protection blockers

- Organization/site isolation is modeled but not enforced end-to-end.
- Backup/restore evidence validator added, but a real restore drill report/signoff is still missing.
- Audit log persistence contract and migration hardening are modeled, but runtime database evidence/signoff is still missing.
- Data retention/archive policy contract added, but clinic/legal approval and execution evidence are still missing.
- No UAT with de-identified workflow data.

## Clinical safety blockers

- Clinical rules are draft and not formally approved.
- Rule approval workflow not fully executable.
- Clinical content and patient education approval not fully executable.
- A5 output QA contract added, but rendered artifact review/signoff is still missing.
- Red flag workflow not tested with real operational users.
- No clinical safety signoff.

## Operations blockers

- Docker one-command run not verified in this environment.
- Prisma migration has schema but no generated migration folder.
- Error logging and monitoring evidence validator added, but deployment smoke evidence/signoff is still missing.
- Incident response process documented and drill validator added, but signed tabletop/drill evidence is still missing.

## AI blocker

- AI must remain disabled until MVP-01 is stable, privacy controls are verified and human review workflow is implemented. (2026-07-12: `lib/ai-guard.ts::assertAiDraftsEnabled()` added as a code-level circuit breaker — any future AI call site must call it first. Still open: this only enforces the flag once a call site exists; the governance/privacy/review-workflow prerequisites above are unaffected.)
