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
curl "http://localhost:8000/rates?date=2025-01-15&symbol=EURCZK&provider=cnb"

# populate symbols then backfill
curl -X POST "http://localhost:8000/populate_symbols?provider=cnb"
curl -X POST "http://localhost:8000/backfill?provider=cnb&length=30"

# backup/restore
curl -X POST "http://localhost:8000/backup"  # creates backup_<timestamp>.json
curl "http://localhost:8000/backups"          # list available backups
curl -X POST "http://localhost:8000/restore?timestamp=20250122_163000"
```

## Env vars

- `PROVIDER_FCS_API_KEY` - FCSAPI key (optional)
- `DB_PATH` - SQLite path (default: `/data/exchanger.db`)
- `BACKUP_DIR` - backup directory (default: `backups/` next to DB file)
- `SYMBOLS` - format: `[provider:]symbol,...` (e.g. `EURCZK,fcs:BTCEUR,cnb:USDCZK`)
  - `provider:symbol` → backfill from specific provider
  - `symbol` (no prefix) → backfill from all providers that support it
- `AUTO_BACKFILL_TIME` - daily backfill time HH:MM (default: `16:30`)
- `LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR (default: `INFO`)
