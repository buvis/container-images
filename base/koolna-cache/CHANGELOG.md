# Changelog

All notable changes to koolna-cache will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Squid caching proxy for package downloads (mise, pip, npm, apt)
- SSL bump for transparent HTTPS caching
- CA certificate auto-generation on first start with PVC persistence
- CA certificate export to Kubernetes ConfigMap for pod trust injection
- Aggressive caching for immutable content (tarballs, wheels, archives)
- Short TTL for mutable metadata (PyPI simple index, npm registry)
