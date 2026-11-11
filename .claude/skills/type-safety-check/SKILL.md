---
name: type-safety-check
description: Use before opening a TypeScript PR to detect weak types, unsafe assertions, and type escape hatches. Scans for `any`, `as unknown as`, `as any`, `@ts-ignore`, `@ts-nocheck`, `Function`/`Object`/`{}` types, `Promise<any>`, `Record<string, any>`, `any[]`, `as` casts, and non-null assertions (`!`). Returns a list of locations with specific rewrite suggestions for stricter types. Triggers on "check type safety", "type review", "kiểm tra type", or before commit/PR commands.
---

# Type Safety Check

## Overview

Run a static analysis pass over recently modified TypeScript files to find weak types and type escape hatches. Report each finding with file:line:col location, the offending pattern, and a concrete rewrite suggestion using stricter alternatives (discriminated unions, satisfies, Result types, etc.).

**Announce at start:** "I'm using the type-safety-check skill to scan for weak types."

## When to Activate

**Activate when:**
- User says "check type safety", "type review", "kiểm tra type", "audit types"
- Before opening a PR (chain with `/avatar:git:pr`)
- After completing a TypeScript feature implementation
- User explicitly invokes: "scan for `any` in this PR"

**Do NOT activate when:**
- Project is not TypeScript (skip — no useful output)
- User wants type errors fixed (use `/avatar:fix:types` instead — different scope)
- File is generated code (`*.d.ts` from codegen, exclude)

## What This Skill Detects

Line-by-line regex scan of `.ts`/`.tsx` (`.d.ts` skipped). Each construct yields
one finding: `as unknown as X` is reported only as the double cast (not also as
`as X`), `: any[]` only as an any array (not also as `: any`).

| Severity | Pattern | Better alternative |
|---|---|---|
| CRITICAL | `@ts-nocheck` | Fix errors one by one instead of silencing the file |
| CRITICAL | `as unknown as X` | Validate with a schema (zod, valibot) |
| HIGH | `: any` | Specific type, or `unknown` + type guard |
| HIGH | `as any` | `satisfies` to assert shape, type guard to narrow |
| HIGH | `@ts-ignore` | `@ts-expect-error <reason>` |
| HIGH | `: Function` | Specific signature `(arg: X) => Y` |
| HIGH | `: Object` | `Record<K, V>` or an interface |
| HIGH | `: {}` | `Record<string, unknown>` or an interface |
| MEDIUM | `Promise<any>` | Specify resolved type |
| MEDIUM | `Record<string, any>` | Specify value type |
| MEDIUM | `any[]` / `Array<any>` | `X[]` or `unknown[]` + type guard |
| MEDIUM | `@ts-expect-error` without reason | Add reason + ticket ref |
| LOW | `as X` cast (non-`unknown`) | `satisfies` if asserting shape, type guard if narrowing |
| LOW | Non-null assertion `x!.y`, `f()!` | Explicit null check, or `?.` |

Not detected by the script (review by hand if relevant): untyped function
returns, unconstrained generics, long optional chains, exported-API context.

## Process

### Step 1 — Identify scope
Determine which files to scan:
- If user says "this PR" → use `git diff --name-only main...HEAD`
- If user says "this file" → just that file
- If user says "all changed" → use `git diff --name-only` (uncommitted)
- Default: files modified in current session

Filter to `*.ts` and `*.tsx` only. Exclude `*.d.ts` (declarations, often legitimate `any`), `node_modules/`, `dist/`, `build/`.

### Step 2 — Run scan
Use the helper script:

```bash
python3 .claude/skills/type-safety-check/scripts/scan-typescript-files-for-weak-types-and-assertions.py \
  --files "src/api/handler.ts src/lib/utils.ts" \
  --format markdown
```

Or for a whole diff:

```bash
git diff --name-only --diff-filter=d main...HEAD | rg '\.(ts|tsx)$' | \
  python3 .claude/skills/type-safety-check/scripts/scan-typescript-files-for-weak-types-and-assertions.py \
    --stdin-files --format markdown
```

### Step 3 — Present findings
Group findings by the severity the script assigns (table above):
- **CRITICAL** — `@ts-nocheck`, `as unknown as`
- **HIGH** — `: any`, `as any`, `@ts-ignore`, `Function`/`Object`/`{}` types
- **MEDIUM** — `Promise<any>`, `Record<string, any>`, `any[]`, `@ts-expect-error` without reason
- **LOW** — single `as` cast, non-null assertion `!`

Format:

```markdown
## Type Safety Scan Result

**Files scanned:** N
**Findings:** X critical, Y high, Z medium, W low

### CRITICAL (must fix)

#### `src/api/handler.ts:42:18`
```ts
const user = response.data as unknown as User;
```
**Issue:** Double escape via `as unknown as`. Bypasses all validation.
**Suggested fix:**
```ts
import { UserSchema } from '@/schemas/user';
const user = UserSchema.parse(response.data);
```

#### ... (more findings)

### HIGH
...

### Suggested commit message
fix(types): tighten weak types in api/handler.ts and lib/utils.ts (12 findings)
```

### Step 4 — Optionally apply fixes
After presenting, ask:
> "Want me to apply the suggested fixes? (y/n)"

If yes, apply suggestions one by one with user confirmation per file (large changes shouldn't be silent).

## Rewrite Suggestions Catalog

### Replace `any` with discriminated union

```ts
// ❌ Weak
function handle(event: any) { ... }

// ✓ Stronger
type Event =
  | { type: 'login'; userId: string }
  | { type: 'logout'; reason: 'user' | 'timeout' };
function handle(event: Event) { ... }
```

### Replace `as` with `satisfies`

```ts
// ❌ Loses type info
const config = { url: '/api', timeout: 5000 } as Config;

// ✓ Validates shape, preserves literal types
const config = { url: '/api', timeout: 5000 } satisfies Config;
```

### Replace nullable chain with Result type

```ts
// ❌ Optional hell
const name = user?.profile?.contact?.email?.split('@')[0];

// ✓ Result with explicit error states
type Result<T> = { ok: true; value: T } | { ok: false; error: string };
function getEmailPrefix(user: User): Result<string> {
  if (!user.profile) return { ok: false, error: 'no profile' };
  if (!user.profile.contact?.email) return { ok: false, error: 'no email' };
  return { ok: true, value: user.profile.contact.email.split('@')[0] };
}
```

### Replace `@ts-ignore` with `@ts-expect-error + reason`

```ts
// ❌ Silences without explanation
// @ts-ignore
const x = legacy.call();

// ✓ Documents why + errors if no longer needed
// @ts-expect-error legacy SDK lacks types — TODO: upgrade to v2 (#1234)
const x = legacy.call();
```

## Anti-Patterns

**DO NOT:**
- Auto-fix without user confirmation. Type changes can ripple.
- Report `: any` in `.d.ts` files (often legitimate).
- Report `as` in test files if used for mock setup (with explicit comment).
- Recommend `as unknown as X` as a fix. It IS the anti-pattern.
- Skip the rewrite suggestion. "This is `any`" without alternative isn't actionable.

## Key Principles

- **Every `any` is a bug waiting to happen.** No exceptions on production code.
- **`as` cast = type assertion = lie to compiler.** Use `satisfies` or type guard instead.
- **Discriminated unions > optional chains.** State should be explicit.
- **Generic constraints are not optional.** `<T>` alone is `any` in disguise.
- **Type escape hatches need a justification comment.** `@ts-expect-error reason: ...`

## Integration

```
TypeScript implementation done
     ↓
type-safety-check (this skill — scan for weak types)
     ↓ (if findings)
/avatar:fix:types (fix the type errors)
     ↓
/avatar:git:cm or /avatar:git:pr (commit + PR)
```
