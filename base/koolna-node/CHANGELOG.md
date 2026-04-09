# Changelog — koolna-node


## 2026-04-09

### Documentation

- update changelogs [skip ci]

## 2026-04-08

### Changed

- pin mise tool versions and add renovate datasource comments

### Documentation

- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]

## 2026-04-07

### Documentation

- update changelogs [skip ci]

## 2026-04-06

### Added

- add Node.js development image with pnpm, deno

### Fixed

- run GPG key import as user, not root, to fix keyring location
- pin stack Dockerfiles to koolna-base digest for reproducible builds
- add explicit USER directives in koolna-python and koolna-node Dockerfiles
- add GPG keyserver fallback for CI reliability
- remove redundant GPG re-import

### Documentation

- update changelogs for image hardening changes
- add changelogs for base slim-down and new stack images
