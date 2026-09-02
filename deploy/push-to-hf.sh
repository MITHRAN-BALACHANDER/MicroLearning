#!/usr/bin/env bash
#
# Push this repo to a Hugging Face Space as a single clean commit.
#
# Why not a plain `git push hf master`? Hugging Face rejects any file over 10 MB
# that is not tracked by git-lfs, and Agents/data.zip (60 MB) sits in this
# repo's history. Sending one squashed commit of the current tree, minus the
# large and local-only files, sidesteps that and keeps private history out of a
# Space that has to be public for Meta to reach it.
#
# Usage:
#   ./deploy/push-to-hf.sh <hf-username>/<space-name>
#
# Run it again after any change to redeploy.

set -euo pipefail

SPACE="${1:-}"
if [ -z "$SPACE" ]; then
  echo "usage: $0 <hf-username>/<space-name>" >&2
  exit 1
fi

REMOTE_URL="https://huggingface.co/spaces/${SPACE}"
BRANCH="hf-deploy-$(date +%Y%m%d%H%M%S)"
ORIGINAL_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

# Files that must never reach the Space: too big for it, or local-only state.
EXCLUDE=(
  "Agents/data.zip"
  "Agents/.env"
  "Agents/.env.backup-"*
  "Agents/microlearning.db"
)

cleanup() {
  git checkout --quiet "$ORIGINAL_BRANCH" 2>/dev/null || true
  git branch -D "$BRANCH" --quiet 2>/dev/null || true
}
trap cleanup EXIT

if ! git remote get-url hf >/dev/null 2>&1; then
  echo "Adding 'hf' remote -> $REMOTE_URL"
  git remote add hf "$REMOTE_URL"
else
  git remote set-url hf "$REMOTE_URL"
fi

echo "Building a squashed deploy commit on $BRANCH..."
git checkout --orphan "$BRANCH" --quiet
git add -A

for path in "${EXCLUDE[@]}"; do
  git rm --cached --quiet --ignore-unmatch -r -- "$path" || true
done

git commit --quiet -m "Deploy MicroLearning bot to Hugging Face Space"

echo "Pushing to $REMOTE_URL (main)..."
echo "When prompted, use your HF username and an access token with WRITE scope"
echo "  -> https://huggingface.co/settings/tokens"
git push --force hf "$BRANCH:main"

echo
echo "Done. The Space is building at $REMOTE_URL"
echo "Webhook callback URL:"
echo "  https://$(echo "$SPACE" | tr '/' '-' | tr '[:upper:]' '[:lower:]').hf.space/webhook/whatsapp"
