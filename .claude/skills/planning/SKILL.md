---
name: planning
description: Use when you need to turn already-gathered information into a concrete, actionable implementation plan with phases and TODO tasks. Focuses on solution design, sequencing, and tradeoff decisions — NOT on gathering external information first (for that, use the `research` skill, then feed its findings here). Triggers (VI): "lên kế hoạch", "lập plan", "lên phương án".
license: MIT
---

# Planning

Create detailed technical implementation plans through research, codebase analysis, solution design, and comprehensive documentation.

> **Domain context:** if `CONTEXT.md` exists at the repo root (or per-context root), read it first for the project's ubiquitous language, and check `docs/adr/` for decisions in the area you're touching — use those terms in the plan. A decision the plan settles between real alternatives that will outlive the plan (framework, schema shape, API contract, auth model) gets an ADR through the `architecture-decision-records` skill, drafted for the user to approve; list it in the plan's deferred items if nobody approves it yet.

## When to Use

Use this skill when:
- Planning new feature implementations
- Architecting system designs
- Evaluating technical approaches
- Creating implementation roadmaps
- Breaking down complex requirements
- Assessing technical trade-offs

## Core Responsibilities & Rules

Always honoring **YAGNI**, **KISS**, and **DRY** principles.

### 1. Research & Analysis
Load: `references/research-phase.md`
**Skip if:** Provided with researcher reports

### 2. Codebase Understanding
Load: `references/codebase-understanding.md`
**Skip if:** Provided with scout reports

### 3. Solution Design
Load: `references/solution-design.md`

### 4. Plan Creation & Organization
Load: `references/plan-organization.md`

### 5. Task Breakdown & Output Standards
Load: `references/output-standards.md`

### 6. Planning Council Protocol (GĐ1)
Load: `references/planning-council-protocol.md`, `references/shared-understanding-contract.md`, `references/functional-review-checklist.md`

**Nguyên tắc GĐ1:**
- Skill này **CONSUME** confirmed Shared Understanding làm **immutable intent** — không sửa SU khi tạo plan.
- **Tách discovery / solution**: discovery (Scout/Researcher) ra evidence; solution (Planner) ra plan. Không trộn.
- **Reopen-on-drift**: nếu SU status = DRIFTED thì **DỪNG**, không dùng SU làm nguồn authoritative cho tới khi challenge/confirm lại.

## Workflow Process

1. **Initial Analysis** → Read codebase docs, understand context
2. **Research Phase** → Spawn researchers, investigate approaches (only when this skill runs inline in the main session; the `planner` agent spawns nothing, its evidence comes from the brief)
3. **Synthesis** → Analyze reports, identify optimal solution
4. **Design Phase** → Create architecture, implementation design
5. **Plan Documentation** → Write comprehensive plan
6. **Review & Refine** → Ensure completeness, clarity, actionability

## Output Requirements

- DO NOT implement code - only create plans
- Respond with plan file path and summary
- Ensure self-contained plans with necessary context
- Include code snippets/pseudocode when clarifying
- Provide multiple options with trade-offs when appropriate

**Plan Directory Structure**
```
plans/
└── YYYYMMDD-HHmm-plan-name/
    ├── research/
    │   ├── researcher-XX-report.md
    │   └── ...
    ├── reports/
    │   ├── XX-report.md
    │   └── ...
    ├── scout/
    │   ├── scout-XX-report.md
    │   └── ...
    ├── plan.md
    ├── phase-XX-phase-name-here.md
    └── ...
```

## Active Plan State

Active-plan file, report location and naming: `references/plan-organization.md` §Active Plan State Tracking.

## Quality Standards

A plan is done when an engineer with no context can execute it: exact files, interfaces, how each acceptance criterion is verified, checked against existing patterns, security and performance risks named.
