---
name: knowledge-extraction
description: Use at the END of a turn to decide whether the turn produced a reusable project lesson worth saving to the team Knowledge Hub. Default is DROP for turns with no lesson. When both hard gates (Reusable + Anchored) pass and the worth-the-shelf-space signal is met, end your reply with one <remember> marker.
---

# Knowledge Extraction — when to print a `<remember>` marker

You have live context for the turn that just happened. Decide if it produced a lesson
worth saving for teammates on this project. **Default: DROP for a turn with no real lesson**
(chit-chat, trivial edits, questions). But when the two hard gates pass, don't second-guess into
silence — a reusable + anchored lesson is worth saving even if it felt routine. Saving pure noise
makes devs turn the feature off; missing real lessons makes the Hub useless. Aim between.

> Editing the filters, types, or marker format here? Condensed copies live in
> `commands/avatar/remember.md` (kept inline so weak models that skip loading this skill
> still emit a valid marker) **and** in the nudge directive
> `tools/team-knowledge/hooks/user-prompt-submit-nudge-remember.js` (`buildDirective()`, which
> reminds Claude to emit a marker every non-trivial turn) — update all three in sync.

## The 2 hard gates + 1 signal — save if BOTH gates pass and the signal is met

**Gate 1 — Reusable** (hard) — a teammate (or you, later) hitting this situation again could
apply it. Not a one-off, not specific to today's single task.

**Gate 2 — Anchored to something concrete** (hard) — `file:line` / function / lib+version for
`gotcha`/`pattern`; a named decision + reason for `decision`; a scope/module + person for
`tribal`. If it anchors to nothing concrete → it's vague → DROP. **These two gates are the
guard against noise — never save something that fails either one.**

**Signal — Worth the shelf space** (soft, met when EITHER holds):
- It took real digging to find out (cost time/struggle), OR contradicts a common assumption
  ("thought X, turned out Y"); OR
- It's a **project-specific convention, setup, config, or environment fact that a teammate
  would trip on** if they didn't know it — even if it feels routine to you now.

Do NOT save pure common knowledge that is true everywhere ("use try/catch", "write tests",
"run npm install") — that has no shelf value. But a setup gotcha specific to THIS project
(a required env var, a build quirk, a non-obvious command) DOES pass the signal.

## The 4 types
`gotcha` (hard trap/bug) · `decision` (technical decision + why) · `pattern` (project code
convention) · `tribal` (who-knows-what / module ownership). Anything else = noise → drop.

## How to save — print exactly ONE marker

If and only if the turn passes both gates + the signal, end your reply with a single marker on its own line, at the
very end of the reply, NOT inside a code block. The literal form is (shown here as inline code — emit it as plain text, not fenced):

`<remember>{"type":"gotcha","title":"short title","summary":"1-2 sentence lesson","code_refs":[{"path":"src/x.ts","line":142}]}</remember>`

Rules: valid JSON between the tags, escape quotes/newlines, one marker per turn,
`type`+`title`+`summary` required, `code_refs` optional. Do not announce it; just print it.
A `Stop` hook captures it.

## Examples

**SAVE:**
- Spent an hour finding the payment service stored local time → fix is force-UTC at
  `payment.service.ts:142` → `gotcha` (dug hard, anchored, reusable).
- `supabase storage cp` no-ops with the new `sb_secret_` key format; must promote via dashboard
  → `gotcha` (project-specific setup fact, anchored to a tool+version, reusable).
- This repo requires `AVATAR_KH_ENABLED=1` in workspace settings or the KH hook silently no-ops
  → `pattern` (config a teammate WOULD trip on, anchored to the env var, reusable).

**DROP:**
- "ran npm install", "renamed a variable", "the test passed" → no anchor, no shelf value.
- "use try/catch around fetch" → common knowledge true everywhere, not project-specific.
- "the `/login` route is at `routes/login.ts`" → anchored but trivially discoverable, not a lesson.

Border rule: a setup/config fact SAVES only when it's **specific to this project AND non-obvious**
(you'd trip without it). A generic best practice, or a fact one grep would reveal, still DROPS.
