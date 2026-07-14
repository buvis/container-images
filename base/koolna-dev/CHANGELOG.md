# Changelog — koolna-dev

## [Unreleased]

### Added

- **koolna-dev**: preinstall libffi-dev for Python/Ruby FFI build dependencies
- **koolna-dev**: bake personal tool set into the image (zoxide, rumdl, buvis-gems, yt-dlp, beets, gita, @github/copilot, pake-cli) so cold-pod first-boot does not re-install them at runtime

### Changed

- **koolna-dev**: zoxide and rumdl now install via mise's cargo backend instead of cargo-binstall ARG/RUN; same versions, removes runtime install path

### Fixed

- **koolna-dev**: drop pre-baked `npm:@anthropic-ai/claude-code` so dotfiles install scripts that guard on `command -v claude` actually run the official `claude.ai/install.sh`; the orphaned mise shim was masking the real installer
- **koolna-dev**: install pnpm via mise's npm backend so bumps stop failing on a GitHub release asset (`pnpm-linux-x64.tar.gz`) that upstream does not publish
- **koolna-dev**: vendor the cargo-binstall installer so a version bump no longer fails `sha256sum -c` against a hand-pinned checksum Renovate cannot co-bump

## 2026-04-07

### Fixed

- **koolna**: add cargo bin to PATH for cargo-binstall tools

## 2026-04-06

### Added

- **koolna-dev**: add universal image combining Node.js, Python, and Rust
