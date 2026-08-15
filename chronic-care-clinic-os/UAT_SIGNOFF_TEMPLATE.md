# UAT Signoff Template

## Scope

- Product: Chronic Care Clinic OS.
- Release ID:
- UAT environment:
- Dataset: synthetic or de-identified only.
- Date range:
- UAT owner reference:

Do not include patient identifiers, PHI, raw datasets, linkage keys or screen captures
that reveal protected information.

## Minimum UAT Coverage

- [ ] Hypertension and type 2 diabetes follow-up workflow.
- [ ] Red flag escalation and blocked automation behavior.
- [ ] Missing data, stale data and conflicting evidence cases.
- [ ] Medication review warnings framed as clinician-review tasks.
- [ ] Handout, A5/PDF and patient communication preview paths.
- [ ] RBAC for physician, nurse, assistant, admin and read-only roles.
- [ ] Audit trail for drafts, approvals, exports and blocked actions.
- [ ] Backup, restore, rollback and incident response drill evidence.

## Exit Criteria

- [ ] No open severity-1 or severity-2 defects.
- [ ] All accepted residual risks have owner, expiry and mitigation.
- [ ] UAT evidence artifacts are listed with safe artifact references.
- [ ] Clinical, operations, data protection and security reviewers can reproduce
      the critical path without manual database edits.

## Decision

- [ ] Failed, return to shadow/review mode.
- [ ] Passed for sandbox/demo only.
- [ ] Passed for limited pilot with fake or de-identified data.
- [ ] Passed for production go-live review after all signoffs are complete.

UAT owner signature:
