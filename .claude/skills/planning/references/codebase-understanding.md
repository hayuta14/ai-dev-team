# Codebase Understanding Phase

**When to skip:** If provided with scout reports, skip this phase.

## Core Activities

### Parallel Scout Agents
- Use `/avatar:scout`, or spawn the `scout` agent directly with `WS`, `TASK`, `REPOS`, `SCOPE`, `QUESTIONS`, `OUTPUT_PATH`, `PROFILE: quick` (contract in `agents/scout.md`)
- Each scout covers one directory set (`SCOPE`) and writes its own report
- Wait for all scout agents to report back before analysis
- Efficient for finding relevant code across large codebases

### Essential Documentation Review
Read the target repo's `docs/` if present (e.g. `code-standards.md`, `system-architecture.md`, `design-guidelines.md`) and its README. Team dev rules are already loaded from `.claude/workflows/development-rules.md`.

### Environment Analysis
- Review development environment setup
- Analyze configuration (env variable names from code and `.env.example`; `.env*` reads are denied)
- Identify required dependencies
- Understand build and deployment processes

### Pattern Recognition
- Study existing patterns in codebase
- Identify conventions and architectural decisions
- Note consistency in implementation approaches
- Understand error handling patterns

### Integration Planning
- Identify how new features integrate with existing architecture
- Map dependencies between components
- Understand data flow and state management
- Consider backward compatibility

## Best Practices

- Start with documentation before diving into code
- Use scouts for targeted file discovery
- Document patterns found for consistency
- Note any inconsistencies or technical debt
- Consider impact on existing features
