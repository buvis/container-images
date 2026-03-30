# Changelog — koolna-operator

## [Unreleased]

### Added

- `sshPublicKey` field in KoolnaSpec CRD for SSH access
- pass KOOLNA_SSH_PUBKEY env var to sidecar when sshPublicKey is set
- SSH port 2222 on service and sidecar container
- aggregate per-pod credential secrets into shared koolna-credentials secret
- pass KOOLNA_CREDENTIAL_PATHS env var to tmux-sidecar
- pass KOOLNA_SHARED_SECRET env var to tmux-sidecar for shared credential reads
- emptyDir cache volume mounted at `$HOME/.cache` for disposable storage
- GIT_CONFIG_GLOBAL env var on main container for git credential discovery
- git credential env vars (GIT_USERNAME, GIT_TOKEN, GIT_NAME, GIT_EMAIL) passed to sidecar unconditionally

### Changed

- revert auth secret to per-pod naming (`<name>-auth`) instead of shared
- PVC mounted at `$HOME/workspace` with subPath instead of entire home directory
- git credentials written to `workspace/.koolna/` (persistent) instead of `$HOME/` (was PVC, now ephemeral)

## 2026-03-29

### Changed

- use shared credential secret name (koolna-credentials) instead of per-pod

## 2026-03-27

### Added

- add readiness probe and pending state for initializing pods

## 2026-03-24

### Fixed

- set HOME in git-clone init container
- create home dir before clone in init container

### Documentation

- update changelogs [ci-skip]
- update changelogs [ci-skip]

## 2026-03-23

### Fixed

- recursive chown for .cache/.local/.config in init container

### Documentation

- update changelog [ci-skip]

## 2026-03-22

### Added

- add configurable shell field
- parameterize pod spec and init container with user config
- add user config resolution, validation, CRD yaml
- add username/uid/homePath CRD fields, dynamic sidecar HOME

### Changed

- rename dotfilesInit to initCommand

### Fixed

- add SYS_ADMIN capability for sidecar nsenter
- harden HomePath validation, fix UID=0 pointer bug

### Documentation

- update changelog [ci-skip]
- update changelog [ci-skip]
- backfill changelogs for all images [ci-skip]

## 2026-03-21

### Changed

- move operator to koolna namespace

## 2026-03-20

### Added

- persist git credentials in home volume, add git identity
- add tmux sidecar and shared home volume to pod spec

### Fixed

- show git identity and credentials fields unconditionally
- address review findings from cycle 1
- restore workspaceVolumeName const removed by linter

## 2026-03-19

### Added

- create /workspace/.koolna/ dir in init container
- support none/command methods and init command in dotfiles
- add dotfilesCommand and dotfilesInit CRD fields
- use full URL in init container with host-aware credentials
- accept full HTTPS URLs with legacy fallback

### Changed

- shorten operator resource names

### Fixed

- update all non-major dependencies to v0.35.3 (#321)
- review fixes — command method guard, validation, env var scoping
- review fixes — label, null branches, deprecation warning, test
- move dotfiles defaults from operator to webui only
- chown workspace to bob after init container clone

### Documentation

- update docs for dotfiles redesign, regenerate CRD
- update samples and README for full URL format

## 2026-03-18

### Added

- universal dotfiles support with configmap defaults

### Fixed

- clone dotfiles to /workspace/.dotfiles, install on startup

### Documentation

- document dotfiles methods and defaults ConfigMap
- add sample koolna-defaults ConfigMap

## 2026-03-17

### Fixed

- clean workspace before git clone
- skip git secret ref for public repos

## 2026-03-05

### Fixed

- update module sigs.k8s.io/controller-runtime to v0.23.3 (#276)
- update module sigs.k8s.io/controller-runtime to v0.23.2 (#274)

## 2026-02-27

### Fixed

- pin dependencies (#245)

## 2026-02-25

### Fixed

- validate inputs and secure credential handling in init containers

### Documentation

- replace boilerplate README with actual docs

## 2026-02-24

### Changed

- add VERSION and PLATFORM files

### Fixed

- resolve deployment blockers and gaps

## 2026-01-22

### Added

- implement status updates with Ready condition
- add update/patch/delete verbs to services RBAC

### Changed

- configure kustomize with resources and sample CR
- set default image to ghcr.io/buvis/koolna-operator

## 2026-01-21

### Added

- implement finalizers and PVC cleanup based on deletionPolicy
- implement Service reconciliation

## 2026-01-19

### Added

- implement pod reconciliation with suspend/resume

## 2026-01-18

### Added

- add buildPodSpec with init containers and main container
- add dotfiles init container helper
- add git-clone init container helper

## 2026-01-15

### Added

- implement PVC reconciliation for workspace storage

## 2026-01-12

### Added

- define Koolna CRD types with spec/status fields
- scaffold kubebuilder project with Koolna CRD
