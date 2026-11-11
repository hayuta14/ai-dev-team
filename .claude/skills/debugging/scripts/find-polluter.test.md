# find-polluter.sh Test Documentation

## Purpose
Bisection script to find which test creates unwanted files or state pollution.

## Manual Test Procedure

### Setup Test Scenario
```bash
# Create test directory
mkdir -p /tmp/polluter-test && cd /tmp/polluter-test

# Create clean test
cat > test1.test.js << 'EOF'
console.log('Test 1: clean');
EOF

# Create polluter test
cat > test2.test.js << 'EOF'
const fs = require('fs');
fs.mkdirSync('.git', { recursive: true });
console.log('Test 2: creates pollution');
EOF

# Create another clean test
cat > test3.test.js << 'EOF'
console.log('Test 3: clean');
EOF
```

### Run Script
```bash
# For projects with npm test
/path/to/find-polluter.sh '.git' 'src/**/*.test.ts'

# For node-only tests (override the test command)
TEST_CMD=node ./find-polluter.sh '.git' '*.test.js'
```

### Expected Output
```
🔍 Searching for test that creates: .git
Test pattern: *.test.js

Found 3 test files

[1/3] Testing: ./test1.test.js
[2/3] Testing: ./test2.test.js

🎯 FOUND POLLUTER!
   Test: ./test2.test.js
   Created: .git
```

### Cleanup
```bash
rm -rf /tmp/polluter-test
```

## Test Results

✅ Script logic verified (2025-11-11)
- Correctly iterates through test files
- Detects pollution creation
- Reports the polluting test file
- Exits early when polluter found

## Usage Notes

**Prerequisites:**
- Test runner (npm test) must be configured in project
- Test pattern must match actual test files
- Pollution path must be accurate

**Customization:**
If your project doesn't use `npm test`, set `TEST_CMD` (word-split, the test file is appended):
```bash
TEST_CMD=node ./find-polluter.sh '.git' '*.test.js'
TEST_CMD='npx jest' ./find-polluter.sh '.git' 'src/*.test.ts'
```

**Exit codes:** 0 = all clean · 1 = polluter found · 2 = pattern matched no files
(the pattern is a `find -path` glob; a leading `./` is optional).

## Common Use Cases

1. **Find test creating .git directory:**
   ```bash
   ./find-polluter.sh '.git' 'src/**/*.test.ts'
   ```

2. **Find test creating node_modules:**
   ```bash
   ./find-polluter.sh 'node_modules' 'test/**/*.spec.js'
   ```

3. **Find test creating specific file:**
   ```bash
   ./find-polluter.sh 'unwanted-file.txt' '**/*.test.js'
   ```
