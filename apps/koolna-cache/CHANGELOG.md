# Changelog — koolna-cache

## [Unreleased]

## 2026-04-09

### Fixed

- **koolna-cache**: disable caching for Claude CLI binary downloads from GCS

## 2026-04-08

### Fixed

- **koolna**: update remaining tmux-sidecar references missed in rename

## 2026-04-02

### Fixed

- **koolna-cache**: disable aggressive caching for claude.ai installer
- **koolna-cache**: use aufs async I/O, disable IPv6 pinger, dns_v4_first

## 2026-04-01

### Fixed

- **koolna-cache**: increase sslcrtd_children and cert cache for concurrent downloads

## 2026-03-31

### Fixed

- **koolna-cache**: export CA ConfigMap to koolna namespace, not koolna-system

## 2026-03-30

### Fixed

- **koolna-cache**: set fsGroup for squid proxy user
- **koolna-cache**: add missing VERSION and PLATFORM files
