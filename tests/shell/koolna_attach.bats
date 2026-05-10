#!/usr/bin/env bats
#
# Tests for apps/koolna-session-manager/koolna-attach.sh.
#
# A stubbed `tmux` is placed at the front of PATH so we can drive
# has-session's exit code and assert which subcommands were invoked,
# without spinning up a real tmux server.

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

# Stub tmux that records every invocation. has-session returns the value of
# HAS_SESSION_RC (default 0). All other subcommands succeed silently.
install_tmux_stub() {
  install_stub tmux "
echo \"\$@\" >> \"\$TMUX_LOG\"
case \"\$1\" in
  has-session)
    exit \${HAS_SESSION_RC:-0}
    ;;
esac
exit 0
"
}

@test "koolna-attach: attaches directly when web-remote already exists" {
  install_tmux_stub
  HAS_SESSION_RC=0 run sh "$ATTACH"
  [ "$status" -eq 0 ]
  grep -q '^has-session -t web-remote' "$TMUX_LOG"
  ! grep -q '^new-session' "$TMUX_LOG"
  grep -q '^-2 attach-session -t web-remote' "$TMUX_LOG"
}

@test "koolna-attach: recreates session from persisted command when missing" {
  install_tmux_stub
  printf '%s\n' 'nsenter --target 99 -- /bin/bash -l' > "$KOOLNA_WEB_REMOTE_CMD_FILE"
  HAS_SESSION_RC=1 run sh "$ATTACH"
  [ "$status" -eq 0 ]
  grep -q '^has-session -t web-remote' "$TMUX_LOG"
  grep -q '^new-session -d -s web-remote nsenter --target 99 -- /bin/bash -l' "$TMUX_LOG"
  grep -q '^-2 attach-session -t web-remote' "$TMUX_LOG"
}

@test "koolna-attach: exits non-zero with stderr when session missing and cmd file absent" {
  install_tmux_stub
  rm -f "$KOOLNA_WEB_REMOTE_CMD_FILE"
  HAS_SESSION_RC=1 run sh "$ATTACH"
  [ "$status" -ne 0 ]
  [[ "$output" == *"$KOOLNA_WEB_REMOTE_CMD_FILE missing"* ]]
  ! grep -q '^new-session' "$TMUX_LOG"
  ! grep -q '^attach-session' "$TMUX_LOG"
}
