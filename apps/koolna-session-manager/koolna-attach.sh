#!/bin/sh
#
# koolna-attach: ensure the `web-remote` tmux session exists, then attach.
# If the user destroyed it from inside the shell, recreate it from the
# command persisted by entrypoint.sh.

set -eu

CMD_FILE="${KOOLNA_WEB_REMOTE_CMD_FILE:-/tmp/koolna-web-remote-cmd}"
SESSION="web-remote"

# `set -e` short-circuits a `cmd; rc=$?` form, so use the POSIX-safe
# `rc=0; cmd || rc=$?` pattern to capture has-session's exit status.
rc=0
tmux has-session -t "$SESSION" 2>/dev/null || rc=$?
if [ "$rc" -ne 0 ]; then
  if [ ! -f "$CMD_FILE" ]; then
    echo "koolna-attach: $CMD_FILE missing; cannot recreate session" >&2
    exit 1
  fi
  cmd=$(cat "$CMD_FILE")
  # Another invocation may create the session after the has-session check;
  # accept that race only if the session now exists.
  tmux new-session -d -s "$SESSION" "$cmd" 2>/dev/null || tmux has-session -t "$SESSION"
fi

exec tmux -2 attach-session -t "$SESSION"
