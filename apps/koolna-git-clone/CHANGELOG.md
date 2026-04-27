# Changelog - koolna-git-clone

## [Unreleased]

### Added

- **koolna-git-clone**: bootstrap.sh now traps non-zero exits, writes `Failed: <phase> (exit <rc>)` to `/cache/.koolna/phase`, and touches `/cache/.koolna/failed` so the session-manager and operator can surface bootstrap failures within seconds instead of waiting for the 40-minute startup-probe ceiling
- **koolna-git-clone**: also write `/cache/.koolna/bootstrap.sh` and chown `/cache` + `/workspace` to `KOOLNA_UID`/`KOOLNA_GID`. The koolna container now execs that script as PID 1, so dotfiles install and `mise install` run inside koolna's own cgroup (8Gi limit) instead of the sidecar's 512Mi. The script self-installs mise on cold images that lack it.
- **koolna-git-clone**: bootstrap.sh writes its PID to `/cache/.koolna/pid` as its first action so the session-manager sidecar can locate it without scanning `/proc` for a changing cmdline.

### Fixed

- **koolna-git-clone**: bootstrap.sh template no longer pins `MISE_CACHE_DIR`, `UV_CACHE_DIR`, or `XDG_CACHE_HOME` to `/cache`; mise/uv caches default to `$HOME/.cache` so they share the install target's filesystem, restoring hardlinks and silencing "Failed to hardlink files" warnings
- **koolna-git-clone**: export `GIT_CONFIG_GLOBAL` before cloning so git reads the credential helper written to `/cache/.koolna/.gitconfig` (private repo clones previously failed with "could not read Username")

### Added

- **koolna-git-clone**: new init-container image replacing the inline `alpine/git` script that the koolna-operator previously embedded in the pod template
