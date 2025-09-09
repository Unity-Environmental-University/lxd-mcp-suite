Unified MCP Installer (MVP)

Purpose
- Avoid hand-coding installers per tool/OS. Use one manifest and a small generator to emit:
  - Local MCP client config (stdio) for development
  - Linux systemd units for stdio servers
  - macOS launchd plists (generated)
  - Windows Task Scheduler XML (generated)
  - Optional HTTP proxy service config (Linux) for HTTPS exposure

Quick start
- Non‑developers: See docs/OPS-QUICKSTART.md for one‑command Linux setup.
- Manifest lives at `scripts/deploy/unified/manifest.yaml`. Edit paths or add tools.
- Generate outputs:
  - `python3 scripts/deploy/unified/mcp_installer.py --list`
  - `python3 scripts/deploy/unified/mcp_installer.py --tool student-guide-mcp --target linux-systemd`
  - `python3 scripts/deploy/unified/mcp_installer.py --tool story-goal-mcp --target local-config`

Generated files land under `scripts/deploy/unified/out/<tool>/<target>/` with exact copy/enable commands printed. No privileged actions are performed by default.

Targets (MVP)
- linux-systemd: writes a unit file for ExecStart and a one-liner to enable it.
- local-config: writes a `.mcp/clients.json` snippet for stdio MCP clients.
- macos-launchd: writes a launchd plist and load/unload commands.
- windows-task: emits a Task Scheduler XML and import command.
- http-proxy-linux: writes a minimal Flask+gunicorn proxy wired to the tool and a systemd unit; nginx vhost is shown as a snippet.

Note
- Paths in the manifest assume this repo layout and sibling repos for certain tools; adjust as needed.
- For production HTTPS, prefer a stable proxy (nginx/Apache/IIS) in front of the generated HTTP proxy.

Non‑developer Linux quick start
- Use the bootstrap helper:
  - `sudo bash scripts/deploy/unified/bootstrap_suite.sh --domain your.domain --install-nginx --enable-tls --email you@domain --gh-token "<token>" --proxy-token "<token>"`
  - It clones the suite, generates the Student Guide HTTPS proxy, installs a system service, and (optionally) configures Nginx + TLS.
  - Endpoints after install:
    - Local: `http://127.0.0.1:8091/healthz`
    - Public: `https://your.domain/mcp/student-guide/healthz` and `/call`

