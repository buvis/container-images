# Changelog — koolna-operator


## 2026-03-31

### Fixed

- set GIT_CONFIG_GLOBAL on init container for credential discovery
- create .koolna dir before writing credentials, trust CA before dotfiles

### Documentation

- update changelogs [skip ci]

## 2026-03-30

### Added

- inject env vars from envSecretRef via EnvFrom
- add EnvSecretRef field to KoolnaSpec CRD
- inject proxy env vars and CA mount into pods
- pass git credential env vars to sidecar unconditionally
- add emptyDir cache volume for disposable storage
- mount PVC at workspace subPath instead of entire home
- add SSH port 2222 to service and sidecar
- pass KOOLNA_SSH_PUBKEY env to sidecar
- add sshPublicKey field to KoolnaSpec CRD

### Changed

- align whitespace in helper functions
- regenerate CRD manifests for EnvSecretRef

### Fixed

- use operator namespace for proxy address, not CR namespace
- review fixes - lowercase proxy vars, JSON encoding, squid config
- set GIT_CONFIG_GLOBAL on main container for credential discovery
- chmod 600 on .git-credentials in init container
- pass REPO_URL to sidecar for correct credential host
- reject sshPublicKey with newlines
- sort by ResourceVersion for true last-write-wins

### Documentation

- update changelogs [skip ci]
- update changelogs for env var config feature
- update changelogs for proxy injection
- update changelogs [ci-skip]
- update changelogs for storage split and git config fix
- fix stale dotfiles-cache path in README
- document storage layout and update changelogs
- update changelogs for SSHFS mount feature
- update changelogs [ci-skip]

## 2026-03-29

### Added

- call reconcileCredentials from Reconcile loop
- add reconcileCredentials function
- add create;update RBAC for secrets
- add KOOLNA_SHARED_SECRET env to sidecar
- revert authSecretName to per-pod naming
- pass KOOLNA_CREDENTIAL_PATHS env to sidecar
- use shared credential secret across all pods

### Changed

- extract sharedSecretName constant, enforce label on update

### Fixed

- delete stale koolna-credentials when no per-pod secrets exist
- sort credential secrets by timestamp for last-write-wins

### Documentation

- update koolna-operator changelog for credential aggregation
- update changelogs for credential read/write split
- update changelogs for configurable credential paths
- update changelogs for shared credential secret

## 2026-03-27

### Added

- add readiness probe and pending state for initializing pods

### Documentation

- update changelogs [ci-skip]

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
