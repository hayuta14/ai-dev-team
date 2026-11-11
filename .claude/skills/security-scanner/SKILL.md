---
name: security-scanner
description: Use when code changes touch authentication, payment processing, user input handling, or before merging PRs in security-sensitive areas. Scans for OWASP Top 10 patterns (injection, broken auth, sensitive data exposure, XSS, etc.) plus NAL-specific rules (hardcoded credentials, .env leaks, exposed API keys). Returns ranked findings with file:line locations and remediation suggestions. Triggers on "security scan", "kiểm tra bảo mật", "audit auth code", or before payment/auth PR commands.
---

# Security Scanner

## Overview

Static analysis pass for code touching auth, payment, user input, or sensitive data. Detects OWASP Top 10 patterns + credential leaks. Reports findings by severity with concrete remediation suggestions.

**Announce at start:** "I'm using the security-scanner skill to scan for vulnerabilities."

## When to Activate

**Activate when:**
- Code changes touch auth, login, password, session, JWT, OAuth
- Code changes touch payment, billing, vendor payout, refund
- Code handles user input (forms, query params, file upload)
- User explicitly says "security scan", "kiểm tra bảo mật", "audit"
- Before `/avatar:git:pr` on sensitive branches

**Do NOT activate when:**
- Pure UI changes with no data flow
- Documentation-only changes
- Already covered by recent scan (within session)

## What This Skill Detects

The script is a line-by-line regex pass: it only sees one line at a time (a
multi-line SQL template or cookie options object is not matched) and it cannot
judge data flow. Everything below is what the script really checks; logic and
design flaws (missing authorization, rate limits, CSRF, mass assignment) need
the `security-auditor` agent.

**Files scanned:** code only — `.js .jsx .ts .tsx .cjs .mjs .py .rb .go .java .php .cs .sh .bash .yml .yaml .sql`.
Docs and data (`.md`, `.html`, `.json`, `.tpl`) are skipped so SQL or key examples
in docs do not become CRITICAL. Secret files (`.env*`, `.envrc`, `secrets.json/.yaml/.yml`)
are flagged by file name regardless of extension. Findings inside line comments are skipped.

### CRITICAL (block merge)

| Pattern | Risk | Example |
|---|---|---|
| Hardcoded credential assignment | Credential leak | `apiKey = "…"` (quoted literal, 8+ chars) |
| Exposed API key (`sk_`/`pk_`/`nal_` + `live_`/`test_`) | Credential leak | `"sk_live_..."` |
| Exposed AWS access key ID | Credential leak | `"AKIA..."` (20 chars) |
| Exposed GitHub token | Credential leak | `"ghp_..."` (40 chars) |
| `.env` / secrets file committed | Secret exposure | `.env` in git diff |
| SQL string concatenation (SELECT…FROM, INSERT INTO, UPDATE…SET, DELETE FROM; any case) | SQL injection | `"DELETE FROM users WHERE id=" + id` |
| SQL in template literal with `${…}` | SQL injection | `` `SELECT * FROM users WHERE id = ${id}` `` |
| SQL in Python f-string with `{…}` | SQL injection | `f"SELECT * FROM users WHERE id = {uid}"` |
| `dangerouslySetInnerHTML` with user input | XSS | `<div dangerouslySetInnerHTML={{__html: userBio}} />` |
| `eval()` / `new Function()` | Code injection | `eval(userInput)` |

### HIGH (must fix before deploy)

| Pattern | Risk |
|---|---|
| Weak hash (`md5(`, `sha1(`) / weak cipher (`createCipher` with DES/RC4) | Hash collision, brute force |
| `Math.random()` for security tokens | Predictable tokens |
| Cookie options object without `httpOnly` or without `secure` (or set to `false`) | Cookie theft via XSS / MITM |
| Hardcoded or short JWT secret in `jwt.sign` | Token forgery |
| `console.log` with `req.body`/`req.headers`/password/token/secret | Credential leak in logs |
| `exec()` with user input | Command injection |
| supabase-js `.or(` / `.filter(` built from a template literal with `${…}` | Filter injection |

### MEDIUM (review)

| Pattern | Risk |
|---|---|
| `JSON.parse` on user input | DoS via malformed JSON |
| `RegExp` from user input | ReDoS attack |
| Permissive CORS (`origin: "*"`) | Cross-origin attack |
| URL with embedded credentials | `https://user:pass@...` |

### LOW (best practice)

| Pattern | Risk |
|---|---|
| `app.listen()` without `host` binding | Exposed to all interfaces |
| `TODO: security` | Unfinished security work |

## NAL-Specific Rules

| Pattern | Severity | NAL convention |
|---|---|---|
| `process.env.NEXT_PUBLIC_*` whose name has a `KEY`/`SECRET`/`TOKEN`/`PASSWORD`/`PRIVATE` segment (except `*_ANON_KEY`, `*_PUBLISHABLE_KEY`, `*_SITE_KEY`) | HIGH | `NEXT_PUBLIC_` is inlined into the client bundle — secrets must stay server-only |
| Webhook secret (`webhookSecret` / `sepaySecret`) compared with `===` | HIGH | Must use `crypto.timingSafeEqual` |
| Logging call (`console.*`, `logger.*`, `logging.*`, `print`) with a VN phone (`0xxxxxxxxx`) or 12-digit CCCD on the same line | HIGH | Must be masked: `0901***456` |

Plain `process.env.X` / `Deno.env.get("X")` reads are not flagged — reading secrets from env is the correct pattern.

## Process

### Step 1 — Identify scope
- If `git diff` available: scan changed files
- If file specified: scan that file
- If "auth files": glob `src/**/auth/**`, `src/**/login*`, `src/middleware/auth*`
- Default: scan modified files in current session

### Step 2 — Run scanner
```bash
python3 .claude/skills/security-scanner/scripts/scan-files-for-owasp-vulnerabilities-and-credential-leaks.py \
  --files "src/auth/login.ts src/api/payment.ts" \
  --format markdown
```

For PR mode:
```bash
git diff --name-only --diff-filter=d main...HEAD | python3 .claude/skills/security-scanner/scripts/scan-files-for-owasp-vulnerabilities-and-credential-leaks.py --stdin-files --format markdown
```

### Step 3 — Present findings

Format:

```markdown
## Security Scan Result

**Files scanned:** N
**Findings:** X critical, Y high, Z medium, W low
**Status:** ⛔ BLOCK MERGE (if critical) | ⚠ FIX BEFORE DEPLOY (if high) | ✓ OK (clean)

### CRITICAL (must fix immediately)

#### `src/auth/login.ts:42:18` — Hardcoded secret
```ts
const JWT_SECRET = "hardcoded-secret-do-not-use";
```
**Risk:** Anyone with repo access can forge tokens.
**Fix:** Move to env var: `const JWT_SECRET = process.env.JWT_SECRET!`
**Reference:** OWASP A02 Cryptographic Failures

#### ... more findings
```

### Step 4 — Decide action

| Severity present | Action |
|---|---|
| Any CRITICAL | BLOCK merge until fixed |
| HIGH only | Allow merge if user acknowledges + creates follow-up ticket |
| MEDIUM/LOW only | Suggest fix, don't block |

### Step 5 — Apply fixes (optional)

If user approves, apply fixes file by file. For each:
- Show before/after diff
- Confirm before writing
- Run `type-safety-check` after if TypeScript file

## Anti-Patterns

**DO NOT:**
- Silently auto-fix security issues. User must approve each.
- Skip the OWASP reference. Linking to OWASP helps team learn.
- Report secrets in plaintext in the report. The script masks key-shaped values (`sk_test_abcd***`, `AKIAABCD***`, `ghp_abcd***`) and credential assignments.
- Ignore `.env.example` (template files are OK if no real secrets).
- Mark hardcoded test credentials in test files as CRITICAL if obviously test-only.

## Key Principles

- **Defense in depth.** Multiple checks reinforcing each other.
- **OWASP Top 10 is the baseline.** NAL adds Vietnam-specific rules on top.
- **Block at PR time, not deploy time.** Earlier = cheaper.
- **Every finding has a remediation.** Pointing without fixing isn't useful.
- **Mask secrets in reports.** Never echo full key in finding output.

## Integration

```
Implementation done (touches auth/payment/user input)
     ↓
security-scanner (this skill — scan for vulnerabilities)
     ↓ (if findings)
Apply fixes → re-scan → confirm clean
     ↓
/avatar:git:pr (open PR, scan as final check)
     ↓
security-auditor agent (deep review by subagent if NAL convention requires)
```
