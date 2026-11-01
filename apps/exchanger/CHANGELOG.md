# Changelog — exchanger

## [Unreleased]

### Added

- **exchanger**: retry failed auto-backfill after 5 min, doubling the delay each failure (capped at 1 h) until it succeeds
- **exchanger**: support multiple daily backfill times via comma-separated AUTO_BACKFILL_TIME config

### Changed

- **exchanger**: migrate the frontend to SvelteKit 3 (with adapter-static 4, svelte 5.57, vite 8.3): config moves from `svelte.config.js` into `sveltekit()` in `vite.config.ts`, `$lib` becomes the `#lib` subpath import, `$app/stores` becomes `$app/state` (the legacy-mode admin page wraps `page.url` with `toStore` so its tabs stay reactive), and `$app/environment` becomes `$app/env`

### Fixed

- **exchanger**: fix the frontend build failing with esrap 2.2.13, which strips TypeScript type annotations but leaves the optional-parameter `?` and emits invalid JavaScript; svelte 5.57 brings esrap 2.4, which no longer has the bug, so the temporary esrap 2.2.11 pin is removed

## 2026-02-24

### Added

- **exchanger**: add providers page with status cards and symbol links

### Fixed

- **exchanger**: pre-release hardening for v0.1.0
- **exchanger**: correct Dockerfile static copy path and healthcheck URL

## 2026-01-27

### Added

- add maximum/minimum to rates graph

## 2026-01-26

### Added

- **exchanger**: stream rates during backfill
- **exchanger**: atomic backup/restore with gzip compression
- **exchanger**: increase backfill limit to 3650 days
- **exchanger**: extend chart range options to 10 years

### Fixed

- **exchanger**: multi-provider symbols query uses actual rate data
- **exchanger**: use provider_symbol for symbol selection in admin
- **exchanger**: calendar week starts on monday

## 2026-01-24

### Added

- **exchanger**: add smart backfill resumption with checkpoints
- **exchanger**: add provider fallback for provider=all
- **exchanger**: add websocket heartbeat and status indicator
- **exchanger**: add frontend pages and ui components
- **exchanger**: add new API endpoints
- **exchanger**: improve backfill tracking and progress
- **exchanger**: migrate db schema to v7 with favorites FK
- **exchanger**: add new config settings
- **exchanger**: add provider_symbol for FCS normalization

### Fixed

- **exchanger**: add a11y labels and document API endpoints
- **exchanger**: reorder E2E mocks to register specific routes first
- **exchanger**: filter coverage by favorites symbols
- **exchanger**: add last_run/error to TaskStateResponse

## 2026-01-23

### Added

- **exchanger**: add /api/rates/list endpoint for date-based rate listing
- **exchanger**: build Providers page
- **exchanger**: build Admin Panel page
- **exchanger**: build Rates Explorer page
- **exchanger**: build Dashboard page with sparklines
- **exchanger**: add typed api.ts client
- **exchanger**: add collapsible sidebar layout
- **exchanger**: mount static files for SPA frontend
- **exchanger**: create SvelteKit frontend with Tailwind + Chart.js
- **exchanger**: add GET /api/providers/status endpoint
- **exchanger**: add favorites API endpoints
- **exchanger**: add GET /api/rates/coverage endpoint
- **exchanger**: add GET /api/rates/history endpoint
- **exchanger**: add favorites table and CRUD
- **exchanger**: add get_coverage() to database
- **exchanger**: add get_rates_range() to database
- **exchanger**: add /api prefix to all routes
- **exchanger**: add FastAPI app factory with lifespan
- **exchanger**: add REST API routes
- **exchanger**: add background task management
- **exchanger**: add backfill and symbols services
- **exchanger**: add rate source providers with registry
- **exchanger**: add core domain models and configuration

### Fixed

- **exchanger**: remove next_run column from admin task status table
- **exchanger**: update E2E mocks to use correct API endpoints
- **exchanger**: use favorites count for heatmap coloring
- **exchanger**: extract timestamp from BackupInfo for restore
- **exchanger**: convert task status dict to array in frontend
- **exchanger**: validate timestamp in restore endpoint to prevent path traversal
- **exchanger**: sanitize error messages in task status endpoint
- **exchanger**: add /api prefix to test routes and fix exception handler
- **exchanger**: correct BackupInfo type and history query params
- **exchanger**: use query params for backfill request
- **exchanger**: correct API endpoint paths in frontend client
- **exchanger**: use Chart.js directly for Svelte 5 compat
