# Slash Commands Reference

Comprehensive catalog of Claude Code slash commands for development workflows.

## What Are Slash Commands?

Slash commands are user-defined operations that:
- Start with `/` (e.g., `/avatar:implement`, `/avatar:test`)
- Expand to full prompts when executed
- Accept arguments
- Located in `.claude/commands/`
- Can be project-specific or global

## This Workspace's Commands

This workspace's commands come from team-ai-pack and are namespaced `/avatar:<name>` (e.g. `/avatar:plan`, `/avatar:implement`, `/avatar:fix`, `/avatar:git:cm`). The live list is `.claude/commands/avatar/`; `/avatar:help` explains each.

## Creating Custom Slash Commands

### Command File Structure
```
.claude/commands/
└── my-command.md
```

### Example Command File
```markdown
# File: .claude/commands/my-command.md

Create comprehensive test suite for {{feature}}.

Include:
- Unit tests
- Integration tests
- Edge cases
- Mocking examples
```

### Usage
```bash
/my-command authentication
# Expands to: "Create comprehensive test suite for authentication..."
```

### Best Practices

**Clear prompts**: Write specific, actionable prompts
**Use variables**: `{{variable}}` for dynamic content
**Document usage**: Add comments explaining the command
**Test thoroughly**: Verify commands work as expected

## Command Arguments

### Single Argument
```bash
/avatar:implement implement user auth
# Argument: "implement user auth"
```

### Multiple Arguments
```bash
/git:pr feature-branch main
# Arguments: "feature-branch", "main"
```

### Optional Arguments
Some commands work with or without arguments:
```bash
/test              # Run all tests
/test user.test.js # Run specific test
```

## See Also

- Creating custom commands: `references/hooks-and-plugins.md`
- Command automation: `references/configuration.md`
- Best practices: `references/best-practices.md`
