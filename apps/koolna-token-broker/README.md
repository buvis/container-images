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

This image ships Claude CLI but no credentials. The credentials must be seeded once by an administrator:

1. On a workstation with Claude Pro or Max:
   ```
   claude setup-token
   ```
   This opens a browser, completes OAuth, and writes `~/.claude/.credentials.json`.

2. Copy the file into the broker's PVC-backed home directory:
   ```
   kubectl -n koolna cp ~/.claude/.credentials.json \
     $(kubectl -n koolna get pod -l app=koolna-token-broker -o name | head -1):/home/node/.claude/.credentials.json
   ```

3. Restart the broker so it picks up the new file cleanly:
   ```
   kubectl -n koolna rollout restart deploy/koolna-token-broker
   ```

4. Verify:
   ```
   kubectl -n koolna run curl-test --rm -it --image=curlimages/curl --restart=Never -- \
     curl -s http://koolna-token-broker:8080/token
   ```

## Rotation

Refresh tokens typically last months, but Anthropic may invalidate them during incidents or policy changes. When the broker cannot refresh anymore you will see repeated errors in its logs:
```
claude refresh exited N: ...
```
Recover by repeating the bootstrap above.

## Configuration

The broker reads credentials from `$HOME/.claude/.credentials.json` and listens on `:8080`. Both are hardcoded: the broker is a single-purpose component and exposing knobs would be misleading.

## Why Python stdlib on a Node base

The broker does two things: read a JSON file and serve HTTP. Python 3 ships both in stdlib. The base image is `node:24-trixie-slim` because `@anthropic-ai/claude-code` is an npm package; adding `python3` via apt keeps the runtime dependency chain to just `node` + `python3` + `tini`. No application dependencies, no virtualenv, no requirements file.
