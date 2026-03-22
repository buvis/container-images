# Changelog — exchanger


## 2026-02-24

### Added

- add providers page with status cards and symbol links

### Changed

- add build-frontend task to mise, dev depends on it
- add VERSION and PLATFORM files

### Fixed

- pre-release hardening for v0.1.0
- correct Dockerfile static copy path and healthcheck URL

## 2026-01-27

### Added

- add maximum/minimum to rates graph

## 2026-01-26

### Added

- stream rates during backfill
- atomic backup/restore with gzip compression
- increase backfill limit to 3650 days
- extend chart range options to 10 years

### Fixed

- multi-provider symbols query uses actual rate data
- use provider_symbol for symbol selection in admin
- calendar week starts on monday

## 2026-01-24

### Added

- add smart backfill resumption with checkpoints
- add provider fallback for provider=all
- add websocket heartbeat and status indicator
- add frontend pages and ui components
- add new API endpoints
- improve backfill tracking and progress
- migrate db schema to v7 with favorites FK
- add new config settings
- add provider_symbol for FCS normalization

### Changed

- update frontend components for provider_symbol

### Fixed

- add a11y labels and document API endpoints
- reorder E2E mocks to register specific routes first
- filter coverage by favorites symbols
- add last_run/error to TaskStateResponse

### Documentation

- update documentation
- fix curl examples to use /api prefix

## 2026-01-23

### Added

- add /api/rates/list endpoint for date-based rate listing
- build Providers page
- build Admin Panel page
- build Rates Explorer page
- build Dashboard page with sparklines
- add typed api.ts client
- add collapsible sidebar layout
- mount static files for SPA frontend
- create SvelteKit frontend with Tailwind + Chart.js
- add GET /api/providers/status endpoint
- add favorites API endpoints
- add GET /api/rates/coverage endpoint
- add GET /api/rates/history endpoint
- add favorites table and CRUD
- add get_coverage() to database
- add get_rates_range() to database
- add /api prefix to all routes
- add FastAPI app factory with lifespan
- add REST API routes
- add background task management
- add backfill and symbols services
- add rate source providers with registry
- add core domain models and configuration

### Changed

- add multi-stage Dockerfile for frontend
- add GitHub Actions CI workflow
- add K8s deployment manifests
- add Dockerfile
- add project setup and dependencies

### Fixed

- remove next_run column from admin task status table
- update E2E mocks to use correct API endpoints
- use favorites count for heatmap coloring
- extract timestamp from BackupInfo for restore
- convert task status dict to array in frontend
- validate timestamp in restore endpoint to prevent path traversal
- sanitize error messages in task status endpoint
- add /api prefix to test routes and fix exception handler
- correct BackupInfo type and history query params
- use query params for backfill request
- correct API endpoint paths in frontend client
- use Chart.js directly for Svelte 5 compat

### Documentation

- add README and CLAUDE.md
