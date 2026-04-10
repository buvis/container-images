# Changelog — mkdocs-git-sync

## [Unreleased]

## 2026-02-27

### Added

- **mkdocs-git-sync**: wire multi-provider config into run.py
- **mkdocs-git-sync**: add multi-provider webhook config
- **mkdocs-git-sync**: refactor server to multi-provider router
- **mkdocs-git-sync**: add Bitbucket webhook provider
- **mkdocs-git-sync**: add GitLab webhook provider
- **mkdocs-git-sync**: add GitHub webhook provider
- **mkdocs-git-sync**: add base webhook provider class

## 2026-02-24

### Added

- **mkdocs-git-sync**: rewire main loop with event-based triggering
- **mkdocs-git-sync**: add source param to Syncer.update()
- **mkdocs-git-sync**: add webhook server with HMAC validation
- **mkdocs-git-sync**: add webhook config env vars
- **mkdocs-git-sync**: add link checker docs, bump to 0.4.0
- **mkdocs-git-sync**: add linkchecker deps and example config
- **mkdocs-git-sync**: integrate link checker into main loop
- **mkdocs-git-sync**: add linkcheck service orchestrator
- **mkdocs-git-sync**: add notification dispatchers
- **mkdocs-git-sync**: add link checker runner
- **mkdocs-git-sync**: add linkcheck config loader

### Fixed

- **mkdocs-git-sync**: don't clear webhook event on error
- **mkdocs-git-sync**: exit on build failure, stream build logs
- **mkdocs-git-sync**: skip link check when build fails
