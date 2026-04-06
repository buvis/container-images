# Changelog — koolna-webui


## 2026-04-06

### Added

- add webui-driven broker bootstrap with paste-credentials flow

### Changed

- replace token broker with koolna-env-defaults Secret injection

### Fixed

- simplify to plain token from setup-token (1 year validity, no refresh needed)

### Documentation

- update changelogs [skip ci]

## 2026-04-05

### Added

- add Claude authentication checkbox to workspace creation form

### Changed

- reduce xterm font size from 14 to 13

### Fixed

- prefix koolna mounts

### Documentation

- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]

## 2026-04-02

### Documentation

- update changelogs [skip ci]

## 2026-04-01

### Fixed

- unmount stale FUSE mount before mkdir in mount script
- clean shutdown of sshfs before port-forward in mount script
- detect gpg-agent SSH socket and use foreground sshfs in mount script
- use StrictHostKeyChecking=no for ephemeral pod mount scripts
- place SSH options before command in mount script pre-connect
- pre-connect SSH in mount script for macOS agent key binding
- create sidecar user for sshd, fix mount script port detection

### Documentation

- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs [skip ci]

## 2026-03-31

### Added

- add tooltip to disabled Mount button
- add SSH key help text to create form
- add SSH key help text to Settings page

### Fixed

- restore existence check in MountScript, update tests
- remove user config fields from create form
- remove username/uid/homePath from create API
- use fixed /workspace path in mount script
- fix EnvVarEditor focus loss and remove value masking

### Documentation

- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs for image-agnostic pod config
- update changelogs [skip ci]

## 2026-03-30

### Added

- add env var section to create form
- add Settings page with env var defaults editor
- add EnvVarEditor component
- add frontend env var types and API functions
- create per-koolna env secret in create flow
- add env var CRUD API handlers
- add koolna-env-defaults Secret deploy manifest
- add Mount button and modal to KoolnaList
- add sshPublicKey to frontend types and create form
- add mount-script endpoint for SSHFS mount
- add sshPublicKey to backend create/defaults/response

### Changed

- revert(deps): revert typescript 6.0.2 bump, typescript-eslint requires <6.0.0

### Fixed

- clean up orphan env secret on CR patch failure
- use useEffect for EnvVarEditor external sync
- validate env var names and allow empty values in create form
- remove redundant Back button from Settings page
- use stable IDs in EnvVarEditor for correct state tracking
- add server-side env var name validation
- upsert env secret and patch CR in UpdateKoolnaEnv
- show OS-specific unmount commands in modal
- harden mount script SSH options and input validation

### Documentation

- update changelogs [skip ci]
- update changelogs [skip ci]
- update changelogs for env var config feature
- update changelogs [ci-skip]
- update changelogs for SSHFS mount feature
- update changelogs [ci-skip]

## 2026-03-29

### Documentation

- update changelogs [ci-skip]

## 2026-03-27

### Added

- disable terminal buttons when pod not ready

### Fixed

- use full page navigation to/from terminal for clean WebGL lifecycle
- use popstate handler instead of pageshow for Firefox back button
- reload on Firefox bfcache restore for browser back button
- use full navigation when leaving terminal to fix Firefox blank page
- handle Firefox bfcache blank page on back navigation
- remove debug logging, canvas addon, unicode11 addon

### Documentation

- update changelogs [ci-skip]
- update changelogs [ci-skip]
- update changelogs [ci-skip]
- update changelogs [ci-skip]
- update changelogs [ci-skip]
- update changelogs [ci-skip]

## 2026-03-26

### Fixed

- log all websocket messages for debugging
- dump all high-byte websocket messages for debugging
- log powerline bytes from websocket for debugging
- decode websocket binary to string for proper glyph rendering
- add inline powerline render test

### Documentation

- update changelogs [ci-skip]
- update changelogs [ci-skip]
- update changelogs [ci-skip]
- update changelogs [ci-skip]
- update changelogs [ci-skip]
- update changelogs [ci-skip]
- update changelogs [ci-skip]

## 2026-03-25

### Fixed

- update all non-major dependencies (#339)
- upgrade to @xterm/ packages for proper customGlyphs support
- add renderer diagnostics logging to console
- fall back to canvas renderer when WebGL unavailable
- use WebGL renderer with explicit customGlyphs for powerline
- remove canvas addon, rely on built-in custom glyph rendering
- add unicode11 addon for proper glyph width calculation
- load canvas addon after terminal is attached to DOM
- use canvas renderer for proper nerd font glyph rendering

### Documentation

- update changelogs [ci-skip]
- update changelogs [ci-skip]
- update changelogs [ci-skip]
- update changelogs [ci-skip]
- update changelogs [ci-skip]
- update changelogs [ci-skip]
- update changelogs [ci-skip]
- update changelogs [ci-skip]

## 2026-03-23

### Fixed

- use MesloLGS NF font for body text
- nsenter as target user, wait for font before terminal init

### Documentation

- update changelogs [ci-skip]
- update changelogs [ci-skip]

## 2026-03-22

### Added

- add configurable shell field
- add username/uid/homePath to create form and API

### Changed

- rename dotfilesInit to initCommand

### Fixed

- restore git fields as required in create form
- make git fields optional, fix status.currentBranch path
- credential sync create-or-update, frontend homePath validation
- harden HomePath validation, fix UID=0 pointer bug

### Documentation

- backfill changelogs for all images [ci-skip]

## 2026-03-21

### Added

- add form validation with field help tooltips

### Fixed

- show field help tooltip on hover instead of click

## 2026-03-20

### Added

- persist git credentials in home volume, add git identity
- replace gotty frontend with raw terminal protocol
- add MesloLGS Nerd Font for terminal rendering
- replace gotty proxy with kubectl exec terminal

### Fixed

- show git identity and credentials fields unconditionally
- remove unused container field in xterm-adapter
- address review findings from cycle 1

## 2026-03-19

### Added

- move private repo after URL, auto-detect on branch fetch failure
- conditional dotfiles form with none/bare-git/clone/command
- add dotfilesCommand and dotfilesInit fields
- full URL repo input with branch combobox
- add defaultBranch and listBranches to frontend API
- add branch listing endpoint via git ls-remote
- add defaultBranch to defaults endpoint

### Fixed

- update all non-major dependencies to v0.35.3 (#321)
- add configmaps RBAC, defaults manifest, fix secrets verbs
- review fixes — label, null branches, deprecation warning, test

## 2026-03-18

### Added

- universal dotfiles support with configmap defaults
- add clipboard bridge for tmux copy to browser sync
- auto-create git secret for private repos

### Fixed

- terminal was centered

## 2026-03-17

### Fixed

- don't default gitSecretRef to git-creds

## 2026-02-27

### Fixed

- correct onInput prop data type
- pin dependencies (#245)
- migrate to @tailwindcss/vite for Tailwind v4
- use type-only imports and explicit field declarations for TS 5.8

## 2026-02-25

### Added

- allow custom container image input with suggestions

### Fixed

- validate WebSocket origin against host header

## 2026-02-24

### Changed

- add VERSION and PLATFORM files

### Fixed

- parse error field from backend responses
- transform API payloads between flat and K8s format
- resolve deployment blockers and gaps

## 2026-01-22

### Added

- add SPA routing and static file serving
- add KoolnaCreate form with validation
- add KoolnaList component with auto-refresh
- add typed API client for koolna endpoints
- add checkout and branch status endpoints

### Changed

- add K8s deployment manifests with RBAC
- add multi-stage Dockerfile

## 2026-01-21

### Added

- add Keypad component for mobile terminal input
- add Terminal React component with xterm integration
- add XtermAdapter implementing TerminalInterface
- port WebTTY/Connection classes to TypeScript
- init React/Vite/TS frontend with Tailwind

## 2026-01-19

### Added

- implement WebSocket terminal proxy
- implement REST API handlers for Koolna CRUD
- add K8s types and dynamic client for Koolna CRD

## 2026-01-12

### Added

- initialize Go project with gorilla/mux router
