# Claude Authentication in Koolna Workspaces

## What it does

`CLAUDE_CODE_OAUTH_TOKEN` is stored as a cluster-wide default environment variable in the `koolna-env-defaults` Secret. The operator injects this Secret into every workspace pod via `envFrom`. The token reaches user shells through the tmux sidecar's nsenter (same path as `SSL_CERT_FILE`, `CARGO_HTTP_TIMEOUT`, and other operator-managed env vars).

Claude Code reads `CLAUDE_CODE_OAUTH_TOKEN` at startup and runs authenticated. No OAuth URLs, no browser prompts, nothing to configure per workspace.

## Setup

1. On any workstation with Claude Pro or Max: `claude setup-token`.
2. Complete the browser OAuth flow.
3. In the webui, open **Settings**. Under **Claude authentication**, paste the printed token and click **Save settings**.

The token is valid for ~1 year. Replace when it expires or is revoked.

## How it works

```
admin: claude setup-token → paste into webui Settings
                                      │
                                      ▼
                         koolna-env-defaults Secret
                         (key: CLAUDE_CODE_OAUTH_TOKEN)
                                      │
                         operator injects via envFrom
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
     workspace A              workspace B              workspace C
     sidecar env has          sidecar env has          sidecar env has
     CLAUDE_CODE_             CLAUDE_CODE_             CLAUDE_CODE_
     OAUTH_TOKEN              OAUTH_TOKEN              OAUTH_TOKEN
              │                       │                       │
         nsenter                 nsenter                 nsenter
              │                       │                       │
     user shell inherits     user shell inherits     user shell inherits
     the token               the token               the token
```

No broker, no sidecar wrapper, no per-workspace opt-in. The token is a cluster-wide default that every workspace receives automatically.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `claude` prints an OAuth URL inside a workspace | Check `echo $CLAUDE_CODE_OAUTH_TOKEN` in the shell. If empty, verify the Secret exists: `kubectl -n koolna get secret koolna-env-defaults -o jsonpath='{.data.CLAUDE_CODE_OAUTH_TOKEN}'`. If the key is missing, paste the token in webui Settings. If the key exists, restart the workspace pod (the env is set at pod creation time). |
| `claude` returns 401 | Token expired (~1 year) or revoked. Re-run `claude setup-token` and paste the new token in Settings. Restart workspace pods to pick up the change. |

## Security notes

- The token is stored as a K8s Secret (`koolna-env-defaults`). K8s Secrets are base64-encoded, not encrypted at rest unless you configure etcd encryption.
- The webui Settings page masks the token value (password input). The webui backend reads and writes it via the standard K8s Secret API.
- Every workspace pod receives the token. If a workspace pod is compromised, the attacker gets the token. Rotate by re-running `claude setup-token` and saving the new value in Settings.

## Alternative: Console API key

For pay-per-use billing instead of Pro/Max subscription, add `ANTHROPIC_API_KEY=sk-ant-api03-...` in webui Settings under **Default environment variables** (the regular env var editor, not the Claude token field). Do not set both `ANTHROPIC_API_KEY` and `CLAUDE_CODE_OAUTH_TOKEN` simultaneously.
