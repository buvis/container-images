# Changelog — koolna-tmux


## 2026-03-25

### Fixed

- wrap shell check in sh for nsenter compatibility
- fall back to /bin/sh instead of /bin/bash

### Documentation

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
