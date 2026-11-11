---
name: requirement-decomposer
description: Use when the user has a large requirement (feature, refactor, migration) that needs breaking into executable steps before coding starts. Produces a decomposition tree with explicit phases, bite-sized tasks (2-15 minutes each), dependency arrows, file ownership map, and parallelizable batches. Output is a Markdown plan ready to feed into `/avatar:implement` (or `/avatar:implement:parallel`). Triggers (VI): "chia nhỏ yêu cầu", "phân rã task".
---

# Requirement Decomposer

## Overview

Take a single large requirement and decompose it into a tree of phases → tasks, with explicit dependencies and parallelization markers. The output is a plan an engineer (or subagent) can execute step by step without re-deriving structure.

**Announce at start:** "I'm using the requirement-decomposer skill to break down this requirement into executable phases."

**Save plan to:** `<WORKING-DIR>/plans/YYYYMMDD-HHmm-<feature-slug>/plan.md` — naming and location per `.claude/skills/planning/references/plan-organization.md` (read it before writing under `plans/`).

## When to Activate

Activate when:
- User has an approved spec or clear requirement (from `feature-spec-writer` or direct)
- The work is multi-step (≥ 3 distinct tasks)
- User explicitly asks "break this down", "phân rã yêu cầu này", "chia nhỏ thành các bước"

**Do NOT activate when:**
- Task is single-step ("rename function X to Y") — just do it
- Requirement is still vague — clarify it first (when the optional `prompt-scoring` tool is enabled, its hook routes vague input to `prompt-improver`; otherwise ask)
- A plan already exists at the expected path — load it, don't redo

## Prerequisites

Before decomposing, verify:

1. **Success criteria is explicit** — if not, clarify first (via the `prompt-improver` skill when `prompt-scoring` is enabled, otherwise ask the user)
2. **Scope is bounded** — files/modules/components listed
3. **Approach is chosen** — from spec or user decision (not 2-3 options)
4. **Tech stack is known** — language, framework, test runner

If any are missing, STOP and ask before decomposing.

## The Decomposition Tree Format

Output follows this exact structure:

```markdown
# [Feature Name] — Decomposition Plan

**Source:** [link to spec / requirement]
**Generated:** YYYY-MM-DD HH:MM
**Total estimated time:** X hours
**Parallelizable:** yes/no

## File Ownership Map

| File | Created/Modified | Owner |
|---|---|---|
| `path/to/file.ts` | created | Phase 1 |
| `path/to/other.ts` | modified | Phase 2 |

## Dependency Graph

\`\`\`
Phase 1 (no deps) ─┐
                   ├─→ Phase 3 (deps: 1, 2)
Phase 2 (no deps) ─┘    │
                        └─→ Phase 4 (deps: 3)
\`\`\`

## Phase 1 — [Name] (no dependencies, parallelizable)

**Goal:** [1-sentence outcome]
**Estimated time:** X minutes
**Files touched:** `path/to/file.ts`

### Task 1.1 — [Action verb + object] (~3 min)
- Step: [concrete action]
- Step: [concrete action]
- Verify: [how to know it's done]

### Task 1.2 — [Action verb + object] (~5 min)
- Step: ...
- Verify: ...

## Phase 2 — [Name] (no dependencies, parallelizable with Phase 1)

...

## Phase 3 — [Name] (depends on Phase 1, 2)

...

## Parallelization Strategy

- **Batch A (parallel):** Phase 1, Phase 2 — no shared files
- **Batch B (after A):** Phase 3
- **Batch C (after B):** Phase 4
```

## Process

### Step 1 — Read the spec / requirement
Load source. Identify the major chunks of work.

### Step 2 — Identify natural phase boundaries
A phase = a coherent chunk of work that:
- Produces a testable artifact on its own
- Has clear inputs and outputs
- Touches a contained set of files
- Can be reviewed independently

Examples of phase boundaries:
- Data model changes (schema migration, type definitions)
- Backend API changes
- Frontend UI changes
- Tests
- Documentation
- Deployment/infra

### Step 3 — Decompose each phase into bite-sized tasks
Each task is **2-15 minutes of work**. If a task exceeds 15 minutes, split it.

Good task examples:
- "Write failing test for empty input case" (3 min)
- "Add `validateInput()` helper, make test pass" (5 min)
- "Run full test suite, verify 0 regressions" (2 min)
- "Update OpenAPI schema for new endpoint" (4 min)

Bad task examples (too big):
- "Implement authentication" → split into: schema, JWT util, middleware, tests, docs
- "Refactor the database layer" → split per-file or per-concern

### Step 4 — Map file ownership
For each file, mark which phase owns it (created or modified). This:
- Surfaces file conflicts between parallel phases
- Helps reviewers understand blast radius
- Enables file-ownership-based parallel execution

If two phases need to modify the same file, either:
- Merge them into one phase
- Mark as serial (one after the other, not parallel)

### Step 5 — Draw dependency graph
ASCII or Mermaid format. Show which phases depend on which. Identify the critical path.

Example dependency rules:
- Schema phase blocks API phase (API needs types)
- API phase blocks UI phase (UI calls API)
- Tests can run in parallel with implementation (TDD style)
- Docs phase typically last (after everything works)

### Step 6 — Identify parallelizable batches
Group phases that can run concurrently into batches:
- Batch A: all phases with no dependencies
- Batch B: phases whose deps are in Batch A
- Batch C: phases whose deps are in Batch A + B
- ...

Each batch executes serially after the previous. Phases within a batch can be done by parallel subagents.

### Step 7 — Estimate time
For each task, estimate in minutes. Sum per phase. Sum per batch. Total = critical path time (not naive sum).

If total estimate > 4 hours, consider splitting the requirement into smaller specs.

### Step 8 — Write the plan file
Save to `<WORKING-DIR>/plans/YYYYMMDD-HHmm-<feature-slug>/plan.md` (naming per `.claude/skills/planning/references/plan-organization.md`).

Use kebab-case slug, max 50 chars. Examples:
- `20260529-1430-vendor-payout-batching`
- `20260529-1530-mobile-app-cold-start-fix`

## Bite-Sized Task Granularity

Each step inside a task is ONE action (2-5 minutes). Inspired by Test-Driven Development:

| Step | Time | Example |
|---|---|---|
| Write the failing test | 3-5 min | Write integration test for new endpoint |
| Run it to make sure it fails | 30 sec | `pnpm test auth.spec.ts` → red |
| Implement minimal code | 5-10 min | Add route handler + service stub |
| Run tests to verify pass | 30 sec | `pnpm test` → green |
| Refactor if needed | 2-5 min | Extract helper, rename for clarity |

Each task leaves a self-contained, reviewable diff; committing is the executor's step and happens only when the user asks.

## Parallelization Rules

**Phases can run in parallel when:**
- They share NO files
- They don't read state the other writes
- Their outputs don't conflict (e.g., both adding to same JSON config)

**Phases MUST run serially when:**
- Phase B depends on type/schema from Phase A
- Phase B modifies a file Phase A creates
- Phase B's test depends on Phase A's implementation

Mark parallelizable phases explicitly: `(parallelizable with Phase X)`.

## Anti-Patterns

**DO NOT:**
- Create phases that span > 1 hour. Split them.
- Allow tasks > 15 minutes. Split them.
- Skip file ownership mapping — it's the source of truth for conflicts.
- Mark phases parallel when they share files — leads to merge hell.
- Write tasks without verification steps. "Write code" without "run test" is incomplete.
- Estimate optimistically. Add 25% buffer for real-world friction.
- Create a plan when one already exists at the path. Load and update instead.

## Example Output Snippet

```markdown
# Vendor Payout Batching — Decomposition Plan

**Source:** docs/specs/20260529-vendor-payout-batching.html
**Generated:** 2026-05-29 14:30
**Total estimated time:** 3.5 hours (critical path)
**Parallelizable:** yes (3 batches)

## File Ownership Map

| File | Action | Phase |
|---|---|---|
| `packages/api/prisma/schema.prisma` | modified | 1 |
| `packages/api/src/jobs/vendor-payout-batch.ts` | created | 2 |
| `packages/api/src/jobs/__tests__/vendor-payout-batch.test.ts` | created | 2 |
| `packages/api/src/workers/payout-worker.ts` | created | 3 |
| `packages/web/src/pages/finance/payout-batches.tsx` | created | 4 |
| `docs/runbooks/payout-batch.md` | created | 5 |

## Dependency Graph

\`\`\`
Phase 1: Schema ─┐
                 ├─→ Phase 2: Job logic ─→ Phase 3: Worker ─┐
                 │                                          ├─→ Phase 5: Runbook
                 └────→ Phase 4: UI ──────────────────────--┘
\`\`\`

## Phase 1 — Schema migration (no deps, ~20 min)

**Goal:** Add `PayoutBatch` table + relation to `Vendor`.
**Files:** `packages/api/prisma/schema.prisma`

### Task 1.1 — Add PayoutBatch model (5 min)
- Open `schema.prisma`
- Add model with fields: id, runAt, totalAmount, vendorCount, status (enum)
- Add relation to Vendor: vendor.payoutBatches (1:N)
- Verify: `pnpm prisma format` → no errors

### Task 1.2 — Generate migration (3 min)
- Run: `pnpm prisma migrate dev --name add-payout-batch`
- Verify: migration file created in `prisma/migrations/`
- Verify: prisma client regenerated

### Task 1.3 — Add Zod schema for API (5 min)
- Open `src/schemas/payout.ts`
- Add `PayoutBatchSchema` matching Prisma model
- Export from `src/schemas/index.ts`
- Verify: `pnpm typecheck` passes

## Phase 2 — Job logic (depends on Phase 1, ~45 min)

...

## Parallelization Strategy

- **Batch A:** Phase 1 (Schema) — alone, blocks everything
- **Batch B (after A):** Phase 2 (Job) + Phase 4 (UI) — run in parallel by 2 subagents
- **Batch C (after B):** Phase 3 (Worker) + Phase 5 (Runbook) — run in parallel
```

## Key Principles

- **Phase = testable artifact, task = 2-15 min.** Smaller than this wastes overhead; larger than this is hard to verify.
- **Dependencies are facts, not preferences.** Don't mark serial because "it feels safer"; mark serial because B literally needs A's output.
- **File ownership is the truth.** Two phases sharing a file = merge conflict waiting to happen.
- **Critical path drives the estimate.** Total time = longest chain, not naive sum.
- **Plans get executed by others.** Write so a future-you (or subagent) can follow without context.

## Integration

This skill chains with the others:

```
feature-spec-writer (defines what)
   ↓
requirement-decomposer (this skill — defines how, in tasks)
   ↓
/avatar:implement or /avatar:implement:parallel (does the work)
   ↓
verification-before-completion (confirms it's done)
```

Hand off:
> "Plan saved at `plans/<dir>/plan.md`. Next: `/avatar:implement` (or `/avatar:implement:parallel` if the batches are independent)."

Do NOT execute the plan in this skill. Hand off cleanly.
