---
name: test-driven-development
description: Use when implementing any feature or bugfix, before writing implementation code Triggers (VI): "viết test trước", "test-first".
license: MIT — vendored from github.com/obra/superpowers (Jesse Vincent). See LICENSE.txt.
---

# Test-Driven Development (TDD)

## Overview

Write the test first. Watch it fail. Write minimal code to pass.

**Core principle:** If you didn't watch the test fail, you don't know if it tests the right thing.

**Violating the letter of the rules is violating the spirit of the rules.**

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

For behaviour you are adding or fixing, the test comes first and you watch it fail for the expected reason before writing the code. Code written before its test is not trusted: set it aside, write the test, watch it fail, then bring the code back only as far as the test demands. Exceptions are the caller's to grant, not yours to assume.

## RED-GREEN-REFACTOR

**RED** → Write one failing test showing what should happen.
**Verify RED** → Run test. Confirm it fails (not errors) for expected reason (feature missing, not typo).
**GREEN** → Write simplest code to pass. No extras, no "while I'm here" improvements.
**Verify GREEN** → Run test. Confirm pass + all other tests still green.
**REFACTOR** → Remove duplication, improve names. Keep tests green. No new behavior.
**Repeat** → Next failing test for next feature.

See `references/tdd-red-green-refactor-typescript-examples.md` for TypeScript before/after examples.

## Naming + Structure (NAL standard)

Test names follow `test_[system]_[scenario]_[expected_outcome]` — see `workflows/test-standards.md`.
Structure: **Arrange / Act / Assert** in every test.

**IMPORTANT**: đọc `references/test-naming-and-aaa-examples.md` **TRƯỚC KHI** viết ca test đầu tiên. <!-- NAL #231 — KHÔNG xoá khi re-vendor -->

Anti-patterns: see `references/testing-anti-patterns-mocks-and-production-code.md`.

## Red Flags — stop and put the test first

- Code before test
- Test passes immediately (you're testing existing behavior)
- Can't explain why test failed
- "I'll write tests after"
- "Just this once"
- "I already manually tested it"
- "Tests after achieve the same purpose"

**Any of these means: set the code aside, write the test, watch it fail.**

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Tests after achieve same goals" | Tests-after = "what does this do?" Tests-first = "what should this do?" |
| "Already manually tested" | Ad-hoc ≠ systematic. No record, can't re-run. |
| "Deleting X hours is wasteful" | Sunk cost. Keeping unverified code is technical debt. |
| "Need to explore first" | Fine. Throw away exploration, start fresh with TDD. |

## Verification Checklist

Before marking work complete:
- [ ] Every new function/method has a test
- [ ] Watched each test fail before implementing
- [ ] Each test failed for expected reason (feature missing, not typo)
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass, output pristine

Can't check all boxes? Write the missing failing test and watch it fail before claiming the work done.
