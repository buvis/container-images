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
| `AUTO_BACKFILL_TIME` | no | `16:30` | Daily backfill time (HH:MM) |
| `AUTO_BACKFILL_DAYS` | no | `31` | Days to fetch per backfill |
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
| GET | `/rates?date=YYYY-MM-DD&symbol=EURCZK&provider=cnb` | Get cached rate |
| POST | `/backfill?provider=cnb&length=30&symbols=EURCZK` | Start backfill |
| POST | `/populate_symbols?provider=cnb` | Fetch symbols from provider |
| GET | `/symbols/list?provider=cnb&type=forex&q=CZK` | List symbols |
| GET | `/task_status` | Check background task status |
| GET | `/backup` | Export all tables as JSON |
| POST | `/restore` | Import JSON, replaces existing data |

## Local testing

```bash
cp .env.example .env
uv sync
mise run dev
```

Test endpoints:

```bash
# rate lookup (CNB, no API key needed)
curl "http://localhost:8000/rates?date=2025-01-15&symbol=EURCZK&provider=cnb"

# list symbols
curl "http://localhost:8000/symbols/list?provider=cnb&q=CZK"

# manual backfill
curl -X POST "http://localhost:8000/backfill?provider=cnb&length=30&symbols=EURCZK"
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
