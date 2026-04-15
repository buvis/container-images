# Changelog - koolna-git-clone

## [Unreleased]

### Fixed

- **koolna-git-clone**: export `GIT_CONFIG_GLOBAL` before cloning so git reads the credential helper written to `/cache/.koolna/.gitconfig` (private repo clones previously failed with "could not read Username")

### Added

- **koolna-git-clone**: new init-container image replacing the inline `alpine/git` script that the koolna-operator previously embedded in the pod template
