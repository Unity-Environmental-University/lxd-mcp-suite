#!/usr/bin/env bash
set -euo pipefail
SVC=${1:?usage: rotate_token.sh <service-name>}
TOKEN=${2:?usage: rotate_token.sh <service-name> <new-token>}
UNIT="/etc/systemd/system/${SVC}.service"
[ -f "$UNIT" ] || { echo "Service unit not found: $UNIT" >&2; exit 1; }
sed -i "s/^Environment=TOKEN=.*$/Environment=TOKEN=$TOKEN/" "$UNIT"
systemctl daemon-reload
systemctl restart "$SVC"
echo "Token rotated for $SVC"
