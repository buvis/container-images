import json
import logging
import re
from datetime import date, datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException, Query, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

from app.config import Settings
from app.database import SQLiteDatabase
from app.models import (
    SymbolType,
    HealthResponse,
    RateResponse,
    RatesResponse,
    RateListItem,
    RateHistoryItem,
    ScheduledResponse,
    SymbolResponse,
    ForexCryptoSymbolResponse,
    TaskStateResponse,
    BackupResponse,
    BackupInfo,
    RestoreResponse,
    ProviderStatusResponse,
    FrontendConfigResponse,
    FavoriteResponse,
    ChainRateResponse,
)
from app.services.backfill import BackfillService
from app.services.symbols import SymbolsService
from app.sources.registry import SourceRegistry
from app.task_manager import TaskManager


def _sanitize_error(e: Exception) -> str:
    """Return a safe error message without internal details."""
    error_type = type(e).__name__
    # Only expose error type, not the full message which may contain paths or internal info
    return f"Task failed ({error_type})"


# Strict pattern: YYYYMMDD_HHMMSS
_TIMESTAMP_PATTERN = re.compile(r"^\d{8}_\d{6}$")

# Providers requiring API keys
_PROVIDERS_REQUIRING_API_KEY = {"fcs": "PROVIDER_FCS_API_KEY"}


def _validate_timestamp(timestamp: str) -> None:
    """Validate timestamp format to prevent path traversal."""
    if not _TIMESTAMP_PATTERN.match(timestamp):
        raise HTTPException(status_code=400, detail="Invalid timestamp format (expected YYYYMMDD_HHMMSS)")


def _require_provider(registry: "SourceRegistry", provider: str) -> None:
    """Raise HTTPException if provider not available, with helpful message."""
    if registry.get(provider):
        return
    if provider in _PROVIDERS_REQUIRING_API_KEY:
        env_var = _PROVIDERS_REQUIRING_API_KEY[provider]
        raise HTTPException(400, f"Provider '{provider}' requires {env_var} to be set")
    raise HTTPException(400, f"Unknown provider: {provider}")


def create_router(
    settings: Settings,
    db: SQLiteDatabase,
    task_manager: TaskManager,
    backfill_service: BackfillService,
    symbols_service: SymbolsService,
    registry: SourceRegistry,
) -> APIRouter:
    router = APIRouter()

    @router.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @router.get("/config", response_model=FrontendConfigResponse)
    def get_config() -> FrontendConfigResponse:
        return FrontendConfigResponse(dashboard_history_days=settings.dashboard_history_days)

    @router.get("/providers")
    def list_providers() -> list[str]:
        logger.debug("list_providers called")
        return registry.ids()

    @router.get("/providers/status", response_model=list[ProviderStatusResponse])
    def providers_status() -> list[ProviderStatusResponse]:
        logger.debug("providers_status requested")
        statuses: list[ProviderStatusResponse] = []
        for provider_id in registry.ids():
            symbol_count = db.count_symbols(provider_id)
            counts_by_type = db.count_symbols_by_type(provider_id)
            statuses.append(
                ProviderStatusResponse(
                    name=provider_id,
                    healthy=symbol_count > 0,
                    symbol_count=symbol_count,
                    symbol_counts_by_type=counts_by_type,
                )
            )
        return statuses

    @router.get("/rates", response_model=RateResponse | RatesResponse)
    def get_rate(
        date_str: str = Query(..., alias="date", description="YYYY-MM-DD"),
        symbol: str = Query(..., description="e.g. EURCZK"),
        provider: str = Query(..., description="Provider: fcs, cnb, or all"),
    ) -> RateResponse | RatesResponse:
        logger.debug("get_rate: date=%s symbol=%s provider=%s", date_str, symbol, provider)

        # Validate date format
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(400, f"Invalid date format: {date_str}, expected YYYY-MM-DD")

        # Handle "all" provider - return rates from all providers
        if provider == "all":
            rates: dict[str, float | None] = {}
            for p in registry.ids():
                rate = db.get_rate(date_str, symbol, p)
                if rate is None:
                    rate = _fetch_rate_on_demand(dt, symbol, p)
                rates[p] = rate
            logger.debug("returning rates=%s", rates)
            return RatesResponse(rates=rates)

        # Validate provider
        _require_provider(registry, provider)

        rate = db.get_rate(date_str, symbol, provider)

        # On-demand fetch if rate not found
        if rate is None:
            logger.debug("rate not cached, fetching on-demand")
            rate = _fetch_rate_on_demand(dt, symbol, provider)

        logger.debug("returning rate=%s", rate)
        return RateResponse(rate=rate)

    @router.get("/rates/list", response_model=list[RateListItem])
    def rates_list(
        date_str: str = Query(..., alias="date", description="YYYY-MM-DD"),
        provider: str = Query(..., description="Provider: fcs, cnb, or all"),
    ) -> list[RateListItem]:
        logger.debug("rates_list: date=%s provider=%s", date_str, provider)

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(400, f"Invalid date format: {date_str}, expected YYYY-MM-DD")

        provider_filter: str | None = None
        if provider != "all":
            _require_provider(registry, provider)
            provider_filter = provider

        rates = db.get_rates_for_date(date_str, provider_filter)
        logger.debug("returning %d rates", len(rates))
        return rates

    @router.get("/rates/history", response_model=list[RateHistoryItem])
    def rates_history(
        symbol: str = Query(..., description="Normalized symbol, e.g. EURCZK"),
        from_date: date | None = Query(None, description="Start date (YYYY-MM-DD)"),
        to_date: date | None = Query(None, description="End date (YYYY-MM-DD)"),
        provider: str | None = Query(None, description="Provider: fcs, cnb, or all"),
        provider_symbol: str | None = Query(None, description="Provider-specific symbol (e.g. EURCZK.ONE). If provided, queries exact match."),
    ) -> list[RateHistoryItem]:
        logger.debug(
            "rates_history: symbol=%s provider_symbol=%s from=%s to=%s provider=%s",
            symbol,
            provider_symbol,
            from_date,
            to_date,
            provider,
        )

        end_date = to_date or date.today()
        start_date = from_date or (end_date - timedelta(days=30))
        if start_date > end_date:
            raise HTTPException(400, "from_date must be on or before to_date")

        provider_filter: str | None = None
        if provider and provider != "all":
            _require_provider(registry, provider)
            provider_filter = provider

        history = db.get_rates_range(symbol, start_date, end_date, provider_filter, provider_symbol)
        logger.debug("returning %d rate entries", len(history))
        return history

    @router.get("/rates/coverage", response_model=dict[str, int])
    def rates_coverage(
        year: int = Query(..., description="Year to analyze"),
        provider: str | None = Query(None, description="Optional provider filter: fcs, cnb, or all"),
        symbols: str | None = Query(None, description="Optional comma-separated symbol list"),
    ) -> dict[str, int]:
        logger.debug("rates_coverage: year=%d provider=%s symbols=%s", year, provider, symbols)

        provider_filter: str | None = None
        if provider:
            if provider == "all":
                provider_filter = None
            else:
                _require_provider(registry, provider)
                provider_filter = provider

        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()] if symbols else None
        coverage = db.get_coverage(year, provider_filter, symbol_list)
        logger.debug("rates_coverage returning %d entries", len(coverage))
        return coverage

    @router.get("/rates/missing", response_model=dict[str, list[str]])
    def rates_missing(
        year: int = Query(..., description="Year to analyze"),
        symbols: str = Query(..., description="Comma-separated symbol list"),
        provider: str | None = Query(None, description="Optional provider filter"),
    ) -> dict[str, list[str]]:
        """Return missing symbols for each date in a year."""
        logger.debug("rates_missing: year=%d symbols=%s provider=%s", year, symbols, provider)

        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
        if not symbol_list:
            return {}

        provider_filter: str | None = None
        if provider and provider != "all":
            _require_provider(registry, provider)
            provider_filter = provider

        missing = db.get_missing_symbols(year, symbol_list, provider_filter)
        logger.debug("rates_missing returning %d entries", len(missing))
        return missing

    def _fetch_rate_on_demand(dt: date, symbol: str, provider: str) -> float | None:
        source = registry.get(provider)
        if not source:
            return None

        logger.debug("fetching rate from source %s", provider)
        try:
            rate = source.fetch_rate(symbol, dt)
        except Exception as e:
            logger.warning("source fetch failed: %s", e)
            return None
        if rate is None:
            logger.debug("source returned no rate")
            return None

        logger.debug("caching rate=%s", rate)
        date_str = dt.strftime("%Y-%m-%d")
        db.upsert_rate(date_str, symbol, provider, rate)
        db.commit()
        return rate

    @router.get("/rates/chain", response_model=ChainRateResponse)
    def get_chain_rate(
        date_str: str = Query(..., alias="date", description="YYYY-MM-DD"),
        from_currency: str = Query(..., description="Source currency (e.g., BTC)"),
        intermediate: str = Query(..., description="Intermediate currency (e.g., EUR)"),
        to_currency: str = Query(..., description="Target currency (e.g., CZK)"),
        from_provider: str = Query(..., description="Provider for first leg"),
        to_provider: str = Query(..., description="Provider for second leg"),
    ) -> ChainRateResponse:
        """Get chained rate through an intermediate currency.

        Automatically handles symbol inversion - if EURBTC not found, uses 1/BTCEUR.
        """
        logger.debug(
            "get_chain_rate: date=%s %s->%s->%s providers=%s/%s",
            date_str, from_currency, intermediate, to_currency, from_provider, to_provider
        )

        # Validate date
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(400, f"Invalid date format: {date_str}, expected YYYY-MM-DD")

        # Validate providers
        _require_provider(registry, from_provider)
        _require_provider(registry, to_provider)

        def fetch_rate_with_inversion(
            base: str, quote: str, provider: str, dt: date, date_str: str
        ) -> tuple[float | None, str, bool]:
            """Try direct symbol, then inverted. Returns (rate, symbol_used, inverted)."""
            direct = f"{base}{quote}"
            inverted = f"{quote}{base}"

            # Try direct symbol first
            rate = db.get_rate(date_str, direct, provider)
            if rate is None:
                rate = _fetch_rate_on_demand(dt, direct, provider)
            if rate is not None:
                return rate, direct, False

            # Try inverted symbol
            rate = db.get_rate(date_str, inverted, provider)
            if rate is None:
                rate = _fetch_rate_on_demand(dt, inverted, provider)
            if rate is not None:
                return 1.0 / rate, inverted, True

            return None, direct, False

        # Fetch first leg: from_currency -> intermediate
        from_rate, from_symbol, from_inverted = fetch_rate_with_inversion(
            from_currency, intermediate, from_provider, dt, date_str
        )

        # Fetch second leg: intermediate -> to_currency
        to_rate, to_symbol, to_inverted = fetch_rate_with_inversion(
            intermediate, to_currency, to_provider, dt, date_str
        )

        # Calculate combined rate
        combined_rate = None
        if from_rate is not None and to_rate is not None:
            combined_rate = from_rate * to_rate

        logger.debug(
            "chain rate: %s(%s)=%s * %s(%s)=%s -> %s",
            from_symbol, "inv" if from_inverted else "dir", from_rate,
            to_symbol, "inv" if to_inverted else "dir", to_rate,
            combined_rate
        )

        return ChainRateResponse(
            from_rate=from_rate,
            from_provider=from_provider,
            from_symbol=from_symbol,
            from_inverted=from_inverted,
            to_rate=to_rate,
            to_provider=to_provider,
            to_symbol=to_symbol,
            to_inverted=to_inverted,
            combined_rate=combined_rate,
            intermediate=intermediate,
        )

    @router.post("/backfill", response_model=ScheduledResponse)
    def manual_backfill(
        provider: str = Query(..., description="Provider: fcs, cnb, or all"),
        length: int = Query(30, ge=1, le=365, description="Number of days to fetch"),
        symbols: str | None = Query(None, description="Comma-separated list; defaults to all symbols for provider"),
    ) -> ScheduledResponse:
        # Parse symbols if provided
        selected = (
            [s.strip() for s in symbols.split(",") if s.strip()]
            if symbols
            else []
        )

        # Determine which providers to backfill
        if provider == "all":
            providers = registry.ids()
        else:
            _require_provider(registry, provider)
            providers = [provider]

        started = []
        already_running = []

        for p in providers:
            task_key = f"backfill:{p}"

            def make_run(prov: str, key: str, days: int, syms: list[str]):
                def run() -> None:
                    logger.info(f"Manual backfill started: provider={prov}, symbols={syms or 'all'}, days={days}")
                    task_manager.update_status(key, per_symbol={})
                    try:
                        results = backfill_service.backfill(
                            prov,
                            syms,
                            days,
                            on_progress=lambda u: task_manager.update_status(key, **(u if isinstance(u, dict) else {"message": u})),
                        )
                        total = sum(results.values())
                        task_manager.set_status(key, {
                            "status": "done",
                            "message": f"Completed: {total} rows",
                            "per_symbol": results,
                            "rows_written": total,
                        })
                        logger.info(f"Manual backfill completed for {prov}: {total} rows")
                    except Exception as e:
                        logger.error(f"Manual backfill failed for {prov}: {e}")
                        task_manager.set_status(key, {"status": "error", "message": _sanitize_error(e)})
                return run

            if task_manager.start_if_idle(task_key, make_run(p, task_key, length, selected)):
                started.append(p)
            else:
                already_running.append(p)

        if not started:
            return ScheduledResponse(
                scheduled=False,
                message="All requested providers already running",
                already_running=already_running,
            )
        return ScheduledResponse(
            scheduled=True,
            started=started,
            already_running=already_running,
            message="Started in background, check /task_status for progress",
        )

    @router.post("/populate_symbols", response_model=ScheduledResponse)
    def populate_symbols_endpoint(
        provider: str = Query(..., description="Provider: fcs, cnb, or all"),
    ) -> ScheduledResponse:
        # Determine which providers to populate
        if provider == "all":
            providers = registry.ids()
        else:
            _require_provider(registry, provider)
            providers = [provider]

        started = []
        already_running = []

        for p in providers:
            task_key = f"populate_symbols:{p}"

            def make_run(prov: str, key: str):
                def run() -> None:
                    logger.info(f"Populate symbols started: provider={prov}")
                    try:
                        results = symbols_service.populate(
                            prov,
                            on_progress=lambda u: task_manager.update_status(key, **(u if isinstance(u, dict) else {"message": u})),
                        )
                        total = sum(results.values())
                        task_manager.set_status(key, {
                            "status": "done",
                            "message": f"Completed: {total} symbols",
                            "symbols_added": total,
                        })
                        logger.info(f"Populate symbols completed for {prov}: {results}")
                    except Exception as e:
                        logger.error(f"Populate symbols failed for {prov}: {e}")
                        task_manager.set_status(key, {"status": "error", "message": _sanitize_error(e)})
                return run

            if task_manager.start_if_idle(task_key, make_run(p, task_key)):
                started.append(p)
            else:
                already_running.append(p)

        if not started:
            return ScheduledResponse(
                scheduled=False,
                message="All requested providers already running",
                already_running=already_running,
            )
        return ScheduledResponse(
            scheduled=True,
            started=started,
            already_running=already_running,
            message="Started in background, check /task_status for progress",
        )

    @router.get("/task_status", response_model=dict[str, TaskStateResponse])
    def task_status() -> dict[str, TaskStateResponse]:
        return task_manager.get_all_status()

    @router.websocket("/ws/tasks")
    async def tasks_ws(websocket: WebSocket) -> None:
        await task_manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            task_manager.disconnect(websocket)

    @router.get("/symbols/list", response_model=list[SymbolResponse])
    def symbols_list(
        provider: str | None = Query(None, description="Filter by provider: fcs, cnb"),
        type: SymbolType | None = Query(None, description="Filter by type: forex, crypto"),
        q: str | None = Query(None, description="Substring filter (case-insensitive)"),
    ) -> list[SymbolResponse]:
        logger.debug("symbols_list: provider=%s type=%s q=%s", provider, type, q)
        symbols = db.list_symbols(provider=provider, sym_type=type, query=q)
        logger.debug("returning %d symbols", len(symbols))
        return [SymbolResponse(provider=s.provider, symbol=s.symbol, provider_symbol=s.provider_symbol, name=s.name, type=s.type) for s in symbols]

    @router.get("/symbols/multi-provider", response_model=list[dict])
    def symbols_multi_provider() -> list[dict]:
        """Get normalized symbols available from multiple providers."""
        logger.debug("symbols_multi_provider requested")
        result = db.list_multi_provider_symbols()
        logger.debug("returning %d multi-provider symbols", len(result))
        return result

    @router.get("/symbols/by-normalized/{normalized_symbol}", response_model=list[SymbolResponse])
    def symbols_by_normalized(normalized_symbol: str) -> list[SymbolResponse]:
        """Get all symbol variants for a normalized symbol."""
        logger.debug("symbols_by_normalized: %s", normalized_symbol)
        symbols = db.get_symbol_variants(normalized_symbol)
        logger.debug("returning %d symbols", len(symbols))
        return [SymbolResponse(provider=s.provider, symbol=s.symbol, provider_symbol=s.provider_symbol, name=s.name, type=s.type) for s in symbols]

    @router.get("/forex/list", response_model=list[ForexCryptoSymbolResponse])
    def forex_list(
        q: str | None = Query(None, description="Substring filter (case-insensitive)"),
    ) -> list[ForexCryptoSymbolResponse]:
        logger.debug("forex_list: q=%s", q)
        symbols = db.list_symbols(sym_type="forex", query=q)
        logger.debug("returning %d forex symbols", len(symbols))
        return [ForexCryptoSymbolResponse(provider=s.provider, symbol=s.symbol, name=s.name) for s in symbols]

    @router.get("/crypto/list", response_model=list[ForexCryptoSymbolResponse])
    def crypto_list(
        q: str | None = Query(None, description="Substring filter (case-insensitive)"),
    ) -> list[ForexCryptoSymbolResponse]:
        logger.debug("crypto_list: q=%s", q)
        symbols = db.list_symbols(sym_type="crypto", query=q)
        logger.debug("returning %d crypto symbols", len(symbols))
        return [ForexCryptoSymbolResponse(provider=s.provider, symbol=s.symbol, name=s.name) for s in symbols]

    @router.get("/favorites", response_model=list[FavoriteResponse])
    def favorites_list() -> list[FavoriteResponse]:
        logger.debug("favorites_list requested")
        return [FavoriteResponse(**f) for f in db.list_favorites()]

    @router.post("/favorites", response_model=FavoriteResponse)
    def add_favorite(
        provider: str = Body(..., description="Provider ID"),
        provider_symbol: str = Body(..., description="Provider-specific symbol"),
    ) -> FavoriteResponse:
        logger.debug("add_favorite requested: provider=%s provider_symbol=%s", provider, provider_symbol)
        if not db.add_favorite(provider, provider_symbol):
            raise HTTPException(status_code=404, detail=f"Symbol not found: {provider}/{provider_symbol}")
        db.commit()
        return FavoriteResponse(provider=provider, provider_symbol=provider_symbol)

    @router.delete("/favorites/{provider}/{provider_symbol}")
    def delete_favorite(provider: str, provider_symbol: str) -> FavoriteResponse:
        logger.debug("remove_favorite requested: provider=%s provider_symbol=%s", provider, provider_symbol)
        if not db.remove_favorite(provider, provider_symbol):
            raise HTTPException(status_code=404, detail=f"Symbol not found: {provider}/{provider_symbol}")
        db.commit()
        return FavoriteResponse(provider=provider, provider_symbol=provider_symbol)

    def _get_backup_dir() -> Path:
        backup_dir = Path(settings.backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    def _backup_filename(timestamp: str) -> str:
        return f"backup_{timestamp}.json"

    def _parse_backup_filename(filename: str) -> str | None:
        """Extract timestamp from backup filename, or None if invalid."""
        if filename.startswith("backup_") and filename.endswith(".json"):
            return filename[7:-5]  # Remove "backup_" prefix and ".json" suffix
        return None

    @router.get("/backups", response_model=list[BackupInfo])
    def list_backups() -> list[BackupInfo]:
        """List available backup files."""
        logger.debug("list_backups requested")
        backup_dir = _get_backup_dir()
        backups = []
        for f in sorted(backup_dir.glob("backup_*.json"), reverse=True):
            ts = _parse_backup_filename(f.name)
            if ts:
                backups.append(BackupInfo(filename=f.name, timestamp=ts))
        return backups

    @router.post("/backup", response_model=BackupResponse)
    def backup() -> BackupResponse:
        """Create backup file with current database contents."""
        logger.debug("backup requested")
        _check_no_task_running()

        rates = db.export_rates()
        symbols = db.export_symbols()
        metadata = db.export_metadata()
        favorites = db.export_favorites()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_data = {"rates": rates, "symbols": symbols, "metadata": metadata, "favorites": favorites}
        backup_dir = _get_backup_dir()
        filename = _backup_filename(timestamp)
        backup_path = backup_dir / filename

        with open(backup_path, "w") as f:
            json.dump(backup_data, f, indent=2)

        logger.info("backup created: %s (%d rates, %d symbols, %d metadata, %d favorites)", filename, len(rates), len(symbols), len(metadata), len(favorites))
        return BackupResponse(
            filename=filename,
            timestamp=timestamp,
            rates_count=len(rates),
            symbols_count=len(symbols),
            metadata_count=len(metadata),
            favorites_count=len(favorites),
        )

    @router.post("/restore", response_model=RestoreResponse, response_model_exclude_none=True)
    def restore(
        timestamp: str = Query(..., description="Backup timestamp (e.g. 20250122_163000)"),
    ) -> RestoreResponse:
        """Restore database from backup file."""
        logger.debug("restore requested: timestamp=%s", timestamp)
        _validate_timestamp(timestamp)
        _check_no_task_running()

        backup_dir = _get_backup_dir()
        backup_path = backup_dir / _backup_filename(timestamp)

        if not backup_path.exists():
            raise HTTPException(status_code=404, detail=f"Backup not found: {timestamp}")

        with open(backup_path) as f:
            data = json.load(f)

        symbols_count = None
        rates_count = None
        metadata_count = None
        favorites_count = None

        # Import symbols first (creates IDs)
        if data.get("symbols"):
            symbols_count = db.import_symbols(data["symbols"])
            logger.debug("restored %d symbols", symbols_count)

        # Then import rates (needs symbol IDs)
        if data.get("rates"):
            rates_count = db.import_rates(data["rates"])
            logger.debug("restored %d rates", rates_count)

        # Import metadata
        if data.get("metadata"):
            metadata_count = db.import_metadata(data["metadata"])
            logger.debug("restored %d metadata entries", metadata_count)

        # Import favorites
        if data.get("favorites"):
            favorites_count = db.import_favorites(data["favorites"])
            logger.debug("restored %d favorites", favorites_count)

        db.commit()
        logger.info("restored from %s: %d symbols, %d rates, %d metadata, %d favorites", timestamp, symbols_count or 0, rates_count or 0, metadata_count or 0, favorites_count or 0)
        return RestoreResponse(timestamp=timestamp, rates=rates_count, symbols=symbols_count, metadata=metadata_count, favorites=favorites_count)

    def _check_no_task_running() -> None:
        # Check for any provider-specific running tasks
        provider_ids = registry.ids()
        task_keys = []
        for p in provider_ids:
            task_keys.append(f"populate_symbols:{p}")
            task_keys.append(f"backfill:{p}")
        running = task_manager.any_running(task_keys)
        if running:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot backup/restore while {running} is running. Wait for it to complete.",
            )

    return router
