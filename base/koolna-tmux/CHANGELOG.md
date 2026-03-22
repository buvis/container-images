# Changelog — koolna-tmux


## 2026-03-22

### Added

- move credential sync to sidecar with POSIX sh + curl
- add username/uid/homePath CRD fields, dynamic sidecar HOME

### Changed

- rename dotfilesInit to initCommand

### Fixed

- credential sync create-or-update, frontend homePath validation

## 2026-03-20

### Added

- move dotfiles installation to sidecar
- add tmux sidecar image for terminal decoupling

### Fixed

- address review findings from cycle 1
