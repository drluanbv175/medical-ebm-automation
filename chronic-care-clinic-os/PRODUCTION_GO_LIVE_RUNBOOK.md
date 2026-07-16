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

Start from a complete template instead of writing the package by hand:

```bash
pnpm production:verify -- --init-template /secure/path/production-evidence-template.json
```

The template deliberately contains `TODO` placeholders. It will not pass production verification until every placeholder is replaced by reviewed evidence/signoff references.

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
      "controlsVerified": ["Route/action RBAC coverage test and reviewer signoff."],
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

## Non-Negotiable Boundaries

- Do not store real patient identifiers in the evidence package.
- Do not clear a clinical blocker with repository tests alone; clinical approval must be signed by the physician lead.
- Do not enable AI drafts unless AI governance evidence and human review workflow signoff are present.
- Do not use this app with real patient data until the production-readiness route returns `PRODUCTION_READY` in the deployed environment.

Can bac si kiem chung.
