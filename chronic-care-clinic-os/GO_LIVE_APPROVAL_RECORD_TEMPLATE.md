# Go-live Approval Record Template

This record is the final human approval gate before the separate go-live
attestation. It must be completed by an authorized clinic/site approver who is
distinct from every production signoff signer.

Do not include patient identifiers, PHI, secrets, raw datasets, linkage keys or
private absolute paths.

## Approval Record Fields

- Approval ID:
- Status: `APPROVED_FOR_GO_LIVE_REVIEW`
- Approver role: `CLINIC_ADMIN`
- Approver reference:
- Approved at: ISO-8601 timestamp.
- Scope: production go-live review for the signed release scope.
- Artifact references:
  - Evidence package:
  - Evidence dossier:
  - Signoff bundle:
  - Change ticket:
  - Rollback plan:

## Separation Of Duties

- [ ] Approver is not the production operator.
- [ ] Approver is not any required signoff signer.
- [ ] Approver has explicit authority for the clinic/site and release scope.
- [ ] Approval artifact references are safe, de-identified and immutable.

Approver signature:
