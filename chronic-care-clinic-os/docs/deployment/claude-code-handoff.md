# Claude Code handoff - Chronic Care Clinic OS

Updated: 2026-07-15

## Current focus

The active product surface is `chronic-care-clinic-os`, a Next.js demo for chronic disease care coordination.
It is a Clinical Coordination Platform, not an EMR replacement and not production-ready.

## Start here

From repository root:

```bash
git status -sb
cat AGENTS.md
cat CLAUDE.md
cd chronic-care-clinic-os
pnpm sync:check
pnpm test
pnpm typecheck:app
```

If pnpm scripts are unavailable in the Codex desktop runtime, use bundled Node or system Node:

```bash
node --test tests/*.test.mjs
node node_modules/typescript/bin/tsc -p tsconfig.check.json --noEmit
node scripts/sync-check.mjs
```

## Completed app modules

- `lib/care-orchestrator.ts`: turns risk, labs, medication, follow-up, post-discharge and care-plan gaps into a command-center queue.
- `lib/program-registry.ts`: tracks chronic disease program coverage and monitoring gaps.
- `lib/visit-prep.ts`: builds pre-visit packets for nurse/physician preparation.
- `lib/care-plan-draft.ts`: creates physician-approved care plan drafts without treatment automation.
- `lib/care-plan-approval.ts`: creates preview-only approval packages with signoff gates, CarePlanVersion metadata and AuditLog preview.
- `lib/patient-education.ts`: gates A5 patient education handouts by approved template, approved care plan and consent.
- `lib/workflow-actions.ts`: defines preview-only server-action contracts for guarded write workflows before persistence exists.
- `lib/workflow-actions.ts`: adds persistent write plans for all guarded write actions, using `buildPersistentAuditWritePlan` while keeping production commit disabled until atomic DB tests exist.
- `lib/persistent-transaction.ts`: provides an in-memory transaction harness with behavior tests; it stages business write + AuditLog together and rolls back both on injected failure before any real database adapter is enabled.
- `lib/prisma-transaction-contract.ts`: defines the disabled Prisma transaction adapter contract, required rollback cases and test-database rollback evidence gate without importing Prisma or enabling production commits.
- `lib/prisma-rollback-evidence.ts`: validates the machine-readable rollback evidence report shape and checks whether the report can unlock only the test-database adapter.
- `docs/templates/prisma-rollback-evidence.template.json`: template for the required rollback evidence artifact; default values are not proof and do not unlock the adapter.
- `/overdue`: claim-call-task workflow now uses `claimOverdueFollowUpTaskAction` preview with `task.manage` guard.
- `/appointments`: create appointment workflow now uses `createCareAppointmentAction` preview with `task.manage` guard.
- `/patients/[id]`: care plan draft workflow now uses `createCarePlanDraftAction` preview with `care_plan.version` guard.
- `/admin/templates`: education template draft workflow now uses `createEducationTemplateDraftAction` preview with `clinical_rules.manage` guard.
- `/patients`: patient registration workflow now uses `registerPatientAction` preview with `patient.register` guard and consent gate.
- `/admin/rules`: clinical rule draft workflow now uses `createClinicalRuleDraftAction` preview with `clinical_rules.manage` guard and approval-before-active boundary.
- `/admin/users`: user invite workflow now uses `inviteUserAction` preview with `user.manage` guard and no-email/no-account-activation boundary.
- `lib/audit-ledger.ts`: builds and validates an append-only hash-chain audit ledger preview.
- `lib/audit-storage-contract.ts`: defines persistent AuditLog insert-only write plans with sequence/previousHash/eventHash and same-transaction requirements.
- `lib/backend-guard.ts` and `lib/rbac.ts`: authorize workflow actions by permission and organization/site scope.
- `lib/write-action-registry.ts`: tracks guarded preview actions, UI placeholders and production-blocked exports.
- `lib/password-security.ts`: defines the scrypt password-hashing contract for future production auth wiring.
- `lib/data-retention.ts`: defines retention/archive decisions that fail closed on legal hold, active care, missing data-protection review and unsafe delete requests.
- `lib/operations-readiness.ts`: validates backup/restore, monitoring-smoke and incident-drill evidence without touching production data.
- `lib/a5-output-qa.ts`: validates A5 rendered output evidence before handout/PDF release evidence can clear the blocker.
- `lib/production-evidence-dossier.ts`: builds a machine-readable dossier for every production blocker, required runtime control ID, artifact reference and signoff before final go-live.
- `lib/production-go-live.ts`: combines evidence package, runtime env, secure headers and attestation into one go-live decision.
- `lib/production-go-live-controls.ts`: validates route/RBAC coverage, organization/site isolation, dependency scan, Prisma migration review, Docker smoke and live governance persistence evidence.

## Pages wired to those modules

- `/command-center`
- `/programs`
- `/visits/prep`
- `/care-plans`
- `/handouts`
- `/patients`
- `/patients/[id]`
- `/admin/rules`
- `/admin/users`

## Safety boundaries that must stay true

- Do not add automatic diagnosis.
- Do not add automatic prescribing.
- Do not add automatic treatment-message sending.
- Clinical decisions must require physician confirmation.
- Patient communication requires approved template and consent.
- Preview packages do not write production data until server actions, persistent audit and immutable versioning are implemented.

## Recommended next tasks

1. Add reviewed Prisma migration/tests for the AuditLog sequence/previousHash/eventHash fields.
2. Build the Prisma test-database adapter to generate a real report matching `docs/templates/prisma-rollback-evidence.template.json`.
3. Promote only to the test-database adapter after `validatePrismaRollbackEvidenceReportSchema` and `evaluatePrismaRollbackEvidenceReport` both pass; production commit must remain disabled until formal signoff.
4. Attach real evidence artifacts for password hashing wiring, route/RBAC coverage, site isolation, dependency scan, Prisma migration review, Docker smoke, governance persistence, retention/archive, backup/restore, monitoring, incident drill and A5 QA into the production evidence package; placeholders must stay blocked.
5. Run `pnpm production:dossier -- --evidence /secure/path/production-evidence.json --out /secure/path/production-evidence-dossier.json` and fix every missing repository control link before `pnpm production:verify` or `pnpm production:go-live`.
6. Add A5 PDF generation only after approved-template, consent and `validateA5OutputQa()` gates remain covered by tests.
7. Configure a private Git remote so Windows, MacBook and Claude Code synchronize through Git, not only OneDrive.

## Do not start with

- Real patient data.
- Production auth claims.
- Automatic treatment changes.
- A database migration that cannot be tested on both Windows and macOS.
