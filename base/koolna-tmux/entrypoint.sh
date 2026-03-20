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
        *startup.sh*|*"sleep infinity"*) echo "$pid"; return 0;;
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
