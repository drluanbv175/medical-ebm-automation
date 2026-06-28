---
document: V4_3_3_2_RETENTION_POLICY
version: V4.3.3.2
generated: 2026-06-28
qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
---

# V4.3.3.2 Repository Retention Policy

## 1. Permanent Retention — Never Delete

These paths must remain in the repository at all times:

### Source Code
- `runtime/` — agent registry, policy gate, workflow state machine, schemas
- `research_project/` — 13-module dossier package (V4.3.3 new)
- `research_studio/` — research governance layer
- `research_automation/` — automation pipeline layer
- `app/` — Streamlit clinical dashboard modules
- `tests/` — all deterministic offline tests
- `scripts/` — verify_manifest_registry.py and supporting scripts
- `.github/workflows/` — CI configuration

### Manifests and Config
- `runtime/manifests/agent_source_manifest.csv` — 48-agent manifest, SHA256 verified
- `.claude/agents/` — 74 agent definition files
- `automation_schedule.yaml`
- `research_project_request.yaml`
- `harness.toml`, `requirements.txt`, `ruff.toml`, `.gitignore`
- `CLAUDE.md`, `AGENTS.md`

### Templates
- `dashboard_mockups/templates/` — EW and DA dashboard templates

### V4.3.3 Frozen Evidence (must not be modified or deleted)
- `V4_3_3_EXECUTIVE_SUMMARY.md`
- `V4_3_3_TEST_REPORT.md`
- `V4_3_3_FRESH_ARCHIVE_ACCEPTANCE.json`
- `V4_3_3_GIT_BASELINE_VERIFICATION.md`
- `V4_3_3_FREEZE_SUMMARY.md`
- `results/v4_3_3_fresh_archive_*.txt` (5 raw log files)

### Data and Evidence
- `evidence/` — EBM evidence library
- `data/` — reference and processed data
- `docs/` — system documentation
- `knowledge-packs/` — clinical knowledge packs

---

## 2. Transient — Safe to Delete (Whitelist Cache Only)

These are fully regenerable and contain no unique data:

| Path Pattern | Regeneration Command |
|-------------|---------------------|
| `**/__pycache__/` | `python3 -m compileall` |
| `**/*.pyc` | auto-generated on import |
| `.pytest_cache/` | `pytest` |
| `.mypy_cache/` | `mypy` |
| `.ruff_cache/` | `ruff check` |
| `.DS_Store` | macOS Finder (auto) |
| `._*` | macOS resource forks (auto) |

All whitelist cache items must be added to `.gitignore`. No other files may be deleted without explicit inventory entry and human review.

---

## 3. Quarantine — Human Review Required Before Any Action

| Path | Reason |
|------|--------|
| `MRAQ100_AUDIT/` | Untracked; contains MRAQ self-assessment; scope not verified |
| `templates/` | Untracked; content not verified |
| `out/` | Untracked; may be build output |
| `projects/` | If created by CLI: synthetic dossiers; if unknown origin: quarantine |

**Action for quarantined items:** Inventory, document, then present to human for decision. Do not delete automatically.

---

## 4. Prohibited Actions

- ❌ Do not delete source code, tests, manifests, or frozen evidence
- ❌ Do not delete MRAQ100_AUDIT/ without human review
- ❌ Do not delete results/ or any V4_3_3_* evidence files
- ❌ Do not skip tests or hard-code PASS to work around failures
- ❌ Do not commit generated dossiers from `projects/` directory
- ❌ Do not alter V4.3.3 freeze receipts
- ❌ Do not change MRAQ score or qualification

---

## 5. .gitignore Policy

The following patterns must be in `.gitignore`:

```gitignore
# Python cache
__pycache__/
*.py[cod]
*.pyo
.pytest_cache/
.mypy_cache/
.ruff_cache/

# macOS
.DS_Store
._*

# Generated dossiers (runtime output, not source)
projects/
```

Secrets are already excluded via `.env` rule (existing).
