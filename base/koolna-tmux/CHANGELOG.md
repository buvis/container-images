# Changelog — koolna-tmux


## 2026-03-30

### Added

- move SSH host keys to workspace/.koolna/ssh for persistence
- set up persistent git credentials from workspace/.koolna
- add setup_sshd for SSH access via sidecar
- add openssh-server to sidecar image

### Fixed

- target ownership fix and move dotfiles cache to .cache/
- restrict .git-credentials file to owner-only read
- pass REPO_URL to sidecar for correct credential host
- preserve root ownership on SSH host keys
- allow root SSH login with pubkey when username is root

### Documentation

- update changelogs for storage split and git config fix
- document storage layout and update changelogs
- update changelogs for SSHFS mount feature

## 2026-03-29

### Added

- restore credentials from shared secret
- add credentials label to per-pod secret
- make restore_credentials use KOOLNA_CREDENTIAL_PATHS
- make sync_credentials use KOOLNA_CREDENTIAL_PATHS
- restore credentials from shared secret on startup

### Fixed

- guard KOOLNA_SHARED_SECRET in restore_credentials
- pass val directly to restore_credential_file, fix formatting
- always restore creds, reorder sync-before-restore
- skip restore if local creds exist, chown dirs
- only log credential sync on errors

### Documentation

- update changelogs for credential read/write split
- update changelogs for configurable credential paths
- update changelogs for shared credential secret

## 2026-03-28

### Fixed

- trust workspace before config detection
- use mise CLI for config and node detection
- make mise bootstrap conditional on config and node usage
- trust workspace mise config before install

### Documentation

- update changelogs [ci-skip]
- update changelogs [ci-skip]
- document mise integration and preference
- update changelogs [ci-skip]
- update changelogs [ci-skip]

## 2026-03-29

### Added

- restore credentials from shared secret
- add credentials label to per-pod secret
- make restore_credentials use KOOLNA_CREDENTIAL_PATHS
- make sync_credentials use KOOLNA_CREDENTIAL_PATHS
- restore credentials from shared secret on startup

### Fixed

- guard KOOLNA_SHARED_SECRET in restore_credentials
- pass val directly to restore_credential_file, fix formatting
- always restore creds, reorder sync-before-restore
- skip restore if local creds exist, chown dirs
- only log credential sync on errors

### Documentation

- update changelogs for credential read/write split
- update changelogs for configurable credential paths
- update changelogs for shared credential secret

## 2026-03-28

### Fixed

- trust workspace before config detection
- use mise CLI for config and node detection
- make mise bootstrap conditional on config and node usage
- trust workspace mise config before install

### Documentation

- update changelogs [ci-skip]
- update changelogs [ci-skip]
- document mise integration and preference
- update changelogs [ci-skip]
- update changelogs [ci-skip]

## 2026-03-27

### Fixed

- use C.UTF-8 locale, make codepoint-widths optional
- switch from alpine to debian for glibc PUA character support

### Documentation

- update changelogs [ci-skip]
- update changelogs [ci-skip]

## 2026-03-26

### Fixed

- set UTF-8 locale and powerline codepoint widths for tmux

### Documentation

- update changelogs [ci-skip]

## 2026-03-25

### Fixed

- wrap shell check in sh for nsenter compatibility
- fall back to /bin/sh instead of /bin/bash

### Documentation

- update changelogs [ci-skip]
- update changelogs [ci-skip]

## 2026-03-23

### Fixed

- import Node.js GPG keys at build, add shell fallback, and install zsh/fish
- run mise install via nsenter into main container
- chown home dir after dotfiles install
- nsenter as target user, wait for font before terminal init

### Documentation

- update changelogs [ci-skip]
- update changelogs [ci-skip]
- update changelogs [ci-skip]

## 2026-03-22

### Added

- add configurable shell field
- move credential sync to sidecar with POSIX sh + curl
- add username/uid/homePath CRD fields, dynamic sidecar HOME

### Changed

- rename dotfilesInit to initCommand

### Fixed

- use bash instead of sh for nsenter login shell
- create sessions before setting global tmux options
- credential sync create-or-update, frontend homePath validation

### Documentation

- update changelog [ci-skip]
- document SYS_ADMIN capability requirement
- update changelog [ci-skip]
- backfill changelogs for all images [ci-skip]

## 2026-03-20

### Added

- move dotfiles installation to sidecar
- add tmux sidecar image for terminal decoupling

### Fixed

- address review findings from cycle 1
