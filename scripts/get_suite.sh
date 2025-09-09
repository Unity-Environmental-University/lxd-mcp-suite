#!/usr/bin/env bash
set -euo pipefail

# Clone the LXD MCP Suite repos into parallel directories.
#
# Usage examples:
#   bash scripts/deploy/get_suite.sh                         # clones into current directory
#   bash scripts/deploy/get_suite.sh --base /opt/lxd-suite   # clones into /opt/lxd-suite
#   GITHUB_TOKEN=... bash scripts/deploy/get_suite.sh        # uses provided token
#   bash scripts/deploy/get_suite.sh --use-gh                # uses `gh auth token` if available
#   bash scripts/deploy/get_suite.sh --org Unity-Environmental-University \
#     --repos student-guide-mcp,kanban-mcp,story-goal-mcp,reflection-mcp,lxd-mcp-suite

ORG="Unity-Environmental-University"
BASE_DIR="$(pwd)"
REPOS="student-guide-mcp,kanban-mcp,story-goal-mcp,reflection-mcp,lxd-mcp-suite"
USE_GH=false
BRANCH="main"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --org) ORG="$2"; shift 2 ;;
    --base) BASE_DIR="$2"; shift 2 ;;
    --repos) REPOS="$2"; shift 2 ;;
    --use-gh) USE_GH=true; shift ;;
    --branch) BRANCH="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

IFS=',' read -r -a REPO_ARR <<< "$REPOS"

get_token() {
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    echo "$GITHUB_TOKEN"
    return 0
  fi
  if $USE_GH; then
    if command -v gh >/dev/null 2>&1; then
      local t
      if t=$(gh auth token 2>/dev/null); then
        echo "$t"
        return 0
      fi
    fi
  fi
  return 1
}

TOKEN=""
if TOKEN=$(get_token); then :; else TOKEN=""; fi

mkdir -p "$BASE_DIR"
cd "$BASE_DIR"

for repo in "${REPO_ARR[@]}"; do
  # Skip empty entries
  [[ -z "$repo" ]] && continue
  url="https://github.com/$ORG/$repo.git"
  if [[ -n "$TOKEN" ]]; then
    clone_url="https://$TOKEN@github.com/$ORG/$repo.git"
  else
    clone_url="$url"
  fi

  if [[ -d "$repo/.git" ]]; then
    echo "==> $repo exists; fetching updates"
    git -C "$repo" remote set-url origin "$url" || true
    git -C "$repo" fetch --prune
    # Try main then master
    if git -C "$repo" rev-parse --verify "$BRANCH" >/dev/null 2>&1; then
      git -C "$repo" checkout "$BRANCH"
    elif git -C "$repo" rev-parse --verify master >/dev/null 2>&1; then
      git -C "$repo" checkout master
    fi
    git -C "$repo" pull --ff-only || true
  else
    echo "==> Cloning $repo into $BASE_DIR"
    git clone --depth 1 --branch "$BRANCH" "$clone_url" "$repo" || {
      echo "   Falling back to default branch for $repo"
      git clone "$clone_url" "$repo"
    }
  fi
done

echo "\nAll done. Cloned/updated repos under: $BASE_DIR"

