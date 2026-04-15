#!/bin/sh
# Clones REPO_URL into /workspace on first run, wires up persistent git
# credentials on the cache volume. Idempotent: subsequent runs do nothing if
# /workspace already contains a git repo.
#
# Required env:
#   REPO_URL       - https URL to clone
#   REPO_BRANCH    - branch to check out
#
# Optional env (when pod has a git credentials secret mounted):
#   GIT_USERNAME, GIT_TOKEN, GIT_NAME, GIT_EMAIL
#
# Mounts:
#   /workspace     - target checkout
#   /cache         - cache PVC; holds .koolna/.gitconfig and .git-credentials
set -eu

KOOLNA_DIR=/cache/.koolna
CRED="$KOOLNA_DIR/.git-credentials"
GC="$KOOLNA_DIR/.gitconfig"

# Point git at our gitconfig so it picks up the credential helper we write
# below during the clone. Without this, git falls back to $HOME/.gitconfig -
# empty in this container - and the clone prompts for a username and fails.
export GIT_CONFIG_GLOBAL="$GC"

mkdir -p "$KOOLNA_DIR"

if [ -n "${GIT_USERNAME:-}" ] && [ -n "${GIT_TOKEN:-}" ]; then
  REPO_HOST=$(echo "$REPO_URL" | sed 's|https://\([^/]*\).*|\1|')
  printf 'https://%s:%s@%s\n' "$GIT_USERNAME" "$GIT_TOKEN" "$REPO_HOST" > "$CRED"
  chmod 600 "$CRED"
  git config -f "$GC" credential.helper "store --file=$CRED"
fi

[ -n "${GIT_NAME:-}" ]  && git config -f "$GC" user.name  "$GIT_NAME"
[ -n "${GIT_EMAIL:-}" ] && git config -f "$GC" user.email "$GIT_EMAIL"

if [ ! -d /workspace/.git ]; then
  git clone "$REPO_URL" /tmp/repo
  cp -a /tmp/repo/. /workspace/
  rm -rf /tmp/repo
  cd /workspace && git checkout "$REPO_BRANCH"
fi
