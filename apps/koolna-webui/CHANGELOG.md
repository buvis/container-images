# Changelog — koolna-webui


## 2026-03-27

### Added

- disable terminal buttons when pod not ready

### Fixed

- remove debug logging, canvas addon, unicode11 addon

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
