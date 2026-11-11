---
name: feature-spec-writer
description: Use when the user explicitly says "write a spec for feature X", "tạo spec cho tính năng Y", "draft a specification", or after brainstorming reaches consensus on requirements. Produces a production-ready HTML spec following NAL Vietnam template (Be Vietnam Pro + Fraunces, Avatar shared stylesheet) with Overview, Scope, Acceptance Criteria, Constraints, Approach, Risks, Open Questions sections.
---

# Feature Spec Writer

## Overview

Convert a brainstormed feature idea into a structured HTML specification document the engineering team can implement against. Output follows NAL Vietnam visual identity (Avatar docs style) and the standard 7-section spec template.

**Announce at start:** "I'm using the feature-spec-writer skill to draft the spec."

**Save specs to:** `docs/specs/YYYYMMDD-<feature-slug>.html` (project-local docs dir, NOT team-ai-pack).

> **Domain context:** if `CONTEXT.md` exists at the repo root, read it first and use the project's ubiquitous language throughout the spec; respect any `docs/adr/` decisions in the area.

## When to Activate

Trigger on phrases like:
- "Write a spec for ..."
- "Draft a specification ..."
- "Tạo spec cho tính năng ..."
- "Viết spec cho ..."
- After a brainstorming session (`/avatar:brainstorm` command or the `brainstormer` agent, if available) reaches consensus and user says "OK, write the spec"

**Do NOT activate when:**
- The request is implementation-ready (already has scope + criteria) — proceed directly to coding
- User wants Markdown not HTML (use a plain markdown spec instead)
- User wants a one-liner summary (too short for a spec)

## Prerequisite Check

Before writing, confirm you have ALL of these. If any are missing, **STOP and ask** rather than guessing:

| # | Item | Question to ask if missing |
|---|---|---|
| 1 | Feature name | "What's the feature name?" |
| 2 | Problem it solves | "Who hits this problem today and what's the current workaround?" |
| 3 | Target users | "Which user persona does this serve?" |
| 4 | Definition of done | "What does success look like? List 3-5 acceptance criteria." |
| 5 | Tech constraints | "Tech stack, performance budget, deadline, backward-compat requirements?" |
| 6 | Out-of-scope items | "What are we explicitly NOT building in this iteration?" |

When input is short and the optional `prompt-scoring` tool is enabled, its hook scores the prompt and routes to the `prompt-improver` skill for clarification; when the tool is off, ask the questions above yourself. No separate quality-check step is needed here.

## The Seven Sections (NAL Standard)

Every spec MUST contain these sections in this order:

### 1. Overview (Tổng quan)
- 2-3 sentences answering: what is this, why now, who benefits
- One-line elevator pitch at the top

### 2. Scope (Phạm vi)
Two subsections:
- **In scope** — bulleted list of what WILL be built
- **Out of scope** — bulleted list of what will NOT be built this iteration

### 3. Acceptance Criteria (Tiêu chí nghiệm thu)
- Numbered list of testable conditions
- Each criterion is a Given-When-Then or pass/fail statement
- Reviewers can check each one without ambiguity

### 4. Constraints (Ràng buộc)
Four sub-categories:
- **Technical** — stack, libraries, runtime, browser support
- **Performance** — latency, throughput, memory, bundle size budgets
- **Business** — deadline, budget, compliance
- **Compatibility** — backward compat, migration path

### 5. Approach (Phương pháp tiếp cận)
- 2-3 candidate approaches with trade-offs (table format)
- Recommended approach highlighted with rationale

### 6. Risks (Rủi ro & Giảm thiểu)
- Table: Risk | Impact (Low/Medium/High) | Likelihood | Mitigation

### 7. Open Questions
- Numbered questions still needing answers before implementation
- Each question marked with owner if known

## Process

### Step 1 — Gather inputs
Read context. Ask the prerequisite questions ABOVE that aren't already answered. Do not skip this step.

### Step 2 — Draft sections in order
Fill each of the 7 sections. Use the template as the structural backbone.

### Step 3 — Spec self-review (inline)
Before generating HTML, check:
- No "TBD" / "TODO" / vague placeholders left
- No section contradicts another
- Each acceptance criterion is testable
- Scope is single-iteration sized (if not, propose decomposition)

### Step 4 — Generate HTML
Use the helper script:

```bash
python3 <workspace-root>/.claude/skills/feature-spec-writer/scripts/generate-spec-html-from-structured-data.py \
  --data /tmp/spec-data.json \
  --output docs/specs/YYYYMMDD-<feature-slug>.html
```

The script reads structured spec data (JSON) and emits HTML using the Avatar shared stylesheet inline (no external CSS dependency — the spec is portable).

### Step 5 — Present to user
Open the generated HTML, summarize key decisions, ask:
> "Spec saved at `<path>`. Please review and tell me if any section needs revision before we move to planning."

If user requests changes, edit the JSON data and regenerate. Do NOT hand-edit HTML.

## Anti-Patterns

**DO NOT:**
- Write speculative requirements ("the system might need ...")
- Use marketing language ("revolutionary", "best-in-class")
- Skip the prerequisite questions to ship faster
- Mix implementation details into acceptance criteria
- Output Markdown when the user asked for HTML (template is HTML-only)
- Hard-code the spec path — always derive from feature slug + today's date

## Key Principles

- **One spec = one iteration.** If scope spans multiple iterations, ask the user to decompose.
- **Testable acceptance criteria.** Each criterion must answer "how do we know it's done?"
- **Visible trade-offs.** Approach section shows 2-3 options, not just the chosen one.
- **Open Questions belong in the spec.** Don't hide ambiguity — surface it at the end.
- **HTML is portable.** Self-contained file, no external CSS, opens anywhere.

## Output File Naming

```
docs/specs/YYYYMMDD-<feature-slug>.html
```

Slug rules:
- Kebab-case, lowercase
- Max 50 chars
- Descriptive (not "spec-1", "feature-x")
- Examples: `20260529-vendor-payout-batching`, `20260529-mobile-app-cold-start-opt`
