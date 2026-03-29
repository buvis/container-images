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
      cache="$HOME/.dotfiles-cache"
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

# Fix ownership of home directory contents created by root during dotfiles/init
KOOLNA_UID="${KOOLNA_UID:-1000}"
echo "fixing home directory ownership (uid=$KOOLNA_UID)..."
chown -R "$KOOLNA_UID:$KOOLNA_UID" "$HOME" 2>/dev/null || true

# --- credential sync ---
extract_field() {
  echo "$1" | sed -n 's/.*"'"$2"'"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p'
}

restore_credentials() {
  ns="${KOOLNA_NAMESPACE:-default}"
  secret_name="$KOOLNA_AUTH_SECRET"

  TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
  CA_CERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
  API_SERVER="https://kubernetes.default.svc"

  resp=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" \
    --cacert "$CA_CERT" \
    "$API_SERVER/api/v1/namespaces/$ns/secrets/$secret_name")
  http_code=$(echo "$resp" | tail -n1)
  body=$(echo "$resp" | sed '$d')

  # 404 means secret doesn't exist yet - skip silently
  [ "$http_code" = "404" ] && return
  if [ "$http_code" != "200" ]; then
    echo "credential-restore: failed ($http_code) reading $ns/$secret_name"
    return
  fi

  # Restore claude credentials (always overwrite - sync runs first to push local changes)
  claude_val=$(extract_field "$body" "claude-credentials")
  if [ -n "$claude_val" ]; then
    mkdir -p "$HOME/.claude"
    chown "$KOOLNA_UID:$KOOLNA_UID" "$HOME/.claude"
    if ! echo "$claude_val" | base64 -d > "$HOME/.claude/credentials.json" 2>/dev/null; then
      echo "credential-restore: failed decoding claude-credentials"
    else
      chown "$KOOLNA_UID:$KOOLNA_UID" "$HOME/.claude/credentials.json"
    fi
  fi

  # Restore codex credentials (always overwrite)
  codex_keys=$(echo "$body" | grep -o '"codex-[^"]*"' | tr -d '"')
  for key in $codex_keys; do
    val=$(extract_field "$body" "$key")
    [ -z "$val" ] && continue
    fname=$(echo "$key" | sed 's/^codex-//')
    mkdir -p "$HOME/.codex"
    chown "$KOOLNA_UID:$KOOLNA_UID" "$HOME/.codex"
    if ! echo "$val" | base64 -d > "$HOME/.codex/$fname" 2>/dev/null; then
      echo "credential-restore: failed decoding $key"
    else
      chown "$KOOLNA_UID:$KOOLNA_UID" "$HOME/.codex/$fname"
    fi
  done
}

sync_credentials() {
  ns="${KOOLNA_NAMESPACE:-default}"
  secret_name="$KOOLNA_AUTH_SECRET"
  claude_creds="$HOME/.claude/credentials.json"
  codex_dir="$HOME/.codex"

  TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
  CA_CERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
  API_SERVER="https://kubernetes.default.svc"

  data_fields=""

  if [ -f "$claude_creds" ]; then
    encoded=$(base64 < "$claude_creds" | tr -d '\n')
    data_fields="\"claude-credentials\": \"$encoded\""
  fi

  if [ -d "$codex_dir" ]; then
    for codex_file in "$codex_dir"/*; do
      [ -f "$codex_file" ] || continue
      fname=$(basename "$codex_file")
      encoded=$(base64 < "$codex_file" | tr -d '\n')
      entry="\"codex-$fname\": \"$encoded\""
      if [ -n "$data_fields" ]; then
        data_fields="$data_fields, $entry"
      else
        data_fields="$entry"
      fi
    done
  fi

  if [ -z "$data_fields" ]; then
    echo "credential-sync: no credential files found, skipping"
    return
  fi

  payload="{\"apiVersion\": \"v1\", \"kind\": \"Secret\", \"metadata\": {\"name\": \"$secret_name\", \"namespace\": \"$ns\"}, \"type\": \"Opaque\", \"data\": {$data_fields}}"

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

    # Import Node.js GPG keys only when node is a configured tool
    if $NSENTER "$KOOLNA_SHELL" -lc "cd $WS && mise ls --current node 2>/dev/null" | grep -q node; then
      echo "importing Node.js GPG keys..."
      # Node.js EDDSA signing key (v24+)
      $NSENTER "$KOOLNA_SHELL" -lc 'gpg --keyserver hkps://keys.openpgp.org --recv-keys 5BE8A3F6C8A5C01D106C0AD820B1A390B168D356 2>/dev/null || true'
      # Node.js RSA signing key (legacy)
      $NSENTER "$KOOLNA_SHELL" -lc 'gpg --keyserver hkps://keys.openpgp.org --recv-keys C82FA3AE1CBEDC6BE46B9360C433C3C1CE20D5E4 2>/dev/null || true'
    fi

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
