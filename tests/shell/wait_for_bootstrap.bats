#!/usr/bin/env bats
#
# Tests for apps/koolna-session-manager/lib.sh:wait_for_bootstrap.
#
# wait_for_bootstrap polls $READY_MARKER and $FAILED_MARKER, forwarding
# phase changes via set_bootstrap_step. Tests stub set_bootstrap_step to
# capture forwards into a log file and use POLL_INTERVAL=0 for fast loops.

load lib/common

LIB="$REPO_ROOT/apps/koolna-session-manager/lib.sh"

setup() {
  setup_isolated_dirs
  use_stubs

  export FORWARD_LOG="$TEST_TMPDIR/forwards.log"
  : > "$FORWARD_LOG"

  set_bootstrap_step() {
    echo "$1" >> "$FORWARD_LOG"
  }

  export POLL_INTERVAL=0

  # shellcheck disable=SC1090
  . "$LIB"
}

teardown() {
  teardown_isolated_dirs
}

@test "wait_for_bootstrap: returns 0 immediately when READY already exists" {
  touch "$READY_MARKER"
  run wait_for_bootstrap
  [ "$status" -eq 0 ]
  # No phase forwards because PHASE was never written.
  [ ! -s "$FORWARD_LOG" ] || [ -z "$(cat "$FORWARD_LOG")" ]
}

@test "wait_for_bootstrap: forwards phase changes then returns 0 on READY" {
  (
    sleep 0.05
    echo "Cloning dotfiles" > "$PHASE_FILE"
    sleep 0.05
    echo "Running dotfiles install" > "$PHASE_FILE"
    sleep 0.05
    echo "Installing tools" > "$PHASE_FILE"
    sleep 0.05
    echo "Ready" > "$PHASE_FILE"
    touch "$READY_MARKER"
  ) &
  writer_pid=$!

  run wait_for_bootstrap
  wait "$writer_pid" 2>/dev/null || true

  [ "$status" -eq 0 ]
  [ -s "$FORWARD_LOG" ]
  while IFS= read -r line; do
    case "$line" in
      "Cloning dotfiles"|"Running dotfiles install"|"Installing tools"|"Ready") ;;
      *) echo "unexpected forward: $line" >&2; return 1 ;;
    esac
  done <"$FORWARD_LOG"
}

@test "wait_for_bootstrap: returns 1 when FAILED appears, forwarding final phase" {
  echo "Failed: Installing mise (exit 7)" > "$PHASE_FILE"
  touch "$FAILED_MARKER"

  run wait_for_bootstrap

  [ "$status" -eq 1 ]
  [[ "$output" == *"bootstrap failed: Failed: Installing mise (exit 7)"* ]]
  grep -F "Failed: Installing mise (exit 7)" "$FORWARD_LOG"
}

@test "wait_for_bootstrap: ignores READY-after-FAILED races" {
  echo "Failed: dotfiles step (exit 1)" > "$PHASE_FILE"
  touch "$FAILED_MARKER"

  (
    sleep 0.05
    echo "False recovery" > "$PHASE_FILE"
  ) &
  writer_pid=$!

  run wait_for_bootstrap
  wait "$writer_pid" 2>/dev/null || true

  [ "$status" -eq 1 ]
  [[ "$output" == *"bootstrap failed:"* ]]
}
