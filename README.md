
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

## Repos (part of the suite)
- student-guide-mcp — agent-first coaching (no drafting). Helps students plan and revise with structured prompts.
- story-goal-mcp — source of truth for stories, acceptance criteria, and sprint meta. Prefer this over ad-hoc TODOs.
- validation-mcp — validation and gating for stories and artifacts; updates Kanban via kanban-mcp. No drafting.
- drafting-mcp (planned) — drafting and writing-eval tools (generation, rubric-based grading, citations/DOI). Optional service.

Coupling and orchestration
- Primary authority: `story-goal-mcp` for story/criteria. Validation services read from its DB when present.
- Coaching avoids drafting: `student-guide-mcp` never drafts. It may consume scores from drafting/validation services.
- Loose coupling: services discover each other via env (`*_MCP_HTTP`/`*_MCP_CMD`) and degrade gracefully when absent.

Migration status
- validation-mcp has been externalized to a sibling repo and references updated.
- drafting-mcp will house evaluate_draft/generate_sample_draft/citations/doi tools, decoupled from validation-mcp.
- kanban-mcp — SQLite Kanban with blocked workflow + events. Great for small project flows.
- story-goal-mcp — goals/stories server. Track outcomes and phases over time.
- reflection-mcp — lightweight provider/LLM adapter (optional) with local memory.

## Bootstrap
Use `scripts/bootstrap.sh` to add servers to your MCP client (adjust paths inside). It generates a local MCP config JSON you can paste into your client.

> Internal Use Only — not licensed for external distribution or hosting.
