---
name: ba-framing
description: Frame a problem the BABOK way before proposing any solution. Use at the start of brainstorming, architecture debates, or any "should we build X" question. Skip for small, purely technical tasks (pick a library, refactor one module).
---

# BA Framing (distilled from BABOK v3)

Purpose: stop solving the wrong problem. Most bad architecture decisions come from accepting the user's framing as the problem, not from picking the wrong technology. Complete this framing before listing approaches. Keep it short: a few lines per item, not an essay.

## 0. Gate

Run the full framing when the task is a feature, a product direction, a migration, a "should we", or anything whose cost of being wrong is more than a day of work. For small technical tasks, write one line ("Framing skipped: narrow technical choice, need and value are obvious") and move on.

## 1. Separate the need from the presumed solution (BABOK 6.1.4)

Users almost always state a need together with a solution they already have in mind ("add real-time notifications", "migrate to GraphQL"). Split them:

- Need: the problem or opportunity, stated from the perspective of the business or product, not of one stakeholder.
- Presumed solution: what the user actually asked for.
- Trigger: what happened that made this come up now (customer complaint, lost revenue, scaling pain, competitor move, a hunch).

Then ask "why" at least twice on the need. If the task is phrased as "fix X" or "X is slow", run a root cause pass (10.40): symptom, probable causes, which cause the evidence supports. Do not propose a fix for a symptom.

## 2. Core Concept Model (BABOK 2.1)

Fill all six. If one cannot be filled, it is an assumption to state or a question to ask.

| Concept | Answer for this task |
|---|---|
| Need | the problem or opportunity (from step 1) |
| Change | what would actually have to be different in the system, process, or team |
| Solution | the candidate ways to satisfy the need (filled later, in the approaches section) |
| Stakeholder | who is affected: end users, developers, operations, the business, external parties. Name them, not "users" |
| Value | how success is measured; a number or an observable outcome, not "better UX" |
| Context | constraints that shape the option space: existing stack, team size and skills, budget, timeline, policies, regulations, data volume |

## 3. Current state and future state (BABOK 6.1, 6.2)

- Current state: what exists now and what specifically is wrong with it. Include the cost of doing nothing. Read the codebase for this; do not guess.
- Future state: the outcome in one or two sentences, with at least one SMART objective (specific, measurable, achievable, relevant, time-bounded). "Notifications arrive within 2s for 99% of events" beats "real-time notifications".
- Scope of solution space: say explicitly what kinds of changes are on the table (code only, infra, process, buy vs build) and what is out of scope.
- Assumptions (6.2.4.10): list every assumption the strategy depends on, and what happens if it is false.

## 4. Classify what you know (BABOK 2.3)

Sort the stated requirements into:

- Business: why the change is wanted (goals, outcomes).
- Stakeholder: what each stakeholder group needs from it.
- Solution, functional: what the system must do.
- Solution, non-functional: performance, reliability, security, cost, operability. Run NFR analysis (10.30) here; this is where most "it worked in the demo" failures hide.
- Transition: temporary needs during rollout (data migration, dual-running, training, feature flags).

An empty category is a finding. Report it as a gap.

## 5. Evaluate options against value, not against taste (BABOK 7.6)

For each approach, fill the same grid so options are comparable:

- Expected benefits: value delivered, risk reduced, experience improved.
- Expected costs: build effort, timeline, operating cost, maintenance, cognitive load on the team, and opportunity cost (what the best alternative would have delivered instead).
- Risks (6.3): consequence, impact, likelihood, when it could hit. Note which risks you would accept and which need mitigation.
- Dependencies and constraints that favour or kill the option.

Include "do nothing" or "smallest possible change" as a real option whenever the need allows it. BABOK is explicit that doing nothing can be the best recommendation.

Recommend the option with the best net value for the enterprise as a whole, not for the loudest stakeholder. Say what evidence would change the recommendation.

## 6. Output of this framing

Write the framing as the first section of the brainstorm report, under "Problem framing". It should let a reader who has not seen the request understand the need, the measure of success, and the boundaries before reading any approach. If framing surfaced a question that changes the recommendation, put it in "Questions for the user" with its impact.
