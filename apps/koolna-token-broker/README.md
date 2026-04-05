# koolna-token-broker

Single-writer HTTP broker that serves short-lived Claude OAuth access tokens to koolna workspace pods. It owns the `~/.claude/.credentials.json` file backing the Claude CLI and triggers refresh when the current access token is close to expiry.

For the full end-to-end auth flow, architecture, and troubleshooting see [koolna-operator's claude-auth doc](../koolna-operator/docs/claude-auth.md).

## Why

Claude CLI uses rotating refresh tokens. If multiple pods share a credentials file, the first one to refresh invalidates every other copy ([anthropics/claude-code#24317](https://github.com/anthropics/claude-code/issues/24317), [#27933](https://github.com/anthropics/claude-code/issues/27933)). The broker is the single writer: workspace pods hold no credentials state and fetch a fresh access token on every new shell.

## Endpoints

| Path | Purpose |
|---|---|
| `GET /token` | Returns the current access token as `text/plain`. Triggers a refresh if expiry < 5 minutes. Returns 503 if the broker is not bootstrapped. |
| `GET /health` | 200 if credentials file is present, 503 otherwise. |

## Bootstrap

This image ships the Claude CLI but no credentials. The broker starts up, sees there is no `~/.claude/.credentials.json`, and serves `503 no token available - broker not bootstrapped` until an administrator seeds it. The seeding is **interactive and cannot be automated**: Claude's OAuth flow requires a real browser to grant consent.

### Prerequisites

- An Anthropic **Claude Pro or Claude Max** personal subscription. Console API keys (`sk-ant-api03-...`) are a different auth path and will not work with `CLAUDE_CODE_OAUTH_TOKEN`; see "Alternative: Console API key" below.
- A workstation with a recent `claude` CLI installed (`npm install -g @anthropic-ai/claude-code` or the native installer from <https://claude.com/product/claude-code>).
- A browser on the same workstation for the interactive OAuth flow.
- `kubectl` configured for your koolna cluster and pointed at the `koolna` namespace.
- The broker pod deployed and in `Running` state (it will be `0/1` NotReady — that is expected before bootstrap).

### Step 1 - run `claude setup-token` locally

On your workstation:

```sh
claude setup-token
```

This opens a browser, completes OAuth against your Claude Pro/Max account, and writes `~/.claude/.credentials.json`. The file is valid JSON containing a `claudeAiOauth` object with `accessToken`, `refreshToken`, `expiresAt`, and `scopes` fields.

**macOS caveat**: as of Claude CLI ~2.1 on macOS, `setup-token` may write credentials only to the system Keychain instead of `~/.claude/.credentials.json` ([claude-code#19274](https://github.com/anthropics/claude-code/issues/19274)). Check:

```sh
test -s ~/.claude/.credentials.json && echo ok || echo EMPTY
```

If the file is empty or missing after setup-token, use a Linux workstation or WSL instead. The broker image runs the CLI on Linux internally, so once the credentials are in the broker PVC everything works; the macOS issue only affects producing the initial file locally.

Before copying, sanity-check the structure:

```sh
jq '.claudeAiOauth | keys' ~/.claude/.credentials.json
```

Expected output:

```json
[
  "accessToken",
  "expiresAt",
  "refreshToken",
  "scopes"
]
```

If the structure is different, stop - the broker expects exactly that shape. Open an issue with the actual keys so the broker parser can be updated.

### Step 2 - copy the credentials into the broker PVC

```sh
BROKER_POD=$(kubectl -n koolna get pod -l app=koolna-token-broker -o jsonpath='{.items[0].metadata.name}')
echo "broker pod: $BROKER_POD"

kubectl -n koolna cp \
  ~/.claude/.credentials.json \
  "$BROKER_POD:/home/node/.claude/.credentials.json"
```

`kubectl cp` runs as the container's `node` user (uid 1000). The file lands owned by that user and the broker can read it.

### Step 3 - restart the broker

The broker reads the file on each request, so technically no restart is needed for the broker to pick up the new credentials. Restart anyway to clear any stale in-memory state and to make the new `Ready` status obvious:

```sh
kubectl -n koolna rollout restart deploy/koolna-token-broker
kubectl -n koolna rollout status deploy/koolna-token-broker --timeout=120s
```

After the restart the pod should reach `1/1 Ready`. If it stays `0/1` the readiness probe is still returning 503 - see "Troubleshooting" below.

### Step 4 - verify

From inside the cluster, fetch a token:

```sh
kubectl -n koolna run curl-test \
  --rm -it \
  --image=curlimages/curl:latest \
  --restart=Never \
  -- curl -sSf http://koolna-token-broker:8080/token
```

Expected output: a single line starting with `sk-ant-oat01-` and no newline. Anything else (empty output, HTTP error, `connection refused`) means bootstrap did not succeed - see troubleshooting.

You can also hit `/health`:

```sh
kubectl -n koolna run curl-test \
  --rm -it \
  --image=curlimages/curl:latest \
  --restart=Never \
  -- curl -sS -w ' %{http_code}\n' http://koolna-token-broker:8080/health
```

Expected: `ok 200`. Before bootstrap it returns `no credentials 503`.

### What happens next

Workspaces created with `claudeAuth: true` will fetch tokens from the broker at every tmux shell launch. Existing workspaces (created before bootstrap) need to be restarted to pick up a fresh token; opening a new tmux pane is enough.

## Token expiration and refresh

The OAuth `accessToken` inside `.credentials.json` is short-lived (~8 hours from issuance). The `refreshToken` is long-lived (typically weeks to months) but it **rotates on use** - each refresh produces a new refresh token that invalidates the old one. This is exactly why the broker exists as a single writer: if multiple pods shared the credentials file, the first one to refresh would invalidate everyone else's copy.

The broker calls `claude -p ok` when an incoming `/token` request finds the current access token expiring within 5 minutes. That command triggers the CLI's internal refresh flow and writes the rotated credentials back to `.credentials.json`. Broker logs will show:

```
INFO koolna-token-broker triggering claude refresh
```

Refresh failures show as:

```
WARNING koolna-token-broker claude refresh exited N: ...
```

If you see repeated refresh failures, the refresh token chain is broken (Anthropic revoked the grant, rate-limiting, incident, etc.). Recovery is **re-bootstrap from scratch**: repeat the bootstrap procedure above with a fresh `claude setup-token` run on your workstation.

## Troubleshooting

| Symptom | Diagnosis | Fix |
|---|---|---|
| Pod stays `0/1` after `rollout status` | Readiness probe returns 503, meaning credentials file is missing or unreadable | Run `kubectl -n koolna logs deploy/koolna-token-broker` - look for the warning line. If the file is missing, repeat step 2. If it is present but unreadable, check ownership inside the pod (`kubectl exec -it "$BROKER_POD" -- ls -la /home/node/.claude/`) |
| `curl /token` returns empty body | `.credentials.json` does not match the expected schema | `kubectl exec -it "$BROKER_POD" -- cat /home/node/.claude/.credentials.json \| jq 'keys'` and confirm it has a top-level `claudeAiOauth` key |
| `curl /token` returns 503 | Broker started before bootstrap, or `.credentials.json` was deleted | Repeat bootstrap |
| `curl /token` returns a valid token but Claude CLI still asks for login inside a workspace | Workspace was created before claudeAuth support, or the sidecar is not receiving `KOOLNA_TOKEN_BROKER_URL` | `kubectl get koolna <name> -o jsonpath='{.spec.claudeAuth}'` - must be `true`. Check sidecar env with `kubectl exec -it <pod> -c tmux-sidecar -- env \| grep KOOLNA_TOKEN` |
| Broker logs show `claude refresh exited 1` with `401` | Refresh token rejected by Anthropic | Re-bootstrap |
| Broker logs show `claude refresh timed out` | Outbound network to `api.anthropic.com` blocked | Check proxy config and NetworkPolicies; the broker honors `HTTPS_PROXY` if set |
| `kubectl cp` fails with `permission denied` | File ownership mismatch on the PVC | Verify the pod is running as uid 1000: `kubectl exec -it "$BROKER_POD" -- id` should print `uid=1000(node)`. The `fsGroup: 1000` in the deployment should handle this automatically |

## Rotation and re-bootstrap

You will need to re-run bootstrap when:

- Anthropic revokes the grant (rare, usually tied to account events or policy changes)
- You rotate your Claude account password or change subscription tier
- The broker PVC is wiped or lost
- You see repeated `claude refresh exited` errors in broker logs that do not self-heal

Re-bootstrap is the same procedure. There is no partial recovery - always start fresh from step 1.

## Alternative: Console API key

If Pro/Max subscription auth is too fragile for your use case, the broker can be bypassed entirely by using an Anthropic **Console API key** (`sk-ant-api03-...`) and injecting it directly as `ANTHROPIC_API_KEY` via the per-workspace env vars or `koolna-env-defaults` secret. That is a different billing model (pay-per-use instead of subscription-flat) and does not require this broker. If you choose that path, set `claudeAuth: false` and add `ANTHROPIC_API_KEY=sk-ant-api03-...` to the workspace's env vars.

## Configuration

The broker reads credentials from `$HOME/.claude/.credentials.json` and listens on `:8080`. Both are hardcoded: the broker is a single-purpose component and exposing knobs would be misleading.

## Why Python stdlib on a Node base

The broker does two things: read a JSON file and serve HTTP. Python 3 ships both in stdlib. The base image is `node:24-trixie-slim` because `@anthropic-ai/claude-code` is an npm package; adding `python3` via apt keeps the runtime dependency chain to just `node` + `python3` + `tini`. No application dependencies, no virtualenv, no requirements file.
