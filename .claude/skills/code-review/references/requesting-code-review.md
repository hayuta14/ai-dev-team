---
name: requesting-code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements - dispatches the code-reviewer subagent with an explicit git range and plan, then acts on its Verdict block
---

# Requesting Code Review

Dispatch the `code-reviewer` subagent to catch issues before they cascade. The reviewer gets a precise brief, never your session history. It returns a Verdict block you gate on.

**Core principle:** Review early, review often. Fix before moving on.

## When to request

**Mandatory:**
- After each task in subagent-driven development
- After completing a plan phase (`/avatar:implement` Step 4)
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before a refactor (baseline)
- After fixing a complex bug

## How to request

**1. Get the git range.** `HEAD~1` is wrong when the work has more than one commit.

```bash
BASE_SHA=$(git merge-base origin/main HEAD)   # or the SHA where this task started
HEAD_SHA=$(git rev-parse HEAD)
```

Uncommitted work: say so in the brief and give `BASE_SHA` only; the reviewer diffs the working tree against it.

**2. Dispatch with the `Agent` tool, `subagent_type: code-reviewer`.** Default model is the agent's own `claude-sonnet-5-5`; pass `model: opus` on the call when the diff touches auth/payment/PII, changes schema or migrations, spans more than ~15 files, or is a re-review after a Critical round. Extended thinking follows the main session: if thinking is off there, the reviewer runs without it. The brief must carry:

```
WHAT_WAS_IMPLEMENTED: <one paragraph, what you built and why>
PLAN: <path, e.g. plans/20261015-1030-feature-x/phase-02-api.md, or inline requirements>
BASE_SHA: <sha>
HEAD_SHA: <sha, or "working tree">
FOCUS (optional): <anything you want checked hard, e.g. "the retry loop in sync.ts">
SECURITY_AUDIT: <path to the security-auditor report for this range | none>
```

`SECURITY_AUDIT` is how the reviewer knows an audit already happened. Leave it `none` on the first pass; after a `security-auditor` run on the same range, put the report path here on the re-review so Risk is not raised again for that reason.

Dispatch brief for `security-auditor` (its input contract): `WS` (workspace root containing `.claude/`), `REPO`, `RANGE: <BASE_SHA>..<HEAD_SHA>` (or `working tree`), `SURFACE` (auth | authz | payment | PII | tenant | webhook | secrets | upload | admin), `SPEC`, `ENV`, `PRIOR: <this reviewer's report path>`, `PLAN`. It writes `<WS>/plans/reports/security-auditor-<YYMMDD>-<slug>.md` (or under the plan's `reports/`) and returns `Report: <path>` first; that path is the `SECURITY_AUDIT` value.

Do not paste your conversation. Do not pre-state your own verdict ("I think it's fine"). The reviewer must form its own.

**3. Read the Verdict block first.** The reviewer returns:

```
## Verdict
- Critical issues: <n>
- Risk: low | medium | high | critical
- Secret scan: clean | FOUND
- Typecheck / Lint / Build / Tests: pass | fail | not run (<why>)
- Handoffs: none | security-auditor | performance-engineer | qa-reviewer
- Plan tasks: <done>/<total>, missing: <list>
```

**4. Act on it, in this order:**

| Verdict field | What you do |
|---|---|
| Critical issues > 0 | STOP. Fix every one. Re-run `tester`. Re-dispatch `code-reviewer`. Repeat until 0. Do not proceed, commit, or claim done. |
| Risk `high` or `critical` from findings | Same as above; `autopilot` blocks push on these. |
| Risk `high` only because Handoffs lists `security-auditor` (no High/Critical finding) | Dispatch `security-auditor` on the same range. If its Critical/High = 0, re-dispatch `code-reviewer` with `SECURITY_AUDIT: <its report path>`; Risk then drops to what the findings justify. If it found something, fix, re-audit, then re-review. |
| Secret scan FOUND | Remove the secret, rotate it if it was ever committed, then re-review. |
| Any check "not run" | Run it yourself before claiming anything about it. "Not run" is not "pass". |
| Handoffs lists an agent | Dispatch that agent before merge. `security-auditor` is mandatory for auth, payment, session, PII. `qa-reviewer` takes `FEATURE`, `REPO`, `RANGE`, `SPEC`, `USERS`, `DATA`, `PLAN`, `WS` (its Input contract); skip it when `/avatar:implement` already ran it on this range (its report is in `WHAT_WAS_IMPLEMENTED`). |
| Plan tasks missing | Finish them or get the user to descope explicitly. Then `project-manager` updates the plan; the reviewer never edits it. |
| High findings | Fix before proceeding to the next task. |
| Medium / Low | Fix now if cheap; otherwise list them in your handoff note so they are not lost. |
| "Declined to judge" entries | Rule on each one yourself: in scope (then fix or ask) or out of scope (say why). Nothing is dropped silently. |
| "Tech debt" entries | Decide whether to run `tech-debt-collector` on them. |

**5. If the reviewer is wrong:** push back with evidence (file:line, a test, command output). Then apply `code-review-reception.md`. Do not "fix" something that is not broken to satisfy a reviewer.

## Example

```
[Finished phase-02 of plans/20261015-1030-ticket-301-sync-retry/]

BASE_SHA=$(git merge-base origin/main HEAD)   # 4f1c2a9
HEAD_SHA=$(git rev-parse HEAD)                # b77e03d

Agent(code-reviewer):
  WHAT_WAS_IMPLEMENTED: Retry with exponential backoff for pack download in
    sync.ts; max 3 attempts; aborts on 401/403.
  PLAN: plans/20261015-1030-ticket-301-sync-retry/phase-02-retry.md
  BASE_SHA: 4f1c2a9
  HEAD_SHA: b77e03d
  FOCUS: the abort path on 401, and that no retry happens on a signed-URL expiry

[Reviewer returns]
  Critical issues: 0 · Risk: medium · Secret scan: clean
  Tests: 146/146 · Typecheck: pass · Lint: pass · Build: pass
  Handoffs: none · Plan tasks: 4/4
  High: H1 sync.ts:88 retry also fires on ENOTFOUND (DNS), plan said network-only
  Declined to judge: jitter not in plan, left as-is
  Tech debt: none

You: fix H1, decide jitter is out of scope (note it), re-run tester, proceed.
```

## Integration with workflows

- **`/avatar:implement` Step 4**: reviewer is mandatory; Critical must be 0 before Step 5.
- **Autopilot `review.md`**: the review session cannot spawn subagents or run tests and reports JSON `review_report`, not this Verdict. It uses the "Inline mode" section of `performing-code-review.md`; `review.md` is the contract.
- **Subagent-driven development**: review after each task, fix, then next task.

## Red flags

**Never:**
- Skip review because "it's simple"
- Dispatch without a git range or a plan path
- Proceed with Critical > 0 or a check marked "not run"
- Treat a green reviewer run as evidence you did not read
- Argue with valid technical feedback
