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

# Use dynamic home from operator env, default to /home/bob
HOME="${KOOLNA_HOME:-/home/bob}"
export HOME

# Update CA certificates before any network operations
NSENTER_ROOT="nsenter --target $TARGET_PID --mount --uts --ipc --net --pid --"
if [ -f /usr/local/share/ca-certificates/koolna-cache.crt ]; then
  echo "updating CA certificates..."
  update-ca-certificates 2>/dev/null || echo "update-ca-certificates failed in sidecar (non-fatal)"
  $NSENTER_ROOT update-ca-certificates 2>/dev/null || echo "update-ca-certificates failed in main (non-fatal)"
fi

if [ -n "${DOTFILES_METHOD:-}" ] && [ "${DOTFILES_METHOD}" != "none" ]; then
  if [ -n "${DOTFILES_REPO:-}" ] && [ -n "${GIT_USERNAME:-}" ] && [ -n "${GIT_TOKEN:-}" ]; then
    repo_host=$(echo "$DOTFILES_REPO" | sed 's|https://\([^/]*\).*|\1|')
    printf "https://%s:%s@%s\n" "$GIT_USERNAME" "$GIT_TOKEN" "$repo_host" > /tmp/.gitcredentials
    git config --global credential.helper "store --file=/tmp/.gitcredentials"
  fi

  echo "installing dotfiles ($DOTFILES_METHOD)..."
  set +e
  case "$DOTFILES_METHOD" in
    bare-git)
      bare_dir="$HOME/${DOTFILES_BARE_DIR:-.cfg}"
      cache="$HOME/.cache/dotfiles"
      if [ ! -d "$bare_dir/HEAD" ]; then
        if [ ! -d "$cache/HEAD" ]; then
          rm -rf "$cache"
          git clone --bare "$DOTFILES_REPO" "$cache"
        fi
        cp -a "$cache" "$bare_dir"
        git --git-dir="$bare_dir" --work-tree="$HOME" config status.showUntrackedFiles no
        git --git-dir="$bare_dir" --work-tree="$HOME" checkout 2>/dev/null || {
          mkdir -p "$bare_dir/backup"
          git --git-dir="$bare_dir" --work-tree="$HOME" checkout 2>&1 \
            | grep -E '^\s+' | awk '{print $1}' | while read -r f; do
              mkdir -p "$bare_dir/backup/$(dirname "$f")"
              mv "$HOME/$f" "$bare_dir/backup/$f" 2>/dev/null || true
            done
          git --git-dir="$bare_dir" --work-tree="$HOME" checkout
        }
      else
        git --git-dir="$bare_dir" --work-tree="$HOME" fetch origin || true
        git --git-dir="$bare_dir" --work-tree="$HOME" merge --ff-only || true
      fi
      git --git-dir="$bare_dir" --work-tree="$HOME" submodule update --init || true
      ;;
    command)
      eval "${DOTFILES_COMMAND:-}"
      ;;
    clone)
      if [ ! -d "$HOME/.dotfiles/.git" ]; then
        git clone "$DOTFILES_REPO" "$HOME/.dotfiles"
      else
        git -C "$HOME/.dotfiles" pull --ff-only || true
      fi
      ;;
  esac
  dotfiles_exit=$?
  set -e
  if [ "$dotfiles_exit" -ne 0 ]; then
    echo "dotfiles installation exited with status $dotfiles_exit (non-fatal)"
  fi
  rm -f /tmp/.gitcredentials
  git config --global --unset credential.helper 2>/dev/null || true
fi

if [ -n "${INIT_COMMAND:-}" ]; then
  echo "running init command..."
  eval "$INIT_COMMAND"
fi

# Set up persistent git credentials from workspace/.koolna/
WS="$HOME/workspace"
KOOLNA_DIR="$WS/.koolna"
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
  git config --global include.path "$KOOLNA_GC"
fi

# Fix ownership of directories written by root during dotfiles/init
KOOLNA_UID="${KOOLNA_UID:-1000}"
echo "fixing ownership (uid=$KOOLNA_UID)..."
chown "$KOOLNA_UID:$KOOLNA_UID" "$HOME" 2>/dev/null || true
chown -R "$KOOLNA_UID:$KOOLNA_UID" "$HOME/workspace" 2>/dev/null || true
chown -R "$KOOLNA_UID:$KOOLNA_UID" "$HOME/.cache" 2>/dev/null || true
[ -d "$HOME/.cfg" ] && chown -R "$KOOLNA_UID:$KOOLNA_UID" "$HOME/.cfg" 2>/dev/null || true
[ -d "$HOME/.dotfiles" ] && chown -R "$KOOLNA_UID:$KOOLNA_UID" "$HOME/.dotfiles" 2>/dev/null || true
[ -d "$HOME/.ssh" ] && chown -R "$KOOLNA_UID:$KOOLNA_UID" "$HOME/.ssh" 2>/dev/null || true

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
  dir=$(dirname "$dest")
  mkdir -p "$dir"
  chown "$KOOLNA_UID:$KOOLNA_UID" "$dir"
  if ! echo "$val" | base64 -d > "$dest" 2>/dev/null; then
    echo "credential-restore: failed decoding $key"
  else
    chown "$KOOLNA_UID:$KOOLNA_UID" "$dest"
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

sync_credentials() {
  ns="${KOOLNA_NAMESPACE:-default}"
  secret_name="$KOOLNA_AUTH_SECRET"

  TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
  CA_CERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
  API_SERVER="https://kubernetes.default.svc"

  data_fields=""

  IFS=','
  for cred_path in $KOOLNA_CREDENTIAL_PATHS; do
    unset IFS
    full_path="$HOME/$cred_path"

    if [ -f "$full_path" ]; then
      key=$(path_to_key "$cred_path")
      encoded=$(base64 < "$full_path" | tr -d '\n')
      entry="\"$key\": \"$encoded\""
      if [ -n "$data_fields" ]; then
        data_fields="$data_fields, $entry"
      else
        data_fields="$entry"
      fi
    elif [ -d "$full_path" ]; then
      for file in "$full_path"/*; do
        [ -f "$file" ] || continue
        fname=$(basename "$file")
        key=$(path_to_key "$cred_path/$fname")
        encoded=$(base64 < "$file" | tr -d '\n')
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

  payload="{\"apiVersion\": \"v1\", \"kind\": \"Secret\", \"metadata\": {\"name\": \"$secret_name\", \"namespace\": \"$ns\", \"labels\": {\"koolna.buvis.net/type\": \"credentials\"}}, \"type\": \"Opaque\", \"data\": {$data_fields}}"

  resp=$(curl -s -o /dev/null -w "%{http_code}" -X PUT \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
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

if [ -n "${KOOLNA_AUTH_SECRET:-}" ]; then
  echo "starting credential sync (30s polling)"
  restore_credentials
  (
    while true; do
      sync_credentials
      sleep 30
      restore_credentials
    done
  ) &
else
  echo "KOOLNA_AUTH_SECRET not set, skipping credential sync"
fi

# --- sshd setup ---
setup_sshd() {
  [ -z "${KOOLNA_SSH_PUBKEY:-}" ] && return

  KOOLNA_USERNAME="${KOOLNA_USERNAME:-bob}"
  SSH_HOST_KEY_DIR="$HOME/workspace/.koolna/ssh"
  SSH_DIR="$HOME/.ssh"

  mkdir -p "$SSH_HOST_KEY_DIR"
  if [ ! -f "$SSH_HOST_KEY_DIR/ssh_host_ed25519_key" ]; then
    echo "generating SSH host key..."
    ssh-keygen -t ed25519 -f "$SSH_HOST_KEY_DIR/ssh_host_ed25519_key" -N "" -q
  fi
  chown root:root "$SSH_HOST_KEY_DIR/ssh_host_ed25519_key"
  chmod 600 "$SSH_HOST_KEY_DIR/ssh_host_ed25519_key"

  mkdir -p "$SSH_DIR"
  echo "$KOOLNA_SSH_PUBKEY" > "$SSH_DIR/authorized_keys"
  chmod 700 "$SSH_DIR"
  chmod 600 "$SSH_DIR/authorized_keys"
  chown "$KOOLNA_UID:$KOOLNA_UID" "$SSH_DIR" "$SSH_DIR/authorized_keys"

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

  echo "starting sshd on port 2222"
  /usr/sbin/sshd -D -f /tmp/sshd_config &
}

setup_sshd

KOOLNA_SHELL="${KOOLNA_SHELL:-/bin/bash}"
KOOLNA_UID="${KOOLNA_UID:-1000}"
NSENTER="nsenter --target $TARGET_PID --mount --uts --ipc --net --pid --setuid $KOOLNA_UID --setgid $KOOLNA_UID --"

# Verify requested shell exists, fallback to /bin/sh if not
if ! $NSENTER sh -c "command -v $KOOLNA_SHELL" >/dev/null 2>&1; then
  echo "warning: $KOOLNA_SHELL not found in main container, falling back to /bin/sh"
  KOOLNA_SHELL="/bin/sh"
fi

NSENTER_CMD="$NSENTER $KOOLNA_SHELL -l"

# Bootstrap mise tools inside the main container
if $NSENTER sh -c 'command -v mise >/dev/null 2>&1'; then
  WS="$HOME/workspace"

  # Trust first so config detection works even in paranoid mode
  $NSENTER "$KOOLNA_SHELL" -lc "mise trust $WS 2>/dev/null || true"

  if $NSENTER "$KOOLNA_SHELL" -lc "cd $WS && mise config ls 2>/dev/null" | grep -q .; then

    echo "running mise install in main container..."
    $NSENTER "$KOOLNA_SHELL" -lc 'mise install --yes' 2>&1 || echo "mise install had errors (non-fatal)"
  fi
fi

export LANG=C.UTF-8
export LC_CTYPE=C.UTF-8

echo "creating tmux sessions"
tmux new-session -d -s manager "$NSENTER_CMD"
tmux new-session -d -s worker "$NSENTER_CMD"

echo "configuring tmux defaults"
tmux set -g remain-on-exit on
tmux set-hook -g pane-died 'respawn-pane'
tmux set -g set-clipboard on
tmux set -s codepoint-widths "E0B0-E0D6=1" 2>/dev/null || true

echo "tmux sidecar ready"
exec sleep infinity
