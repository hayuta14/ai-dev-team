# Testing Anti-Patterns: Mocks and Production Code

Vendored from github.com/obra/superpowers (MIT). See ../LICENSE.txt.

**Load when:** writing or changing tests, adding mocks, or tempted to add test-only methods to production code.

**Core principle:** Test what the code does, not what the mocks do.

## The Iron Laws

```
1. NEVER test mock behavior
2. NEVER add test-only methods to production classes
3. NEVER mock without understanding dependencies
```

## Anti-Pattern 1: Testing Mock Behavior

```typescript
// BAD: testing the mock exists, not component behavior
test('renders sidebar', () => {
  render(<Page />);
  expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();
});

// GOOD: test real behavior
test('renders sidebar', () => {
  render(<Page />); // don't mock sidebar
  expect(screen.getByRole('navigation')).toBeInTheDocument();
});
```

Gate: Before asserting on any mock element — ask "Am I testing real behavior or mock existence?"

## Anti-Pattern 2: Test-Only Methods in Production

```typescript
// BAD: destroy() only used in tests — pollutes production class
class Session {
  async destroy() { await this._workspaceManager?.destroyWorkspace(this.id); }
}

// GOOD: move to test utilities
export async function cleanupSession(session: Session) { ... }
afterEach(() => cleanupSession(session));
```

Gate: Before adding any method — "Is this only called by tests?" → Put it in test utilities instead.

## Anti-Pattern 3: Mocking Without Understanding

```typescript
// BAD: mock breaks test logic (side effect test depends on gets skipped)
vi.mock('ToolCatalog', () => ({ discoverAndCacheTools: vi.fn().mockResolvedValue(undefined) }));

// GOOD: understand what the test needs before mocking
// Run test with real implementation FIRST, observe what breaks, THEN mock minimally
```

Gate: Before mocking — list side effects of real method. Does test depend on any? If unsure, run real first.

## Anti-Pattern 4: Incomplete Mocks

```typescript
// BAD: only mock fields you think you need — downstream code silently breaks
const mockResponse = { status: 'success', data: { userId: '123' } };
// Missing: metadata.requestId that downstream code accesses

// GOOD: mirror real API structure completely
const mockResponse = {
  status: 'success',
  data: { userId: '123', name: 'Alice' },
  metadata: { requestId: 'req-789', timestamp: 1234567890 }
};
```

## Quick Reference

| Anti-Pattern | Fix |
|--------------|-----|
| Assert on mock elements | Test real component or unmock it |
| Test-only methods in production | Move to test utilities |
| Mock without understanding | Understand dependencies first, mock minimally |
| Incomplete mocks | Mirror real API completely |

## Red Flags

- Assertion checks for `*-mock` test IDs
- Methods only called in test files
- Mock setup is >50% of test
- Test fails when you remove mock
- Mocking "just to be safe"

**If testing mock behavior, you violated TDD** — add mocks only after watching test fail against real code.
