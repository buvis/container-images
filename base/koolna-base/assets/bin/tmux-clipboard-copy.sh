#!/usr/bin/env bash
set -euo pipefail

SESSION="${1:-}"
SERVER_URL="${TMUX_CLIPBOARD_BASE_URL:-http://127.0.0.1:4040}"
TIMEOUT="${TMUX_CLIPBOARD_TIMEOUT:-2}"

if [[ -z "$SESSION" ]]; then
  cat >/dev/null
  exit 0
fi

payload="$(cat)"
if [[ -z "$payload" ]]; then
  exit 0
fi

curl --silent --show-error --fail \
  --max-time "$TIMEOUT" \
  -X POST \
  -H 'Content-Type: text/plain; charset=utf-8' \
  --data-binary @- \
  "$SERVER_URL/clipboard/push?session=${SESSION}" <<<"$payload" >/dev/null || true
