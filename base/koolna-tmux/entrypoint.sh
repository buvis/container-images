#!/bin/sh
set -eu

find_koolna_pid() {
  for pid_dir in /proc/[0-9]*; do
    pid=$(basename "$pid_dir")
    [ "$pid" = "1" ] && continue
    [ "$pid" = "$$" ] && continue
    ppid=$(awk '/^PPid:/ {print $2}' "$pid_dir/status" 2>/dev/null) || continue
    [ "$ppid" = "$$" ] && continue
    if [ -f "$pid_dir/cmdline" ]; then
      cmd=$(tr '\0' ' ' < "$pid_dir/cmdline" 2>/dev/null) || continue
      case "$cmd" in
        *"sleep infinity"*) echo "$pid"; return 0;;
      esac
    fi
  done
  return 1
}

echo "waiting for koolna main container process..."
i=0
TARGET_PID=""
while [ -z "$TARGET_PID" ]; do
  i=$((i + 1))
  if [ "$i" -ge 60 ]; then
    echo "timeout: koolna main container process not found after 60s"
    exit 1
  fi
  TARGET_PID=$(find_koolna_pid) || true
  [ -z "$TARGET_PID" ] && sleep 1
done
echo "found koolna main container process at PID $TARGET_PID"

# Use dynamic home from operator env, default to /home/bob
HOME="${KOOLNA_HOME:-/home/bob}"
export HOME
if [ -n "${DOTFILES_METHOD:-}" ] && [ "${DOTFILES_METHOD}" != "none" ]; then
  if [ -n "${DOTFILES_REPO:-}" ] && [ -n "${GIT_USERNAME:-}" ] && [ -n "${GIT_TOKEN:-}" ]; then
    repo_host=$(echo "$DOTFILES_REPO" | sed 's|https://\([^/]*\).*|\1|')
    printf "https://%s:%s@%s\n" "$GIT_USERNAME" "$GIT_TOKEN" "$repo_host" > /tmp/.gitcredentials
    git config --global credential.helper "store --file=/tmp/.gitcredentials"
  fi

  echo "installing dotfiles ($DOTFILES_METHOD)..."
  set +e
  case "$DOTFILES_METHOD" in
    bare-git)
      bare_dir="$HOME/${DOTFILES_BARE_DIR:-.cfg}"
      cache="$HOME/.dotfiles-cache"
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
      eval "${DOTFILES_COMMAND:-}"
      ;;
    clone)
      if [ ! -d "$HOME/.dotfiles/.git" ]; then
        git clone "$DOTFILES_REPO" "$HOME/.dotfiles"
      else
        git -C "$HOME/.dotfiles" pull --ff-only || true
      fi
      ;;
  esac
  dotfiles_exit=$?
  set -e
  if [ "$dotfiles_exit" -ne 0 ]; then
    echo "dotfiles installation exited with status $dotfiles_exit (non-fatal)"
  fi
  rm -f /tmp/.gitcredentials
  git config --global --unset credential.helper 2>/dev/null || true
fi

if [ -n "${INIT_COMMAND:-}" ]; then
  echo "running init command..."
  eval "$INIT_COMMAND"
fi

NSENTER_CMD="nsenter --target $TARGET_PID --mount --uts --ipc --net --pid -- /bin/sh -l"

echo "starting tmux server and configuring defaults"
tmux start-server
tmux set -g remain-on-exit on
tmux set-hook -g pane-died 'respawn-pane'
tmux set -g set-clipboard on

echo "creating tmux session: manager"
tmux new-session -d -s manager "$NSENTER_CMD"

echo "creating tmux session: worker"
tmux new-session -d -s worker "$NSENTER_CMD"

echo "tmux sidecar ready"
exec sleep infinity
