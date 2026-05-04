#!/usr/bin/env bats
#
# Tests for apps/koolna-session-manager/lib.sh credential-sync helpers.
#
# The lib is sourced directly into each test's shell. NSENTER_USER and
# NSENTER_ROOT are stubbed to empty so commands run locally; curl is
# stubbed via PATH for HTTP-side tests.

load lib/common

LIB="$REPO_ROOT/apps/koolna-session-manager/lib.sh"

setup() {
  setup_isolated_dirs
  use_stubs

  # Stubbed nsenter wrappers: empty means "run locally".
  export NSENTER_USER=""
  export NSENTER_ROOT=""
  export KOOLNA_UID="$(id -u)"
  export KOOLNA_GID="$(id -g)"
  export HOME="$TEST_TMPDIR/home"
  mkdir -p "$HOME"

  # shellcheck disable=SC1090
  . "$LIB"
}

teardown() {
  teardown_isolated_dirs
}

# --- json_escape -------------------------------------------------------------

@test "json_escape: passes plain phase string through unchanged" {
  result=$(json_escape "Installing tools")
  [ "$result" = "Installing tools" ]
}

@test "json_escape: backslashes are doubled" {
  result=$(json_escape 'C:\path\to\thing')
  [ "$result" = 'C:\\path\\to\\thing' ]
}

@test "json_escape: double-quotes are backslash-escaped" {
  result=$(json_escape 'said "hi"')
  [ "$result" = 'said \"hi\"' ]
}

@test "json_escape: newlines/tabs/CRs are stripped" {
  input=$(printf 'a\nb\tc\rd')
  result=$(json_escape "$input")
  [ "$result" = "abcd" ]
}

# --- path_to_key -------------------------------------------------------------

@test "path_to_key: hidden file in hidden dir collapses leading dots" {
  result=$(path_to_key ".claude/.credentials.json")
  [ "$result" = "claude---credentials.json" ]
}

@test "path_to_key: top-level hidden dir keeps single leading dot stripped" {
  result=$(path_to_key ".codex")
  [ "$result" = "codex" ]
}

@test "path_to_key: nested non-hidden segments separated by dashes" {
  result=$(path_to_key "config/foo/bar.json")
  [ "$result" = "config---foo---bar.json" ]
}

# --- extract_field -----------------------------------------------------------

@test "extract_field: pulls a string value from JSON-like body" {
  body='{"data":{"foo":"bar","claude---credentials.json":"BASE64DATA"}}'
  result=$(extract_field "$body" "claude---credentials.json")
  [ "$result" = "BASE64DATA" ]
}

@test "extract_field: missing key returns empty" {
  body='{"data":{"foo":"bar"}}'
  result=$(extract_field "$body" "missing")
  [ -z "$result" ]
}

# --- restore_credential_file -------------------------------------------------

@test "restore_credential_file: skips write when destination matches incoming val" {
  dest="$HOME/.claude.json"
  printf '{"hasCompletedOnboarding":true}' > "$dest"
  current_b64=$(base64 < "$dest" | tr -d '\n')

  run restore_credential_file "$current_b64" "test-key" "$dest"

  [ "$status" -eq 0 ]
  [[ "$output" != *"credential-restore: wrote"* ]]
}

@test "restore_credential_file: writes new file when destination differs" {
  dest="$HOME/sub/.claude.json"
  new_content='{"hasCompletedOnboarding":true,"theme":"dark"}'
  new_b64=$(printf '%s' "$new_content" | base64 | tr -d '\n')

  run restore_credential_file "$new_b64" "test-key" "$dest"

  [ "$status" -eq 0 ]
  [ -f "$dest" ]
  [ "$(cat "$dest")" = "$new_content" ]
  [[ "$output" == *"credential-restore: wrote $dest"* ]]
}

@test "restore_credential_file: empty val returns silently without writing" {
  dest="$HOME/.claude.json"
  run restore_credential_file "" "test-key" "$dest"
  [ "$status" -eq 0 ]
  [ ! -f "$dest" ]
  [[ "$output" != *"credential-restore"* ]]
}

# --- upsert_secret -----------------------------------------------------------

@test "upsert_secret: returns 1 on PATCH+POST both 503" {
  if [ ! -r /var/run/secrets/kubernetes.io/serviceaccount/token ]; then
    skip "SA token mount not available in this environment"
  fi
  install_stub curl 'echo "503"; exit 0'
  run upsert_secret "test-secret" "default" "\"k\":\"v\"" "\"label\":\"true\""
  [ "$status" -eq 1 ]
  [[ "$output" == *"credential-sync: failed (503)"* ]]
}
