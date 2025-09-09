
# LXD MCP Suite

Human-friendly quickstarts, MCP client configs, and bootstrap scripts for the Learning eXperience Design (LXD) MCP Suite:
- student-guide-mcp
- kanban-mcp
- story-goal-mcp
- reflection-mcp

## Quickstart
- Ensure Python 3 and an MCP-capable client (Claude Desktop / CLI) are installed.
- Install or clone each server repo locally.
- Add servers to your client using the config examples under `configs/`.

## Windows / PowerShell Notes

PowerShell treats JSON quoting differently from bash and common editors add a UTF‑8 BOM by default. To avoid issues when sending raw JSON‑RPC payloads to stdio servers:

- Prefer file payloads over inline JSON and write them without BOM:

```
$path = Join-Path $env:TEMP 'mcp_payload.json'
[System.IO.File]::WriteAllText($path, '{"jsonrpc":"2.0","id":2,"method":"tools/list"}', (New-Object System.Text.UTF8Encoding($false)))
python clients/python/mcp_call.py --server C:\path\to\mcp_server.py --payload-file $path
```

- Inline JSON often fails due to quoting rules:
  - Not recommended: `--payload '{"jsonrpc": ... }'`
  - Recommended: use `--payload-file` as shown above or the PowerShell wrapper below.

### PowerShell wrapper (helpers)

This repo includes a wrapper that handles encoding/quoting for you:

```
# Examples
powershell -ExecutionPolicy Bypass -File clients\powershell\mcp_call.ps1 \
  -Server C:\path\to\story-goal-mcp\mcp_server.py -InitOnly

powershell -ExecutionPolicy Bypass -File clients\powershell\mcp_call.ps1 \
  -Server C:\path\to\student-guide-mcp\mcp_server.py \
  -PayloadInline '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'

powershell -ExecutionPolicy Bypass -File clients\powershell\mcp_call.ps1 \
  -Server C:\path\to\student-guide-mcp\mcp_server.py \
  -Tool advance_coaching_flow \
  -ArgsJson '{"session_id":"<SESSION>","step":"intent","input":{"claim":"..."}}'
```

## Repos (part of the suite)
- student-guide-mcp — agent-first coaching (no drafting). Helps students plan and revise with structured prompts.
- kanban-mcp — SQLite Kanban with blocked workflow + events. Great for small project flows.
- story-goal-mcp — goals/stories server. Track outcomes and phases over time.
- reflection-mcp — lightweight provider/LLM adapter (optional) with local memory.

## Bootstrap
Use `scripts/bootstrap.sh` to add servers to your MCP client (adjust paths inside). It generates a local MCP config JSON you can paste into your client.

> Internal Use Only — not licensed for external distribution or hosting.
