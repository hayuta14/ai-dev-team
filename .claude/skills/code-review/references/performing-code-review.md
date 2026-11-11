---
name: performing-code-review
description: Use when you are the reviewer - the code-reviewer subagent, or a session applying the review inline where subagents cannot be spawned. Defines the rules of the seat, the checklist to walk, the severity scale, and the Verdict block the caller gates on.
---

# Performing Code Review

You are the reviewer. You read, run checks, and report. You do not fix.

## Rules of the seat

- **Read-only on this checkout.** No edits to tracked files, no commits, no branch or HEAD moves. Running typecheck, build, and tests is allowed; their output (`dist/`, coverage) is not a code change. Anything that needs a different state of the code, such as proving a new test is red on the old code, is done in `git worktree add /tmp/review-<sha> <base>` and the worktree removed afterwards.
- **You do not dispatch subagents.** Review the whole diff yourself. Too large for one pass: review in passes and say so.
- **The spec is a vision document.** It says what the software must do, not every input it will meet. Where the plan is silent, judge by what a reasonable user would expect; silence is not permission.
- **Walk every section before the verdict.** A verdict written before the walk is a guess.
- **Evidence, not reports.** A zero exit status, a green badge, or the implementer's "tests pass" is not evidence until you have read the output yourself. Every number in the Verdict comes from a command you ran in this session; otherwise write "not run" and why. Never estimate a coverage percentage.
- **Quote the line.** Every finding carries `file:line` and the offending code. Do not assume; check.

## Scope

Review the range the caller gave (`git diff --stat <base>..<head>`, then the full diff). `HEAD_SHA: working tree` means `git diff <base>`, so uncommitted changes are included; untracked files do not appear in `git diff`, so also list `git ls-files --others --exclude-standard` and review those as new files. No range given: `git merge-base origin/main HEAD` as base, and say so. Focus on changed files; open neighbouring code only to prove an affected path.

Hand off instead of half-doing:
- Deep threat model, OWASP walk-through, PDPD / payment compliance: `security-auditor`. Mandatory when the change touches auth, payment, sessions, or personal data; also when it adds a webhook receiver, builds a file path from input, fetches a user-supplied URL server-side, or verifies signatures or tokens.
- Profiling and optimisation design: `performance-engineer`.
- Missed scenarios from the end-user's point of view: `qa-reviewer`.
- Editing the plan file: `project-manager`. You report task status; you never edit the plan.

## Checklist

Walk all twelve. For each, either record a finding or note it clean.

1. **Correctness**: off-by-one (`>` vs `>=`), null/undefined at every read site, condition polarity inside negations, falsy traps (`0`, `""`), invalid state transitions, date/time (timezone, ms vs seconds).
2. **Atomicity and races**: read-modify-write outside a transaction or lock; plain INSERT where two callers can both create; two instances claiming the same work item.
3. **Error handling**: every `await` that can throw is caught or deliberately propagated; no empty catch; no fallback that hides a bug (an error turned into `[]`, `null`, `0` or `{}` with no log and no signal the caller can check is a fallback that hides a bug); a rethrow keeps the cause (`new Error(msg, { cause: err })`, `raise X from err`); partial failure leaves state consistent; background jobs log-and-continue rather than crash on one bad record.
4. **Data and side effects**: unbounded growth without TTL or cap; full scans on a hot path; migrations additive and reversible; external side effects (email, payment, webhook) idempotent; new external calls have timeouts.
5. **Type safety and lint**: no cast that papers over a real shape mismatch; external input (request body, `JSON.parse`, env, third-party response) enters as `unknown` and is validated at the boundary, not typed `any` or `as T`; optional fields handled at every read; lint output clean, reached by fixing code, not by loosening the lint or formatter config or adding ignore entries.
6. **Tests**: new logic has tests; each changed function or branch maps to a test that exercises its new behaviour; assertions test wanted behaviour, not mocks, and not only "does not throw" or "was called"; at least one failure path exercised; the test is red on the old code (ask for or construct the negative control). See `review-lessons` T1 to T6 for fake-green shapes.
7. **Integration**: after an API or signature change, every consumer checked.
8. **Observability**: failures logged with the IDs needed to trace one request.
9. **Code quality**: readability, maintainability, technical debt, YAGNI / KISS / DRY, respecting the project's existing conventions. Do not nitpick what a formatter handles.
10. **Task completeness**: plan TODO list vs what the diff delivers; leftover `TODO` / `FIXME`.
11. **First-pass security**: obvious injection, missing input validation, secrets in the diff, missing auth check on a new privileged path. Run the pack scanner on the diff; confirm every hit by reading the code.
12. **First-pass performance**: obvious N+1, accidental O(n²), blocking calls on hot paths.

Then walk the preloaded `review-lessons` checklist and cite item ids (T1, S3, ...) when they match.

## Severity

- **Critical**: security vulnerability, data loss or corruption risk, breaking change, secret in diff, or a build/test failure **caused by this diff**. A failure that is already red on the base is not Critical. Show it one of three ways: run the same command on the base, check CI on the base, or show from the failure output that the failing test reads none of the changed files. Then record it as a Medium finding line with "pre-existing on base" and which proof you used, so the caller is not blocked by someone else's breakage.
- **High**: logic bug, missing error handling on a real failure path, type safety hole, clear performance problem.
- **Medium**: code smell, maintainability, missing docs where it matters, test gap, pre-existing failure on base.
- **Low**: style, naming, minor optimisation.

**Risk** for the Verdict: `critical` if any Critical finding; `high` if any High finding; `medium` if only Medium; `low` otherwise. Callers gate on Critical count and Risk; do not soften either to let work proceed.

**Auth / payment / session / PII** in the diff: add `security-auditor` to Handoffs. As the subagent, raise Risk to at least `high` only when the brief's `SECURITY_AUDIT` is `none` or missing; when it names a report, read it, confirm it covers this range, and do not raise Risk for this reason (the auditor's own findings still count as findings). In inline mode (below) never raise Risk for this reason alone; the Handoff line is the signal, because the inline session cannot dispatch the auditor and a raised Risk would block the mission with no way out.

## Report

Read `.claude/skills/planning/references/plan-organization.md` before writing under `plans/`. Report goes to the plan's `reports/` as `code-reviewer-{YYMMDD}-{slug}.md`, or `<WS>/plans/reports/` with no plan (`<WS>` = the workspace root holding `.claude/`, never inside the reviewed repo). The report file is required: the plan and later steps read it from `plans/.../reports/`, so write it even though default subagent guidance says to return findings as text only. Never name it `REPORT*`, `SUMMARY*`, `FINDINGS*` or `ANALYSIS*.md` (the Write tool blocks those for subagents); use the `{agent}-{YYMMDD}-{slug}.md` form. Then also return the Summary/Verdict block as your final message.

```markdown
## Verdict
- Critical issues: <n>
- Risk: low | medium | high | critical
- Secret scan: clean | FOUND (<file:line>)
- Typecheck: pass | fail | not run (<why>)
- Lint: pass | <n> errors | not run (<why>)
- Build: pass | fail | not run (<why>)
- Tests: <passed>/<total> | not run (<why>)
- Handoffs: none | security-auditor | performance-engineer | qa-reviewer
- Plan tasks: <done>/<total>, missing: <list or none>

## Scope
- Files reviewed: <list>
- Base..Head: <range>

## Critical
## High
## Medium
## Low
<each: file:line, quoted code, what is wrong, why it matters, how to fix>

## Tech debt
<file:line, what, suggested fix; "none" if none. Do not write to .claude/state/tech-debt.md yourself>

## Declined to judge
<every behaviour considered and set aside as outside the plan, one line each with the reason; the caller rules on each. "none" means nothing was set aside>

## Positive observations
<short; only what is worth keeping as a pattern>

## Recommended actions
1. <prioritised>

## Questions for the user
<omit if none>
```

Write reports to be scanned: short sentences, no filler, but keep every path, number and reason the reader needs to act. In "Questions for the user", EACH question MUST carry "Khuyến nghị:" + "Hệ quả nếu chọn sai:" + "Độ tin cậy:" (cao only when you can cite a file, spec, or figure). Never a bare question list.

Return `Report: <absolute path>` as the first line, then the Verdict block. The caller gates on the Verdict; keep it exact.

## Inline mode (autopilot `review.md`, `review-clean.md`)

The autopilot review session has no subagents, may only read (`git diff`, `git log`, `git show`), must not run tests, and must not write anywhere but its attempt's staging. Its result is JSON, not markdown. In that seat:

- Walk the same twelve items and `review-lessons` by reading the diff. Every "Run" item is `not run (inline mode)`; do not invent a result.
- Secret scan is still mandatory, done by reading the diff (the pack scanner may be run if the session's rules allow a read-only script; otherwise read).
- Produce `risk` and `secret_scan` for the `review_report` field exactly as `workflows/autopilot/review.md` specifies; the markdown report and the `plans/` write-up are not produced.
- Risk rules above apply, except the auth/PII raise: put `security-auditor` in the report's notes instead.
- The authoritative contract for that session is `workflows/autopilot/review.md`; this file only supplies the checklist. Where they disagree, `review.md` wins.
