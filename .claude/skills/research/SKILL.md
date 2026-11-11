---
name: research
description: Use when you need to gather and analyze information from external sources (docs, libraries, web, prior art) to understand options and tradeoffs BEFORE a plan exists. Produces findings and recommendations, not an implementation plan — hand the output to the `planning` skill to turn it into actionable steps. Triggers (VI): "nghiên cứu", "tìm hiểu kỹ".
license: MIT
---

# Research

Inline form of the `researcher` agent (`.claude/agents/researcher.md`): same method, same report layout, so Phase 2 of `/avatar:plan` and the planner read one shape whoever wrote it. Answer specific external questions with cited, dated, version-pinned evidence; say plainly what you could not establish.

## Method

1. **Questions before searches.** Number the questions; for each, write what a sufficient answer looks like (a version, a documented behaviour, a licence, a rule citation). A topic with no answerable question is reported as such, with the questions that would make it answerable. No survey for its own sake.
2. **Pin the stack.** Read the manifest (`package.json`, `deno.json`, `pyproject.toml`) for the versions the project runs. "Latest" is not a version; check `date` before judging recency.
3. **Source hierarchy.** Official docs and changelog of the pinned version > library source or issue tracker > maintainer or vendor blog > talk > community post. Each claim names the tier it rests on.
4. **Search to locate, fetch to verify.** `WebSearch` finds leads; a snippet is not evidence. Every claim cites a page fetched in this session (`WebFetch`, `gh release view` / `gh issue view` / `gh api`), quoted in one or two lines with the URL and the version or date on the page.
   - `docs-seeker` scripts read llms.txt sources from context7: `node .claude/skills/docs-seeker/scripts/fetch-docs.js "How do I use <topic> in <library>?"` or `"documentation for <org>/<repo>"`; other phrasings return not found. The content follows the upstream default branch, so confirm version-specific behaviour against the changelog or versioned docs.
   - A remote repository: `repomix --remote <url> -o $TMPDIR/<name>.xml`, never into the working tree.
   - A page that fails to load is listed as `not fetched (<error>)` and nothing rests on it.
5. **Per-version answers.** Behaviour that changed across versions is reported per version, the project's version first.
6. **Conflicts are findings.** Two sources that disagree are reported with both citations and your reading of which applies.
7. **Budget.** Default 5 searches / 8 fetches, or what the user set; stop there and report partial coverage per question. Run independent fetches in parallel.
8. **No decisions.** Options with trade-offs when asked; the choice belongs to the planner or the user.

Never use an external LLM CLI (`gemini` and the like) as a search backend, even where one is installed: it sends the question and any code to a third party, and its answers carry no fetchable source.

Vietnamese legal or compliance questions (NĐ 13/2023, e-invoice decrees, tax) cite the decree or circular number, article, and effective date from an official or law-aggregator page.

## Report

Write to the path the caller gave; otherwise `<WORKING-DIR>/<active plan>/reports/research-{YYMMDD}-{slug}.md` (`date +%y%m%d`), or `<WORKING-DIR>/plans/reports/` when there is no active plan. Use the layout in `.claude/agents/researcher.md` §Report layout: the YAML summary (role, lens, research_trigger, claims with evidence and confidence, constraints, options, risks, unknowns), then Questions, Findings per question, Conflicts between sources, Options (when asked), Unknowns, Sources.

Write reports to be scanned: short sentences, no filler, but keep every path, number and reason the reader needs to act.
In reports, list unresolved questions at the end — EACH question MUST carry "Khuyến nghị:" + "Hệ quả nếu chọn sai:" + "Độ tin cậy:". Never a bare question list.
