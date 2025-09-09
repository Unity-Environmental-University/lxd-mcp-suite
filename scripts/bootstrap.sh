#!/usr/bin/env bash
set -euo pipefail
# Example: inject MCP servers into a JSON config (adjust paths and client as needed)
CONFIG_OUT="${1:-./mcp_config.local.json}"
cat > "$CONFIG_OUT" <<'JSON'
{
  "mcpServers": {
    "student-guide-mcp": {
      "command": "python3",
      "args": ["/ABS/PATH/student-guide-mcp/mcp_server.py"],
      "env": { "GUIDE_DB_PATH": "/ABS/PATH/.local_context/draftguide.db" }
    },
    "kanban-mcp": {
      "command": "python3",
      "args": ["/ABS/PATH/kanban-mcp/mcp_server.py"],
      "env": { "KANBAN_DB_PATH": "/ABS/PATH/.local_context/kanban.db" }
    },
    "story-goal-mcp": {
      "command": "python3",
      "args": ["/ABS/PATH/story-goal-mcp/mcp_server.py"],
      "env": { "PYTHONUNBUFFERED": "1" }
    },
    "reflection-mcp": {
      "command": "python3",
      "args": ["/ABS/PATH/reflection-mcp/mcp_server.py"],
      "env": { }
    }
  }
}
JSON
echo "Wrote MCP config to: $CONFIG_OUT"
