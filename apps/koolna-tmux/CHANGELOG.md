# Changelog — koolna-tmux


## 2026-04-01

### Fixed

- export NODE_EXTRA_CA_CERTS so nsenter'd npm trusts proxy CA

## 2026-03-31

### Added

- auto-detect UID/HOME/PATH/username from /proc

### Fixed

- fix dotfiles command syntax error and gitconfig path
- fix chown paths, add GID detection, HOME fallback, cache path
- run dotfiles and init command in main container via nsenter
- silence credential-sync no-op log in polling loop
- trust proxy CA in sidecar before dotfiles install
- create .koolna dir before writing credentials, trust CA before dotfiles

### Documentation

- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs for image-agnostic pod config
- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]

## 2026-03-30

### Changed

- move koolna-cache and koolna-tmux from base to apps

### Documentation

- update changelogs [skip ci]
