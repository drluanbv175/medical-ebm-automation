# Claude Code handoff - Chronic Care Clinic OS

Updated: 2026-06-19

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
- `lib/persistent-transaction.ts`: provides an in-memory transaction harness that stages business write + AuditLog together and rolls back both on injected failure before any real database adapter is enabled.
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
2. Replace the in-memory transaction harness with a Prisma transaction adapter only after tests prove AuditLog insert and business write commit atomically.
3. Keep rollback tests for failure before business write, after business write before AuditLog, and after AuditLog before commit.
4. Add A5 PDF generation only after approved-template and consent gates remain covered by tests.
5. Configure a private Git remote so Windows, MacBook and Claude Code synchronize through Git, not only OneDrive.

## Do not start with

- Real patient data.
- Production auth claims.
- Automatic treatment changes.
- A database migration that cannot be tested on both Windows and macOS.
