#!/bin/bash
# Respawning shell wrapper for tmux sessions

SESSION_TITLE="$1"
HINT_MESSAGE="$2"

cd /workspace || exit

while true; do
  clear
  echo "=== $SESSION_TITLE ==="
  if [ -n "$HINT_MESSAGE" ]; then
    echo "$HINT_MESSAGE"
  fi
  echo ""

  # Start bash and wait for it to exit
  bash

  # When bash exits, show restart message
  echo ""
  echo "Shell exited. Restarting in 2 seconds... (Ctrl+C to prevent)"
  sleep 2 || break  # Break if Ctrl+C during sleep
done

echo "Respawn loop terminated."
