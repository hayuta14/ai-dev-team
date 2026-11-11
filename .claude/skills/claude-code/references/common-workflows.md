# Common Claude Code Workflows

This workspace's commands come from team-ai-pack and are namespaced `/avatar:<name>` (e.g. `/avatar:plan`, `/avatar:implement`, `/avatar:fix`, `/avatar:git:cm`). The live list is `.claude/commands/avatar/`; `/avatar:help` explains each.

## Feature Implementation

**Plan first approach:**
```bash
/plan implement payment integration with Stripe
# Review plan, then proceed with implementation
/avatar:implement implement payment integration with Stripe
```

**Direct implementation:**
```bash
/avatar:implement implement user authentication with JWT
/avatar:implement add dark mode toggle to settings
```

## Bug Fixing

**Quick fixes:**
```bash
/fix:fast login button not working
/fix:types  # Fix TypeScript errors
```

**Complex debugging:**
```bash
/debug API returns 500 errors intermittently
/fix:hard authentication flow breaks after password reset
```

**Test-driven fixes:**
```bash
/fix:test user service tests failing
/test  # Run full test suite
```


## Code Review & Testing

```bash
# Review recent changes
claude "review my latest commit"
claude "analyze the changes in PR #42"

# Run tests
/test
/fix:test payment tests failing
```

## Documentation Management

```bash
/docs:init                    # Create initial docs structure
/docs:update                  # Update all docs based on codebase
/docs:summarize auth security # Focused documentation update
```

## Git Operations

```bash
/git:cm                        # Stage and commit
/git:cp                        # Stage, commit, and push
/git:pr feature-branch main    # Create pull request from feature-branch to main
```

## Design & Content

**UI/UX design:**
```bash
/design:good build immersive dashboard with data viz
/design:screenshot analyze this design and suggest improvements
```

**Content creation:**
```bash
/content:good write product description for new feature
/content:fast create blog post about our API
/content:cro optimize landing page copy for conversions
```

## Project Initialization

```bash
/avatar:new-project create Next.js app with auth and database
/avatar:new-project quick React app with TypeScript
```

## Advanced Workflows

**Codebase analysis:**
```bash
/review:codebase analyze authentication implementation
/scout:ext find all payment-related files
```

**Strategic planning:**
```bash
/avatar:plan:hard implement real-time collaboration features
/avatar:plan:two compare serverless vs traditional backend approaches
/brainstorm improve onboarding UX
```

**Payment integrations:**
```bash
/integrate:sepay add Vietnamese payment gateway
/integrate:polar implement subscription billing
```

**Skill management:**
```bash
/skill:create payment-processing  # Create new skill
/skill:optimize frontend-dev      # Improve existing skill
```
