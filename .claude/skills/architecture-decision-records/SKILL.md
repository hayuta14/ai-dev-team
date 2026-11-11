---
name: architecture-decision-records
description: Use when a decision between real alternatives has been made (framework, database, API shape, auth strategy, deploy model, a plan's Decisions entry that future readers will question) and should be recorded as a numbered ADR in the repo's docs/adr/, or when someone asks why the codebase is shaped a certain way and docs/adr/ may already answer it. Writes only after the user approves the draft. Triggers (VI): "ghi ADR", "ghi lại quyết định", "vì sao chọn X", "lưu quyết định kiến trúc".
license: MIT — derived from github.com/affaan-m/ECC skills/architecture-decision-records (Affaan Mustafa), condensed for team-ai-pack. See LICENSE.txt.
---

# Architecture decision records

An ADR is a short file that says what was decided, what else was on the table, and what it costs. It lives in the repo it governs, next to the code, so the next person (or agent) who asks "why X and not Y?" finds the answer in `docs/adr/` instead of re-arguing it. `planning`, `debugging`, `planner` and `debugger` already read `docs/adr/`; this skill is how entries get there.

## When to write one

- A choice between alternatives that someone could reasonably revisit: framework, library, database, schema shape, API style, auth model, deploy topology, a cross-repo contract.
- A plan's Decisions section settles a question with the three labels (Khuyến nghị / Hệ quả nếu chọn sai / Độ tin cậy) and the answer outlives the plan.
- Not for: naming, formatting, one-file refactors, anything a linter rule already records.

## Where and how it is numbered

- Repo root `docs/adr/`, one file per decision: `NNNN-kebab-title.md` (`0001-use-supabase-for-telemetry-store.md`). Next number = highest existing + 1; never reuse a number.
- `docs/adr/README.md` holds the index table. Create the directory and README only after the user agrees; never create them silently in a repo that has none.
- The ADR goes in the repo whose code the decision governs, not in the workspace `plans/` tree. A cross-repo decision goes in the repo that owns the contract and is linked from the others.

## Format

```markdown
# ADR-NNNN: <decision as a short statement>

- Date: YYYY-MM-DD (backfilled: decided <original date>, when recording an old decision)
- Status: proposed | accepted | deprecated | superseded by ADR-NNNN
- Deciders: <names or roles>
- Links: <plan dir, MR, ticket>

## Context
<2-6 lines: the problem, the constraints, the forces. Facts with sources.>

## Decision
<1-3 lines, present tense: "We use X for Y.">

## Alternatives considered
- **<Option B>**: <what it would give> · rejected because <specific reason>
- **<Option C>**: ...

## Consequences
- Easier: <...>
- Harder / cost: <...>
- Risk and how we would notice: <...>
```

Index row in `docs/adr/README.md`: `| [NNNN](NNNN-title.md) | <title> | <status> | <date> |`.

## Process

1. Find the decision and its alternatives in the conversation, plan, or MR. An ADR with no rejected alternative is a changelog line, not an ADR; ask what else was considered.
2. Read `docs/adr/README.md` (if present) for the next number and for an existing ADR this one supersedes.
3. Draft the ADR and show it to the user. Write the file and the index row only after they approve; declined ⇒ write nothing.
4. Superseding: set the old ADR's status to `superseded by ADR-NNNN` and link back from the new one. Never delete or rewrite an accepted ADR's body; history is the point.
5. Report the path written. Do not commit unless the user asked for git.

## Answering "why did we choose X?"

Read the index, open the matching ADR, and quote its Decision and the rejected alternatives. No match ⇒ say so plainly and offer to record one; do not invent a rationale from the code.
