# Changelog — mkdocs-git-sync


## 2026-03-30

### Documentation

- update changelogs [skip ci]

## 2026-03-22

### Documentation

- backfill changelogs for all images [ci-skip]

## 2026-02-27

### Added

- wire multi-provider config into run.py
- add multi-provider webhook config
- refactor server to multi-provider router
- add Bitbucket webhook provider
- add GitLab webhook provider
- add GitHub webhook provider
- add base webhook provider class

### Documentation

- add multi-provider webhook docs, bump to 0.6.0
- add multi-provider webhooks implementation plan
- add multi-provider webhooks design

## 2026-02-24

### Added

- rewire main loop with event-based triggering
- add source param to Syncer.update()
- add webhook server with HMAC validation
- add webhook config env vars
- add link checker docs, bump to 0.4.0
- add linkchecker deps and example config
- integrate link checker into main loop
- add linkcheck service orchestrator
- add notification dispatchers
- add link checker runner
- add linkcheck config loader

### Changed

- expose webhook port in Dockerfile

### Fixed

- don't clear webhook event on error
- exit on build failure, stream build logs
- skip link check when build fails

### Documentation

- add webhook configuration to README
- add push-triggered rebuilds implementation plan
- add push-triggered rebuilds design

## 2025-04-26

### Changed

- Update dependencies

## 2025-04-23

### Changed

- Fix release action
- Decrease image size

## 2025-04-22

### Changed

- Fix site not being built after cloning
- Refactor for CLEANer code base
- Update example dependencies
- Bump version
- Add development instructions
- Update dependencies

## 2025-04-20

### Changed

- Update requirements

## 2023-03-08

### Changed

- Update mkdocs-git-sync

## 2022-11-09

### Changed

- Update VERSION manually

## 2022-06-20

### Changed

- Refer to renamed buvis-net organization

## 2022-01-31

### Changed

- Update python and version
- Update dependency mkdocs-zettelkasten to v0.1.6

## 2021-11-30

### Changed

- Fix docker-compose example formatting issues
- Clarify README.md

## 2021-11-29

### Changed

- Update to mkdocs-zettelkasten 0.1.5
- [mkdocs-git-sync] Hide credentials from the log

## 2021-11-28

### Changed

- Push to Docker Hub as well

## 2021-11-27

### Changed

- Switch to absolute path to allow GH action build
- Add workflow to build the containers
- Make credentials strings visible
- Initialize
