# Skill: GitFlow for DTL-Global

## When Starting a New Phase

### Step 1: Create GitHub Issue
```bash
gh issue create --title "Phase {N}: {Phase Name}" --body "## Phase {N}: {Phase Name}\n\n### Objective\n{description}\n\n### Tasks\n- [ ] Task 1\n- [ ] Task 2\n\n### Gate Checklist\nSee DTL_MASTER_PLAN.md Section 21" --label "phase-{N}" --project "DTL-Global Platform"
```

### Step 2: Create Feature Branch
```bash
git checkout main
git pull origin main
git checkout -b feature/{issue-number}-phase-{N}-{short-description}
```

### Step 3: During Development — Granular Commits
```bash
git add .
git commit -m "feat(phase-{N}): {short description} #{issue-number}"
```

### Step 4: Phase Complete — Push and PR
```bash
git push origin feature/{issue-number}-phase-{N}-{short-description}
gh pr create --title "Phase {N}: {Phase Name}" --body "## Summary\n\n{What was built}\n\n## Changes\n\n- {change 1}\n- {change 2}\n\nCloses #{issue-number}" --base main --head feature/{issue-number}-phase-{N}-{short-description}
```

### Step 5: Merge
```bash
gh pr merge --squash --delete-branch --yes
```

## Critical Rules
- NEVER use interactive CLI commands (no vim, no nano, no prompts)
- ALWAYS use --body for PR descriptions (not --editor)
- ALWAYS use --yes for merge confirmations
- ALWAYS use -m for commit messages
- ALWAYS reference the issue number in commits with #{number}
- NEVER commit directly to main
- ONE feature branch per phase, ONE PR per phase
- Squash merge to keep main history clean
