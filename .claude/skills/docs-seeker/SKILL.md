---
name: docs-seeker
description: "Search technical documentation using executable scripts to detect query type, fetch from llms.txt sources (context7.com), and analyze results. Use when user needs: (1) Topic-specific documentation (features/components/concepts), (2) Library/framework documentation, (3) GitHub repository analysis, (4) Documentation discovery with automated agent distribution strategy" Triggers (VI): "tìm tài liệu", "tra docs".
version: 3.1.0
---

# Documentation Discovery via Scripts

## Overview

**Script-first** documentation discovery using llms.txt standard.

Execute scripts to handle entire workflow - no manual URL construction needed.

## Primary Workflow

**Run the scripts in this order:**

```bash
# 1. DETECT query type (topic-specific vs general)
node scripts/detect-topic.js "<user query>"

# 2. FETCH documentation (prints JSON; llms.txt text is in .content)
node scripts/fetch-docs.js "<user query>" > "$TMPDIR/docs-seeker.json"

# 3. ANALYZE results (if multiple URLs returned)
jq -r .content "$TMPDIR/docs-seeker.json" | node scripts/analyze-llms-txt.js -
```

Scripts handle URL construction, fallback chains, and error handling automatically.

## Scripts

**`detect-topic.js`** - Classify query type
- Identifies topic-specific vs general queries
- Extracts library name + topic phrase (up to 3 words, e.g. `date picker`)
- Returns JSON: `{topic, library, isTopicSpecific}`

**`fetch-docs.js`** - Retrieve documentation
- Constructs context7.com URLs automatically
- Handles fallback: topic → general → error
- Prints JSON `{success, url, content, ...}`; the llms.txt text is in `.content`
- Uses `curl` (15 s timeout, honours `HTTPS_PROXY`/`NO_PROXY`)
- Exit `0` found · `1` every URL returned 404 (genuinely not on context7) · `2` network/timeout/proxy/5xx failure: JSON has `error: "network"` + `message` — that does NOT mean the library lacks llms.txt; fix the network or retry

**`analyze-llms-txt.js`** - Process llms.txt
- Categorizes URLs (critical/important/supplementary)
- Suggests a URL split across agents (`distribution`); treat it as a hint — one reader is usually enough, split only when the URL set is large and the parts are independent
- Returns JSON with strategy

## Workflow References

**[Topic-Specific Search](./workflows/topic-search.md)** - Fastest path (10-15s)

**[General Library Search](./workflows/library-search.md)** - Comprehensive coverage (30-60s)

**[Repository Analysis](./workflows/repo-analysis.md)** - Fallback strategy

## References

**[context7-patterns.md](./references/context7-patterns.md)** - URL patterns, known repositories

**[errors.md](./references/errors.md)** - Error handling, fallback strategies

**[advanced.md](./references/advanced.md)** - Edge cases, versioning, multi-language

## Execution Principles

1. **Scripts first** - Execute scripts instead of manual URL construction
2. **Automatic fallback** - Scripts handle topic → general → error chains
3. **Progressive disclosure** - Load workflows/references only when needed
4. **Agent distribution is a hint** - Spawn extra agents only when the URL set justifies the cost

## Quick Start

**Topic query:** "How do I use date picker in shadcn?"
```bash
node scripts/detect-topic.js "<query>"  # → {topic, library, isTopicSpecific}
node scripts/fetch-docs.js "<query>"    # → 2-3 URLs
# Read URLs with WebFetch
```

**General query:** "Documentation for Next.js"
```bash
node scripts/detect-topic.js "<query>"         # → {isTopicSpecific: false}
node scripts/fetch-docs.js "<query>" > "$TMPDIR/docs-seeker.json"   # → 8+ URLs in .content
jq -r .content "$TMPDIR/docs-seeker.json" | node scripts/analyze-llms-txt.js -  # → {totalUrls, distribution}
# Read the critical URLs; split across agents only if the set is large
```

## Environment

Scripts read `process.env` only — they never open `.env` files. `CONTEXT7_API_KEY` is optional (context7 llms.txt works without a key); to raise rate limits set it in your shell: `export CONTEXT7_API_KEY=...`. `DEBUG=true` enables debug logging.
