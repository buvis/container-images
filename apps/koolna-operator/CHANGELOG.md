# Changelog — koolna-operator

## [Unreleased]

### Added

- **koolna-operator**: surface bootstrap state via a typed `Bootstrapped` condition on `Koolna.Status.Conditions` (Reasons: `Bootstrapped`, `BootstrapFailed`, `Bootstrapping`); a `Failed:` prefix in the `koolna.buvis.net/bootstrap-step` annotation drives the condition to `BootstrapFailed` so failures surface in seconds instead of after the 40-minute startup-probe ceiling
- **koolna-operator**: `Bootstrapped` printer column so `kubectl get koolna` shows bootstrap state inline alongside Phase/Repo/Branch/Age
- **koolna-operator**: `spec.runAsUser` (optional, default 1000) controls the UID the koolna container runs as and the owner of workspace/cache volumes.
- **koolna-operator**: default resource requests and limits on both the `koolna` and `session-manager` containers, making pods Guaranteed/Burstable in a predictable way and protecting node capacity during the first-start install storm.
- **koolna-operator**: `Bootstrapping` phase when pod is running but session-manager is not yet ready, with condition message showing the current bootstrap step (Installing dotfiles, Syncing credentials, Installing tools, etc.)
- **koolna-operator**: watch owned pods so annotation changes from session-manager trigger reconcile updates

### Changed

- **koolna-operator**: bump session-manager `StartupProbe.InitialDelaySeconds` to 60s so the kubelet stops emitting `Unhealthy: Startup probe failed` events during the first minute of pod startup
- **koolna-operator**: run dotfiles install and `mise install` as PID 1 of the koolna container instead of via `nsenter` from the sidecar. The koolna container now execs `/cache/.koolna/bootstrap.sh` (written by koolna-git-clone), runs under `securityContext.runAsUser/Group`, and receives the `DOTFILES_*`/`INIT_COMMAND` env vars. Memory bills to the koolna cgroup (8Gi) instead of the sidecar's smaller limit, fixing first-start OOMKills on heavy installs.
- **koolna-operator**: replace the inline `alpine/git` init container (shell script embedded in Go) with the dedicated `ghcr.io/buvis/koolna-git-clone` image, keeping the pod spec under `kubectl describe` readable and letting the image move independently of the operator.
- **koolna-operator**: `spec.resources` is now per-container (`koolna`, `session-manager`); the previous flat `ResourceRequirements` shape is no longer accepted. Operator defaults apply when fields are omitted, and overrides merge by key (set `limits.cpu` alone without losing default memory limit).
- **koolna-operator**: deliver the SSH public key to session-manager via a per-Koolna ConfigMap (`<name>-ssh`) mounted at `/etc/koolna/ssh/authorized_keys` instead of the `KOOLNA_SSH_PUBKEY` env var, keeping `kubectl describe pod` output free of long key literals.

### Fixed

- **koolna-operator**: stop pinning mise/uv caches to `/cache` on the koolna container; drop `XDG_CACHE_HOME`, `MISE_CACHE_DIR`, and `UV_CACHE_DIR` env vars so caches default to `$HOME/.cache/{mise,uv}` on overlay FS (same FS as install target), restoring hardlinks and silencing "Failed to hardlink files" warnings
- **koolna-operator**: replace `tmux has-session` probe with a `test -f /tmp/koolna-ready` sentinel written by the entrypoint, removing the tmux exec that otherwise ran every 30s for the pod's lifetime. Also removes spurious `Unhealthy: can't find session: manager` events during bootstrap.
- **koolna-operator**: mark the ssh-pubkey ConfigMap volume Optional so clearing `spec.sshPublicKey` (which deletes the ConfigMap) does not brick an existing pod on restart.
- **koolna-operator**: stop spamming Unhealthy events during dotfiles install by gating session-manager readiness behind a startup probe with a 40-minute budget
- **koolna-operator**: readiness probe checks for the real `manager` tmux session so the Koolna CR only flips to Running once attach will actually succeed (prevents webui from enabling session buttons that fail with "session not found" while dotfiles is still installing)

### Removed

- **koolna-operator**: remove squid proxy integration (HTTP_PROXY env vars, proxy-ca volume, CA cert mounts) from workspace pods; rely on mise persistent cache PVC instead

## 2026-04-08

### Fixed

- **koolna**: update remaining tmux-sidecar references missed in rename

## 2026-04-07

### Added

- **koolna-operator**: add .claude.json to credential sync paths for interactive login

## 2026-04-06

### Added

- **koolna-operator**: delete cache PVC on CR deletion with Delete policy
- **koolna-operator**: replace EmptyDir with PVC for cache volume
- **koolna-operator**: add cacheSize and cacheStorageClass CRD fields
- **koolna**: add webui-driven broker bootstrap with paste-credentials flow

### Fixed

- **koolna**: simplify to plain token from setup-token (1 year validity, no refresh needed)

## 2026-04-05

### Added

- **koolna-operator**: log when claudeAuth is enabled during reconcile
- **koolna-operator**: add claudeAuth spec field to inject broker URL on sidecar

## 2026-04-02

### Fixed

- **koolna-operator**: add CARGO_HTTP_TIMEOUT and CARGO_HTTP_MULTIPLEXING for proxy

## 2026-04-01

### Fixed

- **koolna**: run dotfiles/init as user, use FQDN for proxy DNS
- **koolna**: export SSL_CERT_FILE and REQUESTS_CA_BUNDLE for uv/pip proxy trust

## 2026-03-31

### Fixed

- **koolna-operator**: add NODE_EXTRA_CA_CERTS for npm proxy trust
- **koolna-operator**: remove username/uid/homePath from CRD YAML
- **koolna-operator**: remove username/uid/homePath from KoolnaSpec CRD
- **koolna-operator**: set GIT_CONFIG_GLOBAL on init container for credential discovery
- **koolna**: create .koolna dir before writing credentials, trust CA before dotfiles

## 2026-03-30

### Added

- **koolna-operator**: inject env vars from envSecretRef via EnvFrom
- **koolna-operator**: add EnvSecretRef field to KoolnaSpec CRD
- **koolna-operator**: inject proxy env vars and CA mount into pods
- **koolna-operator**: pass git credential env vars to sidecar unconditionally
- **koolna-operator**: add emptyDir cache volume for disposable storage
- **koolna-operator**: mount PVC at workspace subPath instead of entire home
- **koolna-operator**: add SSH port 2222 to service and sidecar
- **koolna-operator**: pass KOOLNA_SSH_PUBKEY env to sidecar
- **koolna-operator**: add sshPublicKey field to KoolnaSpec CRD

### Fixed

- **koolna-operator**: use operator namespace for proxy address, not CR namespace
- **koolna-cache**: review fixes - lowercase proxy vars, JSON encoding, squid config
- **koolna-operator**: set GIT_CONFIG_GLOBAL on main container for credential discovery
- **koolna-operator**: chmod 600 on .git-credentials in init container
- **koolna-operator**: pass REPO_URL to sidecar for correct credential host
- **koolna-operator**: reject sshPublicKey with newlines
- **koolna-operator**: sort by ResourceVersion for true last-write-wins

## 2026-03-29

### Added

- **koolna-operator**: call reconcileCredentials from Reconcile loop
- **koolna-operator**: add reconcileCredentials function
- **koolna-operator**: add create;update RBAC for secrets
- **koolna-operator**: add KOOLNA_SHARED_SECRET env to sidecar
- **koolna-operator**: revert authSecretName to per-pod naming
- **koolna-operator**: pass KOOLNA_CREDENTIAL_PATHS env to sidecar
- **koolna-operator**: use shared credential secret across all pods

### Fixed

- **koolna-operator**: delete stale koolna-credentials when no per-pod secrets exist
- **koolna-operator**: sort credential secrets by timestamp for last-write-wins

## 2026-03-27

### Added

- **koolna-operator**: add readiness probe and pending state for initializing pods

## 2026-03-24

### Fixed

- **koolna-operator**: set HOME in git-clone init container
- **koolna-operator**: create home dir before clone in init container

## 2026-03-23

### Fixed

- **koolna-operator**: recursive chown for .cache/.local/.config in init container

## 2026-03-22

### Added

- **koolna**: add configurable shell field
- **koolna-operator**: parameterize pod spec and init container with user config
- **koolna-operator**: add user config resolution, validation, CRD yaml
- **koolna**: add username/uid/homePath CRD fields, dynamic sidecar HOME

### Fixed

- **koolna-operator**: add SYS_ADMIN capability for sidecar nsenter
- **koolna**: harden HomePath validation, fix UID=0 pointer bug

## 2026-03-20

### Added

- **koolna**: persist git credentials in home volume, add git identity
- **koolna**: add tmux sidecar and shared home volume to pod spec

### Fixed

- **koolna**: show git identity and credentials fields unconditionally
- **koolna**: address review findings from cycle 1
- **koolna**: restore workspaceVolumeName const removed by linter

## 2026-03-19

### Added

- **koolna**: create /workspace/.koolna/ dir in init container
- **koolna**: support none/command methods and init command in dotfiles
- **koolna**: add dotfilesCommand and dotfilesInit CRD fields
- **koolna**: use full URL in init container with host-aware credentials
- **koolna**: accept full HTTPS URLs with legacy fallback

### Fixed

- **deps**: update all non-major dependencies to v0.35.3 (#321)
- **koolna**: review fixes — command method guard, validation, env var scoping
- **koolna**: review fixes — label, null branches, deprecation warning, test
- **koolna**: move dotfiles defaults from operator to webui only
- **koolna**: chown workspace to bob after init container clone

## 2026-03-18

### Added

- **koolna**: universal dotfiles support with configmap defaults

### Fixed

- **koolna**: clone dotfiles to /workspace/.dotfiles, install on startup

## 2026-03-17

### Fixed

- **koolna-operator**: clean workspace before git clone
- **koolna-operator**: skip git secret ref for public repos

## 2026-03-05

### Fixed

- **deps**: update module sigs.k8s.io/controller-runtime to v0.23.3 (#276)
- **deps**: update module sigs.k8s.io/controller-runtime to v0.23.2 (#274)

## 2026-02-27

### Fixed

- **deps**: pin dependencies (#245)

## 2026-02-25

### Fixed

- **koolna-operator**: validate inputs and secure credential handling in init containers

## 2026-02-24

### Fixed

- **koolna**: resolve deployment blockers and gaps

## 2026-01-22

### Added

- **koolna-operator**: implement status updates with Ready condition
- **koolna-operator**: add update/patch/delete verbs to services RBAC

## 2026-01-21

### Added

- **koolna-operator**: implement finalizers and PVC cleanup based on deletionPolicy
- **koolna-operator**: implement Service reconciliation

## 2026-01-19

### Added

- **koolna-operator**: implement pod reconciliation with suspend/resume

## 2026-01-18

### Added

- **koolna-operator**: add buildPodSpec with init containers and main container
- **koolna-operator**: add dotfiles init container helper
- **koolna-operator**: add git-clone init container helper

## 2026-01-15

### Added

- **koolna-operator**: implement PVC reconciliation for workspace storage

## 2026-01-12

### Added

- **koolna-operator**: define Koolna CRD types with spec/status fields
- **koolna-operator**: scaffold kubebuilder project with Koolna CRD
