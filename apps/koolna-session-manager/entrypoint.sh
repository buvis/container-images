#!/bin/sh
set -eu

find_koolna_pid() {
  for pid_dir in /proc/[0-9]*; do
    pid=$(basename "$pid_dir")
    [ "$pid" = "1" ] && continue
    [ "$pid" = "$$" ] && continue
    ppid=$(awk '/^PPid:/ {print $2}' "$pid_dir/status" 2>/dev/null) || continue
    [ "$ppid" = "$$" ] && continue
    if [ -f "$pid_dir/cmdline" ]; then
      cmd=$(tr '\0' ' ' < "$pid_dir/cmdline" 2>/dev/null) || continue
      case "$cmd" in
        *"sleep infinity"*) echo "$pid"; return 0;;
      esac
    fi
  done
  return 1
}

echo "waiting for koolna main container process..."
i=0
TARGET_PID=""
while [ -z "$TARGET_PID" ]; do
  i=$((i + 1))
  if [ "$i" -ge 60 ]; then
    echo "timeout: koolna main container process not found after 60s"
    exit 1
  fi
  TARGET_PID=$(find_koolna_pid) || true
  [ -z "$TARGET_PID" ] && sleep 1
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

NSENTER_ROOT="nsenter --target $TARGET_PID --mount --uts --ipc --net --pid --"

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

NSENTER_USER="nsenter --target $TARGET_PID --mount --uts --ipc --net --pid --setuid $KOOLNA_UID --setgid $KOOLNA_GID --"

# Annotate the pod with the current bootstrap step so the operator can surface
# it in the Koolna CR condition message. Uses the same SA token as credential sync.
set_bootstrap_step() {
  step="$1"
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

# Ensure user-writable directories before dotfiles run as user
chown "$KOOLNA_UID:$KOOLNA_GID" /cache 2>/dev/null || true

if [ -n "${DOTFILES_METHOD:-}" ] && [ "${DOTFILES_METHOD}" != "none" ]; then
  CRED_SETUP=""
  CRED_CLEANUP=""
  if [ -n "${DOTFILES_REPO:-}" ] && [ -n "${GIT_USERNAME:-}" ] && [ -n "${GIT_TOKEN:-}" ]; then
    repo_host=$(echo "$DOTFILES_REPO" | sed 's|https://\([^/]*\).*|\1|')
    CRED_SETUP="printf 'https://%s:%s@%s\n' '$GIT_USERNAME' '$GIT_TOKEN' '$repo_host' > /tmp/.gitcredentials && git config --global credential.helper 'store --file=/tmp/.gitcredentials'"
    CRED_CLEANUP="rm -f /tmp/.gitcredentials; git config --global --unset credential.helper 2>/dev/null || true"
  fi

  set_bootstrap_step "Installing dotfiles"
  echo "installing dotfiles ($DOTFILES_METHOD)..."
  set +e
  case "$DOTFILES_METHOD" in
    bare-git)
      $NSENTER_USER sh -c "
        ${CRED_SETUP}
        bare_dir=\"$HOME/${DOTFILES_BARE_DIR:-.cfg}\"
        cache=\"/cache/dotfiles\"
        if [ ! -d \"\$bare_dir/HEAD\" ]; then
          if [ ! -d \"\$cache/HEAD\" ]; then
            rm -rf \"\$cache\"
            git clone --bare '$DOTFILES_REPO' \"\$cache\"
          fi
          cp -a \"\$cache\" \"\$bare_dir\"
          git --git-dir=\"\$bare_dir\" --work-tree=\"$HOME\" config status.showUntrackedFiles no
          git --git-dir=\"\$bare_dir\" --work-tree=\"$HOME\" checkout 2>/dev/null || {
            mkdir -p \"\$bare_dir/backup\"
            git --git-dir=\"\$bare_dir\" --work-tree=\"$HOME\" checkout 2>&1 \
              | grep -E '^\s+' | awk '{print \$1}' | while read -r f; do
                mkdir -p \"\$bare_dir/backup/\$(dirname \"\$f\")\"
                mv \"$HOME/\$f\" \"\$bare_dir/backup/\$f\" 2>/dev/null || true
              done
            git --git-dir=\"\$bare_dir\" --work-tree=\"$HOME\" checkout
          }
        else
          git --git-dir=\"\$bare_dir\" --work-tree=\"$HOME\" fetch origin || true
          git --git-dir=\"\$bare_dir\" --work-tree=\"$HOME\" merge --ff-only || true
        fi
        git --git-dir=\"\$bare_dir\" --work-tree=\"$HOME\" submodule update --init || true
        ${CRED_CLEANUP}
      "
      ;;
    command)
      $NSENTER_USER sh -c "${CRED_SETUP:-true}; ${DOTFILES_COMMAND:-true}; ${CRED_CLEANUP:-true}"
      ;;
    clone)
      $NSENTER_USER sh -c "
        ${CRED_SETUP}
        if [ ! -d '$HOME/.dotfiles/.git' ]; then
          git clone '$DOTFILES_REPO' '$HOME/.dotfiles'
        else
          git -C '$HOME/.dotfiles' pull --ff-only || true
        fi
        ${CRED_CLEANUP}
      "
      ;;
  esac
  dotfiles_exit=$?
  set -e
  if [ "$dotfiles_exit" -ne 0 ]; then
    echo "dotfiles installation exited with status $dotfiles_exit (non-fatal)"
  fi
fi

if [ -n "${INIT_COMMAND:-}" ]; then
  echo "running init command..."
  $NSENTER_USER sh -c "$INIT_COMMAND"
fi

# Set up persistent git credentials on cache volume (not in workspace)
WS="/workspace"
KOOLNA_DIR="/cache/.koolna"
KOOLNA_CRED="$KOOLNA_DIR/.git-credentials"
KOOLNA_GC="$KOOLNA_DIR/.gitconfig"
if [ -n "${GIT_USERNAME:-}" ] && [ -n "${GIT_TOKEN:-}" ] && [ ! -f "$KOOLNA_CRED" ]; then
  mkdir -p "$KOOLNA_DIR"
  REPO_HOST=$(echo "$REPO_URL" | sed 's|https://\([^/]*\).*|\1|')
  printf "https://%s:%s@%s\n" "$GIT_USERNAME" "$GIT_TOKEN" "$REPO_HOST" > "$KOOLNA_CRED"
  chmod 600 "$KOOLNA_CRED"
  git config -f "$KOOLNA_GC" credential.helper "store --file=$KOOLNA_CRED"
fi
if [ -n "${GIT_NAME:-}" ] && ! git config -f "$KOOLNA_GC" user.name >/dev/null 2>&1; then
  mkdir -p "$KOOLNA_DIR"
  git config -f "$KOOLNA_GC" user.name "$GIT_NAME"
fi
if [ -n "${GIT_EMAIL:-}" ] && ! git config -f "$KOOLNA_GC" user.email >/dev/null 2>&1; then
  mkdir -p "$KOOLNA_DIR"
  git config -f "$KOOLNA_GC" user.email "$GIT_EMAIL"
fi
if [ -f "$KOOLNA_GC" ]; then
  $NSENTER_USER git config --global include.path "$KOOLNA_GC"
fi

# Fix ownership of directories written by root during dotfiles/init
echo "fixing ownership (uid=$KOOLNA_UID)..."
chown "$KOOLNA_UID:$KOOLNA_GID" "$HOME" 2>/dev/null || true
chown -R "$KOOLNA_UID:$KOOLNA_GID" /workspace 2>/dev/null || true
chown -R "$KOOLNA_UID:$KOOLNA_GID" /cache 2>/dev/null || true
[ -d "$HOME/.cfg" ] && chown -R "$KOOLNA_UID:$KOOLNA_GID" "$HOME/.cfg" 2>/dev/null || true
[ -d "$HOME/.dotfiles" ] && chown -R "$KOOLNA_UID:$KOOLNA_GID" "$HOME/.dotfiles" 2>/dev/null || true
[ -d "$HOME/.ssh" ] && chown -R "$KOOLNA_UID:$KOOLNA_GID" "$HOME/.ssh" 2>/dev/null || true

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
  fi
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

  # Also sync to shared secret so new workspaces restore these credentials
  upsert_secret "$KOOLNA_SHARED_SECRET" "$ns" "$data_fields" "\"koolna.buvis.net/type\": \"credentials\""

  printf '%s' "$current_hash" > "$last_hash_file"
}

# Ensure ~/.claude.json carries hasCompletedOnboarding=true so the interactive
# `claude` CLI skips the theme picker / login banner. This must run after every
# restore_credentials, because the credential sync includes .claude.json in
# KOOLNA_CREDENTIAL_PATHS and will overwrite our flag from the shared Secret on
# every poll until the secret itself carries the flag.
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

if [ -n "${KOOLNA_AUTH_SECRET:-}" ]; then
  set_bootstrap_step "Syncing credentials"
  echo "starting credential sync (30s polling)"
  restore_credentials
  ensure_claude_onboarded
  (
    while true; do
      sync_credentials
      sleep 30
      restore_credentials
      ensure_claude_onboarded
    done
  ) &
else
  echo "KOOLNA_AUTH_SECRET not set, skipping credential sync"
  ensure_claude_onboarded
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

# Bootstrap mise tools inside the main container
if $NSENTER_USER sh -c 'command -v mise >/dev/null 2>&1'; then
  # Trust first so config detection works even in paranoid mode
  $NSENTER_USER "$KOOLNA_SHELL" -lc "mise trust $WS 2>/dev/null || true"

  if $NSENTER_USER "$KOOLNA_SHELL" -lc "cd $WS && mise config ls 2>/dev/null" | grep -q .; then

    set_bootstrap_step "Installing tools"
    echo "running mise install in main container..."
    $NSENTER_USER "$KOOLNA_SHELL" -lc 'mise install --yes' 2>&1 || echo "mise install had errors (non-fatal)"
  fi
fi

export LANG=C.UTF-8
export LC_CTYPE=C.UTF-8

# `mise install` of claude (re)creates ~/.claude.json without the onboarding
# flag, so re-merge after the install completes. The credential sync loop also
# re-merges after every restore.
ensure_claude_onboarded

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

