# Changelog — koolna-tmux


## 2026-03-31

### Added

- auto-detect UID, GID, HOME, PATH, and username from main container /proc
- HOME detection fallback via getent passwd

### Changed

- use fixed /workspace and /cache paths instead of $HOME-relative
- detect GID separately from UID for correct file ownership

### Fixed

- run dotfiles and init command in main container via nsenter
- silence credential-sync no-op log in polling loop
- trust proxy CA in sidecar before dotfiles install
- create .koolna dir before writing credentials, trust CA before dotfiles

### Documentation

- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]

## 2026-03-30

### Changed

- move koolna-cache and koolna-tmux from base to apps

### Documentation

- update changelogs [skip ci]
