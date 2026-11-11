/**
 * Tests for mcp-client / cli: failed connects, catalog safety, server env.
 * Run: npm test (node --test with the tsx loader). Spawns only local processes.
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { MCPClientManager } from '../mcp-client.js';
import { buildServerArgs, buildServerEnv } from '../server-spawn-environment.js';

const SCRIPTS = join(dirname(fileURLToPath(import.meta.url)), '..');
const ECHO_SERVER = join(SCRIPTS, 'test', 'echo-stdio-server.mjs');
const PREVIOUS_CATALOG = '[{"serverName":"previous","name":"keep_me"}]';

function makeWorkdir(t: { after: (fn: () => void) => void }, servers: Record<string, unknown>) {
  const dir = mkdtempSync(join(tmpdir(), 'mcp-mgmt-test-'));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const config = join(dir, 'mcp.json');
  const catalog = join(dir, 'catalog.json');
  writeFileSync(config, JSON.stringify({ mcpServers: servers }));
  writeFileSync(catalog, PREVIOUS_CATALOG);
  return { config, catalog };
}

const ECHO = { command: process.execPath, args: [ECHO_SERVER] };
const BROKEN = { command: '/nonexistent/mcp-server-binary', args: [] };

function runCli(args: string[], env: Record<string, string>): Promise<{ code: number; out: string }> {
  return new Promise((resolve) => {
    execFile(process.execPath, ['--import', 'tsx', 'cli.ts', ...args],
      { cwd: SCRIPTS, env: { ...process.env, ...env } },
      (error, stdout, stderr) => resolve({ code: error ? Number(error.code) : 0, out: stdout + stderr }));
  });
}

test('test_buildServerEnv_proxyAndCaVarsSet_passedThroughWithDefaults', () => {
  const env = buildServerEnv(undefined, { HTTPS_PROXY: 'http://p:3128', no_proxy: 'localhost', NODE_EXTRA_CA_CERTS: '/ca.pem', SECRET_UNRELATED: 'x' });
  assert.equal(env.HTTPS_PROXY, 'http://p:3128');
  assert.equal(env.no_proxy, 'localhost');
  assert.equal(env.NODE_EXTRA_CA_CERTS, '/ca.pem');
  assert.equal(env.SECRET_UNRELATED, undefined);
  assert.equal(env.PATH, process.env.PATH);
});

test('test_buildServerEnv_configEnvWithVarRef_expandsFromEnvironment', () => {
  const env = buildServerEnv({ API_KEY: '${MY_KEY}', MODE: 'fixed', MISSING: '${NOT_SET_ANYWHERE}' }, { MY_KEY: 'k1' });
  assert.equal(env.API_KEY, 'k1');
  assert.equal(env.MODE, 'fixed');
  assert.equal(env.MISSING, '');
});

test('test_buildServerArgs_varRef_expandsFromEnvironment', () => {
  assert.deepEqual(buildServerArgs(['--root', '${ROOT}/data'], { ROOT: '/srv' }), ['--root', '/srv/data']);
});

test('test_connectAll_brokenServer_returnsFailedNames', async (t) => {
  const { config } = makeWorkdir(t, { echo: ECHO, broken: BROKEN });
  const manager = new MCPClientManager();
  await manager.loadConfig(config);
  const failed = await manager.connectAll();
  await manager.cleanup();
  assert.deepEqual(failed, ['broken']);
});

test('test_cli_listToolsWithBrokenServer_exits2AndKeepsCatalog', async (t) => {
  const { config, catalog } = makeWorkdir(t, { echo: ECHO, broken: BROKEN });
  const { code, out } = await runCli(['list-tools'], { MCP_CONFIG_PATH: config, MCP_TOOLS_PATH: catalog });
  assert.equal(code, 2, out);
  assert.match(out, /Failed to connect: broken/);
  assert.equal(readFileSync(catalog, 'utf-8'), PREVIOUS_CATALOG);
});

test('test_cli_listToolsAllConnected_exits0AndWritesCatalog', async (t) => {
  const { config, catalog } = makeWorkdir(t, { echo: ECHO });
  const { code, out } = await runCli(['list-tools'], { MCP_CONFIG_PATH: config, MCP_TOOLS_PATH: catalog });
  assert.equal(code, 0, out);
  assert.equal(JSON.parse(readFileSync(catalog, 'utf-8'))[0].name, 'echo_env');
});

test('test_cli_callTool_connectsOnlyNamedServerAndExpandsEnv', async (t) => {
  const { config } = makeWorkdir(t, { echo: { ...ECHO, env: { E2E_TOKEN: '${E2E_SECRET}' } }, broken: BROKEN });
  const { code, out } = await runCli(['call-tool', 'echo', 'echo_env', '{"name":"E2E_TOKEN"}'],
    { MCP_CONFIG_PATH: config, E2E_SECRET: 's3cr3t' });
  assert.equal(code, 0, out);
  assert.doesNotMatch(out, /broken/);
  assert.match(out, /s3cr3t/);
});
