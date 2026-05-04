#!/usr/bin/env bats
#
# Tests for apps/koolna-git-clone/bootstrap.sh trap behaviour.
#
# The script's BOOTSTRAP_TEST_MODE env var lets us source it up to and
# including the trap installation, then return cleanly without running the
# tool-install pipeline. We then trigger an exit and assert the trap's
# side effects on the state-protocol files.

load lib/common

BOOTSTRAP="$REPO_ROOT/apps/koolna-git-clone/bootstrap.sh"

setup() {
  setup_isolated_dirs
}

teardown() {
  teardown_isolated_dirs
}

@test "bootstrap.sh: clears stale ready/failed/phase before publishing PID" {
  touch "$READY_MARKER" "$FAILED_MARKER" "$PHASE_FILE"
  BOOTSTRAP_TEST_MODE=1 KOOLNA_DIR="$KOOLNA_DIR" sh "$BOOTSTRAP"
  [ ! -f "$READY_MARKER" ]
  [ ! -f "$FAILED_MARKER" ]
  [ ! -f "$PHASE_FILE" ]
}

@test "bootstrap.sh: writes its PID to the pid file" {
  BOOTSTRAP_TEST_MODE=1 KOOLNA_DIR="$KOOLNA_DIR" sh "$BOOTSTRAP"
  pid_file="$KOOLNA_DIR/pid"
  [ -f "$pid_file" ]
  recorded=$(cat "$pid_file")
  [[ "$recorded" =~ ^[0-9]+$ ]]
}

@test "bootstrap.sh: EXIT trap touches FAILED and writes Failed: <phase> on non-zero exit" {
  cat > "$TEST_TMPDIR/run.sh" <<EOF
set -eu
export BOOTSTRAP_TEST_MODE=1
export KOOLNA_DIR="$KOOLNA_DIR"
. "$BOOTSTRAP"
phase "Custom step"
exit 42
EOF
  run sh "$TEST_TMPDIR/run.sh"
  [ "$status" -eq 42 ]
  [ -f "$FAILED_MARKER" ]
  [ -f "$PHASE_FILE" ]
  contents=$(cat "$PHASE_FILE")
  [ "$contents" = "Failed: Custom step (exit 42)" ]
}

@test "bootstrap.sh: EXIT trap is silent on zero exit" {
  cat > "$TEST_TMPDIR/run.sh" <<EOF
set -eu
export BOOTSTRAP_TEST_MODE=1
export KOOLNA_DIR="$KOOLNA_DIR"
. "$BOOTSTRAP"
phase "Step before clean exit"
exit 0
EOF
  run sh "$TEST_TMPDIR/run.sh"
  [ "$status" -eq 0 ]
  [ ! -f "$FAILED_MARKER" ]
  contents=$(cat "$PHASE_FILE")
  [ "$contents" = "Step before clean exit" ]
}

@test "bootstrap.sh: phase function writes to PHASE file and to stdout" {
  cat > "$TEST_TMPDIR/run.sh" <<EOF
set -eu
export BOOTSTRAP_TEST_MODE=1
export KOOLNA_DIR="$KOOLNA_DIR"
. "$BOOTSTRAP"
phase "Installing X"
EOF
  run sh "$TEST_TMPDIR/run.sh"
  [ "$status" -eq 0 ]
  [[ "$output" == *"[bootstrap] Installing X"* ]]
  [ "$(cat "$PHASE_FILE")" = "Installing X" ]
}
