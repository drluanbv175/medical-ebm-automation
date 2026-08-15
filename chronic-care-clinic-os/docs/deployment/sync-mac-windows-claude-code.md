# Sync workflow for Windows, MacBook and Claude Code

## Source of truth

Use Git commits as the source of truth. OneDrive may mirror files between Windows and macOS, but it should not be the only safety mechanism for clinical or engineering work.

Current repository state:

- Local git repository: `medical-ebm-automation`
- Chronic Care app folder: `chronic-care-clinic-os`
- Package lock: `chronic-care-clinic-os/pnpm-lock.yaml`
- Git remote: not configured yet

## Recommended setup

1. Create a private GitHub/GitLab/Bitbucket repository.
2. On Windows, from `medical-ebm-automation`, add the remote:

```bash
git remote add origin <private-repo-url>
git push -u origin main
```

3. On MacBook, clone from the remote instead of copying the folder by hand:

```bash
git clone <private-repo-url>
cd medical-ebm-automation
```

4. Keep OneDrive as a convenience mirror only. Do not edit the same working tree from Windows and macOS at the same time.

## Daily workflow on every machine

Before work:

```bash
git status -sb
git pull --ff-only
cd chronic-care-clinic-os
pnpm sync:check
```

After work:

```bash
cd chronic-care-clinic-os
pnpm check
cd ..
git status -sb
git add -A
git commit -m "feat: short summary"
git push
```

If there is still no remote, replace `git pull` and `git push` with a manual OneDrive sync check, then avoid opening Claude Code on both machines at the same time.

## Windows notes

- Use PowerShell from the repository root.
- Keep Python virtual environments outside OneDrive, for example `%USERPROFILE%\.ebm-venv`.
- Do not commit `.env`, `node_modules`, `.next`, `.pnpm-store`, local databases or generated logs.

## macOS notes

- Use Terminal from the repository root.
- Keep Python virtual environments outside OneDrive, for example `~/.ebm-venv`.
- If using Homebrew Node, enable pnpm through Corepack:

```bash
corepack enable
corepack prepare pnpm@11.0.7 --activate
```

## Claude Code notes

Claude Code should open the repository root, not only `chronic-care-clinic-os`.

Session start:

```bash
git status -sb
cat AGENTS.md
cat CLAUDE.md
cd chronic-care-clinic-os
pnpm sync:check
```

Session end:

```bash
cd chronic-care-clinic-os
pnpm check
cd ..
git status -sb
git add -A
git commit -m "feat: short summary"
```

Never force-push. If Windows, macOS and Claude Code all have changes, commit each worktree first, then merge through Git instead of relying on OneDrive conflict files.

## Clinical safety sync rule

Clinical rule, automation and patient-communication changes must be committed with tests or docs showing:

- no automatic diagnosis
- no automatic prescribing
- no automatic treatment-message sending
- physician confirmation for clinical decisions
- consent and approved template before patient communication
