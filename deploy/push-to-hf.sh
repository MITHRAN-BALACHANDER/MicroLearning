#!/usr/bin/env bash
#
# Deploy this repo to a Hugging Face Space.
#
# Uploads via `hf upload`, which authenticates with the token stored by
# `hf auth login`. That deliberately avoids `git push`: HF dropped password
# auth for git, so a stale password in a credential manager breaks the push,
# and pushing this repo's history would be rejected anyway because of the
# >10 MB Agents/data.zip sitting in it.
#
# Files are staged into a temp directory first, so your working tree is never
# touched. `--delete "*"` makes the upload a sync: anything on the Space that
# is not in this payload is removed in the same commit.
#
# Prerequisite (once):
#   hf auth login          # token from https://huggingface.co/settings/tokens
#
# Usage:
#   ./deploy/push-to-hf.sh <hf-username>/<space-name>

set -euo pipefail

SPACE="${1:-}"
if [ -z "$SPACE" ]; then
  echo "usage: $0 <hf-username>/<space-name>" >&2
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"

# Never copied to a public Space: secrets, local state, personal notes.
EXCLUDE_RE='^(Agents/data\.zip|Agents/\.env($|\.)|Agents/microlearning\.db|res\.md|resume\.md|.*\.(db|sqlite3|log)$)'

if ! hf auth whoami >/dev/null 2>&1; then
  echo "ERROR: not logged in to Hugging Face." >&2
  echo "       Run: hf auth login" >&2
  exit 1
fi
echo "==> Authenticated as $(hf auth whoami 2>/dev/null | head -1)"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
STAGE="$WORK/stage"
mkdir -p "$STAGE"

echo "==> Collecting files to deploy"
# Everything git knows about, tracked or not, minus whatever .gitignore covers.
{
  git -C "$REPO_ROOT" ls-files
  git -C "$REPO_ROOT" ls-files --others --exclude-standard
} | sort -u | grep -vE "$EXCLUDE_RE" > "$WORK/payload.txt"

COUNT=0
while read -r f; do
  [ -f "$REPO_ROOT/$f" ] || continue

  # HF rejects any file over 10 MB that is not tracked by git-lfs. Fail here,
  # with a useful message, rather than partway through an upload.
  size="$(wc -c < "$REPO_ROOT/$f")"
  if [ "$size" -gt 10485760 ]; then
    echo "ERROR: $f is $((size / 1048576)) MB - over HF's 10 MB non-LFS limit." >&2
    echo "       Add it to EXCLUDE_RE in this script, or track it with git-lfs." >&2
    exit 1
  fi

  mkdir -p "$STAGE/$(dirname "$f")"
  cp "$REPO_ROOT/$f" "$STAGE/$f"
  COUNT=$((COUNT + 1))
done < "$WORK/payload.txt"

if [ "$COUNT" -eq 0 ]; then
  echo "Nothing to deploy." >&2
  exit 1
fi
echo "    $COUNT files staged"

# The Space needs README.md's YAML frontmatter to build as a Docker Space at
# all; without it HF falls back to whatever sdk the Space was created with.
if ! grep -q '^sdk: docker' "$STAGE/README.md" 2>/dev/null; then
  echo "ERROR: README.md is missing 'sdk: docker' frontmatter." >&2
  exit 1
fi

echo "==> Uploading to https://huggingface.co/spaces/${SPACE}"
# Via the Python API rather than `hf upload`: Git Bash on Windows glob-expands
# the --delete "*" pattern before the CLI ever receives it.
python "$REPO_ROOT/deploy/hf_upload.py" "$SPACE" "$STAGE"

echo
echo "Done. The Space is building at https://huggingface.co/spaces/${SPACE}"

# The serving hostname is not derivable from the repo name - HF assigns it and
# strips characters that are illegal in a DNS label - so ask the API for it.
SUBDOMAIN="$(curl -sf --max-time 20 "https://huggingface.co/api/spaces/${SPACE}" \
  | python -c "import json,sys; print(json.load(sys.stdin).get('subdomain',''))" 2>/dev/null || true)"

if [ -n "$SUBDOMAIN" ]; then
  echo
  echo "Health check (once the build finishes):"
  echo "  curl https://${SUBDOMAIN}.hf.space/health"
  echo "Webhook callback URL (paste this into Meta):"
  echo "  https://${SUBDOMAIN}.hf.space/webhook/whatsapp"
else
  echo "Could not read the Space subdomain; find the URL under the Space's ... menu -> Embed."
fi
