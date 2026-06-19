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
- Workflow action contracts now call RBAC/backend guard for role, permission and organization/site scope before any future write.
- Claude Code handoff manifest and sync-check guard so Windows, MacBook, Codex and Claude Code share the same current scope.
- MVP-01 workflow definition and `/mvp-01` page.
- Production blockers, MVP-01 acceptance test, demo guide, limitations and signoff templates.
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
- Backend RBAC is modeled and wired to workflow action contracts, but not yet wired to every route/action.
- Audit immutability is documented, domain-guarded and hash-chain previewed, but not persistent end-to-end.
- Care plan version history is modeled but not wired to write workflow.
- Care plan draft, approval package, education release package and workflow action contracts are deterministic and demo-data backed; final approval/writeback still needs server actions, persistent audit logging and immutable version creation.
- Rule/content approval workflow is modeled but not fully executable.

## Chua hoan thanh

- Production authentication/session/MFA/password hashing.
- Versioned migration files generated from Prisma.
- Docker one-command run verification.
- Database backup/restore test.
- A5 PDF generator and test.
- API/server actions for create patient, appointment, vitals, medication reconciliation, care plan approval, handout approval and task transitions.
- Real audit log persistence on every sensitive action.
- Rate limiting, CSRF, secure headers and environment validation.
- User acceptance testing and formal clinical/data protection signoff.

## Ket luan production

Not production-ready. Do not use with real patient data. See `PRODUCTION_BLOCKERS.md`.
