# Changelog — koolna-node

## [Unreleased]

## 2026-04-06

### Added

- **koolna-node**: add Node.js development image with pnpm, deno

### Fixed

- **koolna-node**: run GPG key import as user, not root, to fix keyring location
- **koolna**: pin stack Dockerfiles to koolna-base digest for reproducible builds
- **koolna**: add explicit USER directives in koolna-python and koolna-node Dockerfiles
- **koolna-node**: add GPG keyserver fallback for CI reliability
- **koolna-node**: remove redundant GPG re-import
