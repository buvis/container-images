# Changelog — koolna-tmux


## 2026-03-22

### Added

- move credential sync to sidecar with POSIX sh + curl
- add username/uid/homePath CRD fields, dynamic sidecar HOME

### Changed

- rename dotfilesInit to initCommand

### Fixed

- use bash instead of sh for nsenter login shell
- create sessions before setting global tmux options
- credential sync create-or-update, frontend homePath validation

### Documentation

- document SYS_ADMIN capability requirement
- update changelog [ci-skip]
- backfill changelogs for all images [ci-skip]

## 2026-03-20

### Added

- move dotfiles installation to sidecar
- add tmux sidecar image for terminal decoupling

### Fixed

- address review findings from cycle 1
