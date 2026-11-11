/**
 * Environment and argument building for spawned stdio MCP servers.
 *
 * The SDK only inherits HOME/LOGNAME/PATH/SHELL/TERM/USER, so `npx -y` servers
 * behind a corporate proxy or custom CA fail to download/connect. We add the
 * proxy/CA variables that are set, then the server's own `env` with `${VAR}`
 * expanded from process.env (same syntax as Claude Code's .mcp.json).
 */

import { getDefaultEnvironment } from '@modelcontextprotocol/sdk/client/stdio.js';

export const PASSTHROUGH_ENV_VARS = [
  'HTTPS_PROXY', 'https_proxy', 'HTTP_PROXY', 'http_proxy', 'NO_PROXY', 'no_proxy',
  'NODE_EXTRA_CA_CERTS', 'SSL_CERT_FILE'
];

/** Replace every `${VAR}` with process.env.VAR; an unset VAR becomes '' with a warning (name only). */
export function expandEnvVars(value: string, source: NodeJS.ProcessEnv = process.env): string {
  return value.replace(/\$\{([A-Za-z_][A-Za-z0-9_]*)\}/g, (_match, name: string) => {
    const resolved = source[name];
    if (resolved === undefined) {
      console.warn(`Warning: \${${name}} is not set; using an empty string`);
      return '';
    }
    return resolved;
  });
}

export function buildServerArgs(args: string[] = [], source: NodeJS.ProcessEnv = process.env): string[] {
  return args.map((arg) => expandEnvVars(arg, source));
}

export function buildServerEnv(
  serverEnv: Record<string, string> = {},
  source: NodeJS.ProcessEnv = process.env
): Record<string, string> {
  const env: Record<string, string> = { ...getDefaultEnvironment() };
  for (const key of PASSTHROUGH_ENV_VARS) {
    const value = source[key];
    if (value !== undefined) env[key] = value;
  }
  for (const [key, value] of Object.entries(serverEnv)) {
    env[key] = expandEnvVars(String(value), source);
  }
  return env;
}
