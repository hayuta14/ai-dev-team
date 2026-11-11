# Error Handling & Fallback Strategies

## Error Codes

**404 Not Found**
- Topic-specific URL not available
- Library not on context7.com
- llms.txt doesn't exist

**Network error (`fetch-docs.js` exit 2, `error: "network"`)**
- Timeout (15 s), connection refused, proxy refused, HTTP 5xx
- Docs may still exist — retry / check `HTTPS_PROXY`; do NOT treat as 404

**Timeout**
- Network issues
- Large repository clone
- Slow API response

**Invalid Response**
- Malformed llms.txt
- Empty content
- Invalid URLs

## Fallback Chain

### For Topic-Specific Queries

```
1. Try topic-specific URL
   https://context7.com/{library}/llms.txt?topic={keyword}
   ↓ 404
2. Try general library URL
   https://context7.com/{library}/llms.txt
   ↓ 404
3. WebSearch for llms.txt
   "[library] llms.txt site:[official domain]"
   ↓ Not found
4. Repository analysis
   Use Repomix on GitHub repo
```

### For General Library Queries

```
1. Try context7.com
   https://context7.com/{library}/llms.txt
   ↓ 404
2. WebSearch for llms.txt
   "[library] llms.txt"
   ↓ Not found
3. Repository analysis
   Clone + Repomix
   ↓ No repo
4. Research agents
   Deploy multiple Researcher agents
```

## Timeout Handling

**Set limits:**
- WebFetch: 60s
- Repository clone: 5min
- Repomix: 10min

**Fail fast:** Don't retry failed methods

## Empty Results

**If llms.txt has 0 URLs:**
→ Note in report
→ Try repository analysis
→ Check official website manually
