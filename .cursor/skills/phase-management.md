# Skill: Phase Management

## Purpose
Manage the phased build process for DTL-Global Platform.

## When to Use
- At the start of every work session
- When the user says "phase status" or "what phase am I on?"
- Before starting any new work

## Process

### Starting a Session
1. Read DTL_MASTER_PLAN.md Section 19 (Phase Gate Checklist)
2. Identify which phase is currently active by checking completed gates
3. Only work on tasks within the current phase
4. Report current phase status to Gerardo

### Phase Status Report Format

Current Phase: [X] — [Phase Name]
Completed: [list completed tasks]
In Progress: [current task]
Remaining: [list remaining tasks]
Gate Status: [X/Y checks passed]

### Phase Completion
1. Run through ALL gate checklist items for the current phase
2. Report gate status (passed/not passed for each item)
3. If ALL pass: Phase [X] GATE PASSED. Ready for Phase [X+1].
4. If any fail: Phase [X] gate not passed. Fix: [specific items]
5. Do NOT proceed to next phase until gate passes

### Phase Order (DO NOT SKIP)
0. Project Bootstrap (this setup)
1. Phase 0: HubSpot and Stripe Setup
2. Phase 1: CDK Infrastructure
3. Phase 2: Lambda Functions
4. Phase 3: AI Layer
5. Phase 4: Website Deployment
6. Phase 5: Add-On Modules
7. Phase 6: End-to-End Testing