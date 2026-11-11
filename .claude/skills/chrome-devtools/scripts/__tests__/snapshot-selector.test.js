/**
 * Tests for the snapshot.js helpers in lib/selector.js
 * Run with: node --test __tests__/snapshot-selector.test.js
 */
import { describe, it } from 'node:test';
import assert from 'node:assert';
import { buildElementSelector, snapshotValue } from '../lib/selector.js';

// Node has no CSS.escape; this stand-in matches its output for ASCII punctuation
// (checked against Chrome: `md:flex w-1/2` -> `md\:flex.w-1\/2`).
const cssEscape = (part) => part.replace(/[^\w-]/g, (c) => `\\${c}`);

describe('buildElementSelector', () => {
  it('escapes Tailwind class names (regression: raw `md:flex` broke the selector)', () => {
    const el = { id: '', tagName: 'BUTTON', classList: ['md:flex', 'w-1/2', 'hover:bg-[#fff]'] };

    const selector = buildElementSelector(el, cssEscape);

    assert.strictEqual(selector, 'button.md\\:flex.w-1\\/2.hover\\:bg-\\[\\#fff\\]');
  });

  it('escapes ids and prefers them over classes', () => {
    const el = { id: 'pw:1', tagName: 'INPUT', classList: ['a'] };

    assert.strictEqual(buildElementSelector(el, cssEscape), '#pw\\:1');
  });

  it('falls back to the lowercase tag name', () => {
    const el = { id: '', tagName: 'A', classList: [] };

    assert.strictEqual(buildElementSelector(el, cssEscape), 'a');
  });
});

describe('snapshotValue', () => {
  it('never returns the value of a password input (regression: it was dumped)', () => {
    assert.strictEqual(snapshotValue({ type: 'password', value: 'hunter2' }), '[redacted]');
    assert.strictEqual(snapshotValue({ type: 'PASSWORD', value: 'x' }), '[redacted]');
    assert.strictEqual(snapshotValue({ type: 'password', value: '' }), null);
  });

  it('returns other values unchanged', () => {
    assert.strictEqual(snapshotValue({ type: 'text', value: 'hello' }), 'hello');
    assert.strictEqual(snapshotValue({ type: undefined, value: undefined }), null);
  });
});
