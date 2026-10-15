# Changelog — koolna-rust

## [Unreleased]

### Fixed

- **koolna-rust**: vendor the cargo-binstall installer so a version bump no longer fails `sha256sum -c` against a hand-pinned checksum Renovate cannot co-bump

## 2026-04-07

### Fixed

- **koolna**: add cargo bin to PATH for cargo-binstall tools

## 2026-04-06

### Added

- **koolna-rust**: add Rust development image with cargo-binstall tools

### Fixed

- **koolna**: pin stack Dockerfiles to koolna-base digest for reproducible builds
- **koolna-rust**: pin cargo-binstall installer to v1.17.9 with SHA256 verification
