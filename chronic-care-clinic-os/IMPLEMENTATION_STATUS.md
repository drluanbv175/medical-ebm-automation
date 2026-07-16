# Implementation Status

## Product classification

Chronic Care Clinic OS is a Clinical Coordination Platform. It is not a legal EMR replacement and must not be described as production-ready.

## Da hoan thanh trong dot nay

- Gap analysis, target architecture, clinical boundary, data classification, automation safety model, integration strategy and production readiness checklist.
- Security threat model, security test cases and incident response playbook.
- Prisma schema expanded for Organization, ClinicSite, Permission, Session, patient identity/contact/consent separation, care program enrollment, confirmed risk assessment, care plan versioning, task escalation, automation rules, rule/content approval, safety alert, incident and quality metric definitions.
- RBAC expanded to Super Admin, Clinic Admin, Physician, Nurse, Care Coordinator, Receptionist, Pharmacist, Quality Manager, Read-only Auditor and Patient Portal User.
- Backend guard domain code for permission and organization/site isolation.
- Automation contract and 12 core automation rule definitions.
- Care orchestration engine that converts risk, abnormal labs, medication review needs, missed follow-up, post-discharge status and care-plan approval gaps into a prioritized command-center queue.
- `/command-center` page for cross-role chronic care coordination with SLA, assigned role, safety communication gate and physician-confirmation requirement.
- Chronic care program registry for hypertension, type 2 diabetes, dyslipidemia, CKD, heart failure/post-discharge and polypharmacy, with `/programs` population view and monitoring-gap detection.
- Pre-visit packet generator and `/visits/prep` page for nurse/physician preparation, medication questions, lab review prompts and safety boundaries before visits.
- Physician-approved care plan draft generator and `/care-plans` workspace for post-visit goals, monitoring plan, medication review, labs, referrals, patient education and safety-netting without automatic treatment changes.
- Preview-only care plan approval package with signoff gates, CarePlanVersion metadata and AuditLog preview before persistent writeback exists.
- Patient education release package and `/handouts` gate for approved templates, approved care plans, consent and audit preview before A5 print/release.
- Preview-only workflow action contracts for future care plan approval and handout release server actions.
- Append-only audit ledger preview with deterministic hash chain and `/admin/audit` integrity view.
- Persistent AuditLog write contract with sequence/previousHash/eventHash, insert-only policy and same-transaction business write requirement.
- Persistent write plans for all guarded write actions now use the AuditLog write contract and define the atomic business write set; production commit remains disabled until database transaction tests exist.
- In-memory transaction harness for guarded persistent plans now stages business write and AuditLog together, validates the audit hash chain, and has behavior tests for commit plus rollback at each injected failure point before a real database adapter is allowed.
- Disabled Prisma transaction contract now defines the required same-transaction operations and rollback cases without importing Prisma or enabling production commits.
- Prisma test-database rollback gate now requires isolated non-production evidence, AuditLog migration proof, AuditLog mutation blocking, all rollback cases, evidence artifact and reviewer signoff before a test adapter can be promoted; production commit remains disabled.
- Prisma rollback evidence report schema/validator and `docs/templates/prisma-rollback-evidence.template.json` now make the required test-database proof machine-checkable before adapter promotion.
- AuditLog hardening migration reviewed at `prisma/migrations/202606190001_audit_log_hash_chain_hardening/migration.sql`, with unique sequence/hash indexes, non-empty hash constraints, immutable-after-append constraint and UPDATE/DELETE blocking triggers.
- Workflow action contracts now call RBAC/backend guard for role, permission and organization/site scope before any future write.
- Write action registry and `/admin/settings` readiness view identify guarded preview actions, UI placeholders and production-blocked exports.
- `/overdue` claim-call-task action now has preview-only workflow contract with RBAC guard, reminder-template boundary and audit preview.
- `/appointments` create-appointment action now has preview-only workflow contract with RBAC guard, future-date guard and audit preview.
- `/patients/[id]` care-plan-draft action now has preview-only workflow contract with RBAC guard and explicit separate physician-approval requirement.
- `/admin/templates` education-template-draft action now has preview-only workflow contract with RBAC guard and separate approval requirement before patient use.
- `/patients` patient-registration action now has preview-only workflow contract with RBAC guard, consent gate and audit preview before persistent writeback.
- `/admin/rules` clinical-rule-draft action now has preview-only workflow contract with RBAC guard and separate approval requirement before rule-engine activation.
- `/admin/users` user-invite action now has preview-only workflow contract with RBAC guard, scope guard and audit preview before account/email creation.
- Claude Code handoff manifest and sync-check guard so Windows, MacBook, Codex and Claude Code share the same current scope.
- MVP-01 workflow definition and `/mvp-01` page.
- Production blockers, MVP-01 acceptance test, demo guide, limitations and signoff templates.
- Runtime hardening controls for environment, secure headers, CSRF/rate-limit, PHI redaction and patient communication policy.
- Production evidence package/go-live report contracts so production can only unlock with explicit blocker evidence plus required sign-offs.
- Password hashing contract using scrypt with salt/pepper support and timing-safe verification.
- Data retention/archive policy contract with fail-closed legal-hold, active-care, review and audit-evidence requirements.
- Backup/restore, monitoring smoke and incident drill evidence validators for operations readiness.
- A5 output QA contract for rendered handout/PDF artifact review, checksum, visual QA, emergency boundary and doctor-verification disclaimer.
- Offline tests updated and passing for docs/schema/RBAC/safety/automation/MVP-01/command-center.

## Da co tu dot truoc

- Next.js app skeleton.
- Dashboard bac si, dieu duong and quality.
- Patient registry and detail UI.
- Appointments, initial/follow-up workflow shell, medication queue, lab queue, care plan list, task list, referral list, A5 printable handout view.
- Clinical rule and audit viewer surfaces.
- Fake seed data with 50 demo patients.

## Dang hoan thanh

- Thin vertical slice MVP-01 at UI/domain level.
- Command Center and Program Registry are deterministic and demo-data backed; they still need persistent task writeback before production use.
- Backend RBAC is modeled and wired to workflow action contracts; write action registry has guarded-preview contracts for UI write actions and keeps production-blocked exports separate.
- Audit immutability is documented, domain-guarded, hash-chain previewed and has a persistent write contract; it still needs real database migrations/server-action wiring.
- Care plan version history is modeled but not wired to write workflow.
- Care plan draft, approval package, education release package and workflow action contracts are deterministic and demo-data backed; all guarded write actions now have persistent write plans, an in-memory atomicity harness, a disabled Prisma adapter contract and a machine-checkable test-database rollback evidence gate, while final approval/writeback still needs real database transaction wiring.
- Rule/content approval workflow is modeled but not fully executable.

## Chua hoan thanh

- Production authentication/session/MFA/password hashing.
- Full baseline Prisma migration files for every model.
- Docker one-command run verification.
- Database backup/restore test.
- A5 PDF generator and test.
- API/server actions for vitals, medication reconciliation and remaining write paths not yet represented by guarded workflow contracts.
- Real Prisma transaction adapter for guarded persistent plans, satisfying the current disabled adapter contract, test-database rollback evidence gate and rollback harness cases for AuditLog/business-write atomicity.
- Real audit log persistence on every sensitive action.
- Rate limiting, CSRF, secure headers and environment validation have repo contracts; still need deployment evidence and sign-off.
- Password hashing has repo contract; still needs production auth/session/MFA wiring and review evidence.
- Data retention/archive, backup/restore, monitoring, incident drill and A5 QA have repo contracts; still need real execution artifacts and owner sign-off.
- User acceptance testing and formal clinical/data protection signoff.

## Ket luan production

Not production-ready. Do not use with real patient data. See `PRODUCTION_BLOCKERS.md`.
