# Changelog — mopidy

## [Unreleased]

### Removed

- **mopidy**: drop Mopidy-YTMusic; its current release declares `Mopidy<4` and the image runs Mopidy 4.x, so it cannot coexist. While the plugin set was unpinned, pip hid this by silently installing YTMusic 0.1.1 (a 2020 release) instead of failing

### Fixed

- **mopidy**: install extensions from a pinned requirements.txt and stop pip failing with `uninstall-no-record-file` when a plugin needs a newer typing-extensions than Debian's apt-owned copy
- **mopidy**: pin pylast to 7.0.2 (last release on httpx; 7.1+ needs httpx2, which conflicts with Debian's h11) and drop `--ignore-installed`, which made pip try to rebuild Mopidy and pygobject from PyPI instead of using the apt packages
- **mopidy**: bump Mopidy-TuneIn to 2.0.0; 1.1.0 imports `mopidy.internal`, which Mopidy 4 removed, so the extension failed during setup

## 2026-02-13

### Fixed

- **mopidy**: move patch after mopidy install to avoid /tmp cleanup
- **mopidy**: patch scan.py for GStreamer 1.26.2 StructureWrapper compat
- **mopidy**: use trixie apt source to get GStreamer >= 1.26.3

## 2026-01-08

### Fixed

- path to files to be copied to mopidy relative to build action context
