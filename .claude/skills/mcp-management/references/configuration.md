# MCP Configuration Guide

## Configuration File Structure

MCP servers are configured in `.claude/.mcp.json`:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "executable",
      "args": ["arg1", "arg2"],
      "env": {
        "API_KEY": "value"
      }
    }
  }
}
```

## Common Server Configurations

### Memory Server

Store and retrieve key-value data:

```json
{
  "memory": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-memory"]
  }
}
```

### Filesystem Server

File operations with restricted access:

```json
{
  "filesystem": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-filesystem",
      "/allowed/path"
    ]
  }
}
```

### Brave Search Server

Web search capabilities:

```json
{
  "brave-search": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
    "env": {
      "BRAVE_API_KEY": "${BRAVE_API_KEY}"
    }
  }
}
```

### Puppeteer Server

Browser automation:

```json
{
  "puppeteer": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
  }
}
```

## Environment Variables

Reference env vars with `${VAR_NAME}` syntax in `env` values and `args` (expanded from the scripts' environment; unset ⇒ empty string + warning):

```json
{
  "api-server": {
    "command": "node",
    "args": ["server.js"],
    "env": {
      "API_KEY": "${MY_API_KEY}",
      "BASE_URL": "${API_BASE_URL}"
    }
  }
}
```

## Server Environment

Scripts read `process.env` only; no `.env` file is loaded. A spawned server gets the SDK default environment (`HOME`, `LOGNAME`, `PATH`, `SHELL`, `TERM`, `USER`), plus `HTTPS_PROXY`/`HTTP_PROXY`/`NO_PROXY` (and lowercase), `NODE_EXTRA_CA_CERTS`, `SSL_CERT_FILE` when set, plus its own `env` (expanded). Anything else (e.g. `NPM_CONFIG_REGISTRY`) must be listed in `env`, e.g. `"NPM_CONFIG_REGISTRY": "${NPM_CONFIG_REGISTRY}"`.

## Validation

Config must:
- Be valid JSON
- Include `mcpServers` object
- Each server must have `command` and `args`
- `env` is optional but must be object if present
