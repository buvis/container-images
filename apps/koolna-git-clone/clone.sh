#!/bin/sh
# Clones REPO_URL into /workspace, wires up persistent git credentials, and
# writes the koolna bootstrap script that the main container will run as its
# entrypoint. Idempotent: the clone is skipped when /workspace/.git exists and
# the bootstrap script is always rewritten (cheap, keeps upgrades in sync).
#
# Required env:
#   REPO_URL       - https URL to clone
#   REPO_BRANCH    - branch to check out
#   KOOLNA_UID     - UID the main container runs as; receives ownership of
#                    /workspace and /cache so it can write during bootstrap
#   KOOLNA_GID     - GID for the same purpose
#
# Optional env (when pod has a git credentials secret mounted):
#   GIT_USERNAME, GIT_TOKEN, GIT_NAME, GIT_EMAIL
#
# Mounts:
#   /workspace     - target checkout
#   /cache         - cache PVC; holds .koolna/ scripts, git config, ready marker
set -eu

KOOLNA_DIR=/cache/.koolna
CRED="$KOOLNA_DIR/.git-credentials"
GC="$KOOLNA_DIR/.gitconfig"
BOOTSTRAP="$KOOLNA_DIR/bootstrap.sh"

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

# bootstrap.sh runs as PID 1 of the main koolna container. Its memory is
# billed to the koolna cgroup (not the sidecar), so heavy installs get the
# full 8Gi limit. The sidecar waits for /cache/.koolna/ready before creating
# tmux sessions. The script source is baked into this image at /bootstrap.sh
# (see Dockerfile) so it can be unit-tested standalone via tests/shell/.
cp /bootstrap.sh "$BOOTSTRAP"
chmod 0755 "$BOOTSTRAP"

# Let the koolna container (running as KOOLNA_UID) own its workspace and cache
# so bootstrap.sh can write without elevation.
UID_VAL="${KOOLNA_UID:-1000}"
GID_VAL="${KOOLNA_GID:-$UID_VAL}"
chown -R "$UID_VAL:$GID_VAL" /workspace /cache
