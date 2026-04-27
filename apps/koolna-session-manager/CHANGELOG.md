# Changelog — koolna-session-manager

## [Unreleased]

### Added

- **koolna-session-manager**: stop forwarding phase writes once `/cache/.koolna/failed` appears so a late-arriving phase string from a child process can't overwrite the recorded bootstrap-failure message; the sidecar then exits non-zero so the pod surfaces as not-ready

### Changed

- **koolna-session-manager**: poll the bootstrap phase file every 0.5s (was 2s) so fine-grained sub-phases written in tight succession surface in the bootstrap-step annotation without coalescing
- **koolna-session-manager**: locate koolna's PID by reading `/cache/.koolna/pid` (written by bootstrap.sh) instead of scanning `/proc` for a `sleep infinity` cmdline. The old scan failed during the install phase because bootstrap.sh's cmdline isn't `sleep infinity` until the install completes.
- **koolna-session-manager**: dotfiles and `mise install` no longer run here. The koolna-git-clone init container writes `/cache/.koolna/bootstrap.sh` which the main container execs as PID 1, so install memory bills to koolna's 8Gi cgroup instead of the sidecar's 512Mi. The sidecar now waits on `/cache/.koolna/ready` and forwards `/cache/.koolna/phase` into the `bootstrap-step` annotation, then handles only the root-privileged work (sshd, credential sync, tmux).
- **koolna-session-manager**: drop chown+credential-helper setup blocks now handled by koolna-git-clone and bootstrap.sh.

### Fixed

- **koolna-session-manager**: enter the koolna container's cgroup (add `--cgroup` to `nsenter`) so any follow-up installs dispatched by the sidecar bill memory to koolna's limit (8Gi) instead of the sidecar's 512Mi

### Added

- **koolna-session-manager**: on non-zero exit, annotate the pod with `Failed: <step> (exit <code>)` so the Koolna CR condition surfaces the failing phase instead of freezing on the last successful one

### Changed

- **koolna-session-manager**: read authorized_keys from `/etc/koolna/ssh/authorized_keys` (mounted by the operator from a per-Koolna ConfigMap) instead of the `KOOLNA_SSH_PUBKEY` env var.
- **koolna-session-manager**: write `/tmp/koolna-ready` sentinel at the end of the entrypoint for cheap file-based readiness probing; drop the tmux bootstrap placeholder session (no longer needed now that probes use the sentinel).

### Fixed

- **koolna-session-manager**: credential restore/sync skips writes when content is unchanged
- **koolna-session-manager**: merge `hasCompletedOnboarding=true` into `.claude.json` after every credential restore so claude never drops to the theme picker, even when the shared Secret carries a flagless version
- **koolna-session-manager**: start a placeholder tmux session at entrypoint start so the startup probe passes within seconds, eliminating 60+ Unhealthy events per bootstrap while dotfiles install runs

### Added

- **koolna-session-manager**: annotate pod with `koolna.buvis.net/bootstrap-step` at each entrypoint phase so the operator can surface progress in the Koolna CR condition

### Removed

- **koolna-session-manager**: remove squid proxy CA handling, DNS-to-IP resolution, and cargo proxy tuning from entrypoint

## 2026-04-09

### Fixed

- **koolna-session-manager**: use PATCH for credential sync to preserve unsynced keys

## 2026-04-08

### Fixed

- **koolna**: add 256-color terminal feature for tmux clients

## 2026-04-07

### Added

- **koolna-tmux**: sync credentials to shared secret for cross-workspace reuse

### Fixed

- **koolna-tmux**: set TERM for 256-color tmux client attach
- **koolna-tmux**: enable 256-color support in tmux sessions

## 2026-04-06

### Fixed

- **koolna-tmux**: always run claude bootstrap when token is set (dotfiles may precreate ~/.claude)
- **koolna-tmux**: bootstrap claude config on first run when CLAUDE_CODE_OAUTH_TOKEN is set

## 2026-04-05

### Added

- **koolna-tmux**: add koolna-auth-init for opt-in Claude token injection

## 2026-04-02

### Fixed

- **koolna-tmux**: replace proxy hostname with IP, export cargo timeout for nsenter
- **koolna-tmux**: pin proxy hostname in /etc/hosts to avoid DNS contention
- **koolna-tmux**: restore WS variable removed during .koolna refactor

## 2026-04-01

### Fixed

- **koolna**: create sidecar user for sshd, fix mount script port detection
- **koolna**: run dotfiles/init as user, use FQDN for proxy DNS
- **koolna**: export SSL_CERT_FILE and REQUESTS_CA_BUNDLE for uv/pip proxy trust
- **koolna-tmux**: export NODE_EXTRA_CA_CERTS so nsenter'd npm trusts proxy CA

## 2026-03-31

### Added

- **koolna-tmux**: auto-detect UID/HOME/PATH/username from /proc

### Fixed

- **koolna-tmux**: fix dotfiles command syntax error and gitconfig path
- **koolna-tmux**: fix chown paths, add GID detection, HOME fallback, cache path
- **koolna-tmux**: run dotfiles and init command in main container via nsenter
- **koolna-tmux**: silence credential-sync no-op log in polling loop
- **koolna-tmux**: trust proxy CA in sidecar before dotfiles install
- **koolna**: create .koolna dir before writing credentials, trust CA before dotfiles
