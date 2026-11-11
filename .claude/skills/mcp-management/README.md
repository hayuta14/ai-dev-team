# MCP Management Skill

Intelligent management and execution of Model Context Protocol (MCP) servers.

## Overview

This skill enables Claude to discover, analyze, and execute MCP server capabilities without polluting the main context window. Perfect for context-efficient MCP integration using subagent-based architecture.

## Features

- **Multi-Server Management**: Connect to multiple MCP servers from single config
- **Intelligent Tool Discovery**: Analyze which tools are relevant for specific tasks
- **Progressive Disclosure**: Load only necessary tool definitions
- **Execution Engine**: Call MCP tools with proper parameter handling
- **Context Efficiency**: Delegate MCP operations to `mcp-manager` subagent

## Quick Start

### 1. Install Dependencies

```bash
cd .claude/skills/mcp-management/scripts
npm install
```

### 2. Configure MCP Servers

Create `.claude/.mcp.json`:

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"]
    }
  }
}
```

See [references/configuration.md](./references/configuration.md) for more examples.

### 3. Test Connection

```bash
cd .claude/skills/mcp-management/scripts
npx tsx cli.ts list-tools
```

## Usage Patterns

### Pattern 1: Discover Available Tools

```bash
npx tsx scripts/cli.ts list-tools
npx tsx scripts/cli.ts list-prompts
npx tsx scripts/cli.ts list-resources
```

### Pattern 2: LLM-Driven Tool Selection

The LLM reads the saved catalog (`$MCP_TOOLS_PATH`, default `$TMPDIR/mcp-management-tools.json`) and intelligently selects tools. No separate analysis command needed - the LLM's understanding of context and intent is superior to keyword matching.

### Pattern 3: Execute MCP Tools

```bash
npx tsx scripts/cli.ts call-tool memory add '{"key":"name","value":"Alice"}'
```

### Pattern 4: Use with Subagent

In main Claude conversation:

```
User: "I need to search the web and save results"
Main Agent: [Spawns mcp-manager subagent]
mcp-manager: Discovers brave-search + memory tools, reports back
Main Agent: Uses recommended tools for implementation
```

## Architecture

```
Main Agent (Claude)
    ↓ (delegates MCP tasks)
mcp-manager Subagent
    ↓ (uses skill)
mcp-management Skill
    ↓ (connects via)
MCP Servers (memory, filesystem, etc.)
```

**Benefits**:
- Main agent context stays clean
- MCP discovery happens in isolated subagent context
- Only relevant tool definitions loaded when needed
- Reduced token usage

## File Structure

```
mcp-management/
├── SKILL.md                    # Skill definition
├── README.md                   # This file
├── scripts/
│   ├── mcp-client.ts          # Core MCP client manager
│   ├── server-spawn-environment.ts  # Env/args for spawned servers (proxy/CA, ${VAR})
│   ├── cli.ts                 # Command-line interface
│   ├── test/                  # node:test suite (`npm test`) + echo fixture server
│   ├── package.json           # Dependencies
│   └── tsconfig.json          # TypeScript config
└── references/
    ├── mcp-protocol.md        # MCP protocol reference
    └── configuration.md       # Config guide
```

## Scripts Reference

### mcp-client.ts

Core client manager class:
- Load config from `.claude/.mcp.json` (relative to cwd) or `$MCP_CONFIG_PATH`
- Connect to multiple MCP servers
- List/execute tools, prompts, resources
- Lifecycle management

### cli.ts

Command-line interface:
- `list-tools` - Show all tools and save the catalog to `$MCP_TOOLS_PATH` (default `$TMPDIR/mcp-management-tools.json`); the catalog is NOT written when any server fails to connect, so a good catalog is never replaced by a partial one
- `list-prompts` - Show all prompts
- `list-resources` - Show all resources
- `call-tool <server> <tool> <json>` - Execute tool (connects to `<server>` only)
- Exit codes: `0` ok · `1` error/usage · `2` a requested server failed to connect (its name is printed; results are partial)

**Note**: Tool analysis is performed by the LLM reading the saved catalog, which provides better context understanding than algorithmic matching.

## Configuration

### Environment Variables

Scripts read `process.env` only (no `.env` file is loaded): `MCP_CONFIG_PATH`, `MCP_TOOLS_PATH`, `MCP_TIMEOUT`.

Each spawned server gets the SDK default environment (`HOME`, `LOGNAME`, `PATH`, `SHELL`, `TERM`, `USER`), plus `HTTPS_PROXY`/`HTTP_PROXY`/`NO_PROXY` (and lowercase), `NODE_EXTRA_CA_CERTS`, `SSL_CERT_FILE` when set, plus its config `env`. `${VAR}` in `env` values and in `args` is expanded from the environment (unset ⇒ empty string + warning).

### MCP Config Format

```json
{
  "mcpServers": {
    "server-name": {
      "command": "executable",          // Required
      "args": ["arg1", "arg2"],        // Required
      "env": {                          // Optional
        "VAR": "value",
        "API_KEY": "${ENV_VAR}"        // Expanded from the environment (also in args)
      }
    }
  }
}
```

## Common MCP Servers

Install with `npx`:

- `@modelcontextprotocol/server-memory` - Key-value storage
- `@modelcontextprotocol/server-filesystem` - File operations
- `@modelcontextprotocol/server-brave-search` - Web search
- `@modelcontextprotocol/server-puppeteer` - Browser automation
- `@modelcontextprotocol/server-fetch` - HTTP requests

## Integration with mcp-manager Agent

The `mcp-manager` agent (`.claude/agents/mcp-manager.md`) uses this skill to:

1. **Discover**: Connect to MCP servers, list capabilities
2. **Analyze**: Filter relevant tools for tasks
3. **Execute**: Call MCP tools on behalf of main agent
4. **Report**: Send concise results back to main agent

This architecture keeps main context clean and enables efficient MCP integration.

## Troubleshooting

### "Config not found"

Ensure `.claude/.mcp.json` exists and is valid JSON.

### "Server connection failed"

The CLI prints `✗ Failed to connect: <names>` and exits `2`. Check:
- Server command is installed (`npx` packages installed?)
- Server args are correct
- Environment variables are set

### "Tool not found"

List available tools first:
```bash
npx tsx scripts/cli.ts list-tools
```

## Resources

- [MCP Specification](https://modelcontextprotocol.io/specification/latest)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [Official MCP Servers](https://github.com/modelcontextprotocol/servers)
- [Skill References](./references/)

## License

MIT
