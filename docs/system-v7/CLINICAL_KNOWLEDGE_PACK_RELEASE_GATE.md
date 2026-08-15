# Clinical Knowledge Pack Release Gate

Schema PASS only means a pack is readable and safe for review-only workflows
such as morning brief. It does not mean the pack is approved for clinical use.

Use:

```bash
python tools/validate_knowledge_packs.py
python tools/assess_knowledge_pack_release.py
python tools/assess_knowledge_pack_release.py --json
python tools/assess_knowledge_pack_release.py --output results/knowledge_pack_release_readiness.json
python tools/assess_knowledge_pack_release.py --require-clinical-release-ready
```

The release gate reports three separate levels:

- `schema_ok`: files are parseable and satisfy the draft schema.
- `review_ready`: pack can be used for internal draft review workflows.
- `clinical_release_ready`: pack has explicit approval and verified evidence.

Clinical release remains blocked unless all of these are true:

- `01_scope.yaml` explicitly allows clinical release while EMR write and
  prescription generation remain disabled.
- `13_approval_record.json` exists, has `status: approved`,
  `clinical_release_allowed: true`, `pii_present: false`, reviewer role,
  created date, and `next_review_due`.
- `10_evidence_manifest.json` exists, has `release_allowed: true`, and every
  claim has traceable source data, `verification_status: VERIFIED`,
  `approval_status: approved`, and `release: allowed`.

Current `2026.1-draft` packs are expected to be review-ready but
clinical-release-blocked.

Automation should consume the JSON payload, not parse CLI text. The payload kind
is `knowledge_pack_release_readiness_report`; `clinical_release_allowed` must be
`false` unless every pack is clinical-release-ready.
