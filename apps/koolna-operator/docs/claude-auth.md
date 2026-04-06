# Claude Authentication in Koolna Workspaces

This document explains how Koolna workspaces can be configured for automatic Claude Code authentication, how the flow works end to end, and how to troubleshoot it.

## What it does

When `spec.claudeAuth: true` is set on a Koolna resource, every new tmux shell in that workspace starts with `CLAUDE_CODE_OAUTH_TOKEN` already exported. Claude Code reads this variable at startup and runs authenticated immediately, so there are no OAuth URLs, no browser prompts, and nothing to paste.

When `claudeAuth` is not set or is `false`, the workspace is identical to a vanilla Koolna pod and nothing about Claude Code is assumed or modified.

## Why this exists

Clicking an OAuth URL inside the webui's xterm.js terminal is unreliable because long wrapped URLs are not selected as a single unit. Sidestepping the interactive login is the robust fix.

A simpler "just stash one long-lived token in a secret" approach does not work either. Claude Code uses rotating refresh tokens: whichever pod refreshes first invalidates every other pod's copy, so concurrent workspaces fight each other. The broker pattern below makes a single pod the only writer, so rotations never race.

Relevant public issues documenting the race behaviour:
- [anthropics/claude-code#24317](https://github.com/anthropics/claude-code/issues/24317)
- [anthropics/claude-code#27933](https://github.com/anthropics/claude-code/issues/27933)
- [anthropics/claude-code#37402](https://github.com/anthropics/claude-code/issues/37402)

## Architecture

```
                  ┌─────────────────────────────┐
  admin once ───▶ │ claude setup-token (local)  │
                  │        │                    │
                  │        ▼                    │
                  │  ~/.claude/.credentials.json│
                  └───────────────┬─────────────┘
                                  │ kubectl cp, once
                                  ▼
                  ┌─────────────────────────────┐
                  │  koolna-token-broker (pvc)  │
                  │  single replica, sole writer│
                  │  GET /token → sk-ant-oat01- │
                  └───────────────┬─────────────┘
                                  │ in-cluster HTTP :8080
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
 ┌────────▼────────┐     ┌────────▼────────┐     ┌────────▼────────┐
 │ workspace A     │     │ workspace B     │     │ workspace C     │
 │ (claudeAuth)    │     │ (claudeAuth)    │     │ (vanilla)       │
 │                 │     │                 │     │                 │
 │ tmux sidecar ──▶│     │ tmux sidecar ──▶│     │ tmux sidecar    │
 │ koolna-auth-init│     │ koolna-auth-init│     │ (no token fetch)│
 │     │           │     │     │           │     │                 │
 │     ▼ nsenter   │     │     ▼ nsenter   │     │     ▼ nsenter   │
 │ user shell with │     │ user shell with │     │ user shell      │
 │ CLAUDE_CODE_    │     │ CLAUDE_CODE_    │     │ (no token)      │
 │ OAUTH_TOKEN     │     │ OAUTH_TOKEN     │     │                 │
 └─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Components

| Component | Role |
|---|---|
| `koolna-token-broker` | Single-replica pod on a PVC holding `.credentials.json`. Serves `GET /token` with the current access token. Triggers a Claude CLI refresh if expiry is within 5 minutes. |
| `koolna-auth-init` (script in `koolna-tmux`) | Runs in the sidecar before `nsenter` into the main container. Curls the broker, exports `CLAUDE_CODE_OAUTH_TOKEN`, then execs the shell. Token lives in the calling process env and is inherited by the nsenter'd shell. |
| `koolna-operator` | When `spec.claudeAuth: true`, injects `KOOLNA_TOKEN_BROKER_URL` on the sidecar container and strips `.claude/.credentials.json` from `KOOLNA_CREDENTIAL_PATHS` so the pre-existing credential sync does not clobber broker-managed state. |
| `koolna-webui` | Exposes the opt-in as a checkbox on the workspace creation form. |

### End-to-end flow

1. **One-time setup** (admin): run `claude setup-token` on a workstation with a Claude Pro or Max subscription, then `kubectl cp ~/.claude/.credentials.json` into the broker pod. See `apps/koolna-token-broker/README.md` for the exact commands.
2. **Workspace creation**: user checks "Enable Claude authentication" in the webui. The webui posts `claudeAuth: true` to the operator's API. The operator creates a pod where the sidecar has `KOOLNA_TOKEN_BROKER_URL` set.
3. **Shell launch**: user connects to the workspace. The tmux sidecar runs `NSENTER_CMD` which starts with `/usr/local/bin/koolna-auth-init`. The script curls the broker, receives a fresh access token, exports it, then exec's nsenter into the main container. The shell sees `CLAUDE_CODE_OAUTH_TOKEN` in its environment.
4. **Claude invocation**: user runs `claude`. Claude reads the env var, skips interactive login entirely, runs authenticated.
5. **Token aging**: access tokens live ~8 hours. Long-running shells do not auto-refresh. When the token expires the user opens a new tmux pane (`Ctrl-B c`) and the new pane fetches a fresh token. See "Token lifetime" below for the manual refresh one-liner if you need it inside an existing shell.

## How to enable it

### From the webui

Creating a workspace with auth:
1. Open the webui workspace creation form.
2. Check **Enable Claude authentication**.
3. Submit.

### From a raw manifest

```yaml
apiVersion: koolna.buvis.net/v1alpha1
kind: Koolna
metadata:
  name: my-workspace
spec:
  repo: https://github.com/owner/repo
  branch: main
  image: ghcr.io/buvis/koolna-base:latest
  storage: 10Gi
  claudeAuth: true
```

## Token lifetime and in-shell refresh

OAuth access tokens issued by `claude setup-token` are short-lived (typically 8-12 hours). Long-running tmux panes can observe a stale token mid-session. Two ways to refresh:

- **New pane** (blessed path): `Ctrl-B c` opens a new tmux window. The new shell goes through `koolna-auth-init` and gets a fresh token.
- **In-place**: inside an existing shell:
  ```sh
  export CLAUDE_CODE_OAUTH_TOKEN=$(curl -sf "$KOOLNA_TOKEN_BROKER_URL/token")
  ```

The broker transparently handles refresh token rotation behind this. It is the single writer of the credentials file, so rotation never races.

## Bootstrap

Two equivalent paths. See [apps/koolna-token-broker/README.md](../../koolna-token-broker/README.md) for the full procedure including prerequisites and troubleshooting.

**Webui (recommended):**
1. On a Linux workstation: `claude setup-token`, then `cat ~/.claude/.credentials.json`.
2. In the webui, navigate to **Settings → Claude authentication**.
3. Paste the JSON contents into the textarea, click **Bootstrap broker**.
4. Status badge flips to **Bootstrapped**.

**CLI fallback:**
1. `claude setup-token` on a Linux workstation.
2. `kubectl -n koolna cp ~/.claude/.credentials.json <broker-pod>:/home/node/.claude/.credentials.json`.
3. `kubectl -n koolna rollout restart deploy/koolna-token-broker`.
4. Verify with `curl http://koolna-token-broker:8080/token` from an in-cluster debug pod.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `claude` prints an OAuth URL | `claudeAuth: false` on the workspace, or the sidecar did not pick up the env var | Confirm `kubectl get koolna <name> -o yaml` shows `claudeAuth: true`; check `kubectl logs <pod> -c tmux-sidecar` for `koolna-auth-init:` error lines |
| Shell starts with `koolna-auth-init: token broker unreachable` | Broker pod not running, or NetworkPolicy blocking access | `kubectl -n koolna get pods -l app=koolna-token-broker`; if the pod is up, test reachability from a debug pod in the koolna namespace |
| Broker pod is `Running` but `/health` returns 503 | Credentials file not yet seeded | Run the admin bootstrap above |
| `claude` returns 401 mid-session | Access token expired inside the running shell | Open a new tmux pane or run the in-place refresh one-liner |
| Broker logs `claude refresh exited N:` repeatedly | Refresh token has been revoked or expired | Re-run `claude setup-token` locally and re-bootstrap the broker |
| Workspace has `claudeAuth: true` but its own credential-sync overwrites the broker token | Operator did not strip `.claude/.credentials.json` from `KOOLNA_CREDENTIAL_PATHS` | Should be automatic; if you hit this, confirm operator version matches the release that added claudeAuth and report a bug |

## Why not other approaches

| Approach | Rejected because |
|---|---|
| Fix the webui xterm.js URL matcher | Only sidesteps one symptom; wrapped-URL selection is a recurring xterm.js limitation, not specific to one URL format |
| Mount `~/.claude/` read-write across all pods | Refresh token rotation races; the first pod to refresh invalidates every other copy |
| Mount `~/.claude/` read-only | Claude Code unconditionally writes back on refresh; read-only mounts cause EROFS errors on every invocation ([claude-code#37512](https://github.com/anthropics/claude-code/issues/37512)) |
| Use `apiKeyHelper` returning a Claude OAuth token | Anthropic rejects `sk-ant-oat01-*` tokens sent via the Messages API ([claude-code#28091](https://github.com/anthropics/claude-code/issues/28091), [#37205](https://github.com/anthropics/claude-code/issues/37205)). Only the `CLAUDE_CODE_OAUTH_TOKEN` path still accepts them |
| Bake a Claude wrapper into `koolna-base` | Koolna is universal; users bring their own images. Feature additions must stay out of the base |
| Inject via a `PATH`-based wrapper from the operator | User dotfiles routinely prepend to `PATH`, pushing operator-injected dirs out of first position. The sidecar-level injection is reliable regardless of user shell configuration |

## Security notes

- The broker holds your real Pro/Max OAuth credentials. Treat its PVC like any other secret material.
- In-cluster access is not authenticated beyond namespace boundaries. If you run untrusted workloads in the `koolna` namespace, consider adding a NetworkPolicy that restricts ingress to pods carrying the `koolna.buvis.net/name` label.
- The broker does not expose an ingress. Access is `ClusterIP` only.
- Refresh tokens issued by Anthropic are bearer credentials. If a workspace pod is compromised, rotate by re-running `claude setup-token` locally and re-seeding the broker.
