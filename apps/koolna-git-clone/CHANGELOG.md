# Changelog - koolna-git-clone

## [Unreleased]

### Added

- **koolna-git-clone**: also write `/cache/.koolna/bootstrap.sh` and chown `/cache` + `/workspace` to `KOOLNA_UID`/`KOOLNA_GID`. The koolna container now execs that script as PID 1, so dotfiles install and `mise install` run inside koolna's own cgroup (8Gi limit) instead of the sidecar's 512Mi. The script self-installs mise on cold images that lack it.

### Fixed

- **koolna-git-clone**: export `GIT_CONFIG_GLOBAL` before cloning so git reads the credential helper written to `/cache/.koolna/.gitconfig` (private repo clones previously failed with "could not read Username")

### Added

- **koolna-git-clone**: new init-container image replacing the inline `alpine/git` script that the koolna-operator previously embedded in the pod template
