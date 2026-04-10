# Changelog — koolna-webui

## [Unreleased]

### Removed

- **koolna-webui**: remove back button from terminal header since sessions open in a new tab

## 2026-04-10

### Added

- **koolna-webui**: add Claude credentials paste form to global settings

## 2026-04-08

### Added

- **koolna-webui**: replace hardcoded Tailwind colors with design tokens in Terminal and Keypad
- **koolna-webui**: update env var editor with token classes
- **koolna-webui**: update settings form with token classes and amber save button
- **koolna-webui**: update create form with token classes and green submit button
- **koolna-webui**: add mobile card view, icon action buttons, and responsive mount modal
- **koolna-webui**: replace header buttons with cogwheel icon and onCreate prop
- **koolna-webui**: add warm dark utility design tokens and system font stack
- **koolna-webui**: redesign settings with git identity, image, and storage defaults

### Fixed

- **koolna-webui**: add 44px mobile input height for tap target compliance
- **koolna-webui**: add aria-label to icon-only action buttons for accessibility
- **koolna-webui**: shift warning token hue to distinguish from accent
- **koolna-webui**: replace raw emerald-400 with phase-running design token
- **koolna-webui**: increase mobile tap targets to 44px for icon buttons and modal close
- **koolna-webui**: avoid ref access during render in EnvVarEditor initializer
- **koolna**: update remaining tmux-sidecar references missed in rename
- **koolna**: add 256-color terminal feature for tmux clients

## 2026-04-07

### Added

- **koolna-webui**: make repository link clickable in koolna list

### Fixed

- **koolna-webui**: remove WebGL renderer to fix 256-color rendering

## 2026-04-06

### Added

- **koolna**: add webui-driven broker bootstrap with paste-credentials flow

### Fixed

- **koolna**: simplify to plain token from setup-token (1 year validity, no refresh needed)

## 2026-04-05

### Added

- **koolna-webui**: add Claude authentication checkbox to workspace creation form

### Fixed

- **koolna**: prefix koolna mounts

## 2026-04-01

### Fixed

- **koolna-webui**: unmount stale FUSE mount before mkdir in mount script
- **koolna-webui**: clean shutdown of sshfs before port-forward in mount script
- **koolna-webui**: detect gpg-agent SSH socket and use foreground sshfs in mount script
- **koolna-webui**: use StrictHostKeyChecking=no for ephemeral pod mount scripts
- **koolna-webui**: place SSH options before command in mount script pre-connect
- **koolna-webui**: pre-connect SSH in mount script for macOS agent key binding
- **koolna**: create sidecar user for sshd, fix mount script port detection

## 2026-03-31

### Added

- **koolna-webui**: add tooltip to disabled Mount button
- **koolna-webui**: add SSH key help text to create form
- **koolna-webui**: add SSH key help text to Settings page

### Fixed

- **koolna-webui**: restore existence check in MountScript, update tests
- **koolna-webui**: remove user config fields from create form
- **koolna-webui**: remove username/uid/homePath from create API
- **koolna-webui**: use fixed /workspace path in mount script
- **koolna-webui**: fix EnvVarEditor focus loss and remove value masking

## 2026-03-30

### Added

- **koolna-webui**: add env var section to create form
- **koolna-webui**: add Settings page with env var defaults editor
- **koolna-webui**: add EnvVarEditor component
- **koolna-webui**: add frontend env var types and API functions
- **koolna-webui**: create per-koolna env secret in create flow
- **koolna-webui**: add env var CRUD API handlers
- **koolna-webui**: add koolna-env-defaults Secret deploy manifest
- **koolna-webui**: add Mount button and modal to KoolnaList
- **koolna-webui**: add sshPublicKey to frontend types and create form
- **koolna-webui**: add mount-script endpoint for SSHFS mount
- **koolna-webui**: add sshPublicKey to backend create/defaults/response

### Fixed

- **koolna-webui**: clean up orphan env secret on CR patch failure
- **koolna-webui**: use useEffect for EnvVarEditor external sync
- **koolna-webui**: validate env var names and allow empty values in create form
- **koolna-webui**: remove redundant Back button from Settings page
- **koolna-webui**: use stable IDs in EnvVarEditor for correct state tracking
- **koolna-webui**: add server-side env var name validation
- **koolna-webui**: upsert env secret and patch CR in UpdateKoolnaEnv
- **koolna-webui**: show OS-specific unmount commands in modal
- **koolna-webui**: harden mount script SSH options and input validation

## 2026-03-27

### Added

- **koolna-webui**: disable terminal buttons when pod not ready

### Fixed

- **koolna-webui**: use full page navigation to/from terminal for clean WebGL lifecycle
- **koolna-webui**: use popstate handler instead of pageshow for Firefox back button
- **koolna-webui**: reload on Firefox bfcache restore for browser back button
- **koolna-webui**: use full navigation when leaving terminal to fix Firefox blank page
- **koolna-webui**: handle Firefox bfcache blank page on back navigation
- **koolna-webui**: remove debug logging, canvas addon, unicode11 addon

## 2026-03-26

### Fixed

- **koolna-webui**: log all websocket messages for debugging
- **koolna-webui**: dump all high-byte websocket messages for debugging
- **koolna-webui**: log powerline bytes from websocket for debugging
- **koolna-webui**: decode websocket binary to string for proper glyph rendering
- **koolna-webui**: add inline powerline render test

## 2026-03-25

### Fixed

- **deps**: update all non-major dependencies (#339)
- **koolna-webui**: upgrade to @xterm/ packages for proper customGlyphs support
- **koolna-webui**: add renderer diagnostics logging to console
- **koolna-webui**: fall back to canvas renderer when WebGL unavailable
- **koolna-webui**: use WebGL renderer with explicit customGlyphs for powerline
- **koolna-webui**: remove canvas addon, rely on built-in custom glyph rendering
- **koolna-webui**: add unicode11 addon for proper glyph width calculation
- **koolna-webui**: load canvas addon after terminal is attached to DOM
- **koolna-webui**: use canvas renderer for proper nerd font glyph rendering

## 2026-03-23

### Fixed

- **koolna-webui**: use MesloLGS NF font for body text
- **koolna**: nsenter as target user, wait for font before terminal init

## 2026-03-22

### Added

- **koolna**: add configurable shell field
- **koolna-webui**: add username/uid/homePath to create form and API

### Fixed

- **koolna-webui**: restore git fields as required in create form
- **koolna-webui**: make git fields optional, fix status.currentBranch path
- **koolna**: credential sync create-or-update, frontend homePath validation
- **koolna**: harden HomePath validation, fix UID=0 pointer bug

## 2026-03-21

### Added

- **koolna-webui**: add form validation with field help tooltips

### Fixed

- **koolna-webui**: show field help tooltip on hover instead of click

## 2026-03-20

### Added

- **koolna**: persist git credentials in home volume, add git identity
- **koolna-webui**: replace gotty frontend with raw terminal protocol
- **koolna-webui**: add MesloLGS Nerd Font for terminal rendering
- **koolna-webui**: replace gotty proxy with kubectl exec terminal

### Fixed

- **koolna**: show git identity and credentials fields unconditionally
- **koolna-webui**: remove unused container field in xterm-adapter
- **koolna**: address review findings from cycle 1

## 2026-03-19

### Added

- **koolna-webui**: move private repo after URL, auto-detect on branch fetch failure
- **koolna-webui**: conditional dotfiles form with none/bare-git/clone/command
- **koolna-webui**: add dotfilesCommand and dotfilesInit fields
- **koolna-webui**: full URL repo input with branch combobox
- **koolna-webui**: add defaultBranch and listBranches to frontend API
- **koolna-webui**: add branch listing endpoint via git ls-remote
- **koolna-webui**: add defaultBranch to defaults endpoint

### Fixed

- **deps**: update all non-major dependencies to v0.35.3 (#321)
- **koolna-webui**: add configmaps RBAC, defaults manifest, fix secrets verbs
- **koolna**: review fixes — label, null branches, deprecation warning, test

## 2026-03-18

### Added

- **koolna**: universal dotfiles support with configmap defaults
- **koolna**: add clipboard bridge for tmux copy to browser sync
- **koolna-webui**: auto-create git secret for private repos

### Fixed

- terminal was centered

## 2026-03-17

### Fixed

- **koolna-webui**: don't default gitSecretRef to git-creds

## 2026-02-27

### Fixed

- **koolna-webui**: correct onInput prop data type
- **deps**: pin dependencies (#245)
- **koolna-webui**: migrate to @tailwindcss/vite for Tailwind v4
- **koolna-webui**: use type-only imports and explicit field declarations for TS 5.8

## 2026-02-25

### Added

- **koolna-webui**: allow custom container image input with suggestions

### Fixed

- **koolna**: validate WebSocket origin against host header

## 2026-02-24

### Fixed

- **koolna-webui**: parse error field from backend responses
- **koolna-webui**: transform API payloads between flat and K8s format
- **koolna**: resolve deployment blockers and gaps

## 2026-01-22

### Added

- **koolna-webui**: add SPA routing and static file serving
- **koolna-webui**: add KoolnaCreate form with validation
- **koolna-webui**: add KoolnaList component with auto-refresh
- **koolna-webui**: add typed API client for koolna endpoints
- **koolna-webui**: add checkout and branch status endpoints

## 2026-01-21

### Added

- **koolna-webui**: add Keypad component for mobile terminal input
- **koolna-webui**: add Terminal React component with xterm integration
- **koolna-webui**: add XtermAdapter implementing TerminalInterface
- **koolna-webui**: port WebTTY/Connection classes to TypeScript
- **koolna-webui**: init React/Vite/TS frontend with Tailwind

## 2026-01-19

### Added

- **koolna-webui**: implement WebSocket terminal proxy
- **koolna-webui**: implement REST API handlers for Koolna CRUD
- **koolna-webui**: add K8s types and dynamic client for Koolna CRD

## 2026-01-12

### Added

- **koolna-webui**: initialize Go project with gorilla/mux router
