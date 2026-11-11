#!/bin/bash
# Bisection script to find which test creates unwanted files/state
# Usage: ./find-polluter.sh <file_or_dir_to_check> <test_pattern>
# Example: ./find-polluter.sh '.git' 'src/**/*.test.ts'
# Pattern is a find -path glob, relative to the current dir (leading ./ optional).
# Test command: $TEST_CMD (default: npm test), e.g. TEST_CMD='npx jest' or TEST_CMD=node

set -e

if [ $# -ne 2 ]; then
  echo "Usage: $0 <file_to_check> <test_pattern>" >&2
  echo "Example: $0 '.git' 'src/**/*.test.ts'" >&2
  echo "Override the test command with TEST_CMD (default: npm test)" >&2
  exit 1
fi

POLLUTION_CHECK="$1"
TEST_PATTERN="$2"
TEST_CMD="${TEST_CMD:-npm test}"

echo "🔍 Searching for test that creates: $POLLUTION_CHECK"
echo "Test pattern: $TEST_PATTERN"
echo "Test command: $TEST_CMD"
echo ""

# Get list of test files (find prints ./path, so match the pattern with and without ./)
TEST_FILES=$(find . \( -path "$TEST_PATTERN" -o -path "./$TEST_PATTERN" \) -type f | sort)
if [ -z "$TEST_FILES" ]; then
  echo "❌ No test files match '$TEST_PATTERN' under $(pwd) - nothing was tested" >&2
  exit 2
fi
TOTAL=$(echo "$TEST_FILES" | wc -l | tr -d ' ')

echo "Found $TOTAL test files"
echo ""

COUNT=0
while IFS= read -r TEST_FILE; do
  COUNT=$((COUNT + 1))

  # Skip if pollution already exists
  if [ -e "$POLLUTION_CHECK" ]; then
    echo "⚠️  Pollution already exists before test $COUNT/$TOTAL"
    echo "   Skipping: $TEST_FILE"
    continue
  fi

  echo "[$COUNT/$TOTAL] Testing: $TEST_FILE"

  # Run the test (TEST_CMD is word-split on purpose: command plus flags)
  # shellcheck disable=SC2086
  $TEST_CMD "$TEST_FILE" > /dev/null 2>&1 < /dev/null || true

  # Check if pollution appeared
  if [ -e "$POLLUTION_CHECK" ]; then
    echo ""
    echo "🎯 FOUND POLLUTER!"
    echo "   Test: $TEST_FILE"
    echo "   Created: $POLLUTION_CHECK"
    echo ""
    echo "Pollution details:"
    ls -la "$POLLUTION_CHECK"
    echo ""
    echo "To investigate:"
    echo "  $TEST_CMD $TEST_FILE    # Run just this test"
    echo "  cat $TEST_FILE         # Review test code"
    exit 1
  fi
done <<< "$TEST_FILES"

echo ""
echo "✅ No polluter found - all tests clean!"
exit 0
