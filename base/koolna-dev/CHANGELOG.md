# Changelog — koolna-dev

## [Unreleased]

### Added

- **koolna-dev**: preinstall libffi-dev for Python/Ruby FFI build dependencies
- **koolna-dev**: bake personal tool set into the image (zoxide, rumdl, buvis-gems, yt-dlp, beets, gita, @github/copilot, pake-cli, claude-code) so cold-pod first-boot does not re-install them at runtime

### Changed

- **koolna-dev**: zoxide and rumdl now install via mise's cargo backend instead of cargo-binstall ARG/RUN; same versions, removes runtime install path

## 2026-04-07

### Fixed

- **koolna**: add cargo bin to PATH for cargo-binstall tools

## 2026-04-06

### Added

- **koolna-dev**: add universal image combining Node.js, Python, and Rust
