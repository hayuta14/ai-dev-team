---
name: tech-debt-collector
description: Use when Claude takes a shortcut or temporary workaround, leaves a TODO, or the user asks to log tech debt. Appends a scored entry (priority ((Impact + Risk) × (6 − Effort))) to `.claude/state/tech-debt.md`.
---

# Tech Debt Collector

## Overview

When you take a shortcut OR detect existing tech debt, capture it in a structured log. Each entry has reason, priority score, and proposed fix. Over time, `.claude/state/tech-debt.md` becomes the backlog for refactoring sprints.

**Announce at start:** "I'm using the tech-debt-collector skill to log this as tech debt."

## When to Activate

**Consider logging when you see these patterns in code or commit messages** (log only material debt — see Anti-Patterns):
- `TODO:`, `FIXME:`, `HACK:`, `XXX:` comments
- "for now", "for the time being", "tạm thời", "trước mắt"
- "we'll fix later", "future improvement", "follow-up"

**Activate when user says:**
- "log this as tech debt", "ghi nhận tech debt"
- "we cut a corner here", "đây là shortcut"
- "this should be rewritten later", "cần refactor sau"

**Activate proactively when Claude itself takes a shortcut:**
- Used `any` to ship faster (note + log)
- Skipped a test (note + log)
- Hardcoded a value that should be config
- Duplicated logic to avoid touching shared code
- Disabled a lint rule with inline override

## State File Location

```
.claude/state/tech-debt.md
```

If not exists, create from template. Append-only — never overwrite past entries.

## Categories (NAL convention)

| Category | Examples |
|---|---|
| **Code debt** | Duplicated logic, magic numbers, poor abstractions |
| **Architecture debt** | Monolith should be split, wrong data store choice |
| **Test debt** | Low coverage, flaky tests, missing integration tests |
| **Dependency debt** | Outdated libs, unmaintained packages, security advisories |
| **Documentation debt** | Missing runbook, outdated README, tribal knowledge |
| **Infrastructure debt** | Manual deploys, no monitoring, no IaC |
| **Type debt** | `any` cast, weak types, missing generics |
| **Security debt** | TODO security items, hardcoded test secrets, disabled checks |

## Priority Score

NAL formula: `Priority = (Impact + Risk) × (6 - Effort)`

| Dimension | Scale | What it means |
|---|---|---|
| **Impact** | 1-5 | How much does it slow team down or hurt UX? 1=barely, 5=blocking |
| **Risk** | 1-5 | What happens if not fixed? 1=cosmetic, 5=incident waiting |
| **Effort** | 1-5 | How hard is the fix? 1=trivial, 5=multi-week refactor |

Priority range: 2 (low) to 50 (top of backlog).

Bands:
- **Priority ≥ 30**: Top of backlog. Fix in next sprint.
- **Priority 15-29**: Schedule within quarter.
- **Priority < 15**: Park, revisit at quarterly debt review.

## Process

### Step 1 — Detect or accept tech debt
Either auto-detected (saw a `TODO` or shortcut taken) or user-flagged.

### Step 2 — Capture context
- **What:** 1-line description
- **Where:** file:line if specific, or component/module
- **Why created:** reason for the shortcut (deadline, scope, blocker)
- **Category:** from list above
- **Suggested fix:** 1-2 sentences how to resolve properly
- **Effort estimate:** XS/S/M/L/XL or hours

### Step 3 — Score priority
Ask user for Impact + Risk + Effort if not obvious from context. Use NAL formula.

### Step 4 — Append entry
Use helper script:

```bash
python3 .claude/skills/tech-debt-collector/scripts/append-tech-debt-entry-to-state-file.py \
  --description "Hardcoded webhook secret in tests" \
  --location "packages/api/src/__tests__/sepay.test.ts:42" \
  --category "security" \
  --reason "Test was passing in CI but failing locally — used hardcoded for speed" \
  --suggested-fix "Move to test fixture loader, generate per-test secret" \
  --impact 3 \
  --risk 4 \
  --effort 2
```

### Step 5 — Confirm
```
✓ Tech debt logged: TD-007
  Priority: 28 (schedule within quarter)
  Category: security
  Location: packages/api/src/__tests__/sepay.test.ts:42

Now: continue with current task. The debt is captured for later.
```

## State File Format

```markdown
# Tech Debt Backlog

**Last updated:** YYYY-MM-DD HH:MM
**Total items:** N
**Top-priority items (≥30):** M

## Active Items

### TD-001 — <one-line description>
- **Priority:** XX
- **Category:** <category>
- **Location:** path/to/file.ts:42 (or component name)
- **Reason created:** <why shortcut was taken>
- **Suggested fix:** <how to resolve>
- **Estimate:** <effort>
- **Logged:** YYYY-MM-DD HH:MM
- **Status:** open

### TD-002 — ...

## Resolved Items

(Move items here when fixed, with resolution note + commit/PR link)
```

## Anti-Patterns

**DO NOT:**
- Log every minor issue. Filter for actually material debt.
- Skip the priority score. Without it, the backlog is unsortable.
- Forget to mention WHO took the shortcut and WHY (helps future context).
- Treat tech-debt.md as a wish list. Each item must be actionable.
- Re-log the same debt twice. Search first, dedupe.

## Key Principles

- **Capture at the moment of creation.** Easier than archeology later.
- **Priority drives action.** Without it, debt is just noise.
- **Reason matters more than the debt itself.** Context teaches the team.
- **Resolved doesn't mean deleted.** Move to "Resolved Items" with proof.
- **Quarterly debt review.** Top 5 items get sprint capacity.

## Integration

```
Current task in flight
     ↓
Shortcut taken / TODO left / weak type / hardcoded value
     ↓
tech-debt-collector (this skill — log it now, don't forget)
     ↓
Continue current task
     ↓
End of sprint → review tech-debt.md → schedule top items
```

## Quick Capture Triggers

When one of these is material (see Anti-Patterns), log it without waiting to be asked:

| Pattern | Auto-log? | Priority hint |
|---|---|---|
| `// TODO: <text>` | Yes | I=2, R=2, E=? |
| `// FIXME: <text>` | Yes | I=3, R=3, E=? |
| `// HACK: <text>` | Yes | I=3, R=4, E=3 |
| `// @ts-ignore` (uncommented) | Yes | I=2, R=3, E=2 |
| `any` cast in production code | Yes | I=2, R=3, E=2 |
| Test marked `.skip` / `.only` | Yes | I=3, R=4, E=1 |
| Code duplication > 5 lines | Yes | I=2, R=2, E=3 |
| Disabled lint inline | Yes | I=1, R=2, E=1 |
