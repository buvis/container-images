# Claude Authentication in Koolna Workspaces

## What it does

When `spec.claudeAuth: true` is set on a Koolna resource, every new tmux shell in that workspace starts with `CLAUDE_CODE_OAUTH_TOKEN` already exported. Claude Code reads this variable at startup and runs authenticated immediately. No OAuth URLs, no browser prompts, nothing to paste inside the workspace.

When `claudeAuth` is not set or is `false`, the workspace is vanilla and nothing about Claude Code is assumed or modified.

## How it works

```
admin once: claude setup-token → copies printed token into webui settings

                    ┌──────────────────────────┐
                    │ koolna-token-broker (PVC) │
                    │ GET /token → sk-ant-...   │
                    └────────────┬─────────────┘
                                 │ in-cluster HTTP
              ┌──────────────────┼──────────────────┐
              │                  │                  │
     ┌────────▼──────┐  ┌───────▼───────┐  ┌───────▼───────┐
     │ workspace A   │  │ workspace B   │  │ workspace C   │
     │ claudeAuth    │  │ claudeAuth    │  │ vanilla       │
     │               │  │               │  │               │
     │ sidecar ──────│  │ sidecar ──────│  │ sidecar       │
     │ koolna-auth-  │  │ koolna-auth-  │  │ (no fetch)    │
     │ init → curl   │  │ init → curl   │  │               │
     │     │         │  │     │         │  │     │         │
     │     ▼ nsenter │  │     ▼ nsenter │  │     ▼ nsenter │
     │ shell with    │  │ shell with    │  │ shell         │
     │ CLAUDE_CODE_  │  │ CLAUDE_CODE_  │  │ (no token)    │
     │ OAUTH_TOKEN   │  │ OAUTH_TOKEN   │  │               │
     └───────────────┘  └───────────────┘  └───────────────┘
```

### Components

| Component | Role |
|---|---|
| `koolna-token-broker` | Single-replica pod on a PVC storing the token. Serves `GET /token` and `POST /bootstrap`. No Claude CLI dependency; token is stored as a plain text file. |
| `koolna-auth-init` (script in `koolna-tmux`) | Runs in the sidecar before `nsenter`. Curls the broker, exports `CLAUDE_CODE_OAUTH_TOKEN`, execs the shell. |
| `koolna-operator` | When `spec.claudeAuth: true`, injects `KOOLNA_TOKEN_BROKER_URL` on the sidecar and strips `.claude/.credentials.json` from the credential sync path. |
| `koolna-webui` | Workspace creation checkbox + Settings page for bootstrap. |

### End-to-end flow

1. **Bootstrap (once)**: admin runs `claude setup-token` on a workstation, pastes the printed token into webui Settings. Token is valid ~1 year.
2. **Workspace creation**: user checks "Enable Claude authentication". Operator injects `KOOLNA_TOKEN_BROKER_URL` on the sidecar.
3. **Shell launch**: tmux sidecar runs `koolna-auth-init`, which curls the broker, receives the token, exports it, nsenter's into the main container. Shell inherits `CLAUDE_CODE_OAUTH_TOKEN`.
4. **Claude invocation**: `claude` reads the env var, runs authenticated.

## How to enable

### From the webui

Check **Enable Claude authentication** when creating a workspace.

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

## Bootstrap

Two equivalent paths. See [apps/koolna-token-broker/README.md](../../koolna-token-broker/README.md) for detailed steps.

**Webui (recommended):**
1. On any workstation: `claude setup-token`, complete browser OAuth.
2. In the webui, navigate to **Settings → Claude authentication**.
3. Paste the printed token, click **Bootstrap broker**.

**CLI fallback:**
```sh
claude setup-token
# Then POST the token to the broker directly:
curl -X POST -H 'Content-Type: text/plain' -d '<token>' \
  http://koolna-token-broker.koolna.svc.cluster.local:8080/bootstrap
```

## Token lifetime

The token from `claude setup-token` is valid for ~1 year. No automatic refresh is involved. When the token expires or is revoked, repeat the bootstrap. The broker logs `503` on `/token` requests when the stored token is rejected by Claude; the admin replaces it via the same bootstrap path.

## In-shell refresh

Every new tmux pane fetches a fresh copy of the stored token from the broker. For a long-running pane, the env var is a snapshot from launch time. If you need to re-fetch in-place (e.g., after the admin replaces the token):

```sh
export CLAUDE_CODE_OAUTH_TOKEN=$(curl -sf "$KOOLNA_TOKEN_BROKER_URL/token")
```

Or open a new pane (`Ctrl-B c`), which fetches automatically.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `claude` prints OAuth URL | `claudeAuth: false` on workspace, or sidecar missing env var | `kubectl get koolna <name> -o jsonpath='{.spec.claudeAuth}'` should be `true` |
| `koolna-auth-init: token broker unreachable` in sidecar logs | Broker pod not running | `kubectl -n koolna get pods -l app=koolna-token-broker` |
| Broker `/health` returns 503 | Not bootstrapped | Paste token via webui Settings |
| `claude` returns 401 | Token expired or revoked (~1 year lifetime) | Re-run `claude setup-token` and re-bootstrap |
| Workspace credential sync overwrites broker token | Operator not stripping `.claude` from credential paths | Confirm operator version includes claudeAuth support |

## Why not simpler approaches

| Approach | Rejected because |
|---|---|
| Fix webui xterm.js URL matcher | Only sidesteps one symptom; wrapped-URL selection is a recurring xterm.js limitation |
| Inject token as K8s Secret env var directly | Would require operator to read a Secret and mount it. Broker is a cleaner indirection: the Secret contents change via webui, no pod restarts needed. |
| Bake wrapper into koolna-base | Koolna is universal; users bring their own images |
| PATH-based wrapper from operator | User dotfiles routinely prepend to PATH, pushing operator-injected dirs out of first position |

## Security notes

- The broker holds your Pro/Max OAuth token. Treat its PVC like any other secret material.
- In-cluster access is not authenticated beyond namespace boundaries. Add a NetworkPolicy if running untrusted workloads in the koolna namespace.
- The broker exposes no ingress. ClusterIP only.
- If compromised, rotate by running `claude setup-token` and re-bootstrapping.
