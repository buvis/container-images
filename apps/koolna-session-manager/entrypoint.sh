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

# Helper functions (json_escape, credential sync, wait_for_bootstrap, ...)
# live in /lib.sh so they can be unit-tested via tests/shell/ without
# spinning up the whole entrypoint. Source before defining set_bootstrap_step
# so the EXIT trap (installed below) can rely on json_escape being available.
. /lib.sh

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
  escaped_step=$(json_escape "$step")
  curl -s -o /dev/null -X PATCH \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/merge-patch+json" \
    --cacert "$CA_CERT" \
    "$API_SERVER/api/v1/namespaces/$ns/pods/$pod_name" \
    -d "{\"metadata\":{\"annotations\":{\"koolna.buvis.net/bootstrap-step\":\"$escaped_step\"}}}" \
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

# Wait for bootstrap.sh to finish (writes /cache/.koolna/ready) or fail
# (touches /cache/.koolna/failed). wait_for_bootstrap is sourced from /lib.sh
# and forwards each phase change to the bootstrap-step annotation as it goes.
# No timeout: if the install genuinely hangs, the readiness probe keeps the
# pod un-ready and an operator can investigate via `kubectl logs ... -c koolna`.
READY_MARKER="$KOOLNA_DIR/ready"
PHASE_FILE="$KOOLNA_DIR/phase"
FAILED_MARKER="$KOOLNA_DIR/failed"
if ! wait_for_bootstrap; then
  # The phase string written by bootstrap.sh's trap is already in
  # "Failed: <phase> (exit <rc>)" shape. Clear our own EXIT trap before
  # exiting so it doesn't re-wrap that string with another "Failed: ..."
  # prefix when we exit non-zero.
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
