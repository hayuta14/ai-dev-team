---
name: review-lessons
description: Team-specific checklist of defect classes that have slipped past review in this workspace (avatar-cli, team-ai-pack, telemetry, avatar-supabase). Preloaded into code-reviewer; each line names the pattern, how to check for it, and the report or ticket it came from. Add a line whenever a bug that review should have caught reaches main.
---

# Review lessons

Each item is a defect class that was found late (by a second reviewer, a dogfood run, or in production) in this team's code. Generic review knowledge will not catch these; a line here will. Check every item against the diff. Cite the item id in a finding when it matches.

Format of an item: **id. pattern**. How to check. Source.

## Tests that cannot fail (xanh giả)

- **T1. Test fixtures all share one shape, so the bug lives in the shape nobody built.** Read the fixture helper, not only the asserts: if every transcript line has one `tool_use`, every path is spelled the same way, every input is well-formed, the test is blind to multi-tool lines, `./x` vs `x`, and malformed input. Ask: which input shape would make this fail, and is it present? Source: `fix-resolveslug-multirepo` (one tool_use per line), `ticket-283` NIT-6 (identical paths hide a cache miss).
- **T2. Test still green after the code under test is deleted or reverted.** For any fix, ask for a negative control: the new test must be red on the old code. If the report cannot show that, treat the test as a shape guard, not a regression guard. Source: `ticket-283` "xanh giả" table, README v1.1.64 (mutation controls, `ast.parse` before trusting a red).
- **T3. Test file in a directory no CI job runs.** Before counting a new test as coverage, open the CI config (`.gitlab-ci.yml` for the pack) and confirm a job's `pytest`/`node --test` path list actually includes that directory; path lists change (`tools/` was added in `#287`), so never rely on a remembered list. Source: README v1.1.64 (`#257`, `#263`).
- **T4. Assertion that is vacuous for an empty collection.** A `for item in cases: assert ...` with zero cases passes. Require `assert len(cases) > 0` or an equivalent guard, and check that the collection is not derived from the thing it is supposed to verify. Source: `ticket-189` (`COVERAGE_CASES` guard, frozen out-of-scope list).
- **T5. Policy not pinned.** When behaviour on an edge (resolve fails, input unparseable) is a deliberate choice, there must be a test that states it. Without one, the next change can flip it silently. Source: `ticket-283` ("hint có mà resolve trượt" had no test either way).
- **T6. `it.each` with interpolated names under vitest 4.1.x truncates the case name.** Prefer a `for` loop that calls `it(...)` per case. Source: `ticket-189`, memory `vitest-each-truncate-ten-ca-noi-suy`.

## Silent wrong answers

- **S1. Fallback to a plausible-but-wrong value instead of a visible null.** Resolve fails and the code "borrows" `cwd`, a default label, a previous value. Prefer `None`/`null` that shows up in data over a wrong label that does not. Check every `for ... else`, `or default`, `except: return <something>` on a labelling path. Source: `ticket-283` MAJOR-1, MINOR-3.
- **S2. Docstring or comment states a policy the code does not implement.** Read the docstring, then trace the code path for the case it describes. Source: `ticket-283` (`_duong_dan_ung_vien`: "drop the hint" documented, "fall back to cwd" implemented).
- **S3. Two parallel branches with asymmetric handling.** The `git` branch strips `sudo`/`env`/`VAR=` wrappers and the `gh`/`glab` branch does not; `_next_cwd` expands `~` and blocks `$`, the hint path does neither. When a diff adds a second branch next to an existing one, diff the two branches against each other. Source: `ticket-283` MAJOR-2, NIT-7.
- **S4. Mirrored implementations drift (js / cjs / sh / ps1).** When one file in a mirrored set changes, check every sibling; `.ps1` has no automated verification, so diff it by hand. Source: `improve-scout-block-false-positive` D3.
- **S5. Tool name drift in hooks and matchers.** Claude Code emits `Agent`; `Task` is the old name. Any `ENFORCED_TOOLS`, matcher, or allowlist that names tools must carry both. Grep the pack for the old name when a hook changes. Source: README v1.1.64 (`#285`, gate allowed silently).
- **S6. `json.loads` on a line without `.strip()`, or a "corrupt line" counter that treats whitespace as corruption.** Check line parsers for leading/trailing whitespace and for the `errors="replace"` path. Source: `ticket-207`.

## Guards and regexes

- **G1. Verb-boundary regex bypassed by shell syntax.** `{ cmd; }`, `$(cmd)`, backticks, `FOO=bar cmd`, `sudo cmd` all slip past a `^cmd` or `\bcmd` anchor. For any command guard, run the bypass set by hand. Source: `improve-scout-block-false-positive` H1.
- **G2. Comment or quote stripping without the multiline flag.** A sanitiser that works on one line and leaves `# comment\ncmd` intact. Test with a two-line input. Source: `improve-scout-block-false-positive` M1.
- **G3. Error-pattern match not anchored to line start.** `error:` appears inside commit messages echoed in output; anchor with `^` (multiline) when scanning output for failure. Source: README v1.1.64 (`#282`).
- **G4. Allowlist is shallow.** Top-level keys are filtered, nested blobs (`agents`, `gates`) pass through untouched. Ask what stops a nested `prompt` or secret from reaching disk. Source: `plan-monitor-council-gd1` M2.
- **G5. Unbounded loop over attacker- or input-controlled count that spawns a subprocess per iteration.** Cap it. Measure one iteration's cost and multiply by the realistic max. Source: `ticket-283` MINOR-5 (4001 resolver calls, ~48 s).
- **G6. Fail-open vs fail-closed not stated.** Every hook or gate must say which it is and have a test for the failure path (module missing, exception, bad return type). Source: `ticket-283` fail-open review, `ticket-207` `read_health`.

## State, files, concurrency

- **C1. Atomic write with a fixed temp name.** `path + ".tmp"` then `os.replace` is atomic for readers but two writers truncate each other's tmp. Temp name must include the PID or be unique. Source: README v1.1.64 (`#216` follow-up, 14% torn reads under contention).
- **C2. Read-modify-write without a lock on shared state.** `read_state(); update; os.replace` loses the other writer's update. If more than one process can write the same file, reuse `tools/debate-review/lib/debate-state-store.py`'s locked helper. Source: `plan-monitor-council-gd1` M1.
- **C3. Leftover environment variable from a manual test run changes a later `npm test` in the same shell.** Any test that honours an override env var should warn when it is set. Source: `ticket-189` R1.
- **C4. Path built from the hook process's cwd instead of the session's cwd.** Hook paths must be absolute (`${CLAUDE_PROJECT_DIR}/...`); a relative hint resolved in the hook process is non-reproducible. Source: `ticket-283` MINOR-3, orientation "Bất biến".

## Conventions this team enforces

- **V1. Hook scripts must run on Python 3.9.** No PEP 604 unions (`X | Y`) in annotations, no walrus, no `match`. Check with `/usr/bin/python3 -m ast` or `ast.parse` under 3.9. Source: `ticket-283` review, CI `py39-hook-smoke`.
- **V2. 200-line cap per code file.** Report files at or near the cap (a file at 198 lines will break on the next edit). Source: `development-rules.md`, `ticket-283` (`payload` at 198).
- **V3. Untracked files are dropped by the clean-clone tarball build.** A new file that is not `git add`ed never ships. Check `git status` for untracked files the diff depends on. Source: orientation "commit MỌI file trước khi build".
- **V4. CHANGELOG, README inventory counts, `docs/*.html` counts go stale.** When a diff adds or removes a skill, command, agent, tool, or hook, the counts in `README.md`, `skills/README.md`, `docs/*.html` must move too. Source: `ticket-189` R3, README v1.1.68.
- **V5. Changing a subagent definition does not need a CLI release; changing `settings.json.tpl` does not reach existing workspaces.** When a fix lives in the template, say so in the report so the author adds the manual migration note. Source: `settings.json.tpl` `_comment_env`, README v1.2.8.

- **V6. Example commands in SKILL.md and docstrings are not tested and can be wrong.** Run a command before copying it into an agent or skill, and run the agent's commands once before shipping the agent. Case: `xargs python3 ... --stdin-files` (fails: `--stdin-files` reads stdin, `xargs` passes paths as arguments) sat in the security-scanner and type-safety-check SKILL.md files and the type-safety script docstring, was copied into a new agent from there, and was caught only by a reviewer running it; fixed 2026-10-15. Related traps in this workspace: `$CLAUDE_PROJECT_DIR` is set only for hooks and is empty in the Bash tool; Bash cwd persists between calls so `$PWD` is unreliable; `Bash(grep:*)` is denied and a denied segment fails the whole pipe, use `rg`. Source: code-reviewer reviews, 2026-10-15.
- **V7. Claude Code's subagent system prompt says "Do NOT write report/summary/findings/analysis .md files" and the Write tool blocks `REPORT*|SUMMARY*|FINDINGS*|ANALYSIS*.md` for subagents.** A "the report file is required" sentence alone does not beat the harness: added to the trailing Report Output block of 8 older agents, only 1 of 8 wrote its report (2026-10-16, Claude Code 2.1.296). What worked: the report as a numbered Process step plus a final message that returns the report path (rewritten agents; database-optimizer 3/3), or the caller naming the exact report path in the brief (4/4). When a review touches an agent that must leave a file, check for one of those two. Source: reviewer spawn tests 2026-10-15/16.
- **V8. `Grep`/`Glob` may not exist as tools in the subagent (absent on Claude Code 2.1.296; subagent got "No such tool" and fell back to `find`).** Listing them in `tools:` is harmless (unresolved entries are ignored while at least one resolves), but any instruction that says "use Grep/Glob" must name the Bash fallback (`rg`, `find`), and in a guarded session that fallback must be on the read-only allowlist. Source: debate-refiner spawn test, 2026-10-16.

## Maintaining this list

- Add a line when a bug reaches `main` that a reviewer should have caught. One line: pattern, how to check, source. No essays.
- Remove a line when a lint rule, a test gate, or a CI job now catches the class automatically; note the replacement in the commit.
- Keep the file under 120 lines. If it grows past that, merge items by class rather than appending.
