# Production Go-Live Runbook

Status: technical production-readiness contract. Real go-live still requires signed evidence from the clinic, deployment owner, data protection owner and clinical lead.

## Gate To Production

The system may be called production-ready only when `/api/admin/production-readiness` returns:

- `summary.productionReady = true`
- `releaseDecision.status = "PRODUCTION_READY"`
- `releaseDecision.blockedReasons = []`
- `evidenceSummary.validEvidenceRecords = 24`
- `evidenceSummary.validSignoffs = 5`
- `findings = []`

The route reads `PRODUCTION_READINESS_EVIDENCE_PATH`. If that environment variable is missing, unreadable, malformed, incomplete, expired or missing any signoff, the route stays blocked.

CI/deployment should also run the same contract with an exit code:

```bash
pnpm production:verify -- --evidence /secure/path/production-evidence.json
```

Exit code `0` means the evidence package unlocks `PRODUCTION_READY`; exit code `1` means the package is readable but still blocked; exit code `2` means the package cannot be read or the command is malformed.

Before final verification, build the evidence dossier. This produces a machine-readable checklist for every blocker, required repository runtime control, residual gate, artifact reference and signoff:

```bash
pnpm production:dossier -- \
  --evidence /secure/path/production-evidence.json \
  --out /secure/path/production-evidence-dossier.json
```

The dossier may say `READY_FOR_FINAL_GO_LIVE_CHECK` only when every blocker record is valid, every required repository control ID is named in `controlsVerified`, and all five signoffs are valid. It is still not a production approval by itself; it only means the package is ready to enter the final go-live command below.

For the final one-run go-live gate, use:

```bash
pnpm production:go-live -- \
  --evidence /secure/path/production-evidence.json \
  --release-id release-2026-07-16-001 \
  --source-commit <deployed-git-sha> \
  --operator-ref OPS_GO_LIVE_001 \
  --admin-approver ADMIN_APPROVER_001 \
  --change-ticket CHANGE_TICKET_2026_07_16_001 \
  --rollback-plan operations/evidence/rollback-plan-001.json \
  --post-deploy-checklist operations/evidence/post-deploy-checklist-001.json \
  --out /secure/path/go-live-report.json
```

This command validates four layers together: signed evidence package, evidence dossier hash, production runtime environment variables, emitted production readiness headers and admin change-control attestation. It treats runtime warnings as blockers. The system may be called production only when this command exits `0` and writes `status = "PRODUCTION_READY"`.
The command records both evidence package SHA-256 and evidence dossier SHA-256 in the go-live report and writes a sidecar `go-live-report.json.sha256` so the final report is tamper-evident.
The `--admin-approver` reference must be distinct from `--operator-ref`; the system blocks operator self-approval.

Start from a complete template instead of writing the package by hand:

```bash
pnpm production:verify -- --init-template /secure/path/production-evidence-template.json
```

The template deliberately contains `TODO` placeholders. It will not pass production verification until every placeholder is replaced by reviewed evidence/signoff references.
For blockers with repository controls, keep the exact control IDs in `controlsVerified`, for example `RUNTIME-RBAC-COVERAGE-001` for `SEC-001` and `RUNTIME-DEPENDENCY-SCAN-001` for `SEC-007`.

## Required Evidence Package Shape

Store the evidence package outside source control, for example in a restricted deployment folder:

```json
{
  "kind": "chronic_care_production_evidence_package",
  "generatedAt": "2026-07-16T00:00:00.000Z",
  "evidence": [
    {
      "blockerId": "SEC-001",
      "status": "CLEARED",
      "reviewedByRole": "CLINIC_ADMIN",
      "reviewerReference": "CLINIC_ADMIN_REVIEWER_001",
      "reviewedAt": "2026-07-15T12:00:00.000Z",
      "artifactRefs": ["production-readiness/evidence/SEC-001-rbac-coverage.json"],
      "controlsVerified": ["Route/action RBAC coverage test and reviewer signoff.", "RUNTIME-RBAC-COVERAGE-001"],
      "expiresAt": "2027-07-16T00:00:00.000Z"
    }
  ],
  "signoffs": [
    {
      "role": "security_owner",
      "signerReference": "SECURITY_OWNER_001",
      "signedAt": "2026-07-15T18:00:00.000Z",
      "scope": "production release for chronic care clinic os MVP-01",
      "artifactRefs": ["production-readiness/signoffs/security-owner.json"]
    }
  ]
}
```

Repeat `evidence[]` for every blocker in `lib/production-readiness.ts`, and include all five signoffs:

- `security_owner`
- `data_protection_owner`
- `physician_lead`
- `operations_owner`
- `ai_governance_owner`

Each signoff role must use a distinct accountable signer reference. The package is blocked if one signer reference is reused across multiple production signoff roles.

## Non-Negotiable Boundaries

- Do not store real patient identifiers in the evidence package.
- Do not clear a clinical blocker with repository tests alone; clinical approval must be signed by the physician lead.
- Do not enable AI drafts unless AI governance evidence and human review workflow signoff are present.
- Do not use this app with real patient data until the production-readiness route returns `PRODUCTION_READY` in the deployed environment.

Can bac si kiem chung.
