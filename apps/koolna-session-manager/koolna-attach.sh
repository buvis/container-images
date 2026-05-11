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
  # $cmd is passed as a single string; tmux re-shells it via $SHELL -c, so
  # the persisted command must NOT contain shell metacharacters, glob
  # patterns, or whitespace-in-args. Today entrypoint.sh writes
  # `nsenter ... /bin/bash -l` which is safe. If that shape ever changes,
  # switch to an argv-array form (`tmux new-session -d -s "$SESSION" --
  # "$@"`) sourced from a NUL-delimited file.
  #
  # TOCTOU absorber: another koolna-attach invocation may have created the
  # session between has-session above and new-session below. The fallback
  # `has-session` distinguishes "raced creation" (benign, attach below) from
  # "real tmux failure" (propagate via set -e).
  tmux new-session -d -s "$SESSION" "$cmd" 2>/dev/null || tmux has-session -t "$SESSION"
fi

exec tmux -2 attach-session -t "$SESSION"
