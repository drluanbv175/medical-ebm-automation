# Go-live Attestation Template

This attestation is completed only after the evidence package, evidence dossier,
required signoffs and final approval record are valid. It does not override any
failed verifier or missing human gate.

Do not include patient identifiers, PHI, secrets, raw datasets, linkage keys or
private absolute paths.

## Required Fields

- Evidence package SHA-256:
- Evidence dossier SHA-256:
- Evidence package path:
- Source commit SHA:
- Release ID:
- Operator reference:
- Admin approver reference:
- Change ticket reference:
- Rollback plan artifact reference:
- Post-deployment checklist reference:

## Required Environment Variables For The Go-live Script

- `PRODUCTION_EVIDENCE_DOSSIER_SHA256`
- `SOURCE_COMMIT_SHA`
- `PRODUCTION_RELEASE_ID`
- `PRODUCTION_OPERATOR_REF`
- `PRODUCTION_ADMIN_APPROVER_REF`
- `PRODUCTION_CHANGE_TICKET_REF`
- `PRODUCTION_ROLLBACK_PLAN_REF`
- `PRODUCTION_POST_DEPLOY_CHECKLIST_REF`

## Attestation Checks

- [ ] `npm run production:dossier -- --evidence <path>` produced a reviewed dossier.
- [ ] `npm run production:go-live -- --evidence <path>` passes with production runtime flags.
- [ ] Operator and admin approver are distinct.
- [ ] Evidence hashes match immutable reviewed artifacts.
- [ ] Rollback owner, incident owner and post-deployment monitor are assigned.

Operator signature:

Admin approver signature:
