# Shared bats helpers for shell-script tests.
#
# Each test file should `load lib/common` (relative to tests/shell/).

# Repo root for resolving paths to scripts under test.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
export REPO_ROOT

# Set up an isolated tmpdir for the test, with PATH-front stubs available.
setup_isolated_dirs() {
  TEST_TMPDIR="$(mktemp -d)"
  export TEST_TMPDIR
  export KOOLNA_DIR="$TEST_TMPDIR/cache/.koolna"
  mkdir -p "$KOOLNA_DIR"
  export READY_MARKER="$KOOLNA_DIR/ready"
  export PHASE_FILE="$KOOLNA_DIR/phase"
  export FAILED_MARKER="$KOOLNA_DIR/failed"
}

teardown_isolated_dirs() {
  if [ -n "${TEST_TMPDIR:-}" ] && [ -d "$TEST_TMPDIR" ]; then
    rm -rf "$TEST_TMPDIR"
  fi
}

# Prepend the project's stub directory to PATH so `curl`, `base64`, etc. can
# be intercepted in tests without root.
use_stubs() {
  export STUB_BIN="$TEST_TMPDIR/stubs"
  mkdir -p "$STUB_BIN"
  export PATH="$STUB_BIN:$PATH"
}

# Install a stub script under STUB_BIN. The body is the shell content that
# runs when the stub is invoked (it has access to STUB_LOG and stub-specific
# env vars set by the caller).
install_stub() {
  name="$1"
  body="$2"
  cat > "$STUB_BIN/$name" <<STUB
#!/bin/sh
$body
STUB
  chmod +x "$STUB_BIN/$name"
}
