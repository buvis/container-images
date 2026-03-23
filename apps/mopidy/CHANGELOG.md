# Changelog — mopidy


## 2026-03-22

### Documentation

- backfill changelogs for all images [ci-skip]

## 2026-02-13

### Fixed

- move patch after mopidy install to avoid /tmp cleanup
- patch scan.py for GStreamer 1.26.2 StructureWrapper compat
- use trixie apt source to get GStreamer >= 1.26.3

## 2026-01-08

### Changed

- Updated to v34.1.0

### Fixed

- path to files to be copied to mopidy relative to build action context

## 2025-05-03

### Changed

- Updated to v3.70.0

## 2024-03-07

### Changed

- Add YTMusic

## 2024-02-08

### Changed

- Update exclusions

## 2024-01-03

### Changed

- Updated to v3.69.3

## 2023-11-01

### Changed

- Switch mopidy to latest base

## 2023-10-24

### Changed

- Updated to v3.69.2

## 2023-09-26

### Changed

- Generalize local scan instructions

## 2023-08-17

### Changed

- Add rescan instruction

## 2023-08-12

### Changed

- Updated to v3.68.0

## 2023-08-02

### Changed

- Update base image

## 2023-06-20

### Changed

- Fix missing extensions
- Fix missing extensions

## 2023-06-19

### Changed

- Attempt fixing failing build
- Attempt fixing failing build
- Attempt fixing failing build
- Attempt fixing failing build

## 2023-06-17

### Changed

- Fix build error
- Fix build error
- Fix build error
- Fix build error
- Fix build error
- Fix build error
- Fix build error
- Fix build error
- Fix build error
- Fix build error
- Fix build error
- Fix build error
- Fix build error
- Update base image

## 2023-05-20

### Changed

- Updated to v26.1.0

## 2023-03-26

### Changed

- Set specific base image version

## 2023-03-01

### Changed

- Updated to v3.66.1

## 2023-01-14

### Changed

- Updated to v25.3.0

## 2022-11-25

### Changed

- Updated to v3.65.0
- Test version detection

## 2022-11-09

### Changed

- Remove force flag
- Force mopidy release

## 2022-07-14

### Changed

- Add Muse frontend

## 2022-06-24

### Changed

- Update to reflect latest changes
- Fix failing goss tests
- Increase formatting consistency
- Adapt for better experience in kubernetes

## 2022-06-20

### Changed

- Remove kah from sudoers because Iris calls wrong commands anyway
- Fix typos and add pulseaudio instructions
- Separate base and app
- Fix comment made incorrectly
- Fix sever control from Iris
- Fix ownership inside container
- Update README.md
- Fix volume's ownership
- Redirect user's home
- Fix app directory owner
- Refer to renamed buvis-net organization
- Fix mopidy's version getter
- Only test if Mopidy-Iris is running
- Track Mopidy-Iris versions for mopidy
- Fix path to config file
- Include default config
- Add tests
- Update Mopidy-Iris to 3.64.0
- Align to look more like k8s at home container
- Fix RUN directive continuing to VOLUME directive
- Switch to k8s at home format
- Switch to mopidy as a system user
- Copy scripts where user has write access to
- Make sure mopidy owns the app directory
- Fix workdir path

## 2022-06-19

### Changed

- Fix calling the entrypoint
- Add scanning script

## 2022-06-18

### Changed

- Add pulseaudio support This is useful if you want to play over bluetooth speaker for example

## 2022-05-14

### Changed

- Update packages

## 2022-05-05

### Changed

- Update mopidy

## 2022-03-29

### Changed

- Remove soundcloud because of https://github.com/mopidy/mopidy-soundcloud/issues/123
- Update README to solve no audio on Arch Linux host
- Add SoundCloud
- Fix mopidy-youtube not starting https://github.com/natumbri/mopidy-youtube/issues/224

## 2022-03-28

### Changed

- Fix youtube extension
- Switch to extensions provided by pip
- Fix instructions
- Update documentation for Tidal
- Release version 0.5.0
- Replace YT Music by Tidal
- Switch to buster
- Fix Dockerfile syntax error
- Fix Mopidy's GPG key retrieval
- Run as mopidy user
- Remove unnecessary forcing of user ID

## 2022-03-09

### Changed

- Fix 'Warning: apt-key is deprecated'
- Update Iris

## 2022-02-02

### Changed

- Fix local path
- Add example of permanent NFS mount

## 2022-02-01

### Changed

- Improve README.md for first time users

## 2022-01-31

### Changed

- Add YTMusic
- Add links to config file
- Add mopidy
