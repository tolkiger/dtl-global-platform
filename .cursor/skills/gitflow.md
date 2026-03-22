# Skill: GitFlow for DTL-Global

Aligned with **DTL_MASTER_PLAN.md Section 20**. All `git` / `gh` usage must be **non-interactive** (`--body`, `--yes`, `-m`, never `--editor` or interactive prompts).

---

## 20.1 One-time setup (GitHub Project)

Create the project once; reuse it for every phase:

```bash
gh project create --title "DTL-Global Platform" --owner @me --format json
```

---

## 20.2 Per-phase workflow

| When | Action |
|------|--------|
| **Before** | Create a GitHub Issue for the phase; create a **feature branch** from `main` |
| **During** | Granular commits: `feat(phase-{N}): {description} #{issue-number}` |
| **After** | Push branch → `gh pr create ... --body "..."` → `gh pr merge --squash --delete-branch --yes` |

### Create issue (example)

```bash
gh issue create \
  --title "Phase {N}: {Phase Name}" \
  --body "## Phase {N}: {Phase Name}

### Objective
{description}

### Tasks
- [ ] Task 1
- [ ] Task 2

### Gate checklist
See DTL_MASTER_PLAN.md Section 21" \
  --label "phase-{N}" \
  --project "DTL-Global Platform"
```

### Branch from main

```bash
git checkout main
git pull origin main
git checkout -b feature/{issue-number}-phase-{N}-{short-description}
```

### Granular commits

```bash
git add .
git commit -m "feat(phase-{N}): {short description} #{issue-number}"
```

### Push and open PR

```bash
git push origin feature/{issue-number}-phase-{N}-{short-description}
gh pr create \
  --title "Phase {N}: {Phase Name}" \
  --body "## Summary

{What was built}

## Changes

- {change 1}
- {change 2}

Closes #{issue-number}" \
  --base main \
  --head feature/{issue-number}-phase-{N}-{short-description}
```

### Merge (squash)

```bash
gh pr merge --squash --delete-branch --yes
```

---

## 20.3 Branch naming

```
feature/{issue-number}-phase-{N}-{short-description}
```

---

## 20.4 Critical rules

- **Never** commit directly to `main`
- **Never** use interactive CLI commands (vim, nano, `gh`/`git` interactive editors)
- **Always** use `--body` for PR text (not `--editor`)
- **Always** use `--yes` for merge confirmation
- **Always** use `-m` for commit messages when scripting
- **Always** reference the issue number in commits (`#{number}`)
- **One** feature branch per phase, **one** PR per phase
- **Squash merge** to keep `main` history clean
