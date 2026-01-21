#!/bin/bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESPAWN_SCRIPT="${RESPAWN_SCRIPT:-$SCRIPT_DIR/respawn-shell.sh}"
KOOLNA_BIN="${KOOLNA_BIN:-/usr/local/bin/koolna}"
KOOLNA_PORT="${KOOLNA_PORT:-3000}"

log_info "Creating tmux sessions..."

tmux new-session -d -s manager "${RESPAWN_SCRIPT} 'Manager shell' 'Primary manager session'" 2>/dev/null || true
tmux new-session -d -s worker "${RESPAWN_SCRIPT} 'Worker shell' 'Worker session'" 2>/dev/null || true

touch /tmp/tmux-ready

log_info "Launching gotty consoles (manager, worker)..."
"${SCRIPT_DIR}/start-gotty.sh" &
GOTTY_PID=$!

log_info "Starting clipboard bridge on 127.0.0.1:4040"
/usr/local/bin/tmux-clipboard-server.js >/tmp/tmux-clipboard.log 2>&1 &
CLIPBOARD_PID=$!

if [ -n "${KOOLNA_AUTH_SECRET:-}" ]; then
  log_info "Starting auth sync to secret: $KOOLNA_AUTH_SECRET"
  /usr/local/bin/sync-auth-to-secret.sh >/tmp/sync-auth.log 2>&1 &
  SYNC_AUTH_PID=$!
fi

log_info "Starting koolna web server on http://localhost:${KOOLNA_PORT}"
"${KOOLNA_BIN}" --port "${KOOLNA_PORT}" >/tmp/koolna.log 2>&1 &
KOOLNA_PID=$!

shutdown() {
  if [ -n "${SHUTTING_DOWN:-}" ]; then
    return
  fi
  SHUTTING_DOWN=1
  if [ -n "${KOOLNA_PID:-}" ]; then
    log_info "Stopping koolna web server..."
    kill "${KOOLNA_PID}" 2>/dev/null || true
    wait "${KOOLNA_PID}" 2>/dev/null || true
  fi
  if [ -n "${GOTTY_PID:-}" ]; then
    log_info "Stopping gotty web consoles..."
    kill "${GOTTY_PID}" 2>/dev/null || true
    wait "${GOTTY_PID}" 2>/dev/null || true
  fi
  if [ -n "${CLIPBOARD_PID:-}" ]; then
    log_info "Stopping clipboard bridge..."
    kill "${CLIPBOARD_PID}" 2>/dev/null || true
    wait "${CLIPBOARD_PID}" 2>/dev/null || true
  fi
  if [ -n "${SYNC_AUTH_PID:-}" ]; then
    log_info "Stopping auth sync..."
    kill "${SYNC_AUTH_PID}" 2>/dev/null || true
    wait "${SYNC_AUTH_PID}" 2>/dev/null || true
  fi
}

trap shutdown EXIT INT TERM

set +e
wait "${KOOLNA_PID}"
EXIT_STATUS=$?
set -e
shutdown
exit "$EXIT_STATUS"
