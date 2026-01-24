# exchanger

Multi-provider caching proxy for exchange rates. Stores daily rates in SQLite, auto-backfills on schedule.

## Providers

- **CNB** (Czech National Bank) - forex rates, no auth required
- **FCS** (FCSAPI) - forex/crypto rates, requires API key

## Config (env vars)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PROVIDER_FCS_API_KEY` | no | - | FCSAPI key (only if using FCS provider) |
| `DB_PATH` | no | `/data/exchanger.db` | SQLite path |
| `SYMBOLS` | no | - | Format: `provider:symbol,...` (e.g. `fcs:EURCZK,cnb:USDCZK`) |
| `AUTO_BACKFILL_TIME` | no | `16:30` | Daily task time (HH:MM) |
| `AUTO_BACKFILL_DAYS` | no | `31` | Days to fetch per backfill |
| `SYMBOLS_MAX_AGE_DAYS` | no | `30` | Refresh symbols after N days |
| `LOG_LEVEL` | no | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |

## API

Interactive API docs available at:

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>
- **OpenAPI JSON**: <http://localhost:8000/openapi.json>

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/providers` | List registered providers |
| GET | `/providers/status` | Provider health and symbol counts |
| GET | `/rates?date=&symbol=&provider=` | Get single rate |
| GET | `/rates/list?date=&provider=` | List all rates for date |
| GET | `/rates/history?symbol=&from_date=&to_date=&provider=` | Rate history for charting |
| GET | `/rates/coverage?year=&provider=&symbols=` | Coverage counts per date |
| POST | `/backfill?provider=&length=&symbols=` | Start backfill task |
| POST | `/populate_symbols?provider=` | Fetch symbols from provider |
| GET | `/symbols/list?provider=&type=&q=` | List symbols with filter |
| GET | `/task_status` | Background task status |
| GET | `/favorites` | User's favorite symbols |
| POST | `/favorites` | Add favorite (body: `{symbol}`) |
| DELETE | `/favorites/{symbol}` | Remove favorite |
| GET | `/backups` | List available backups |
| POST | `/backup` | Create backup |
| POST | `/restore?timestamp=` | Restore from backup |

## Backup/restore

Backup exports all user data as denormalized JSON using natural keys (not internal IDs).

**What's backed up:**
- `symbols` → `{provider, symbol, provider_symbol, type, name}`
- `rates` → `{date, provider, symbol, provider_symbol, rate}`
- `metadata` → `{key, value}` (excludes schema_version)
- `favorites` → `{symbol, created_at}`

**Excluded:** `schema_version` (auto-managed by migrations)

**ID handling:** Internal IDs and sqlite_sequence are not backed up. On restore, symbols get fresh IDs and rates are re-linked by `(provider, symbol)` lookup. Safe because backup uses natural keys as identifiers.

## Local testing

```bash
cp .env.example .env
uv sync
mise run dev
```

Test endpoints:

```bash
# rate lookup (CNB, no API key needed)
curl "http://localhost:8000/api/rates?date=2025-01-15&symbol=EURCZK&provider=cnb"

# list symbols
curl "http://localhost:8000/api/symbols/list?provider=cnb&q=CZK"

# manual backfill
curl -X POST "http://localhost:8000/api/backfill?provider=cnb&length=30&symbols=EURCZK"
```

## Testing

### Backend (pytest)

```bash
uv run pytest -q
```

Tests use in-memory SQLite and mock HTTP for external providers.

### Frontend E2E (Playwright)

```bash
cd frontend
npm run test:e2e
```

Builds the frontend, starts preview server on port 4173, runs Playwright tests with mocked API responses.

### Full stack

Run both in sequence:

```bash
uv run pytest -q && (cd frontend && npm run test:e2e)
```

## Docker

```bash
docker build -t exchanger .
docker run -d \
  -v exchanger-data:/data \
  -p 8000:8000 \
  exchanger
```

Add `-e PROVIDER_FCS_API_KEY=your_key` if using FCS provider.
