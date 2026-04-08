# Changelog — koolna-tmux


## 2026-04-08

### Fixed

- add 256-color terminal feature for tmux clients

## 2026-04-07

### Added

- sync credentials to shared secret for cross-workspace reuse

### Fixed

- set TERM for 256-color tmux client attach
- enable 256-color support in tmux sessions

### Documentation

- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]

## 2026-04-06

### Changed

- remove slop from recent changes
- replace token broker with koolna-env-defaults Secret injection

### Fixed

- always run claude bootstrap when token is set (dotfiles may precreate ~/.claude)
- bootstrap claude config on first run when CLAUDE_CODE_OAUTH_TOKEN is set

### Documentation

- update changelogs [skip ci]
- update changelogs [skip ci]

## 2026-04-05

### Added

- add koolna-auth-init for opt-in Claude token injection

### Documentation

- update changelogs [skip ci]

## 2026-04-02

### Fixed

- replace proxy hostname with IP, export cargo timeout for nsenter
- pin proxy hostname in /etc/hosts to avoid DNS contention
- restore WS variable removed during .koolna refactor

### Documentation

- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]

## 2026-04-01

### Changed

- move .koolna config from /workspace to /cache, add CURL_CA_BUNDLE

### Fixed

- create sidecar user for sshd, fix mount script port detection
- run dotfiles/init as user, use FQDN for proxy DNS
- export SSL_CERT_FILE and REQUESTS_CA_BUNDLE for uv/pip proxy trust
- export NODE_EXTRA_CA_CERTS so nsenter'd npm trusts proxy CA

### Documentation

- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]

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
- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs for image-agnostic pod config
- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]

## 2026-04-01

### Changed

- move .koolna config from /workspace to /cache, add CURL_CA_BUNDLE

### Fixed

- create sidecar user for sshd, fix mount script port detection
- run dotfiles/init as user, use FQDN for proxy DNS
- export SSL_CERT_FILE and REQUESTS_CA_BUNDLE for uv/pip proxy trust
- export NODE_EXTRA_CA_CERTS so nsenter'd npm trusts proxy CA

### Documentation

- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]

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
- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs for image-agnostic pod config
- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]

## 2026-04-01

### Changed

- move .koolna config from /workspace to /cache, add CURL_CA_BUNDLE

### Fixed

- create sidecar user for sshd, fix mount script port detection
- run dotfiles/init as user, use FQDN for proxy DNS
- export SSL_CERT_FILE and REQUESTS_CA_BUNDLE for uv/pip proxy trust
- export NODE_EXTRA_CA_CERTS so nsenter'd npm trusts proxy CA

### Documentation

- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]

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
