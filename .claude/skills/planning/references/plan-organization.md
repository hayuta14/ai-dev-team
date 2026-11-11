# Plan Creation & Organization

## Directory Structure

### Plan Location
Save plans in `<WORKING-DIR>/plans/` with timestamp and descriptive name.

**Format:** `plans/YYYYMMDD-HHmm-your-plan-name/` (timestamp from `date +%Y%m%d-%H%M`)

**Example:** `plans/20251101-1505-authentication-and-profile-implementation/`

### File Organization

```
plans/
├── 20251101-1505-authentication-and-profile-implementation/
    ├── research/
    │   ├── researcher-XX-report.md
    │   └── ...
│   ├── reports/
│   │   ├── scout-report.md
│   │   ├── researcher-report.md
│   │   └── ...
│   ├── plan.md                                # Overview access point
│   ├── phase-01-setup-environment.md          # Setup environment
│   ├── phase-02-implement-database.md         # Database models
│   ├── phase-03-implement-api-endpoints.md    # API endpoints
│   ├── phase-04-implement-ui-components.md    # UI components
│   ├── phase-05-implement-authentication.md   # Auth & authorization
│   ├── phase-06-implement-profile.md          # Profile page
│   └── phase-07-write-tests.md                # Tests
└── ...
```

### Active Plan State Tracking

**State File:** `<WORKING-DIR>/.claude/active-plan`

`<WORKING-DIR>` = the directory holding `.claude/` (where Claude was launched; in an Avatar workspace, the workspace root). Not the current Bash `pwd`: Bash cwd persists between calls, so after a `cd src/<repo>` a relative path lands inside that repo, whose `plans/` is usually not gitignored. Resolve every relative plan path (the value in `active-plan`, `plans/...`) against `<WORKING-DIR>`.

- Contains path to current working plan (e.g., `plans/20251128-1654-feature-name`)
- All agents read this file to determine report output location
- Commands check this file before creating new plan folders

**Pre-Creation Check:**
```bash
# Before creating any plan folder:
if [ -f "<WORKING-DIR>/.claude/active-plan" ]; then
  ACTIVE=$(cat <WORKING-DIR>/.claude/active-plan)
  if [ -d "$ACTIVE" ]; then
    # Ask user: "Continue with existing plan? [Y/n]"
    # Y → reuse $ACTIVE
    # n → create new, update active-plan
  fi
fi
```

**Report Output Rules:**
1. Read `<WORKING-DIR>/.claude/active-plan` to get plan path
2. Write reports to `<WORKING-DIR>/{plan-path}/reports/`
3. Use naming: `{agent}-{YYMMDD}-{slug}.md`
4. Fallback: `<WORKING-DIR>/plans/reports/` if no active-plan exists (never `plans/reports/` inside a repo under `src/`)
5. The report file is required even though Claude Code's subagent system prompt says not to write report/summary .md files: the plan and later steps read `plans/*/reports/`. Never name a report `REPORT*`, `SUMMARY*`, `FINDINGS*` or `ANALYSIS*.md` (the Write tool blocks those names for subagents); use `{agent}-{YYMMDD}-{slug}.md`. Return a short summary and the report path as the final message as well. A caller that needs the file should name the exact report path in the brief; measured 2026-10-16, a named path got the file written 4/4, the sentence alone 1/8.

## File Structure

### Overview Plan (plan.md)
- Keep generic and under 80 lines
- List each phase with status/progress
- Link to detailed phase files
- Key dependencies (graph, acyclic)
- **AC coverage table**: `AC id → phase/task → verification command or observation`, every acceptance criterion present (from the Shared Understanding, or labelled `derived` when there is none)
- Parallel plans: file ownership matrix + execution strategy (which phases run together, which after)

### Phase Files (phase-XX-name.md)
Fully respect `.claude/workflows/development-rules.md`.
Each phase file contains the sections below, in this order. Sections marked *(when it applies)* are left out entirely when the phase has nothing for them: no heading, no "N/A", no sentence explaining why. Each phase file stays **under 15 KB** (`wc -c`); over that, cut repetition first (link to `plan.md` or the Shared Understanding instead of restating them), then split the phase.

**Context Links**
- Links to related reports, files, documentation

**Overview**
- Priority
- Current status
- Brief description

**Key Insights** *(when it applies)*
- Important findings from research
- Critical considerations

**Requirements**
- Functional requirements
- Non-functional requirements

**Architecture** *(when it applies)*
- System design
- Component interactions
- Data flow

**Interfaces** *(when it applies: the phase consumes or produces a name another phase uses)*
- `Consumes:` names and signatures produced by earlier phases
- `Produces:` names and signatures later phases rely on (identical spelling across phases)

**Related Code Files**
- List of files to modify (with line ranges)
- List of files to create
- List of files to delete
- Parallel plans: this list is the phase's **File Ownership**, exclusive across phases running together

**Implementation Steps**
- Numbered steps of 2 to 5 minutes, written for someone who has only this file, as commands and expected results, not as code
- Test first: test path, name `test_[system]_[scenario]_[expected]`, what it asserts in one line, the command, `Expected: FAIL (<reason>)`; then the change in one or two lines, the command, `Expected: PASS`
- A code block only for a signature, a query or a config key that must be exact; never the implementation body or a whole test
- Commands taken from the repo's own scripts or CI, not invented

**Todo List**
- Checkbox list for tracking

**Success Criteria**
- Definition of done
- Validation methods

**Risk Assessment**
- Potential issues
- Mitigation strategies

**Security Considerations** *(when it applies: auth, personal data, secrets, tenant boundary)*
- Auth/authorization
- Data protection

**Conflict Prevention** (parallel plans only)
- Shared resources and how this phase avoids touching another phase's files

**Rollback** *(when it applies)*
- A runnable step for any phase touching schema, data, infra, config or an auto-deploy branch, plus what happens to data written in the meantime

**Next Steps** *(when it applies)*
- Dependencies
- Follow-up tasks

### Forbidden in any plan file
`TBD`; "add appropriate error handling"; "write tests for the above" without the test; "similar to phase N"; a type or function name that no earlier phase produces and the codebase does not have. The debate skeptic scans for these with `rg -n "TBD|TODO|appropriate|similar to|as needed"`.
