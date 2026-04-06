# koolna-token-broker

Thin HTTP service that stores and serves a Claude OAuth token to koolna workspace pods.

For the full end-to-end auth flow, architecture, and troubleshooting see [koolna-operator's claude-auth doc](../koolna-operator/docs/claude-auth.md).

## Why

The token produced by `claude setup-token` is valid for ~1 year. The broker persists it on a PVC and serves it over in-cluster HTTP so workspace pods can fetch it at every tmux shell launch without the token being scattered across K8s Secrets or individual pod specs.

## Endpoints

| Path | Method | Purpose |
|---|---|---|
| `/token` | GET | Returns the current token as `text/plain`. 503 if not bootstrapped. |
| `/health` | GET | 200 if a token is stored, 503 otherwise. |
| `/status` | GET | JSON `{"bootstrapped": true/false}`. Used by the webui settings page. |
| `/bootstrap` | POST | Accepts a plain-text token in the request body, validates the `sk-ant-*` format, and persists it atomically to the PVC. |

## Bootstrap

**How often?** Once per token lifetime (~1 year). Replace when the token expires or is revoked.

### Via webui (recommended)

1. On any workstation with Claude Pro or Max: `claude setup-token`.
2. Complete the browser OAuth flow.
3. Copy the printed token (starts with `sk-ant-`).
4. Open the webui **Settings** page. Under **Claude authentication**, paste the token and click **Bootstrap broker**.
5. Status badge flips from amber ("Not bootstrapped") to green ("Bootstrapped").

### Via CLI (fallback)

```sh
# Get the token
claude setup-token
# Copy the printed value, then:
BROKER_POD=$(kubectl -n koolna get pod -l app=koolna-token-broker -o jsonpath='{.items[0].metadata.name}')
curl -X POST -H 'Content-Type: text/plain' -d 'sk-ant-oat01-YOUR_TOKEN_HERE' \
  http://koolna-token-broker.koolna.svc.cluster.local:8080/bootstrap
```

Or write the token directly into the broker pod's PVC:

```sh
kubectl exec -n koolna "$BROKER_POD" -- sh -c 'mkdir -p ~/.claude && cat > ~/.claude/token' <<< 'sk-ant-oat01-YOUR_TOKEN_HERE'
```

### Verify

```sh
kubectl -n koolna run curl-test \
  --rm -it \
  --image=curlimages/curl:latest \
  --restart=Never \
  -- curl -sSf http://koolna-token-broker:8080/token
```

Expected: a single line starting with `sk-ant-`. Anything else means bootstrap did not succeed.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Pod stays `0/1` NotReady | No token stored yet. Bootstrap via webui or CLI. |
| `curl /token` returns 503 | Same: not bootstrapped, or token file was deleted. |
| `curl /token` returns a value but Claude CLI still prompts for login | Workspace `claudeAuth` not set to true, or sidecar not receiving `KOOLNA_TOKEN_BROKER_URL`. Check operator logs. |
| Token rejected by Claude CLI with 401 | Token expired (~1 year) or revoked. Re-run `claude setup-token` and re-bootstrap. |

## Alternative: Console API key

If Pro/Max subscription auth is not suitable, bypass the broker entirely: set `claudeAuth: false` on workspaces and add `ANTHROPIC_API_KEY=sk-ant-api03-...` to the workspace env vars. Different billing model (pay-per-use) but no broker infrastructure needed.
