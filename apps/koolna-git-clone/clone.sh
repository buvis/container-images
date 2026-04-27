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
# tmux sessions.
cat > "$BOOTSTRAP" <<'BOOTSTRAP_EOF'
#!/bin/sh
set -eu

KOOLNA_DIR=/cache/.koolna
READY="$KOOLNA_DIR/ready"
PHASE="$KOOLNA_DIR/phase"
PID_FILE="$KOOLNA_DIR/pid"

# Record our PID so the session-manager sidecar can nsenter into the right
# process. Writing before any exec keeps the PID stable for the container's
# lifetime: the final "exec sleep infinity" replaces this shell in place.
echo "$$" > "$PID_FILE"

export PATH="$HOME/.local/bin:$PATH"
export GIT_CONFIG_GLOBAL="$KOOLNA_DIR/.gitconfig"
export MISE_TRUSTED_CONFIG_PATHS="${MISE_TRUSTED_CONFIG_PATHS:-/workspace}"

phase() { echo "$1" > "$PHASE"; echo "[bootstrap] $1"; }

rm -f "$READY"

if ! command -v mise >/dev/null 2>&1; then
  phase "Installing mise"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL https://mise.run | sh
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://mise.run | sh
  else
    echo "[bootstrap] FATAL: neither curl nor wget available to install mise" >&2
    exit 1
  fi
fi
mise trust /workspace 2>/dev/null || true

if [ -n "${DOTFILES_METHOD:-}" ] && [ "$DOTFILES_METHOD" != "none" ]; then
  phase "Installing dotfiles"
  case "$DOTFILES_METHOD" in
    bare-git)
      bare_dir="$HOME/${DOTFILES_BARE_DIR:-.cfg}"
      cache="/cache/dotfiles"
      if [ ! -d "$bare_dir/HEAD" ]; then
        if [ ! -d "$cache/HEAD" ]; then
          rm -rf "$cache"
          git clone --bare "$DOTFILES_REPO" "$cache"
        fi
        cp -a "$cache" "$bare_dir"
        git --git-dir="$bare_dir" --work-tree="$HOME" config status.showUntrackedFiles no
        git --git-dir="$bare_dir" --work-tree="$HOME" checkout 2>/dev/null || {
          mkdir -p "$bare_dir/backup"
          git --git-dir="$bare_dir" --work-tree="$HOME" checkout 2>&1 \
            | grep -E '^\s+' | awk '{print $1}' | while read -r f; do
              mkdir -p "$bare_dir/backup/$(dirname "$f")"
              mv "$HOME/$f" "$bare_dir/backup/$f" 2>/dev/null || true
            done
          git --git-dir="$bare_dir" --work-tree="$HOME" checkout
        }
      else
        git --git-dir="$bare_dir" --work-tree="$HOME" fetch origin || true
        git --git-dir="$bare_dir" --work-tree="$HOME" merge --ff-only || true
      fi
      git --git-dir="$bare_dir" --work-tree="$HOME" submodule update --init || true
      ;;
    command)
      sh -c "${DOTFILES_COMMAND:-true}"
      ;;
    clone)
      if [ ! -d "$HOME/.dotfiles/.git" ]; then
        git clone "$DOTFILES_REPO" "$HOME/.dotfiles"
      else
        git -C "$HOME/.dotfiles" pull --ff-only || true
      fi
      ;;
  esac
fi

if [ -n "${INIT_COMMAND:-}" ]; then
  phase "Running init command"
  sh -c "$INIT_COMMAND"
fi

if mise config ls 2>/dev/null | grep -q .; then
  phase "Installing tools"
  cd /workspace && mise install --yes || echo "[bootstrap] mise install had errors (non-fatal)"
fi

phase "Ready"
touch "$READY"
exec sleep infinity
BOOTSTRAP_EOF
chmod 0755 "$BOOTSTRAP"

# Let the koolna container (running as KOOLNA_UID) own its workspace and cache
# so bootstrap.sh can write without elevation.
UID_VAL="${KOOLNA_UID:-1000}"
GID_VAL="${KOOLNA_GID:-$UID_VAL}"
chown -R "$UID_VAL:$GID_VAL" /workspace /cache
