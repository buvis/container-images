#!/bin/sh
set -eu

echo "waiting for main container PID 1..."
i=0
while [ ! -e /proc/1/root ]; do
  i=$((i + 1))
  if [ "$i" -ge 60 ]; then
    echo "timeout: main container PID 1 not accessible after 60s"
    exit 1
  fi
  sleep 1
done
echo "main container PID 1 accessible"

NSENTER_CMD="nsenter --target 1 --mount --uts --ipc --net --pid -- /bin/sh -l"

echo "creating tmux session: manager"
tmux new-session -d -s manager "$NSENTER_CMD"

echo "configuring tmux defaults"
tmux set -g remain-on-exit on
tmux set-hook -g pane-died 'respawn-pane'
tmux set -g set-clipboard on

echo "creating tmux session: worker"
tmux new-session -d -s worker "$NSENTER_CMD"

echo "tmux sidecar ready"
exec sleep infinity
