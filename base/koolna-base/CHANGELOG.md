# Changelog — koolna-base

## [Unreleased]

### Changed

- **koolna-base**: strip to slim foundation, remove build-essential, python3, node, tmux, vim, whatwedo

### Added

- **koolna-base**: add neovim

## 2026-03-30

### Fixed

- remove claude-code from default npm packages

## 2026-03-28

### Fixed

- update mise to 2026.3.17 for freethreaded python fix
- remove stale /workspace dir, use $HOME paths

### Documentation

- update changelogs [ci-skip]

## 2026-03-27

### Documentation

- update changelogs [ci-skip]

## 2026-03-28

### Fixed

- update mise to 2026.3.17 for freethreaded python fix
- remove stale /workspace dir, use $HOME paths

### Documentation

- update changelogs [ci-skip]

## 2026-03-25

### Fixed

- remove PEP 668 marker and add pipx
- use system python3 + pip instead of mise-compiled python

### Documentation

- update changelogs [ci-skip]
- update changelogs [ci-skip]

## 2026-03-23

### Fixed

- replace gnupg-curl with dirmngr for keyserver access
- import Node.js GPG keys at build, add shell fallback, and install zsh/fish

### Documentation

- update changelogs [ci-skip]

## 2026-03-22

### Changed

- remove startup.sh and sync-auth-to-secret.sh

### Fixed

- compile python from source, add build deps
- remove @openai/codex-cli from default npm packages

### Documentation

- backfill changelogs for all images [ci-skip]

## 2026-03-20

### Added

- move dotfiles installation to sidecar
- strip terminal stack, keep pure dev environment
- add Meslo LGS Nerd Font for terminal

### Fixed

- clipboard bridge fallback with clickable toast
- make dotfiles installation non-fatal

## 2026-03-19

### Added

- replace script method with command, add init command
- use full repo URL in dotfiles clone commands

### Fixed

- review fixes — command method guard, validation, env var scoping
- clean partial dotfiles cache before re-cloning
- pull dotfiles updates on every pod start

## 2026-03-18

### Added

- universal dotfiles support with configmap defaults
- add clipboard bridge for tmux copy to browser sync

### Fixed

- clone dotfiles to /workspace/.dotfiles, install on startup
- use env vars for mise runtime settings
- suppress mise trust and idiomatic version file warnings

## 2026-02-27

### Fixed

- pin dependencies (#245)

## 2026-02-25

### Changed

- pin mise installer to specific version

### Fixed

- scope sudo to package management and service commands
- validate WebSocket origin against host header

## 2026-01-21

### Added

- add conditional sync-auth-to-secret in startup.sh
- add inotify-tools, kubectl, whatwedo and sync-auth scripts
- port whatwedo session manager from sw-factory

### Fixed

- add mise shims to PATH in .profile for login shells

## 2026-01-12

### Added

- add Python 3.12 to mise config

## 2026-01-11

### Added

- add sync-auth-to-secret script for K8s credential sync

### Fixed

- use correct @openai/codex-cli package name

## 2026-02-17

### Fixed

- fix vifm COPY paths and add koolna-base PLATFORM

## 2026-01-10

### Added

- add proof of concept
- implement xterm/WebSocket terminal client for manager/worker sessions
- implement koolna Go web server with WebSocket proxy
- simplify Dockerfile with Go builder, remove nginx/rust/python
- add placeholder web UI files for session picker and terminal
- add Go placeholder and shell scripts for 2-session layout
- add xterm.js vendor assets for terminal rendering
- add tmux config and clipboard scripts for 2-session setup
- scaffold koolna-base directory structure

### Fixed

- update module github.com/gorilla/websocket to v1.5.3
