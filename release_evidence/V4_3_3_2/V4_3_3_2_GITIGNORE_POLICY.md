---
document: V4_3_3_2_GITIGNORE_POLICY
version: V4.3.3.2
generated: 2026-06-28
---

# V4.3.3.2 .gitignore Policy

## Rules Added in V4.3.3.2

| Pattern | Reason |
|---------|--------|
| `.mypy_cache/` | Type-check cache — 128MB, fully regenerable |
| `.ruff_cache/` | Lint cache — regenerable |
| `._*` | macOS resource fork files — no data content |
| `projects/` | CLI-generated runtime dossiers — not source, not evidence |

## Existing Rules (confirmed correct)

| Pattern | Reason |
|---------|--------|
| `.env` | Secrets — never commit |
| `__pycache__/` | Python bytecode cache |
| `*.pyc`, `*.pyo` | Python compiled files |
| `.pytest_cache/` | pytest cache |
| `.DS_Store` | macOS Finder metadata |
| `out/` | Build output |
| `.venv/`, `venv/` | Virtual environments |
| `**/node_modules/` | Node dependencies |
| `data/raw/*`, `data/processed/*` etc | Large generated data |
| `.claude/state/`, `.claude/sessions/` | Runtime harness state |

## What Must NOT Be in .gitignore

| Pattern | Reason to keep tracked |
|---------|----------------------|
| `results/` | Contains frozen V4.3.3 evidence logs |
| `V4_3_3_*.md`, `V4_3_3_*.json` | Frozen release evidence |
| `runtime/manifests/` | Source-controlled manifest |
| `.claude/agents/` | Agent definitions |
| `tests/` | All test files |
| `research_project/` | Package source |

## Key Decision: `projects/`

CLI-generated dossiers (`researchctl project-build`) produce output in `projects/`. These are:
- DRAFT artifacts (synthetic only)
- Runtime output, not source code
- Not suitable for version control (contain REQUIRE_HUMAN_INPUT placeholders)

Therefore `projects/` is gitignored. A synthetic example is maintained in `examples/` for CLI smoke-testing.
