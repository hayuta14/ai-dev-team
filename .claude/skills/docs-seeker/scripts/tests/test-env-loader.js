#!/usr/bin/env node

/**
 * Tests for utils/env-loader.js: secrets come from process.env ONLY.
 * The loader is copied into a throwaway skill tree so planted .env files
 * sit exactly where the old loader used to look (skill/.env, skills/.env,
 * .claude/.env) without touching the repo.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

let passed = 0;
let failed = 0;

function assertEqual(actual, expected, message) {
  if (actual === expected) {
    console.log(`✓ ${message}`);
    passed++;
  } else {
    console.error(`✗ ${message}`);
    console.error(`  Expected: ${expected}`);
    console.error(`  Actual:   ${actual}`);
    failed++;
  }
}

// Arrange: tree = <root>/.claude/skills/docs-seeker/scripts/utils/env-loader.js
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'docs-seeker-env-'));
const claudeDir = path.join(root, '.claude');
const skillsDir = path.join(claudeDir, 'skills');
const skillDir = path.join(skillsDir, 'docs-seeker');
const utilsDir = path.join(skillDir, 'scripts', 'utils');
fs.mkdirSync(utilsDir, { recursive: true });
fs.copyFileSync(path.join(__dirname, '..', 'utils', 'env-loader.js'), path.join(utilsDir, 'env-loader.js'));

const FILE_ONLY = 'DOCS_SEEKER_TEST_FILE_ONLY';
const BOTH = 'DOCS_SEEKER_TEST_BOTH';
for (const dir of [skillDir, skillsDir, claudeDir]) {
  fs.writeFileSync(path.join(dir, '.env'), `${FILE_ONLY}=from-dotenv-file\n${BOTH}=from-dotenv-file\n`);
}
delete process.env[FILE_ONLY];
process.env[BOTH] = 'from-process-env';

try {
  const { loadEnv, getEnv } = require(path.join(utilsDir, 'env-loader.js'));

  console.log('\n## test_env_loader_dotenv_in_skill_dirs_is_ignored');
  // Act
  const env = loadEnv();
  // Assert
  assertEqual(env[FILE_ONLY], undefined, 'loadEnv ignores .env in skill/, skills/ and .claude/');
  assertEqual(getEnv(FILE_ONLY, 'fallback'), 'fallback', 'getEnv falls back when only a .env file has the key');

  console.log('\n## test_env_loader_process_env_is_returned_as_is');
  assertEqual(env[BOTH], 'from-process-env', 'loadEnv returns process.env value, not the .env value');
  assertEqual(getEnv(BOTH), 'from-process-env', 'getEnv returns process.env value');

  console.log('\n## test_env_loader_module_exposes_no_dotenv_parser');
  const mod = require(path.join(utilsDir, 'env-loader.js'));
  assertEqual(typeof mod.parseEnvFile, 'undefined', 'parseEnvFile is not exported');
} finally {
  fs.rmSync(root, { recursive: true, force: true });
}

console.log('\n## Test Summary');
console.log(`Passed: ${passed}`);
console.log(`Failed: ${failed}`);
console.log(`Total: ${passed + failed}`);

process.exit(failed > 0 ? 1 : 0);
