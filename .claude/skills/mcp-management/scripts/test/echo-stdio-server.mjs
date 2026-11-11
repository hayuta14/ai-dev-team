#!/usr/bin/env node
/**
 * Test fixture: minimal stdio MCP server with one `echo_env` tool that
 * returns the value of the env var named in its `name` argument.
 */
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

const server = new McpServer({ name: 'echo', version: '1.0.0' });
server.tool('echo_env', 'Return an environment variable and argv', { name: z.string() }, async ({ name }) => ({
  content: [{ type: 'text', text: JSON.stringify({ value: process.env[name] ?? null, argv: process.argv.slice(2) }) }],
}));
await server.connect(new StdioServerTransport());
