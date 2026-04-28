#!/bin/sh
set -eu

# The koolna container's bootstrap.sh writes its PID to this file as its
# first action. We poll for it and verify the PID is still alive. This is
# more reliable than scanning /proc for a distinctive cmdline because
# bootstrap.sh changes what it's running mid-bootstrap (shell -> dotfiles
# command -> mise install -> sleep infinity, all as the same PID via exec).
KOOLNA_PID_FILE="/cache/.koolna/pid"
echo "waiting for koolna bootstrap.sh to publish its PID at $KOOLNA_PID_FILE..."
i=0
TARGET_PID=""
while [ -z "$TARGET_PID" ]; do
  i=$((i + 1))
  if [ "$i" -ge 60 ]; then
    echo "timeout: koolna PID file not found after 60s"
    exit 1
  fi
  if [ -f "$KOOLNA_PID_FILE" ]; then
    candidate=$(cat "$KOOLNA_PID_FILE" 2>/dev/null || true)
    if [ -n "$candidate" ] && [ -d "/proc/$candidate" ]; then
      TARGET_PID="$candidate"
      break
    fi
  fi
  sleep 1
done
echo "found koolna main container process at PID $TARGET_PID"

# Auto-detect UID, GID, HOME, PATH, and username from main container
KOOLNA_UID=$(awk '/^Uid:/ {print $2}' "/proc/$TARGET_PID/status")
KOOLNA_GID=$(awk '/^Gid:/ {print $2}' "/proc/$TARGET_PID/status")
HOME=$(tr '\0' '\n' < "/proc/$TARGET_PID/environ" | sed -n 's/^HOME=//p')
DETECTED_PATH=$(tr '\0' '\n' < "/proc/$TARGET_PID/environ" | sed -n 's/^PATH=//p')
if [ -n "$DETECTED_PATH" ]; then
  export PATH="$DETECTED_PATH"
fi

NSENTER_ROOT="nsenter --target $TARGET_PID --mount --uts --ipc --net --pid --cgroup --"

# Fallback for HOME if not found in environ
if [ -z "$HOME" ]; then
  HOME=$($NSENTER_ROOT getent passwd "$KOOLNA_UID" 2>/dev/null | cut -d: -f6)
fi
if [ -z "$HOME" ]; then
  if [ "$KOOLNA_UID" = "0" ]; then HOME="/root"; else HOME="/home/user"; fi
fi
export HOME

# Detect username from main container
KOOLNA_USERNAME=$($NSENTER_ROOT getent passwd "$KOOLNA_UID" 2>/dev/null | cut -d: -f1)
if [ -z "$KOOLNA_USERNAME" ]; then
  if [ "$KOOLNA_UID" = "0" ]; then
    KOOLNA_USERNAME="root"
  else
    KOOLNA_USERNAME="user"
  fi
fi

echo "detected uid=$KOOLNA_UID gid=$KOOLNA_GID home=$HOME user=$KOOLNA_USERNAME"

NSENTER_USER="nsenter --target $TARGET_PID --mount --uts --ipc --net --pid --cgroup --setuid $KOOLNA_UID --setgid $KOOLNA_GID --"

# Annotate the pod with the current bootstrap step so the operator can surface
# it in the Koolna CR condition message. Uses the same SA token as credential sync.
# Tracks the last announced step so the EXIT trap can report where we failed.
LAST_STEP="starting"
set_bootstrap_step() {
  step="$1"
  LAST_STEP="$step"
  pod_name="$(hostname)"
  ns="${KOOLNA_NAMESPACE:-koolna}"
  TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token 2>/dev/null) || return 0
  CA_CERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
  API_SERVER="https://kubernetes.default.svc"
  curl -s -o /dev/null -X PATCH \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/merge-patch+json" \
    --cacert "$CA_CERT" \
    "$API_SERVER/api/v1/namespaces/$ns/pods/$pod_name" \
    -d "{\"metadata\":{\"annotations\":{\"koolna.buvis.net/bootstrap-step\":\"$step\"}}}" \
    2>/dev/null || true
}

# On any unexpected non-zero exit, surface which phase failed in the
# bootstrap-step annotation so the Koolna CR condition shows the root cause
# instead of a frozen mid-phase message. SIGKILL (e.g. OOM) bypasses this
# trap - those cases still need cgroup/memory fixes upstream.
on_exit() {
  rc=$?
  if [ "$rc" -ne 0 ]; then
    set_bootstrap_step "Failed: $LAST_STEP (exit $rc)"
  fi
}
trap on_exit EXIT

WS="/workspace"
KOOLNA_DIR="/cache/.koolna"
KOOLNA_GC="$KOOLNA_DIR/.gitconfig"
if [ -f "$KOOLNA_GC" ]; then
  $NSENTER_USER git config --global include.path "$KOOLNA_GC"
fi

# --- credential sync ---
KOOLNA_CREDENTIAL_PATHS="${KOOLNA_CREDENTIAL_PATHS:-.claude/.credentials.json,.codex}"

extract_field() {
  echo "$1" | sed -n 's/.*"'"$2"'"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p'
}

# Encode a relative path to a secret key: strip leading dots from segments, replace / with ---
# .claude/.credentials.json -> claude---credentials.json
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
  last_hash_file="/tmp/.koolna-last-sync-hash"
  if [ -f "$last_hash_file" ] && [ "$(cat "$last_hash_file")" = "$current_hash" ]; then
    return
  fi

  # Sync to per-workspace secret
  upsert_secret "$KOOLNA_AUTH_SECRET" "$ns" "$data_fields" "\"koolna.buvis.net/type\": \"credentials\""
  auth_rc=$?

  # Also sync to shared secret so new workspaces restore these credentials
  upsert_secret "$KOOLNA_SHARED_SECRET" "$ns" "$data_fields" "\"koolna.buvis.net/type\": \"credentials\""
  shared_rc=$?

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
  $NSENTER_USER python3 -c "
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
" 2>/dev/null || echo "warning: failed to set claude onboarding flag"
}

# Pre-bootstrap: restore once so the dev shell sees existing credentials when
# it starts. The 30s polling loop deliberately does NOT start here; it is
# launched post-bootstrap (after ensure_claude_onboarded + sync_credentials)
# so the loop can never observe a transient flagless `.claude.json`.
if [ -n "${KOOLNA_AUTH_SECRET:-}" ]; then
  set_bootstrap_step "Syncing credentials"
  echo "restoring credentials from shared Secret"
  restore_credentials
else
  echo "KOOLNA_AUTH_SECRET not set, skipping credential sync"
fi

# --- sshd setup ---
setup_sshd() {
  SSH_PUBKEY_FILE="/etc/koolna/ssh/authorized_keys"
  [ ! -r "$SSH_PUBKEY_FILE" ] && return

  SSH_HOST_KEY_DIR="/cache/.koolna/ssh"
  SSH_DIR="$HOME/.ssh"

  mkdir -p "$SSH_HOST_KEY_DIR"
  if [ ! -f "$SSH_HOST_KEY_DIR/ssh_host_ed25519_key" ]; then
    echo "generating SSH host key..."
    ssh-keygen -t ed25519 -f "$SSH_HOST_KEY_DIR/ssh_host_ed25519_key" -N "" -q
  fi
  chown root:root "$SSH_HOST_KEY_DIR/ssh_host_ed25519_key"
  chmod 600 "$SSH_HOST_KEY_DIR/ssh_host_ed25519_key"

  mkdir -p "$SSH_DIR"
  cp "$SSH_PUBKEY_FILE" "$SSH_DIR/authorized_keys"
  chmod 700 "$SSH_DIR"
  chmod 600 "$SSH_DIR/authorized_keys"
  chown "$KOOLNA_UID:$KOOLNA_GID" "$SSH_DIR" "$SSH_DIR/authorized_keys"

  # sshd requires the user to exist in the sidecar's /etc/passwd
  if ! grep -q "^${KOOLNA_USERNAME}:" /etc/passwd 2>/dev/null; then
    echo "${KOOLNA_USERNAME}:x:${KOOLNA_UID}:${KOOLNA_GID}::${HOME}:/bin/sh" >> /etc/passwd
  fi

  # sshd requires /run/sshd
  mkdir -p /run/sshd

  PERMIT_ROOT="no"
  if [ "$KOOLNA_USERNAME" = "root" ]; then
    PERMIT_ROOT="prohibit-password"
  fi

  cat > /tmp/sshd_config <<SSHD
Port 2222
HostKey $SSH_HOST_KEY_DIR/ssh_host_ed25519_key
AuthorizedKeysFile $SSH_DIR/authorized_keys
PasswordAuthentication no
PubkeyAuthentication yes
AllowUsers $KOOLNA_USERNAME
PermitRootLogin $PERMIT_ROOT
Subsystem sftp /usr/lib/openssh/sftp-server
SSHD

  set_bootstrap_step "Configuring SSH"
  echo "starting sshd on port 2222"
  /usr/sbin/sshd -D -f /tmp/sshd_config &
}

setup_sshd

KOOLNA_SHELL="${KOOLNA_SHELL:-/bin/bash}"

# Verify requested shell exists, fallback to /bin/sh if not
if ! $NSENTER_USER sh -c "command -v $KOOLNA_SHELL" >/dev/null 2>&1; then
  echo "warning: $KOOLNA_SHELL not found in main container, falling back to /bin/sh"
  KOOLNA_SHELL="/bin/sh"
fi

NSENTER_CMD="$NSENTER_USER $KOOLNA_SHELL -l"

# Wait for the main container's bootstrap.sh to finish dotfiles + mise install.
# That script writes /cache/.koolna/ready when done. The phase file gives us a
# live progress message to surface in the bootstrap-step annotation. No timeout
# here: if the install genuinely hangs, the readiness probe will keep the pod
# un-ready and an operator can investigate via `kubectl logs ... -c koolna`.
READY_MARKER="$KOOLNA_DIR/ready"
PHASE_FILE="$KOOLNA_DIR/phase"
FAILED_MARKER="$KOOLNA_DIR/failed"
last_phase=""
while [ ! -f "$READY_MARKER" ]; do
  if [ -f "$PHASE_FILE" ]; then
    cur_phase=$(cat "$PHASE_FILE" 2>/dev/null || true)
    if [ -n "$cur_phase" ] && [ "$cur_phase" != "$last_phase" ]; then
      set_bootstrap_step "$cur_phase"
      last_phase="$cur_phase"
    fi
  fi
  # Failed marker is one-way state set by bootstrap.sh's EXIT trap. Forward
  # the final phase string once and stop polling so a late phase write from
  # a child process can't overwrite the recorded failure.
  if [ -f "$FAILED_MARKER" ]; then
    break
  fi
  sleep 1
done

if [ -f "$FAILED_MARKER" ]; then
  # Final forward of the failure phase. Closes a race where the trap's
  # phase write lands AFTER this iteration's read but BEFORE the marker
  # check, leaving last_phase pointing at the pre-trap value. Re-reading
  # here and forwarding when it differs guarantees the annotation reflects
  # "Failed: <phase> (exit <rc>)" before we exit.
  final_phase=$(cat "$PHASE_FILE" 2>/dev/null || echo unknown)
  if [ -n "$final_phase" ] && [ "$final_phase" != "$last_phase" ]; then
    set_bootstrap_step "$final_phase"
  fi
  # The phase string written by bootstrap.sh's trap is already in
  # "Failed: <phase> (exit <rc>)" shape. Clear our own EXIT trap before
  # exiting so it doesn't re-wrap that string with another "Failed: ..."
  # prefix when we exit non-zero.
  echo "bootstrap failed: $final_phase"
  trap - EXIT
  exit 1
fi

export LANG=C.UTF-8
export LC_CTYPE=C.UTF-8

# `mise install` of claude (re)creates ~/.claude.json without the onboarding
# flag, so re-merge after the install completes. Push the flagged file to the
# shared Secret immediately so the next restore_credentials loop iteration
# sees matching content and no-ops, breaking the rewrite-on-every-poll loop.
# Order matters: ensure_claude_onboarded MUST run before sync_credentials so
# data_fields includes the flagged content. sync_credentials' hash-skip would
# otherwise pin the secret at the pre-flag hash forever.
ensure_claude_onboarded
if [ -n "${KOOLNA_AUTH_SECRET:-}" ]; then
  sync_credentials
  # Start the 30s polling loop only AFTER the flagged secret has been pushed,
  # so an iteration's restore_credentials cannot race ahead and rewrite local
  # `.claude.json` back to the pre-flag content.
  echo "starting credential sync polling (30s)"
  (
    while true; do
      sleep 30
      sync_credentials
      restore_credentials
    done
  ) &
fi

set_bootstrap_step "Creating sessions"
echo "configuring tmux defaults"
cat > /tmp/tmux.conf <<'EOF'
set -g default-terminal "tmux-256color"
set -g terminal-features[0] "xterm*:256:clipboard:ccolour:cstyle:focus:title"
set -g remain-on-exit on
set-hook -g pane-died 'respawn-pane'
set -g set-clipboard on
EOF

echo "creating tmux sessions"
tmux -f /tmp/tmux.conf new-session -d -s manager "$NSENTER_CMD"
tmux new-session -d -s worker "$NSENTER_CMD"
tmux set -s codepoint-widths "E0B0-E0D6=1" 2>/dev/null || true
rm -f /tmp/tmux.conf

set_bootstrap_step "Ready"
echo "tmux sidecar ready"
# Readiness sentinel: probes check for this file instead of spawning tmux every
# 30s for the pod's lifetime. Container restart removes the tmpfs file, which
# correctly forces the pod un-ready until the entrypoint re-runs to completion.
touch /tmp/koolna-ready
exec sleep infinity
