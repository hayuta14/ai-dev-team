#!/usr/bin/env node
/**
 * MCP Management CLI - Command-line interface for MCP operations
 */

import { MCPClientManager } from './mcp-client.js';
import { writeFileSync, mkdirSync } from 'fs';
import { tmpdir } from 'os';
import { dirname, join } from 'path';

const GLOBAL_TIMEOUT_MS = parseInt(process.env.MCP_TIMEOUT || '120000', 10);
let globalManager: MCPClientManager | null = null;

function setupShutdownHandlers() {
  const shutdown = async (signal: string) => {
    console.log(`\nReceived ${signal}, cleaning up...`);
    if (globalManager) {
      await globalManager.cleanup();
    }
    process.exit(0);
  };

  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGHUP', () => shutdown('SIGHUP'));

  process.on('unhandledRejection', (reason) => {
    console.error('Unhandled rejection:', reason);
    process.exit(1);
  });
}

async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  // Setup shutdown handlers
  setupShutdownHandlers();

  // Check for help flags BEFORE connecting to servers
  if (!command || command === '--help' || command === 'help') {
    printUsage();
    process.exit(0);
  }

  // Global timeout
  const timeoutHandle = setTimeout(() => {
    console.error('Global timeout exceeded, forcing exit');
    process.exit(1);
  }, GLOBAL_TIMEOUT_MS);
  timeoutHandle.unref();

  const manager = new MCPClientManager();
  globalManager = manager;

  try {
    // Load config
    // MCP_CONFIG_PATH overrides the cwd-relative default `.claude/.mcp.json`.
    await manager.loadConfig(process.env.MCP_CONFIG_PATH);
    console.log('✓ Config loaded');

    // call-tool needs only its own server; everything else connects to all
    if (command === 'call-tool' && (!args[1] || !args[2] || !args[3])) {
      console.error('Usage: cli.ts call-tool <server> <tool> <json-args>');
      process.exit(1);
    }
    const failed = await manager.connectAll(command === 'call-tool' ? [args[1]] : undefined);
    if (failed.length > 0) {
      console.error(`✗ Failed to connect: ${failed.join(', ')}\n`);
    } else {
      console.log('✓ Connected to all MCP servers\n');
    }

    switch (command) {
      case 'list-tools':
        await listTools(manager, failed);
        break;

      case 'list-prompts':
        await listPrompts(manager);
        break;

      case 'list-resources':
        await listResources(manager);
        break;

      case 'call-tool':
        if (failed.length === 0) await callTool(manager, args[1], args[2], args[3]);
        break;

      default:
        printUsage();
    }

    await manager.cleanup();
    // 2 = at least one requested server did not connect (results are partial)
    process.exit(failed.length > 0 ? 2 : 0);
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

async function listTools(manager: MCPClientManager, failed: string[]) {
  const tools = await manager.getAllTools();
  console.log(`Found ${tools.length} tools:\n`);

  for (const tool of tools) {
    console.log(`📦 ${tool.serverName} / ${tool.name}`);
    console.log(`   ${tool.description}`);
    if (tool.inputSchema?.properties) {
      console.log(`   Parameters: ${Object.keys(tool.inputSchema.properties).join(', ')}`);
    }
    console.log('');
  }

  // Save tools to JSON file outside the skill directory: the pack copy under
  // .claude/pack/ is overwritten by `avatar sync`. MCP_TOOLS_PATH overrides.
  const toolsPath = process.env.MCP_TOOLS_PATH || join(tmpdir(), 'mcp-management-tools.json');

  // A partial list must not replace a good catalog
  if (failed.length > 0) {
    console.error(`\n✗ Catalog NOT written (failed: ${failed.join(', ')}); ${toolsPath} left unchanged`);
    return;
  }

  try {
    mkdirSync(dirname(toolsPath), { recursive: true });
    writeFileSync(toolsPath, JSON.stringify(tools, null, 2));
    console.log(`\n✓ Tools saved to ${toolsPath}`);
  } catch (error) {
    console.error(`\n✗ Failed to save tools: ${error}`);
  }
}

async function listPrompts(manager: MCPClientManager) {
  const prompts = await manager.getAllPrompts();
  console.log(`Found ${prompts.length} prompts:\n`);

  for (const prompt of prompts) {
    console.log(`💬 ${prompt.serverName} / ${prompt.name}`);
    console.log(`   ${prompt.description}`);
    if (prompt.arguments && prompt.arguments.length > 0) {
      console.log(`   Arguments: ${prompt.arguments.map((a: any) => a.name).join(', ')}`);
    }
    console.log('');
  }
}

async function listResources(manager: MCPClientManager) {
  const resources = await manager.getAllResources();
  console.log(`Found ${resources.length} resources:\n`);

  for (const resource of resources) {
    console.log(`📄 ${resource.serverName} / ${resource.name}`);
    console.log(`   URI: ${resource.uri}`);
    if (resource.description) {
      console.log(`   ${resource.description}`);
    }
    if (resource.mimeType) {
      console.log(`   Type: ${resource.mimeType}`);
    }
    console.log('');
  }
}

async function callTool(
  manager: MCPClientManager,
  serverName: string,
  toolName: string,
  argsJson: string
) {
  const args = JSON.parse(argsJson);
  console.log(`Calling ${serverName}/${toolName}...`);

  const result = await manager.callTool(serverName, toolName, args);
  console.log('\nResult:');
  console.log(JSON.stringify(result, null, 2));
}

function printUsage() {
  console.log(`
MCP Management CLI

Usage:
  cli.ts <command> [options]

Commands:
  list-tools                        List all tools and save the catalog to $MCP_TOOLS_PATH ($TMPDIR/mcp-management-tools.json);
                                    not written when any server fails to connect
  list-prompts                      List all prompts from all MCP servers
  list-resources                    List all resources from all MCP servers
  call-tool <server> <tool> <json>  Call a specific tool (connects to <server> only)

Examples:
  cli.ts list-tools
  cli.ts call-tool memory create_entities '{"entities":[{"name":"Alice","entityType":"person"}]}'
  cli.ts call-tool human-mcp playwright_screenshot_fullpage '{"url":"https://example.com"}'

Environment:
  MCP_CONFIG_PATH   config file (default: .claude/.mcp.json relative to cwd)
  MCP_TOOLS_PATH    where list-tools writes the catalog (default: $TMPDIR/mcp-management-tools.json)
  MCP_TIMEOUT       global timeout in ms (default: 120000)

Exit codes: 0 ok · 1 error/usage · 2 a requested server failed to connect (partial results)
Server env: SDK defaults + proxy/CA vars that are set + config "env"; \${VAR} in env/args expands from the environment.

Note: Tool analysis is done by the LLM reading the saved catalog directly.
  `);
}

main();
