#!/bin/sh
set -eu

# Bootstrap state protocol (see apps/koolna-git-clone/README.md for details):
#
#   /cache/.koolna/phase   - single-line status string. Last-writer-wins.
#                            Any process with write access can append a phase
#                            (bootstrap.sh, dotfiles install hooks, kubectl exec
#                            during bootstrap). session-manager polls the file
#                            and forwards each new value to the pod's
#                            koolna.buvis.net/bootstrap-step annotation.
#   /cache/.koolna/failed  - one-way failure marker. Once it exists,
#                            session-manager freezes the bootstrap-step
#                            annotation so a late phase write cannot overwrite
#                            the recorded failure. This script's EXIT trap
#                            touches it on any non-zero exit.
#   /cache/.koolna/ready   - one-way success sentinel. session-manager waits
#                            for it before creating tmux sessions and writing
#                            its own /tmp/koolna-ready probe target.

KOOLNA_DIR="${KOOLNA_DIR:-/cache/.koolna}"
READY="$KOOLNA_DIR/ready"
PHASE="$KOOLNA_DIR/phase"
FAILED="$KOOLNA_DIR/failed"
PID_FILE="$KOOLNA_DIR/pid"

# Clear stale signal files from any previous incarnation BEFORE publishing our
# PID. session-manager waits for $PID_FILE before honoring $FAILED/$PHASE, so
# this ordering guarantees the sidecar never observes leftover failure state
# from a prior run as if it belonged to this one.
rm -f "$READY" "$FAILED" "$PHASE"

# Record our PID so the session-manager sidecar can nsenter into the right
# process. Writing before any exec keeps the PID stable for the container's
# lifetime: the final "exec sleep infinity" replaces this shell in place.
echo "$$" > "$PID_FILE"

export PATH="$HOME/.local/bin:$PATH"
export GIT_CONFIG_GLOBAL="$KOOLNA_DIR/.gitconfig"
export MISE_TRUSTED_CONFIG_PATHS="${MISE_TRUSTED_CONFIG_PATHS:-/workspace}"

# Track the last announced phase so the EXIT trap can name where we failed.
# Same shape as session-manager's LAST_STEP tracker (entrypoint.sh:67-95).
LAST_PHASE="starting"
phase() { LAST_PHASE="$1"; echo "$1" > "$PHASE"; echo "[bootstrap] $1"; }

# On any non-zero exit, surface the failing phase via the dedicated marker
# file and a Failed: <phase> (exit <rc>) string in $PHASE. The marker is
# one-way state: once it exists, session-manager freezes the bootstrap-step
# annotation so a late-arriving phase write can't overwrite the failure.
# SIGKILL (e.g. OOM) bypasses this trap; those cases need cgroup-level fixes.
on_exit() {
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "Failed: $LAST_PHASE (exit $rc)" > "$PHASE"
    touch "$FAILED"
  fi
}
trap on_exit EXIT

# When BOOTSTRAP_TEST_MODE is set, stop here. The shell-test harness sources
# this script up to this point to assert trap behaviour without running the
# tool-install pipeline.
if [ -n "${BOOTSTRAP_TEST_MODE:-}" ]; then
  return 0 2>/dev/null || exit 0
fi

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
  phase "Cloning dotfiles"
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
        phase "Running dotfiles install"
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
        phase "Running dotfiles install"
        git --git-dir="$bare_dir" --work-tree="$HOME" merge --ff-only || true
      fi
      git --git-dir="$bare_dir" --work-tree="$HOME" submodule update --init || true
      ;;
    command)
      phase "Running dotfiles install"
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
