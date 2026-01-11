#!/usr/bin/env bash
set -euo pipefail

KOOLNA_NAMESPACE=${KOOLNA_NAMESPACE:-default}
SYNC_INTERVAL=${SYNC_INTERVAL:-30}

if [[ -z "${KOOLNA_AUTH_SECRET:-}" ]]; then
  echo "KOOLNA_AUTH_SECRET is not set; skipping credential sync."
  exit 0
fi

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl is required for credential sync but was not found in PATH." >&2
  exit 1
fi

HOME_DIR=${HOME:-}
CLAUDE_DIR="$HOME_DIR/.claude"
CODEX_DIR="$HOME_DIR/.codex"

mkdir -p "$CLAUDE_DIR" "$CODEX_DIR"

sync_credentials() {
  local -a from_args=()

  if [[ -f "$CLAUDE_DIR/credentials.json" ]]; then
    from_args+=("--from-file=claude-credentials=$CLAUDE_DIR/credentials.json")
  fi

  if [[ -d "$CODEX_DIR" ]]; then
    shopt -s nullglob
    local codex_files=("$CODEX_DIR"/*)
    shopt -u nullglob

    for codex_file in "${codex_files[@]:-}"; do
      [[ -f "$codex_file" ]] || continue
      local key="codex-$(basename "$codex_file")"
      from_args+=("--from-file=${key}=${codex_file}")
    done
  fi

  if [[ ${#from_args[@]} -eq 0 ]]; then
    echo "No credential files found; skipping secret update."
    return
  fi

  echo "Synchronizing credentials to kube secret ${KOOLNA_NAMESPACE}/${KOOLNA_AUTH_SECRET}"
  kubectl create secret generic "$KOOLNA_AUTH_SECRET" \
    --namespace "$KOOLNA_NAMESPACE" \
    --dry-run=client \
    -o yaml \
    "${from_args[@]}" \
    | kubectl apply -f -
}

sync_credentials

if command -v inotifywait >/dev/null 2>&1; then
  echo "Watching credential directories with inotifywait."
  while true; do
    if inotifywait -qq -e close_write,create,delete,moved_to,attrib "$CLAUDE_DIR" "$CODEX_DIR"; then
      sync_credentials
    else
      sleep 1
    fi
  done
else
  echo "inotifywait not available; polling every ${SYNC_INTERVAL}s."
  while true; do
    sync_credentials
    sleep "$SYNC_INTERVAL"
  done
fi
