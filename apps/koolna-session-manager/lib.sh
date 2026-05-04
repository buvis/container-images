#!/bin/sh
# Helper functions for entrypoint.sh, extracted into a sourceable lib so the
# functions can be unit-tested standalone via tests/shell/.
#
# Required env when entrypoint.sh sources this:
#   NSENTER_USER, NSENTER_ROOT, KOOLNA_UID, KOOLNA_GID, HOME
#   KOOLNA_AUTH_SECRET, KOOLNA_SHARED_SECRET, KOOLNA_NAMESPACE
#   KOOLNA_CREDENTIAL_PATHS
#
# Tests stub NSENTER_USER/NSENTER_ROOT to empty (so commands run locally) and
# put fake `curl` / `base64` shims on PATH where needed.

# Escape JSON-meaningful characters in a phase string so callers writing
# arbitrary content (e.g. dotfiles repos appending diagnostic detail) can't
# corrupt a merge-patch payload. Strips control chars (CR/LF/TAB) since the
# bootstrap-step annotation is single-line by contract.
json_escape() {
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | tr -d '\r\n\t'
}

# Read a JSON string field from a Kubernetes Secret response body.
extract_field() {
  echo "$1" | sed -n 's/.*"'"$2"'"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p'
}

# Encode a relative path to a secret key: strip leading dots from segments,
# replace / with ---. Example: .claude/.credentials.json -> claude---credentials.json
path_to_key() {
  echo "$1" | sed 's|^\./||; s|^\.|/|; s|/\.|/|g; s|^/||; s|/|---|g'
}

restore_credential_file() {
  val="$1" key="$2" dest="$3"
  [ -z "$val" ] && return

  # Skip write if destination already matches incoming value. Compare the
  # round-tripped base64 form (same encoding pipeline as sync_credentials)
  # so the comparison is symmetric with what was last uploaded.
  if $NSENTER_USER sh -c "[ -f '$dest' ]"; then
    current=$($NSENTER_USER sh -c "base64 < '$dest' | tr -d '\\n'" 2>/dev/null || true)
    if [ "$current" = "$val" ]; then
      return
    fi
  fi

  dir=$(dirname "$dest")
  $NSENTER_ROOT mkdir -p "$dir"
  $NSENTER_ROOT chown "$KOOLNA_UID:$KOOLNA_GID" "$dir"
  if ! echo "$val" | $NSENTER_USER sh -c "base64 -d > '$dest'" 2>/dev/null; then
    echo "credential-restore: failed decoding $key"
  else
    $NSENTER_ROOT chown "$KOOLNA_UID:$KOOLNA_GID" "$dest"
    echo "credential-restore: wrote $dest"
  fi
}

restore_credentials() {
  [ -z "${KOOLNA_SHARED_SECRET:-}" ] && return
  ns="${KOOLNA_NAMESPACE:-default}"
  secret_name="$KOOLNA_SHARED_SECRET"

  TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
  CA_CERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
  API_SERVER="https://kubernetes.default.svc"

  resp=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" \
    --cacert "$CA_CERT" \
    "$API_SERVER/api/v1/namespaces/$ns/secrets/$secret_name")
  http_code=$(echo "$resp" | tail -n1)
  body=$(echo "$resp" | sed '$d')

  [ "$http_code" = "404" ] && return
  if [ "$http_code" != "200" ]; then
    echo "credential-restore: failed ($http_code) reading $ns/$secret_name"
    return
  fi

  IFS=','
  for cred_path in $KOOLNA_CREDENTIAL_PATHS; do
    unset IFS
    key=$(path_to_key "$cred_path")

    # Try exact key match (file entry)
    val=$(extract_field "$body" "$key")
    if [ -n "$val" ]; then
      restore_credential_file "$val" "$key" "$HOME/$cred_path"
      continue
    fi

    # Try prefix match (directory entry)
    dir_keys=$(echo "$body" | grep -o "\"${key}---[^\"]*\"" | tr -d '"')
    for dk in $dir_keys; do
      suffix=$(echo "$dk" | sed "s|^${key}---||")
      val=$(extract_field "$body" "$dk")
      restore_credential_file "$val" "$dk" "$HOME/$cred_path/$suffix"
    done
  done
  unset IFS
}

upsert_secret() {
  secret_name="$1" ns="$2" data_fields="$3" labels="$4"

  TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
  CA_CERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
  API_SERVER="https://kubernetes.default.svc"

  # Use PATCH to merge keys instead of PUT which replaces the entire secret.
  # This prevents wiping credentials that exist in the secret but not yet in
  # this pod (e.g. .claude/.credentials.json before the user authenticates).
  payload="{\"apiVersion\": \"v1\", \"kind\": \"Secret\", \"metadata\": {\"name\": \"$secret_name\", \"namespace\": \"$ns\", \"labels\": {$labels}}, \"type\": \"Opaque\", \"data\": {$data_fields}}"

  resp=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/strategic-merge-patch+json" \
    --cacert "$CA_CERT" \
    "$API_SERVER/api/v1/namespaces/$ns/secrets/$secret_name" \
    -d "$payload")
  if [ "$resp" = "404" ]; then
    resp=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      --cacert "$CA_CERT" \
      "$API_SERVER/api/v1/namespaces/$ns/secrets" \
      -d "$payload")
  fi
  if [ "$resp" != "200" ] && [ "$resp" != "201" ]; then
    echo "credential-sync: failed ($resp) syncing to $ns/$secret_name"
    return 1
  fi
  return 0
}

sync_credentials() {
  ns="${KOOLNA_NAMESPACE:-default}"

  data_fields=""

  IFS=','
  for cred_path in $KOOLNA_CREDENTIAL_PATHS; do
    unset IFS
    full_path="$HOME/$cred_path"

    if $NSENTER_USER sh -c "[ -f '$full_path' ]"; then
      key=$(path_to_key "$cred_path")
      encoded=$($NSENTER_USER sh -c "base64 < '$full_path' | tr -d '\\n'")
      entry="\"$key\": \"$encoded\""
      if [ -n "$data_fields" ]; then
        data_fields="$data_fields, $entry"
      else
        data_fields="$entry"
      fi
    elif $NSENTER_USER sh -c "[ -d '$full_path' ]"; then
      for fname in $($NSENTER_USER sh -c "ls '$full_path'" 2>/dev/null); do
        $NSENTER_USER sh -c "[ -f '$full_path/$fname' ]" || continue
        key=$(path_to_key "$cred_path/$fname")
        encoded=$($NSENTER_USER sh -c "base64 < '$full_path/$fname' | tr -d '\\n'")
        entry="\"$key\": \"$encoded\""
        if [ -n "$data_fields" ]; then
          data_fields="$data_fields, $entry"
        else
          data_fields="$entry"
        fi
      done
    fi
  done
  unset IFS

  if [ -z "$data_fields" ]; then
    return
  fi

  # Skip the API round-trip entirely if nothing changed since the last sync.
  # The hash covers the full data_fields payload, so any key add/remove or
  # content change forces a resync.
  current_hash=$(printf '%s' "$data_fields" | sha256sum | awk '{print $1}')
  last_hash_file="${LAST_SYNC_HASH_FILE:-/tmp/.koolna-last-sync-hash}"
  if [ -f "$last_hash_file" ] && [ "$(cat "$last_hash_file")" = "$current_hash" ]; then
    return
  fi

  # Sync to per-workspace secret. The `|| rc=$?` form is required because
  # `set -e` (script header) would otherwise exit the script on any non-zero
  # upsert_secret return BEFORE the assignment runs, killing the sidecar
  # instead of letting us record the failure.
  auth_rc=0
  upsert_secret "$KOOLNA_AUTH_SECRET" "$ns" "$data_fields" "\"koolna.buvis.net/type\": \"credentials\"" || auth_rc=$?

  # Also sync to shared secret so new workspaces restore these credentials
  shared_rc=0
  upsert_secret "$KOOLNA_SHARED_SECRET" "$ns" "$data_fields" "\"koolna.buvis.net/type\": \"credentials\"" || shared_rc=$?

  # Only record the hash when at least one upsert succeeded. Otherwise a
  # transient k8s API failure would pin the hash and skip every subsequent
  # retry, leaving the Secret stale forever within this pod's lifetime.
  if [ "$auth_rc" -eq 0 ] || [ "$shared_rc" -eq 0 ]; then
    printf '%s' "$current_hash" > "$last_hash_file"
  fi
}

# Ensure ~/.claude.json carries hasCompletedOnboarding=true so the interactive
# `claude` CLI skips the theme picker / login banner. Runs once after the
# main container's bootstrap finishes (post-`/cache/.koolna/ready`), then is
# pushed straight to the shared Secret via sync_credentials so subsequent
# restore_credentials polls see matching content and no-op.
ensure_claude_onboarded() {
  err_file=$(mktemp)
  if ! $NSENTER_USER python3 -c "
import json
path = '$HOME/.claude.json'
try:
    with open(path) as f:
        cfg = json.load(f)
except (FileNotFoundError, ValueError):
    cfg = {}
if cfg.get('hasCompletedOnboarding') is not True:
    cfg['hasCompletedOnboarding'] = True
    with open(path, 'w') as f:
        json.dump(cfg, f, indent=2)
" 2>"$err_file"; then
    echo "warning: failed to set claude onboarding flag"
    while IFS= read -r err_line; do
      echo "  $err_line"
    done <"$err_file"
  fi
  rm -f "$err_file"
}

# Wait for bootstrap.sh to write /cache/.koolna/ready, forwarding any phase
# changes to the bootstrap-step annotation as we go. Stops polling once the
# failed marker appears so a late phase write from a child process cannot
# overwrite the recorded failure. Returns 0 on success, 1 if the failed
# marker appeared (caller surfaces the failure and exits the entrypoint).
#
# Required env: READY_MARKER, PHASE_FILE, FAILED_MARKER, plus a callable
# set_bootstrap_step. POLL_INTERVAL defaults to 1s; tests override to 0.
wait_for_bootstrap() {
  poll_interval="${POLL_INTERVAL:-1}"
  last_phase=""
  while [ ! -f "$READY_MARKER" ]; do
    if [ -f "$PHASE_FILE" ]; then
      cur_phase=$(cat "$PHASE_FILE" 2>/dev/null || true)
      if [ -n "$cur_phase" ] && [ "$cur_phase" != "$last_phase" ]; then
        set_bootstrap_step "$cur_phase"
        last_phase="$cur_phase"
      fi
    fi
    if [ -f "$FAILED_MARKER" ]; then
      break
    fi
    sleep "$poll_interval"
  done

  if [ -f "$FAILED_MARKER" ]; then
    # Final forward of the failure phase. Closes a race where the trap's
    # phase write lands AFTER this iteration's read but BEFORE the marker
    # check, leaving last_phase pointing at the pre-trap value.
    final_phase=$(cat "$PHASE_FILE" 2>/dev/null || echo unknown)
    if [ -n "$final_phase" ] && [ "$final_phase" != "$last_phase" ]; then
      set_bootstrap_step "$final_phase"
    fi
    echo "bootstrap failed: $final_phase"
    return 1
  fi
  return 0
}
