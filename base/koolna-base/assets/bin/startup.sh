#!/bin/bash
set -euo pipefail

# Dotfiles are now installed by the tmux-sidecar container.
# This script just keeps the container alive.

echo "[INFO] koolna-base ready, sleeping"
exec sleep infinity
