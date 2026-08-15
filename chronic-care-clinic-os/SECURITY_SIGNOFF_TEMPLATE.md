# Security Signoff Template

## Scope

- Product: Chronic Care Clinic OS.
- Release ID:
- Environment:
- Date:
- Reviewer reference:

Do not include patient identifiers, PHI, secrets, raw logs, `.env` values or private
absolute paths in this record.

## Review items

- [ ] Production secrets are stored outside synced folders and are not committed.
- [ ] MFA and least-privilege admin access are enforced.
- [ ] Backend authorization checks protect every server action and API route.
- [ ] Audit logging is append-only or has equivalent tamper-evidence.
- [ ] Secure headers and runtime production flags are verified.
- [ ] Prompt-injection and unsafe automation controls are enabled.
- [ ] Backup, restore and rollback evidence was reviewed.
- [ ] Incident response contact path is assigned and tested.

## Decision

- [ ] Not approved.
- [ ] Approved for sandbox/demo only.
- [ ] Approved for limited pilot with fake or de-identified data.
- [ ] Approved for production go-live review after all other signoffs are complete.

Reviewer signature:
