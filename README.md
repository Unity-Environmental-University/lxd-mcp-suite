# Suite Meta (MCP Servers)

This repository centralizes quickstarts, MCP client configs, and bootstrap scripts for the suite:
- student-guide-mcp
- kanban-mcp
- story-goal-mcp
- reflection-mcp

## Quickstart
- Ensure Python 3 and an MCP-capable client (Claude Desktop / CLI) are installed.
- Install or clone each server repo locally.
- Add servers to your client using the config examples under `configs/`.

## Repos
- student-guide-mcp: agent-first coaching (no drafting)
- kanban-mcp: SQLite Kanban with blocked workflow and events
- story-goal-mcp: goals/stories server
- reflection-mcp: provider/LLM adapter (optional)

## Bootstrap
Use `scripts/bootstrap.sh` to add servers to your MCP client (adjust paths inside).
