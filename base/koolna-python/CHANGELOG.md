# Changelog — koolna-python

## [Unreleased]

### Fixed

- **koolna-python**: authenticate the GitHub API calls made while installing python, uv and ruff (aqua release lookups, artifact attestations) with a BuildKit secret, so CI builds stop failing on the shared unauthenticated rate limit; the token is scoped to that one step and never stored in the image

## 2026-04-06

### Added

- **koolna-python**: add Python development image with uv, ruff, poetry

### Fixed

- **koolna**: pin stack Dockerfiles to koolna-base digest for reproducible builds
- **koolna**: add explicit USER directives in koolna-python and koolna-node Dockerfiles
