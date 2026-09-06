---
document: V4_3_3_2_CLEANUP_DECISION_MATRIX
version: V4.3.3.2
generated: 2026-06-28
---

# V4.3.3.2 Cleanup Decision Matrix

## Decision Rules

| Category | Auto-delete allowed | Archive required | Human review |
|----------|--------------------|--------------------|--------------|
| DELETE_SAFE_CACHE | YES | NO | NO |
| GITIGNORE_GENERATED | YES (after gitignore) | NO | NO |
| ARCHIVE_OUTSIDE_REPOSITORY | NO (move, not delete) | YES | RECOMMENDED |
| QUARANTINE_REVIEW_REQUIRED | NO | NO | YES — mandatory |
| BLOCKED_UNKNOWN_CONTENT | NO | NO | YES — mandatory |
| KEEP_* | NO | NO | N/A |

## Per-Item Decisions

### SAFE TO DELETE — Whitelist Cache

| Path | Decision | Reason |
|------|----------|--------|
| `.mypy_cache/` | DELETE + GITIGNORE | 128MB regenerable cache; no unique data |
| `.ruff_cache/` | DELETE + GITIGNORE | Small regenerable cache |
| `.pytest_cache/` | DELETE + GITIGNORE | Small regenerable cache |
| `.DS_Store` (root) | DELETE + GITIGNORE | macOS metadata, no data |
| `docs/.DS_Store` | DELETE + GITIGNORE | macOS metadata |
| `tests/evals/.DS_Store` | DELETE + GITIGNORE | macOS metadata |
| `tests/evals/red_team/.DS_Store` | DELETE + GITIGNORE | macOS metadata |

### QUARANTINE — No Automatic Action

| Path | Decision | Required action |
|------|----------|----------------|
| `MRAQ100_AUDIT/` | QUARANTINE | Human must confirm content before any action. Contains `MRAQ_V4_X_SELF_REASSESSMENT.md`. Not committed to git. |
| `templates/` | QUARANTINE | Untracked; content type not verified. |
| `out/` | QUARANTINE | Untracked; likely build output but not confirmed. |

### KEEP — No Action

All paths in `KEEP_*` categories: **no action taken**.

### .gitignore Additions Required

The following must be added to `.gitignore` to prevent future accidental commits:

```
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.DS_Store
._*
projects/
```

Note: `projects/` added because CLI-generated dossiers are runtime output, not source.
`results/` is NOT gitignored because it contains tracked freeze evidence.
