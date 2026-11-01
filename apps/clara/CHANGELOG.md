# Changelog — clara

## [Unreleased]

### Changed

- **clara**: migrate the frontend to SvelteKit 3 (with adapter-static 4, svelte 5.57, vite 8.3): config moves from `svelte.config.js` into `sveltekit()` in `vite.config.ts`, `$lib` becomes the `#lib` subpath import, `$app/stores` becomes `$app/state`, `$app/environment` becomes `$app/env`, and the `uuid` param matcher moves to `src/params.ts`

## 2026-03-26

### Fixed

- **deps**: update dependency lucide-svelte to v1

## 2026-03-07

### Fixed

- **deps**: update dependency lucide-svelte to ^0.577.0 (#281)

## 2026-03-05

### Fixed

- **deps**: update dependency lucide-svelte to ^0.576.0 (#272)

## 2026-02-27

### Fixed

- **clara**: pin uv version in Dockerfile
- **clara**: pin pnpm version in Dockerfile

## 2026-02-25

### Added

- **clara**: add personal CRM app as unified container

### Fixed

- **deps**: pin dependencies (#231)
