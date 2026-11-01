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
- **koolna-dev**: authenticate the GitHub API calls made while installing python, uv and ruff (aqua release lookups, artifact attestations) with a BuildKit secret, so CI builds stop failing on the shared unauthenticated rate limit; the token is scoped to that one step and never stored in the image
- **koolna-dev**: set `BUVIS_AUTO_UPDATE=false` so buvis-gems CLIs (`dot`, `pidash`, ...) stop self-upgrading from PyPI on every start; the upgrade ran synchronously even for `--help`, hanging the goss checks and stalling first use in fresh pods, and it replaced the Renovate-pinned version at runtime
- **koolna-dev**: set `COPILOT_AUTO_UPDATE=false` so the Copilot CLI stops downloading newer CLI versions at launch and runs the Renovate-pinned `npm:@github/copilot` version

## 2026-04-07

### Fixed

- **koolna**: add cargo bin to PATH for cargo-binstall tools

## 2026-04-06

### Added

- **koolna-dev**: add universal image combining Node.js, Python, and Rust
