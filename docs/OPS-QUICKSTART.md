Non‑Developer Quick Start — LXD MCP Suite

Who this is for
- Team members who want to get the Student Guide and other MCP tools running quickly without deep command‑line experience.

What you’ll set up
- Student Guide MCP over HTTPS on a Linux server (droplet) at a friendly URL, ready for tools to call.
- Optional: firewall & cleanup.

Part A — Fastest Path (Linux droplet)
1) Prepare
   - You need: a Linux server (Ubuntu/Debian), an org GitHub token with read permission.
   - Have a domain (optional) if you want HTTPS (we can also use the server IP temporarily).

2) Download the bootstrap script
   - Log into the server (SSH), then run:
     - export GITHUB_TOKEN="<your GitHub token>"
     - curl -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github.raw" -L \
       https://raw.githubusercontent.com/Unity-Environmental-University/lisa_brain/main/scripts/deploy/unified/bootstrap_suite.sh -o bootstrap.sh

3) Run the installer
   - Basic (no HTTPS yet):
     - sudo bash bootstrap.sh
   - With HTTPS (recommended):
     - sudo bash bootstrap.sh --domain your.domain --install-nginx --enable-tls --email you@domain \
       --gh-token "$GITHUB_TOKEN" --proxy-token "<any long random string>"

4) Confirm it’s working
   - Local health (on the server): curl -sS http://127.0.0.1:8091/healthz
   - Public health (if domain/TLS set): https://your.domain/mcp/student-guide/healthz

5) Call the API (example)
   - Using curl (replace TOKEN if you set one):
     - curl -sS -X POST https://your.domain/mcp/student-guide/call \
       -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
       -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

6) Optional — Firewall and removal
   - Firewall: sudo bash /opt/lxd-webhook/ufw_setup.sh --allow-ssh --allow-http --allow-https --force-enable
   - Uninstall: sudo bash /opt/lxd-webhook/uninstall.sh --purge

Part B — Windows IIS (when the server is back)
- Use the IIS Webhook install guide:
  - scripts/deploy/iis-webhook/README.md
- This covers secure GitHub webhook intake + a queue runner with guardrails.

Part C — Local developer use
1) Run Story/Reflection MCP locally
   - Story Goal MCP: python3 story_goal_mcp.py
   - Reflection MCP: python3 reflection_mcp/mcp_server.py
2) Use the unified generator (advanced)
   - List: python3 scripts/deploy/unified/mcp_installer.py --list
   - Generate local MCP config snippet: python3 scripts/deploy/unified/mcp_installer.py --tool story-goal-mcp --target local-config

Where to get help
- If a step fails, copy/paste the command and its error into chat, and we’ll triage.
- Common issues:
  - Token: ensure your GitHub token allows reading the repos.
  - DNS: your.domain must point to the server’s IP for HTTPS.
  - Nginx reload: sudo nginx -t && sudo systemctl reload nginx

