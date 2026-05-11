#!/usr/bin/env bats
#
# Tests for apps/koolna-session-manager/koolna-attach.sh.
#
# A stubbed `tmux` is placed at the front of PATH so we can drive
# has-session's exit code and assert which subcommands were invoked,
# without spinning up a real tmux server.
#
# Each tmux invocation is logged as a multi-line block:
#
#     ---
#     argc=<n>
#     arg=<arg_0>
#     arg=<arg_1>
#     ...
#
# Logging argc and each arg on its own `arg=` line preserves argv shape, so
# the recreate test can detect a `"$cmd"` -> `$cmd` regression in
# koolna-attach.sh: the cmd must arrive as a single argv slot, not
# word-split into multiple args.

load lib/common

ATTACH="$REPO_ROOT/apps/koolna-session-manager/koolna-attach.sh"

setup() {
  setup_isolated_dirs
  use_stubs
  export KOOLNA_WEB_REMOTE_CMD_FILE="$TEST_TMPDIR/cmd"
  export TMUX_LOG="$TEST_TMPDIR/tmux.log"
  : > "$TMUX_LOG"
}

teardown() {
  teardown_isolated_dirs
}

# Stub tmux that records every invocation as an argc + arg= block.
# has-session returns the value of HAS_SESSION_RC (default 0). All other
# subcommands succeed silently.
install_tmux_stub() {
  install_stub tmux '
{
  printf -- "---\n"
  printf "argc=%d\n" "$#"
  for a in "$@"; do
    printf "arg=%s\n" "$a"
  done
} >> "$TMUX_LOG"
case "$1" in
  has-session)
    exit ${HAS_SESSION_RC:-0}
    ;;
esac
exit 0
'
}

# block_at_index <log> <n>
# Print the n-th invocation block (1-indexed), excluding the leading "---".
block_at_index() {
  awk -v target="$2" '
    /^---$/ { i++; next }
    i == target { print }
  ' "$1"
}

@test "koolna-attach: attaches directly when web-remote already exists" {
  install_tmux_stub
  HAS_SESSION_RC=0 run sh "$ATTACH"
  [ "$status" -eq 0 ]

  [ "$(grep -c '^---$' "$TMUX_LOG")" -eq 2 ]

  run block_at_index "$TMUX_LOG" 1
  [ "${lines[0]}" = "argc=3" ]
  [ "${lines[1]}" = "arg=has-session" ]
  [ "${lines[2]}" = "arg=-t" ]
  [ "${lines[3]}" = "arg=web-remote" ]

  run block_at_index "$TMUX_LOG" 2
  [ "${lines[0]}" = "argc=4" ]
  [ "${lines[1]}" = "arg=-2" ]
  [ "${lines[2]}" = "arg=attach-session" ]
  [ "${lines[3]}" = "arg=-t" ]
  [ "${lines[4]}" = "arg=web-remote" ]

  ! grep -q '^arg=new-session$' "$TMUX_LOG"
}

@test "koolna-attach: recreates session from persisted command when missing" {
  install_tmux_stub
  printf '%s\n' 'nsenter --target 99 -- /bin/bash -l' > "$KOOLNA_WEB_REMOTE_CMD_FILE"
  HAS_SESSION_RC=1 run sh "$ATTACH"
  [ "$status" -eq 0 ]

  [ "$(grep -c '^---$' "$TMUX_LOG")" -eq 3 ]

  # 2nd invocation must be: tmux new-session -d -s web-remote <cmd>
  # with <cmd> as a SINGLE argv slot. argc=5 catches the unquoted-$cmd
  # regression where the command word-splits into 6 separate args (argc=10).
  run block_at_index "$TMUX_LOG" 2
  [ "${lines[0]}" = "argc=5" ]
  [ "${lines[1]}" = "arg=new-session" ]
  [ "${lines[2]}" = "arg=-d" ]
  [ "${lines[3]}" = "arg=-s" ]
  [ "${lines[4]}" = "arg=web-remote" ]
  [ "${lines[5]}" = "arg=nsenter --target 99 -- /bin/bash -l" ]
}

@test "koolna-attach: exits non-zero with stderr when session missing and cmd file absent" {
  install_tmux_stub
  rm -f "$KOOLNA_WEB_REMOTE_CMD_FILE"
  HAS_SESSION_RC=1 run sh "$ATTACH"
  [ "$status" -ne 0 ]
  [[ "$output" == *"$KOOLNA_WEB_REMOTE_CMD_FILE missing"* ]]
  ! grep -q '^arg=new-session$' "$TMUX_LOG"
  ! grep -q '^arg=attach-session$' "$TMUX_LOG"
}

@test "koolna-attach: shebang, set -eu, parses with bash -n" {
  run bash -n "$ATTACH"
  [ "$status" -eq 0 ]
  head -1 "$ATTACH" | grep -q '^#!'
  grep -q '^set -eu' "$ATTACH"
}
