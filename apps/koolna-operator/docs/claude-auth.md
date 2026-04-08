# Claude Authentication in Koolna Workspaces

## What it does

Claude Code credentials are stored in the `koolna-credentials` shared Secret. The session-manager sidecar restores them into each workspace pod on startup via `restore_credentials()`. Interactive `claude` picks up the credentials from `~/.claude/.credentials.json` and runs on your subscription (no API billing).

## Setup

1. Log in to Claude Code on your Mac (run `claude` and complete the OAuth flow once).
2. Run `seed-claude-credentials.bash` from the clusters repo. This extracts your Keychain credentials and writes them to the `koolna-credentials` Secret.
3. New workspaces pick up credentials automatically. Existing workspaces sync within 30 seconds.

## How it works

```
mac: claude login -> Keychain stores OAuth tokens
                          |
         seed-claude-credentials.bash
                          |
                          v
              koolna-credentials Secret
              (key: claude---credentials.json)
                          |
            sidecar restore_credentials()
                          |
           +──────────────+──────────────+
           |              |              |
      workspace A    workspace B    workspace C
      ~/.claude/     ~/.claude/     ~/.claude/
      .credentials   .credentials   .credentials
      .json          .json          .json
           |              |              |
      interactive    interactive    interactive
      claude works   claude works   claude works
```

The sidecar also writes `~/.claude.json` with `hasCompletedOnboarding: true` so the interactive banner is skipped. When a user logs in inside a workspace, the sidecar syncs the credentials back to the shared Secret for other workspaces.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `claude` shows login menu | Check `ls ~/.claude/.credentials.json`. If missing, verify the Secret exists: `kubectl -n koolna get secret koolna-credentials -o jsonpath='{.data}'`. If empty, re-run `seed-claude-credentials.bash`. If the Secret has data, check sidecar logs for restore errors. |
| `claude` returns 401 | Credentials expired. Re-run `seed-claude-credentials.bash` from your Mac after logging in again. Restart workspace pods to pick up new credentials. |
| API billing instead of subscription | You may have `CLAUDE_CODE_OAUTH_TOKEN` set as an env var. Remove it from `koolna-env-defaults` Secret and restart the pod. Subscription auth uses file-based credentials, not env vars. |

## Security notes

- Credentials are stored as a K8s Secret (`koolna-credentials`). K8s Secrets are base64-encoded, not encrypted at rest unless you configure etcd encryption.
- Every workspace pod receives the credentials via sidecar restore. If a workspace pod is compromised, the attacker gets the OAuth tokens.
- To rotate: log in again on your Mac and re-run `seed-claude-credentials.bash`.
