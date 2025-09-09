#!/usr/bin/env bash
set -euo pipefail

# Bootstrap /opt/mcp-suite with HTTPS proxies and/or services for selected tools.
# Requires: Ubuntu/Debian, sudo/root.
#
# Examples:
#   sudo bash scripts/unified/bootstrap_suite.sh \
#     --domain your.domain --install-nginx --enable-tls --email you@domain \
#     --gh-token "<github-token>" --proxy-token "<bearer-token>" \
#     --tools student-guide-mcp,story-goal-mcp --targets http-proxy-linux

BASE="/opt/mcp-suite"
DOMAIN=""
EMAIL=""
INSTALL_NGINX=false
ENABLE_TLS=false
GH_TOKEN=""
PROXY_TOKEN=""
BRANCH="main"
TOOLS="student-guide-mcp"
TARGETS="http-proxy-linux"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base) BASE="$2"; shift 2 ;;
    --domain) DOMAIN="$2"; shift 2 ;;
    --email) EMAIL="$2"; shift 2 ;;
    --install-nginx) INSTALL_NGINX=true; shift ;;
    --enable-tls) ENABLE_TLS=true; shift ;;
    --gh-token) GH_TOKEN="$2"; shift 2 ;;
    --proxy-token) PROXY_TOKEN="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --tools) TOOLS="$2"; shift 2 ;;
    --targets) TARGETS="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y git python3-venv python3-pip curl

if $INSTALL_NGINX; then
  apt-get install -y nginx
  if $ENABLE_TLS; then
    apt-get install -y certbot python3-certbot-nginx
  fi
fi

mkdir -p "$BASE"
cd "$BASE"

# Clone or update suite (current repo)
if [[ -d .git ]]; then
  git fetch --prune && git checkout "$BRANCH" && git pull --ff-only || true
else
  echo "==> Ensure you are executing this script from the suite repo or fetched via raw URL"
fi

# Clone siblings via get_suite
if [[ -n "$GH_TOKEN" ]]; then export GITHUB_TOKEN="$GH_TOKEN"; fi
bash scripts/get_suite.sh --base "$BASE" --use-gh || true

# Generate for each tool/target
IFS=',' read -r -a TOOL_ARR <<< "$TOOLS"
IFS=',' read -r -a TARGET_ARR <<< "$TARGETS"

for tool in "${TOOL_ARR[@]}"; do
  for tgt in "${TARGET_ARR[@]}"; do
    echo "==> Generating $tgt for $tool"
    python3 scripts/unified/mcp_installer.py --tool "$tool" --target "$tgt"
    if [[ "$tgt" == "http-proxy-linux" ]]; then
      OUTDIR="scripts/unified/out/$tool/http-proxy-linux"
      echo "==> Installing proxy for $tool"
      python3 -m venv "$OUTDIR/.venv"
      source "$OUTDIR/.venv/bin/activate"
      pip install -r "$OUTDIR/requirements.txt"
      deactivate
      SVC="/etc/systemd/system/mcp-$tool-proxy.service"
      cp "$OUTDIR/mcp-$tool-proxy.service" "$SVC"
      if [[ -n "$PROXY_TOKEN" ]]; then sed -i "s/^Environment=TOKEN=.*$/Environment=TOKEN=$PROXY_TOKEN/" "$SVC"; fi
      systemctl daemon-reload
      systemctl enable --now "mcp-$tool-proxy.service"
      sleep 1
      curl -fsS http://127.0.0.1:8091/healthz >/dev/null || echo "Warning: proxy health not responding for $tool (port 8091 shared; deploy one tool per host or adjust ports)"
    fi
  done
done

# Nginx (basic) for student-guide path; other tools require additional locations
if $INSTALL_NGINX && [[ -n "$DOMAIN" ]]; then
  echo "==> Configuring nginx for $DOMAIN (student-guide path)"
  cat > /etc/nginx/sites-available/mcp-suite <<NGINX
server {
    listen 80;
    server_name $DOMAIN;
    # Rate limiting (optional): uncomment the lines below and include the map/zone in nginx.conf
    # limit_req zone=mcp burst=10 nodelay;
    location /mcp/student-guide/ {
        proxy_pass http://127.0.0.1:8091/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX
  ln -sf /etc/nginx/sites-available/mcp-suite /etc/nginx/sites-enabled/mcp-suite
  nginx -t && systemctl reload nginx
  if $ENABLE_TLS; then
    if [[ -n "$EMAIL" ]]; then
      certbot --nginx -d "$DOMAIN" --agree-tos -m "$EMAIL" --non-interactive || echo "Certbot failed; continuing with HTTP"
    fi
  fi
fi

echo
echo "Done. Endpoints:"
echo "- Local health:  http://127.0.0.1:8091/healthz (shared port)"
if [[ -n "$DOMAIN" ]]; then
  echo "- Public health: http${ENABLE_TLS:+s}://$DOMAIN/mcp/student-guide/healthz"
  echo "- Public call:   http${ENABLE_TLS:+s}://$DOMAIN/mcp/student-guide/call (Authorization: Bearer $PROXY_TOKEN)"
  echo "Add more locations in nginx for other tools (see scripts/unified/out/<tool>/http-proxy-linux/nginx.conf.example)"
fi
