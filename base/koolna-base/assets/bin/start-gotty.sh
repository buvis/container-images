#!/bin/bash
set -euo pipefail

log() {
  echo "[gotty] $1"
}

SESSIONS=("manager:8080" "worker:8081")
PIDS=()

cleanup() {
  log "Stopping gotty instances..."
  for pid in "${PIDS[@]}"; do
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
  done
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null || true
  done
}

trap cleanup EXIT INT TERM

for entry in "${SESSIONS[@]}"; do
  name="${entry%%:*}"
  port="${entry##*:}"
  log "Starting $name session on http://localhost:${port}"
  /usr/local/bin/gotty \
    --address 127.0.0.1 \
    --port "$port" \
    --permit-write \
    --reconnect \
    --reconnect-time 5 \
    --title-format "tmux: $name" \
    --ws-origin ".*" \
    bash -lc "tmux attach-session -t $name" &
  PIDS+=("$!")
  sleep 0.5
done

log "All gotty sessions launched"
wait -n "${PIDS[@]}"
wait
