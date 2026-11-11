#!/usr/bin/env node

/**
 * Environment accessor for docs-seeker skill.
 *
 * Secrets (e.g. CONTEXT7_API_KEY) are read from process.env ONLY.
 * This module never opens a .env file: the workspace denies Claude's Read
 * tool on .env*, and a script Claude runs must not bypass that policy.
 * Set values in your shell instead: `export CONTEXT7_API_KEY=...`
 */

/**
 * Snapshot of the current process environment.
 * @returns {Object} Copy of process.env
 */
function loadEnv() {
  return { ...process.env };
}

/**
 * Get environment variable with fallback
 * @param {string} key - Environment variable key
 * @param {string} defaultValue - Default value if not found
 * @returns {string} Environment variable value
 */
function getEnv(key, defaultValue = '') {
  return process.env[key] || defaultValue;
}

module.exports = {
  loadEnv,
  getEnv,
};
