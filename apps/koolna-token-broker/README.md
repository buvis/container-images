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

**How often is this needed? Once.** You run `claude setup-token` a single time, seed the file into the broker, and the broker takes it from there. From that point on, every request for a fresh access token is served from the broker's own refresh loop - you are not in the critical path. You only re-run the bootstrap if the refresh chain breaks, which is rare (account changes, PVC loss, Anthropic revocation). See [Frequency and lifetime](#frequency-and-lifetime) below for a concrete model of what refreshes automatically and what does not.

This image ships the Claude CLI but no credentials. The broker starts up, sees there is no `~/.claude/.credentials.json`, and serves `503 no token available - broker not bootstrapped` until an administrator seeds it. The seeding is **interactive and cannot be automated**: Claude's OAuth flow requires a real browser to grant consent.

There are two equivalent paths for seeding the broker. The webui path is the blessed one; the kubectl cp path is the CLI-only fallback.

### Path A (recommended): bootstrap via webui

1. On a Linux workstation with Claude Pro or Max, run `claude setup-token` and complete the browser OAuth. A file is written at `~/.claude/.credentials.json`. macOS users: see the caveat under Path B and fall back to Path B, because setup-token writes to the Keychain instead of the file on macOS.
2. Print the file contents:
   ```sh
   cat ~/.claude/.credentials.json
   ```
3. Open the webui, navigate to **Settings → Claude authentication**. The section shows the broker status. If it says "Not bootstrapped" (amber badge), paste the JSON contents into the textarea and click **Bootstrap broker**.
4. The webui's backend `POST /api/claude-auth/bootstrap` validates the payload client-side and server-side, forwards to the broker's `POST /bootstrap` endpoint, and the broker atomically writes the credentials to its PVC.
5. The status badge flips to "Bootstrapped" (green). Workspaces with `claudeAuth: true` can now fetch tokens.

The credentials JSON never touches disk in the webui pod - it is held only as the HTTP request body and forwarded to the broker. The broker is the single writer.

### Path B (fallback): bootstrap via kubectl cp

Use this path if you do not have access to the webui, or when writing runbooks that need to be scriptable outside a browser.

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

## Frequency and lifetime

Three distinct things live in `.credentials.json`, with very different lifetimes and very different "who refreshes them" answers:

| Value | Typical lifetime | Who keeps it fresh | Your involvement |
|---|---|---|---|
| `accessToken` (the short-lived bearer sent to `api.anthropic.com`) | ~8 hours from issuance | The broker, automatically, on demand | None. You never handle it |
| `refreshToken` (the long-lived credential the broker uses to mint new access tokens) | Weeks to months, rotates on use | The broker writes the new one back to `.credentials.json` atomically after every refresh | None in normal operation |
| The initial seed (the first `(accessToken, refreshToken)` pair) | Produced once by `claude setup-token` on your workstation | You | **Once at initial bootstrap.** Re-run only on the rare failure modes in [Rotation and re-bootstrap](#rotation-and-re-bootstrap) |

### What the broker does on every `/token` request

1. Read `.credentials.json`.
2. Is the current `accessToken` expiring within 5 minutes? If no → return it as-is.
3. If yes → run `claude -p ok`. That command causes the CLI to use the current `refreshToken`, obtain a new `accessToken` + new `refreshToken` from Anthropic, and atomically write the rotated pair back to `.credentials.json`.
4. Re-read the file and return the new `accessToken`.

You are not in that loop. The broker is the single writer of `.credentials.json`, so the rotation never races - which is exactly why concurrent workspaces cannot share a credentials file directly and why this component exists.

Broker logs during a refresh:

```
INFO koolna-token-broker triggering claude refresh
```

Broker logs during a refresh failure:

```
WARNING koolna-token-broker claude refresh exited N: ...
```

A healthy broker only logs refreshes every ~8 hours (when the previous access token nears expiry) and otherwise serves tokens from the cached file.

### When users see the 8-hour limit

A long-running tmux shell captured its `CLAUDE_CODE_OAUTH_TOKEN` env var at shell launch. That env var is a snapshot - it does not auto-update in place. So if a single shell stays alive past the ~8-hour mark, the in-shell token is stale even though the broker has a fresh one.

The blessed refresh path is to open a new tmux pane (`Ctrl-B c`): the new pane goes through `koolna-auth-init`, hits the broker, and exports a fresh token. Or inside an existing shell:

```sh
export CLAUDE_CODE_OAUTH_TOKEN=$(curl -sf "$KOOLNA_TOKEN_BROKER_URL/token")
```

This is a user-level convenience for long-running shells, not an admin bootstrap concern.

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
