---
name: code-review
description: Use for every side of a code review - requesting one (dispatch code-reviewer with a git range and plan, then gate on its Verdict), performing one (the code-reviewer subagent, or a session reviewing inline where subagents cannot be spawned), receiving feedback with technical rigor over performative agreement, and verification gates requiring evidence before any status claim. Essential for subagent-driven development, /avatar:implement Step 4, PRs, and preventing false completion claims. For an automated risk-scored PR gate with call-graph impact analysis use `pr-gatekeeper-local` instead. Triggers (VI): "review code", "soi lại code", "kiểm tra code".
---

# Code Review

One contract, four seats. The requester and the reviewer must agree on the brief going in and the Verdict coming out; the other two practices keep both honest.

## Core principle

YAGNI, KISS, DRY. Technical correctness over social comfort. Verify before implementing. Ask before assuming. Evidence before claims. Be direct and concise.

## Which reference to read

```
WHO ARE YOU RIGHT NOW?
│
├─ About to ask for a review (task done, phase done, before merge)
│  → references/requesting-code-review.md
│
├─ The reviewer (code-reviewer subagent, or autopilot review session inline)
│  → references/performing-code-review.md  (inline: its "Inline mode" section + workflows/autopilot/review.md)
│
├─ Holding review feedback and deciding what to do with it
│  ├─ Unclear items? → STOP, ask first
│  └─ → references/code-review-reception.md
│
└─ About to say "done", "passes", "fixed", or commit / push / PR
   ├─ Fresh command output in hand? → claim WITH the evidence
   └─ No? → references/verification-before-completion.md, run it first
```

Read only the reference for your seat. Each is self-contained.

## The contract in one screen

**Requester sends** (see requesting-code-review.md):
```
WHAT_WAS_IMPLEMENTED, PLAN (path), BASE_SHA, HEAD_SHA, FOCUS (optional), SECURITY_AUDIT (report path | none)
```
Range via `git merge-base origin/main HEAD`, not `HEAD~1`. Dispatch with the `Agent` tool, `subagent_type: code-reviewer`. No session history, no pre-stated verdict.

**Reviewer returns** (see performing-code-review.md):
```
## Verdict
- Critical issues: <n>
- Risk: low | medium | high | critical
- Secret scan: clean | FOUND
- Typecheck / Lint / Build / Tests: pass | fail | not run (<why>)
- Handoffs: none | security-auditor | performance-engineer | qa-reviewer
- Plan tasks: <done>/<total>, missing: <list>
```
plus findings by severity (Critical / High / Medium / Low), Tech debt, Declined to judge, and questions each carrying "Khuyến nghị:" + "Hệ quả nếu chọn sai:" + "Độ tin cậy:".

**Requester gates on**: Critical = 0 and Risk not high/critical before proceeding; every "not run" re-run by hand; every Handoff dispatched; every "Declined to judge" line ruled on; plan status updated by `project-manager`, never by the reviewer.

One severity vocabulary everywhere: **Critical / High / Medium / Low** for findings, **low / medium / high / critical** for Risk. `/avatar:implement` gates on Critical = 0; autopilot `review.md` gates on Risk.

## Receiving feedback (summary)

READ → UNDERSTAND → VERIFY → EVALUATE → RESPOND → IMPLEMENT. No "You're absolutely right!", no implementing before verifying, one item at a time with a test each. Human partner: trusted, implement after understanding. External or agent reviewer: verify technically, check for breakage, push back with evidence when wrong. YAGNI check before adding any "proper" feature a reviewer suggests.

## Verification gate (summary)

**NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.** Identify the command that proves the claim, run it in full, read the output, confirm it supports the claim, then claim with the evidence attached. "Should pass", a previous run, a green badge, or an agent's "success" is not evidence. This binds the reviewer's Verdict numbers and the requester's "done" equally.

## Integration with workflows

- **`/avatar:implement` Step 4**: reviewer mandatory; Critical must be 0 before Step 5. Fixes are made by the session or `fullstack-developer`, never by the reviewer.
- **Autopilot `review.md` / `review-clean.md`**: no subagents, no test runs, JSON `review_report` instead of a markdown Verdict. The session uses the checklist from `performing-code-review.md` (section "Inline mode") and the contract from `workflows/autopilot/review.md`; `review.md` wins on any conflict.
- **Subagent-driven development**: review after each task, fix, then the next task.
- **Pull requests**: verify tests pass, request review before merge; `pr-gatekeeper-local` runs alongside for risk scoring, it does not replace this review.

## Bottom line

1. One brief in, one Verdict out, same vocabulary on both sides.
2. The reviewer reads and runs; it never edits code or the plan.
3. Evidence before claims, for everyone.
