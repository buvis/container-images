# container-images — agent guardrails

A monorepo of 20 container images (`apps/*`, `base/*`). Most complexity lives in the **koolna** dev-environment ecosystem (operator, webui, session-manager, git-clone, base chain). See `dev/local/evolution-assessment-2026-07-09.md` for the current health assessment and `dev/local/prds/ROADMAP.md` for the phased backlog.

These invariants encode the failure modes that have actually bitten this repo. Marked ✅ (holds today) or ⚠️ (gap, tracked by a PRD).

## Operator (koolna-operator)

- ⚠️ **PVC lifecycle is the finalizer's job, never ownerRef GC.** Setting `SetControllerReference` on a PVC makes Kubernetes GC delete it on CR delete regardless of `deletionPolicy` — envtest has no GC so tests won't catch it. Assert PVCs carry no ownerRef. (Gap → PRD 00029.)
- ⚠️ **Reconcile must converge, not create-only.** Returning an existing Pod/Service/Secret untouched means live spec edits are silent no-ops. Hash the pod-spec inputs into an annotation and recreate-on-drift; `CreateOrUpdate` the Service. (Gap → PRD 00034.)
- ✅ **After any `koolna_types.go` change run BOTH `make manifests` (CRD YAML) and `make generate` (deepcopy); commit with zero drift.**
- ✅ **Validate at the boundary AND the helper.** New operator env vars validate in `cmd/main.go` and again where consumed. Prefer CRD `+kubebuilder:validation` markers over controller-only checks (Gap for repo/branch/dotfilesMethod → PRD 00038).
- ✅ **Operator-managed images are digest-pinned** (`repo:tag@sha256:...`); the operator refuses to start on an unpinned `KOOLNA_GIT_CLONE_IMAGE`/`KOOLNA_SESSION_MANAGER_IMAGE`. Keep it that way.
- Cache-PVC wipe on **CR delete** is by design. Only the **workspace** PVC under `Retain` must survive.

## Shell (session-manager, git-clone, bootstrap)

- ⚠️ **`set -eu` does not forgive silent failures.** A `( while …; cmd; done ) &` subshell inherits `-e`; one unguarded `curl`/`cat` kills the loop with no log. Guard every command in a long-lived loop (`cmd || echo "…failed rc=$?"`). A `curl … | sh` cannot fail under POSIX sh — check `command -v` after. (Gap → PRD 00032.)
- ✅ **`cmd; rc=$?` is a trap under `set -e`** — the assignment never runs on failure. Use `rc=0; cmd || rc=$?`.
- ✅ **Absorb TOCTOU on session/marker creation** — `tmux new-session … 2>/dev/null || tmux has-session` (pattern from a0e77a6). Hunt for unguarded siblings when touching these scripts.
- ⚠️ **The `/cache/.koolna/{phase,ready,failed,pid,bootstrap.sh}` marker protocol is a cross-image contract.** Names/paths are duplicated across git-clone, session-manager, and the operator (+tests). Changing one silently breaks bootstrap. (Single-sourcing → PRD 00037.)
- ✅ Bats harness at `tests/shell/` runs in CI (`test.yaml` `shell-tests` job). Ship a bats test with any shell-contract change; watch it fail once against the old line. Bats is required locally (`brew install bats-core`).

## Webui

- ⚠️ **The terminal proxy is an unauthenticated in-cluster shell** if reachable. Keep a NetworkPolicy limiting ingress to the nginx controller; never expose it without an auth layer. (Gap → PRD 00035.)
- ⚠️ **webui hand-mirrors the operator CRD (`k8s/types.go`) and phase constants — this drifts.** Prefer importing operator types / generating the TS phase union. (Gap → PRD 00039.)
- ✅ Frontend requires git identity + credentials even though the API treats them as optional — **intentional**, do not relax on reviewer feedback.
- ✅ `@xterm/xterm` v6 is **blocked**: its three addons (fit, web-links, webgl) only have beta v6 releases; CI compiles but runtime breaks. Do not merge a Renovate xterm-v6 PR until addons ship stable.

## CI / release

- ⚠️ **The "Test" summary gate must fail-closed.** Check `needs.*.result` for `failure` OR `cancelled` (skipped is allowed for path-filtered builds); a hand-listed per-job condition silently skips new jobs and treats skipped-on-error as green. (Gap → PRD 00030.)
- ⚠️ **Renovate can bump a version but not a hand-pinned checksum next to it.** Never pair a Renovate-tracked `ARG *_VERSION` with a static `ARG *_SHA256`; vendor the script or pin by commit SHA. (Gap → PRD 00031.)
- ⚠️ **A single failed release run strands a release indefinitely** (the job only reconciles the pushed set). Sweep all images where tag < VERSION. (Gap → PRD 00041.)
- ✅ **CHANGELOG discipline** (buvis rule): every `feat`/`fix`/breaking commit updates the image's `CHANGELOG.md` under `[Unreleased]`, prefixed `**<image>**:`. Read the existing structure first — duplicate `### Added` blocks have shipped twice and corrupt cut release notes. (Dup-block CI lint → PRD 00041.)
- ✅ Every image needs `Dockerfile`, `VERSION`, `PLATFORM`, `CHANGELOG.md`; CI auto-detects `apps/` vs `base/`. A koolna-base change cascades to stack images via `.github/dep-map.json` (incomplete for debian-slim → PRD 00042).
- ✅ Third-party GitHub Actions are SHA-pinned; Dockerfile FROMs are digest-pinned. Keep both.

## Packaging

- ⚠️ **Pin what installs; verify what downloads.** Unpinned apt/pip resolution (mopidy) turns upstream drift into master fix-storms; `curl -k` / checksum-less downloads are a supply-chain hole. Non-root `USER` and `exec`-ed entrypoints (SIGTERM) are the fleet norm — match it. (Gaps → PRD 00042.)

## Working documents

- Self-created working docs go in `dev/local/` (gitignored). PRDs live in `dev/local/prds/{backlog,wip,done}/`, numbered `NNNNN-slug-vN.md`. `dev/internal/` is also gitignored.
