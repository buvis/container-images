# AGENTS.md

Agent instructions for this repo. The image-specific guardrails are in `CLAUDE.md`.

## Dependency upgrades

- ⚠️ **TypeScript 7 is on hold** (Renovate #580 is kept open on purpose as the reminder; do not pin it away). TS 7 is the native compiler, and its package no longer exports the classic `typescript` JS API that these tools call:
  - `@sveltejs/kit`: clara and exchanger `vite build` fails in `write_tsconfig`
  - `svelte-check`: clara and exchanger type checking crashes
  - `typescript-eslint`: koolna-webui `npm run lint` crashes

  Merge a TS 7 bump only when all three tools declare `typescript` 7 in their `peerDependencies` (`npm view <pkg> peerDependencies`) and these all pass locally on the bump:
  - clara: `pnpm build`, `pnpm check`, `pnpm test --run`
  - exchanger: `npm run build`, `npm run check`
  - koolna-webui: `npm run build`, `npm run lint`

  A green #580 doesn't prove this: CI only builds the images and never runs svelte-check or eslint.
