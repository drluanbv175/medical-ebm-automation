---
_harness_template: "AGENTS.md.template"
_harness_version: "4.3.3"
---

# AGENTS.md - Development Flow Overview

> **Project**: medical-ebm-automation
> **Created**: 2026-06-07
> **Setup locale**: vi

---

## 0. Development Flow Overview

### Two-Agent Operating Model

| Agent | Role | Main responsibilities |
|-------|------|-----------------------|
| **PM** | Project manager | Task management, review, and release decisions |
| **Claude Code** | Worker | Implementation, tests, CI fixes, and staging deploys |

### Workflow

```
PM                    Claude Code (Worker)
    |                       |
    |  1. Request work      |
    |---------------------->|
    |                       | 2. Plan -> implement -> commit
    |                       |    (/harness-plan -> /harness-work)
    |  3. Completion report |
    |<----------------------|
    | 4. Review and release |
    |    (/harness-review)  |
    |                       |
```

---

## 1. File Map

| File | Purpose | Readers |
|------|---------|---------|
| `AGENTS.md` | Shared development flow overview | Both agents |
| `CLAUDE.md` | Claude Code-specific instructions | Claude Code |
| `Plans.md` | Task tracking | Both agents |
| `harness.toml` | Harness config (safety rules, metadata) | Harness tooling |

---

## 2. Task Tracking (`Plans.md`)

### State Flow

```
pm:requested -> cc:wip -> cc:done -> pm:approved
```

| Marker | Meaning |
|--------|---------|
| `pm:requested` | PM requested work |
| `cc:todo` | Not started by Claude Code |
| `cc:wip` | Claude Code is working |
| `cc:done` | Claude Code completed the work |
| `pm:approved` | PM confirmed completion |
| `blocked` | Blocked; include the reason |

---

## 3. Commit Message Convention

```text
feat: add a new feature
fix: fix a bug
docs: update documentation
refactor: refactor code
test: add or update tests
chore: maintenance work
```

---

## 4. Prohibited Actions

- Do not force-push (`--force` / `--force-with-lease`)
- Do not commit secrets (`.env` is git-ignored and read-blocked)
- Do not work outside the requested scope
- Do not change security-sensitive settings unless explicitly requested

> **Note**: This is a solo project — direct pushes to `main` are allowed.

---

*Both PM and Claude Code may read this document.*
