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
- `lib/workflow-actions.ts`: defines preview-only server-action contracts for care plan approval and handout release.
- `lib/audit-ledger.ts`: builds and validates an append-only hash-chain audit ledger preview.
- `lib/backend-guard.ts` and `lib/rbac.ts`: authorize workflow actions by permission and organization/site scope.
- `lib/write-action-registry.ts`: tracks guarded preview actions, UI placeholders and production-blocked exports.

## Pages wired to those modules

- `/command-center`
- `/programs`
- `/visits/prep`
- `/care-plans`
- `/handouts`
- `/patients/[id]`

## Safety boundaries that must stay true

- Do not add automatic diagnosis.
- Do not add automatic prescribing.
- Do not add automatic treatment-message sending.
- Clinical decisions must require physician confirmation.
- Patient communication requires approved template and consent.
- Preview packages do not write production data until server actions, persistent audit and immutable versioning are implemented.

## Recommended next tasks

1. Implement persistent append-only AuditLog storage using the same sequence/previousHash/eventHash contract.
2. Implement real server actions behind `approveCarePlanVersionAction` and `releaseApprovedPatientHandoutAction` only after persistent audit tests exist.
3. Work down `writeActionRegistry`: replace each `UI_PLACEHOLDER` with guarded workflow action contracts and keep exports blocked until de-identification/audit is implemented.
4. Add A5 PDF generation only after approved-template and consent gates remain covered by tests.
5. Configure a private Git remote so Windows, MacBook and Claude Code synchronize through Git, not only OneDrive.

## Do not start with

- Real patient data.
- Production auth claims.
- Automatic treatment changes.
- A database migration that cannot be tested on both Windows and macOS.
