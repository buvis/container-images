# Exchanger

Multi-provider caching proxy for exchange rates. SQLite storage, daily auto-backfill.

## Architecture

```
app/
├── main.py          # FastAPI app factory, Application class, lifespan
├── config.py        # Settings dataclass, env var parsing
├── database.py      # SQLiteDatabase with thread-safe ops
├── models.py        # Symbol, Rate, TaskState dataclasses
├── routes.py        # All API endpoints
├── scheduler.py     # BackgroundScheduler for daily tasks
├── task_manager.py  # Background task tracking
├── sources/
│   ├── protocol.py  # RateSource protocol
│   ├── registry.py  # SourceRegistry for provider lookup
│   ├── fcs.py       # FCSAPI (forex/crypto, needs API key)
│   └── cnb.py       # Czech National Bank (forex, no auth)
├── services/
│   ├── backfill.py  # BackfillService - fetch historical rates
│   └── symbols.py   # SymbolsService - populate symbol metadata
└── utils/
    └── retry.py     # Rate limit handling for FCS API
```

## Key patterns

- **Provider registry**: Sources register via `SourceRegistry`, looked up by ID
- **DB as source of truth**: Symbols must exist in DB before backfill (run `/populate_symbols` first)
- **Background tasks**: `TaskManager` tracks running tasks, prevents duplicates
- **Protocol-based DI**: Services depend on Protocol types, not concrete implementations

## Testing

```bash
uv run pytest -q
```

Tests use in-memory SQLite, mock HTTP for CNB.

## Common tasks

```bash
# dev server
mise run dev

# rate lookup
curl "http://localhost:8000/api/rates?date=2025-01-15&symbol=EURCZK&provider=cnb"

# populate symbols then backfill
curl -X POST "http://localhost:8000/api/populate_symbols?provider=cnb"
curl -X POST "http://localhost:8000/api/backfill?provider=cnb&length=30"

# backup/restore
curl -X POST "http://localhost:8000/api/backup"  # creates backup_<timestamp>.json
curl "http://localhost:8000/api/backups"          # list available backups
curl -X POST "http://localhost:8000/api/restore?timestamp=20250122_163000"
```

## Env vars

- `PROVIDER_FCS_API_KEY` - FCSAPI key (optional)
- `DB_PATH` - SQLite path (default: `/data/exchanger.db`)
- `BACKUP_DIR` - backup directory (default: `backups/` next to DB file)
- `SYMBOLS` - format: `provider:symbol,...` (e.g. `fcs:BTCEUR,cnb:USDCZK`)
- `AUTO_BACKFILL_TIME` - daily task time HH:MM (default: `16:30`)
- `SYMBOLS_MAX_AGE_DAYS` - refresh symbols after N days (default: `30`)
- `PROVIDER_CNB_FETCH_DELAY` - seconds between CNB API calls (default: `2.0`, polite rate limiting)
- `DASHBOARD_HISTORY_DAYS` - default range for dashboard sparklines (default: `7`)
- `LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR (default: `INFO`)
