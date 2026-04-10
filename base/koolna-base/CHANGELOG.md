# Changelog — koolna-base

## [Unreleased]

## 2026-04-06

### Changed

- **koolna-base**: **BREAKING**: strip to slim foundation for stack image split

## 2026-03-30

### Fixed

- **koolna-base**: remove claude-code from default npm packages

## 2026-03-28

### Fixed

- **koolna-base**: update mise to 2026.3.17 for freethreaded python fix
- **koolna-base**: remove stale /workspace dir, use $HOME paths

## 2026-03-25

### Fixed

- **koolna-base**: remove PEP 668 marker and add pipx
- **koolna-base**: use system python3 + pip instead of mise-compiled python

## 2026-03-23

### Fixed

- **koolna-base**: replace gnupg-curl with dirmngr for keyserver access
- **koolna**: import Node.js GPG keys at build, add shell fallback, and install zsh/fish

## 2026-03-22

### Fixed

- **koolna-base**: compile python from source, add build deps
- **koolna-base**: remove @openai/codex-cli from default npm packages

## 2026-03-20

### Added

- **koolna-tmux**: move dotfiles installation to sidecar
- **koolna-base**: add Meslo LGS Nerd Font for terminal

### Changed

- **koolna-base**: **BREAKING**: strip terminal stack, keep pure dev environment

### Fixed

- **koolna-base**: clipboard bridge fallback with clickable toast
- **koolna-base**: make dotfiles installation non-fatal

## 2026-03-19

### Added

- **koolna-base**: replace script method with command, add init command
- **koolna-base**: use full repo URL in dotfiles clone commands

### Fixed

- **koolna**: review fixes — command method guard, validation, env var scoping
- **koolna**: clean partial dotfiles cache before re-cloning
- **koolna**: pull dotfiles updates on every pod start

## 2026-03-18

### Added

- **koolna**: universal dotfiles support with configmap defaults
- **koolna**: add clipboard bridge for tmux copy to browser sync

### Fixed

- **koolna**: clone dotfiles to /workspace/.dotfiles, install on startup
- **koolna-base**: use env vars for mise runtime settings
- **koolna-base**: suppress mise trust and idiomatic version file warnings

## 2026-02-27

### Fixed

- **deps**: pin dependencies (#245)

## 2026-02-25

### Fixed

- **koolna-base**: scope sudo to package management and service commands
- **koolna**: validate WebSocket origin against host header

## 2026-02-17

### Fixed

- **ci**: fix vifm COPY paths and add koolna-base PLATFORM

## 2026-01-21

### Added

- **koolna-base**: add conditional sync-auth-to-secret in startup.sh
- **koolna-base**: add inotify-tools, kubectl, whatwedo and sync-auth scripts
- **koolna-base**: port whatwedo session manager from sw-factory

### Fixed

- **koolna-base**: add mise shims to PATH in .profile for login shells

## 2026-01-12

### Added

- **koolna-base**: add Python 3.12 to mise config

## 2026-01-11

### Added

- **koolna-base**: add sync-auth-to-secret script for K8s credential sync

### Fixed

- **koolna-base**: use correct @openai/codex-cli package name

## 2026-01-10

### Added

- **koolna**: add proof of concept
- implement xterm/WebSocket terminal client for manager/worker sessions
- implement koolna Go web server with WebSocket proxy
- simplify Dockerfile with Go builder, remove nginx/rust/python
- add placeholder web UI files for session picker and terminal
- add Go placeholder and shell scripts for 2-session layout
- add xterm.js vendor assets for terminal rendering
- add tmux config and clipboard scripts for 2-session setup
- scaffold koolna-base directory structure

### Fixed

- **deps**: update module github.com/gorilla/websocket to v1.5.3
