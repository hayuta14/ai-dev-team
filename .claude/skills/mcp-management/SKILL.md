---
name: mcp-management
description: Manage Model Context Protocol (MCP) servers - discover, analyze, and execute tools/prompts/resources from configured MCP servers. Use when working with MCP integrations, need to discover available MCP capabilities, filter MCP tools for specific tasks, execute MCP tools programmatically, access MCP prompts/resources, or implement MCP client functionality. Supports intelligent tool selection, multi-server management, and context-efficient capability discovery.
---

# MCP Management

Skill for managing and interacting with Model Context Protocol (MCP) servers.

## Overview

MCP is an open protocol enabling AI agents to connect to external tools and data sources. This skill provides scripts to discover, analyze, and execute MCP capabilities from configured servers without polluting the main context window.

**Key Benefits**:
- Progressive disclosure of MCP capabilities (load only what's needed)
- Intelligent tool/prompt/resource selection based on task requirements
- Multi-server management from single config file
- Context-efficient: the `mcp-manager` subagent handles heavy MCP jobs
- Persistent tool catalog: discovered tools are saved to JSON for fast reference

## When to Use This Skill

Use this skill when:
1. **Discovering MCP Capabilities**: Need to list available tools/prompts/resources from configured servers
2. **Task-Based Tool Selection**: Analyzing which MCP tools are relevant for a specific task
3. **Executing MCP Tools**: Calling MCP tools programmatically with proper parameter handling
4. **MCP Integration**: Building or debugging MCP client implementations
5. **Context Management**: Avoiding context pollution by delegating MCP operations to a subagent

## Execution Priority

1. **Session tools first.** A server already loaded in this Claude Code session exposes `mcp__<server>__<tool>`; call it directly (load a deferred tool with ToolSearch). `claude mcp list` shows configured servers and their health.
2. **Scripts** for a server that is not loaded in the session: point them at its config file (below).
3. **`mcp-manager` subagent** when the job is many calls or large payloads: it runs in its own context, writes the bulk to a file and returns a short summary. Brief it with `JOB`, `SERVERS`, `CONFIG`, `WRITE_OK` (the mutating tools the user approved, else `none`) and `WS` (the absolute workspace root). For one or two calls, do them yourself.

Never hand an MCP task to an external LLM CLI (`gemini`, `codex`, ...): their auto-approve mode runs every tool call, including writes and deletes, without review, and the task leaves for a third party.

## Configuration

Scripts read `.claude/.mcp.json` relative to the current directory, or the file named by `MCP_CONFIG_PATH`. See [references/configuration.md](references/configuration.md). The config carries tokens in `env`/`headers`: never print it, only server names.

## Scripts

Dependencies once per machine (the pack directory is replaced by `avatar sync`, so reinstall after a sync if `node_modules` is gone):

```bash
npm install --prefix .claude/skills/mcp-management/scripts
```

```bash
S=.claude/skills/mcp-management/scripts
MCP_CONFIG_PATH=/abs/path/.mcp.json npx tsx $S/cli.ts list-tools      # catalog → $MCP_TOOLS_PATH
MCP_CONFIG_PATH=/abs/path/.mcp.json npx tsx $S/cli.ts list-prompts
MCP_CONFIG_PATH=/abs/path/.mcp.json npx tsx $S/cli.ts list-resources
MCP_CONFIG_PATH=/abs/path/.mcp.json npx tsx $S/cli.ts call-tool <server> <tool> '<json>'
```

| Variable | Default | Meaning |
|---|---|---|
| `MCP_CONFIG_PATH` | `.claude/.mcp.json` (relative to cwd) | server config |
| `MCP_TOOLS_PATH` | `$TMPDIR/mcp-management-tools.json` | where `list-tools` writes the catalog (outside the pack, which sync overwrites) |
| `MCP_TIMEOUT` | `120000` | global timeout in ms |

Exit `2` = a requested server failed to connect (named in the output; results partial) and `list-tools` then leaves the existing catalog unchanged. `call-tool` connects to its server only. Spawned servers get the SDK default env + proxy/CA vars (`HTTPS_PROXY`, `NO_PROXY`, `NODE_EXTRA_CA_CERTS`, `SSL_CERT_FILE`, ...) when set + the config `env`; `${VAR}` in `env`/`args` expands from the environment. No `.env` file is read.

### scripts/mcp-client.ts
Core client manager: loads the config, connects to every server over stdio, lists tools/prompts/resources across servers, executes tools, closes connections.

### scripts/cli.ts
Command-line wrapper around the client (commands above).

## Tool Selection

The LLM reads the saved catalog (or the tool definitions ToolSearch returns) and picks tools by intent, synonyms and input schema; this beats keyword matching. Each tool keeps its source server for routing across servers.

## Safety

- Read-only by default. A tool that creates, updates, deletes, sends, posts, deploys or pays runs only when the user asked for that action; a neutral name (`execute_sql`, `run`, `apply`) counts as mutating unless its arguments are plainly read-only.
- Adding or editing servers (`claude mcp add`, editing `.mcp.json`) is proposed to the user, not done silently.
- Browser-type servers (Playwright, Puppeteer) drive a real browser; navigating authenticated sites is treated as mutating.

## Technical Details

See [references/mcp-protocol.md](references/mcp-protocol.md) for JSON-RPC protocol details, message types, error codes, transports (stdio, HTTP+SSE) and best practices.
