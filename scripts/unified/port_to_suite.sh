#!/usr/bin/env bash
set -euo pipefail

# Port unified installer + docs into the suite repo and open a PR.
# Requires git. Uses gh if available to open PR.
#
# Usage examples:
#   GITHUB_TOKEN=... bash scripts/deploy/unified/port_to_suite.sh \
#     --suite https://github.com/Unity-Environmental-University/lxd-mcp-suite.git \
#     --branch chore/move-unified-installer --open-pr

SUITE_URL="https://github.com/Unity-Environmental-University/lxd-mcp-suite.git"
BRANCH="chore/move-unified-installer"
OPEN_PR=false
WORKDIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --suite) SUITE_URL="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --open-pr) OPEN_PR=true; shift ;;
    --workdir) WORKDIR="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

if [[ -z "$WORKDIR" ]]; then
  WORKDIR="$(mktemp -d)"
fi

echo "==> Cloning suite repo to $WORKDIR"
pushd "$WORKDIR" >/dev/null
git clone "$SUITE_URL" suite
cd suite

echo "==> Creating branch $BRANCH"
git checkout -b "$BRANCH"

echo "==> Copying unified installer and docs"
mkdir -p scripts/unified docs
rsync -a --delete "$ROOT/scripts/deploy/unified/" scripts/unified/
rsync -a "$ROOT/docs/OPS-QUICKSTART.md" docs/ 2>/dev/null || true
rsync -a "$ROOT/scripts/deploy/get_suite.sh" scripts/ 2>/dev/null || true

echo "==> Adding files"
git add scripts/unified docs/OPS-QUICKSTART.md scripts/get_suite.sh 2>/dev/null || true
git status --porcelain

if ! git diff --cached --quiet; then
  git commit -m "feat(unified): add manifest-driven installer, bootstrap, and ops quickstart; include get_suite.sh"
  echo "==> Pushing branch"
  git push -u origin "$BRANCH"
  if $OPEN_PR; then
    if command -v gh >/dev/null 2>&1; then
      gh pr create --fill --title "Move unified installer + ops quickstart into suite" --body "This ports the unified manifest, generator, bootstrap, and non-developer quickstart into the suite repo."
    else
      echo "gh CLI not found; open the PR manually on GitHub."
    fi
  else
    echo "Branch pushed. Open a PR from $BRANCH into default branch."
  fi
else
  echo "No changes to commit (suite may already contain these files)."
fi

popd >/dev/null
echo "Done."

