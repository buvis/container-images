# Multi-provider webhook support for mkdocs-git-sync

Issue: #218 (extending GitHub-only implementation to GitLab + Bitbucket)

## Decisions

- Per-provider env vars: `GITHUB_WEBHOOK_SECRET`, `GITLAB_WEBHOOK_SECRET`, `BITBUCKET_WEBHOOK_SECRET`
- Implicit mode: any secret set = webhook+polling, none = polling only
- Provider handler pattern: base class + per-provider implementations
- Bitbucket auth via secret-in-URL path (Bitbucket Cloud lacks header signing)
- Shared webhook port (default 9000), all providers on same server
- Only configured providers get routes registered

## Provider details

### GitHub (existing, extracted)

- Auth: HMAC-SHA256 via `X-Hub-Signature-256` header
- Ping: `X-GitHub-Event: ping` → 200, no trigger
- Branch ref: `payload["ref"]` → `"refs/heads/<branch>"`
- Endpoint: `POST /hooks/github`

### GitLab (new)

- Auth: `X-Gitlab-Token` header, constant-time string compare
- Ping: none (test button sends valid push event)
- Branch ref: `payload["ref"]` → `"refs/heads/<branch>"`
- Endpoint: `POST /hooks/gitlab`

### Bitbucket (new)

- Auth: secret embedded in URL path, constant-time compare
- Ping: `X-Event-Key: diagnostics:ping` → 200, no trigger
- Branch ref: `payload["push"]["changes"][0]["new"]["name"]` → bare branch name
- Endpoint: `POST /hooks/bitbucket/<token>`

## Architecture

### File structure

```
webhook/
├── __init__.py
├── server.py              # HTTPServer + path router
├── providers/
│   ├── __init__.py
│   ├── base.py            # Base provider class
│   ├── github.py          # GitHub handler
│   ├── gitlab.py          # GitLab handler
│   └── bitbucket.py       # Bitbucket handler
```

### Base provider interface

Each provider implements:
- `validate(headers, body) -> bool` — auth check
- `extract_ref(payload) -> str | None` — branch ref from provider-specific JSON
- `is_ping(headers) -> bool` — detect test/ping events

### Server routing

`_WebhookHandler.do_POST()` maps request path to provider:
- `/hooks/github` → GitHub provider
- `/hooks/gitlab` → GitLab provider
- `/hooks/bitbucket/<token>` → Bitbucket provider (token extracted from path)

Unconfigured provider paths return 404.

### WebhookServer init

```python
WebhookServer(
    trigger_event=event,
    branch="main",
    port=9000,
    providers={"github": "hmac-secret", "gitlab": "token", "bitbucket": "url-secret"}
)
```

Only providers present in dict get routes.

## Configuration

| Env var | Default | Description |
|---|---|---|
| `GITHUB_WEBHOOK_SECRET` | `None` | HMAC-SHA256 secret for GitHub |
| `GITLAB_WEBHOOK_SECRET` | `None` | Token for GitLab X-Gitlab-Token header |
| `BITBUCKET_WEBHOOK_SECRET` | `None` | Token matched against URL path segment |
| `WEBHOOK_PORT` | `9000` | Shared port for all providers |

Mode logic: `webhook_enabled = any([github_secret, gitlab_secret, bitbucket_secret])`

Backward compatible: existing deployments with only `GITHUB_WEBHOOK_SECRET` work identically.

## Testing

### Per-provider tests

Each provider: valid push, bad auth, wrong branch, ping event.

### Routing tests (test_webhook_server.py)

Correct path → correct provider, unknown path → 404, unconfigured provider → 404, multi-provider server.

### Config tests

Per-provider secrets, provider dict construction, webhook_enabled with any/all/none set.

### Integration tests (test_run.py)

Updated mocks for new WebhookServer signature (providers dict).
