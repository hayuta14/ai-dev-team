---
name: verification-before-completion
description: Use before claiming any work is done, fixed, passing, or ready for review - run the command that proves the claim, read its full output, then claim with the evidence attached. Preloaded into fullstack-developer; useful for any agent that reports status. Triggers (VI): "xong rồi", "test pass rồi", "đã sửa".
license: MIT — derived from github.com/obra/superpowers (Jesse Vincent), condensed for team-ai-pack. See LICENSE.txt.
---

# Verification before completion

A claim about the state of the code is worth exactly the evidence attached to it. "Should work", "I'm confident", "the earlier run passed" are not evidence. The failure this skill prevents: an agent reports green, the reviewer or CI finds red, and everyone downstream has built on the report.

## The gate

Before writing "done", "fixed", "passes", "compiles", "ready":

1. **Name the command that proves the claim.** Tests pass ⇒ the test command. Compiles ⇒ the typecheck or build command. Bug fixed ⇒ the reproduction from the bug report, re-run. Regression test added ⇒ the test fails on the old code and passes on the new.
2. **Run it now, in full.** Not a cached result, not a subset you remember passing, not a run from before the last edit. If the last edit touched anything, the previous run is stale.
3. **Read the whole output.** Exit code, failure count, skipped count, warnings that became errors. A green summary line above twenty lines of stack trace is red.
4. **Compare output to claim.** Lint clean does not mean build passes. Unit green does not mean the integration suite ran. One file compiling does not mean the project compiles.
5. **Claim with evidence.** The command, the exit code, the relevant lines. Put it in the report where the reader will look for it.

## What counts

| Claim | Evidence required |
|---|---|
| Tests pass | Full suite command, exit 0, `N passed, 0 failed` line quoted, run after the last edit |
| Type check passes | `tsc --noEmit` / project typecheck script, exit 0 |
| Bug fixed | Original reproduction re-run, symptom gone, quoted |
| Regression test works | Shown red on the old code (stash, worktree, or revert), green on the new |
| File changed as planned | `git diff --stat` of the files, not the memory of editing them |
| Subagent finished X | Its diff and its test output, not its summary |
| Nothing else broke | Full suite, not the one test file you touched |

## Red flags in your own writing

- "should", "probably", "I believe", "looks correct"
- "tests passed earlier"
- "I'll verify after reporting"
- satisfaction before the command finished
- counting on the reviewer to catch it

Any of these ⇒ go back to step 1.

## When verification is impossible

Cannot run the suite (no database, tool missing, CI-only step)? Say exactly that: what you could not run, why, and what you ran instead. "Not verified: integration suite needs `DATABASE_URL`, absent in this environment" is a valid, honest line. "Tests pass" without the run is not.
