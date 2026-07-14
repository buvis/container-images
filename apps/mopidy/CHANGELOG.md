# Changelog — mopidy

## [Unreleased]

### Fixed

- **mopidy**: install extensions from a pinned requirements.txt and stop pip failing with `uninstall-no-record-file` when a plugin needs a newer typing-extensions than Debian's apt-owned copy

## 2026-02-13

### Fixed

- **mopidy**: move patch after mopidy install to avoid /tmp cleanup
- **mopidy**: patch scan.py for GStreamer 1.26.2 StructureWrapper compat
- **mopidy**: use trixie apt source to get GStreamer >= 1.26.3

## 2026-01-08

### Fixed

- path to files to be copied to mopidy relative to build action context
