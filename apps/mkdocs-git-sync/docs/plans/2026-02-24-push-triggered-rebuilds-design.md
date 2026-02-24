# Push-triggered rebuilds for mkdocs-git-sync

Issue: #218 (GitHub-only scope for first iteration)

## Decisions

- GitHub webhooks only (GitLab/Bitbucket later)
- Default mode: webhook + polling fallback when secret is set; polling-only when not
- Stdlib `http.server` in a daemon thread — no framework dependency
- Webhook thread sets a `threading.Event`, main thread does all sync/build work
- Coalesce: at most current build + one more (event is a flag, not a queue)
- Endpoint: `POST /hooks/github`
- Separate port (default 9000), not proxied through nginx

## Configuration

| Env var | Default | Description |
|---|---|---|
| `GITHUB_WEBHOOK_SECRET` | `None` | HMAC-SHA256 secret; enables webhook server when set |
| `WEBHOOK_PORT` | `9000` | Port for webhook HTTP server |

Mode logic:
- Secret set → webhook + polling
- Secret not set → polling only (backward-compatible)

## Webhook server

New module: `container-files/syncer/webhook/server.py`

- `WebhookServer` wraps `http.server.HTTPServer` in a daemon thread
- Single route: `POST /hooks/github`
- Validation chain:
  1. POST method (405 otherwise)
  2. Path is `/hooks/github` (404 otherwise)
  3. `X-Hub-Signature-256` header present (401)
  4. HMAC-SHA256 matches (403)
  5. `ref` matches monitored branch (200, no action)
- Valid push → sets `threading.Event`, returns 200
- Logs trigger source, branch, action/reason

## Main loop changes

Replace `time.sleep(UPDATE_INTERVAL)` with `trigger_event.wait(timeout=UPDATE_INTERVAL)`.

```
trigger_event = threading.Event()

if webhook configured:
    start WebhookServer(trigger_event, config) as daemon thread

while True:
    triggered = trigger_event.wait(timeout=UPDATE_INTERVAL)
    trigger_event.clear()
    source = "webhook" if triggered else "poll"
    syncer.update(source=source)
```

Coalesce: webhooks arriving during a build keep the event set. Next iteration picks it up, does one more sync.

## Syncer changes

`update()` accepts optional `source` param for logging. No logic changes.

## Testing

### New: `test_webhook_server.py`
- Valid push → event set, 200
- Missing signature → 401
- Invalid signature → 403
- Wrong branch → 200, event not set
- Wrong method → 405
- Wrong path → 404
- Ping event → 200, event not set

### Extended: `test_run.py`
- Webhook configured → server thread starts
- Webhook not configured → no server thread
- Event triggers immediate sync (source="webhook")
- Timeout triggers sync (source="poll")

### Manual verification
1. Run container with `GITHUB_WEBHOOK_SECRET=test123 WEBHOOK_PORT=9000`
2. curl with valid HMAC signature → check logs for "webhook" trigger
3. curl with bad signature → verify 403
4. Real GitHub webhook via ngrok → push and observe rebuild
