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

install_dotfiles() {
  local repo="$1" method="$2"
  local cache="/workspace/.dotfiles-cache"

  case "$method" in
    bare-git)
      local bare_dir="$HOME/${DOTFILES_BARE_DIR:-.cfg}"
      if [ ! -d "$bare_dir/HEAD" ]; then
        if [ ! -d "$cache/HEAD" ]; then
          rm -rf "$cache"
          git clone --bare "$repo" "$cache"
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
        git clone "$repo" "$HOME/.dotfiles"
      else
        git -C "$HOME/.dotfiles" pull --ff-only || true
      fi
      ;;
  esac

  if [ -n "${DOTFILES_INIT:-}" ]; then
    eval "$DOTFILES_INIT"
  fi
}

if [ -n "${DOTFILES_METHOD:-}" ] && [ "${DOTFILES_METHOD}" != "none" ]; then
  if [ -n "${DOTFILES_REPO:-}" ] && [ -n "${GIT_USERNAME:-}" ] && [ -n "${GIT_TOKEN:-}" ]; then
    repo_host=$(echo "$DOTFILES_REPO" | sed 's|https://\([^/]*\).*|\1|')
    printf "https://%s:%s@%s\n" "$GIT_USERNAME" "$GIT_TOKEN" "$repo_host" > /tmp/.gitcredentials
    git config --global credential.helper "store --file=/tmp/.gitcredentials"
  fi

  if [ -n "${DOTFILES_REPO:-}" ]; then
    log_info "Installing dotfiles ($DOTFILES_METHOD) from $DOTFILES_REPO..."
  else
    log_info "Installing dotfiles ($DOTFILES_METHOD)..."
  fi

  set +e
  install_dotfiles "${DOTFILES_REPO:-}" "$DOTFILES_METHOD"
  dotfiles_exit=$?
  set -e

  if [ "$dotfiles_exit" -ne 0 ]; then
    log_warn "Dotfiles installation exited with status $dotfiles_exit (non-fatal)"
  fi

  rm -f /tmp/.gitcredentials
  git config --global --unset credential.helper 2>/dev/null || true
fi

log_info "koolna-base ready, sleeping"
exec sleep infinity
