# Claude Search Optimization (CSO) — Skill Description Principles

Source: github.com/obra/superpowers / writing-skills (MIT). Adapted for Avatar pack.

## The Critical Rule

**`description` = TRIGGERING CONDITIONS only. NEVER summarize the workflow.**

If description summarizes what the skill does, Claude will follow the description instead of reading the skill body.

### Why This Matters (Tested Failure)

A description saying "code review between tasks" caused Claude to do ONE review — even though the skill's body clearly showed TWO reviews (spec compliance + code quality). When changed to just "Use when executing implementation plans with independent tasks" (no workflow summary), Claude correctly read the body and followed the two-stage process.

**The trap:** Description summaries create a shortcut Claude will take. The skill body becomes documentation Claude skips.

## Bad → Good Examples

```yaml
# BAD: summarizes workflow — Claude follows description, skips body
description: Use when executing plans - dispatches subagent per task with code review between tasks

# BAD: too much process detail
description: Use for TDD - write test first, watch it fail, write minimal code, refactor

# GOOD: triggering conditions only, no workflow
description: Use when executing implementation plans with independent tasks in the current session

# GOOD: triggering conditions only
description: Use when implementing any feature or bugfix, before writing implementation code
```

## CSO Checklist

- [ ] Starts with "Use when..." (focuses on triggering conditions)
- [ ] Written in third person (injected into system prompt)
- [ ] Does NOT summarize the skill's process or workflow steps
- [ ] Uses concrete triggers, symptoms, situations
- [ ] Under 500 characters
- [ ] Technology-agnostic unless skill is tech-specific
- [ ] Keywords: error messages, symptoms, tool names

## TDD-for-Skills: Test Description Before Writing Skill

Run a pressure scenario WITHOUT the skill. Document exact rationalizations agent uses. Then write skill to address those specific failures.

**RED:** Agent violates rule without skill (baseline behavior documented)
**GREEN:** Agent complies with skill present
**REFACTOR:** Find new rationalizations → plug loopholes → re-verify

## Taxonomy

| Type | Purpose | Example |
|------|---------|---------|
| **Technique** | Concrete method with steps | `root-cause-tracing`, `condition-based-waiting` |
| **Pattern** | Way of thinking about problems | `flatten-with-flags` |
| **Reference** | API docs, syntax, tool documentation | `pptxgenjs-api-reference` |

## Token Efficiency

Skills load into every conversation — every token counts.

- SKILL.md body: under 100 lines
- References: under 100 lines each (progressive disclosure)
- Use cross-references: `references/heavy-detail.md` — don't repeat inline
- Move heavy reference (100+ lines) to separate file, link from SKILL.md
