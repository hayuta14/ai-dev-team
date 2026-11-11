# Research & Analysis Phase

**When to skip:** If provided with researcher reports, skip this phase. The `planner` agent always skips it: in the council flow Phase 1 gathers evidence, and the agent does not spawn subagents.

## Core Activities

Everything below is for the main session running this skill inline; the `researcher` agent itself spawns nothing and only answers the questions it is given.

### Parallel Researcher Agents
- Spawn multiple `researcher` agents in parallel to investigate different approaches; pass each one numbered `QUESTIONS`, a `LENS`, `STACK` (manifest path), an absolute `OUTPUT_PATH`, `BUDGET` and `WS` (`.claude/agents/researcher.md` §Input contract). No answerable question ⇒ do not spawn
- Wait for all researcher agents to report back before proceeding
- Each researcher investigates a specific aspect or approach

### Documentation Research
- Use `docs-seeker` skill to read and understand documentation
- Research plugins, packages, and frameworks
- Find latest technical documentation using llms.txt standard

### GitHub Analysis
- Use `gh` command to read and analyze:
  - GitHub Actions logs
  - Pull requests
  - Issues and discussions
- Extract relevant technical context from GitHub resources

### Remote Repository Analysis
When given GitHub repository URL, generate fresh codebase summary:
```bash
# usage (always -o: without it repomix writes repomix-output.xml into the cwd, i.e. a repo):
repomix --remote <github-repo-url> -o "$TMPDIR/<name>.xml"
# example:
repomix --remote https://github.com/mrgoonie/human-mcp -o "$TMPDIR/human-mcp.xml"
```

### Debugger Delegation
- Delegate to `debugger` agent for root cause analysis
- Use when investigating complex issues or bugs
- Debugger agent specializes in diagnostic tasks

## Best Practices

- Research breadth before depth
- Document findings for synthesis phase
- Identify multiple approaches for comparison
- Consider edge cases during research
- Note security implications early
