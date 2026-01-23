import json
import logging
from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

from app.config import Settings
from app.database import SQLiteDatabase
from app.models import (
    SymbolType,
    HealthResponse,
    RateResponse,
    RatesResponse,
    ScheduledResponse,
    SymbolResponse,
    ForexCryptoSymbolResponse,
    TaskStateResponse,
    BackupResponse,
    BackupInfo,
    RestoreResponse,
)
from app.services.backfill import BackfillService
from app.services.symbols import SymbolsService
from app.sources.registry import SourceRegistry
from app.task_manager import TaskManager


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

    @router.get("/providers")
    def list_providers() -> list[str]:
        logger.debug("list_providers called")
        return registry.ids()

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
        if not registry.get(provider):
            raise HTTPException(400, f"Unknown provider: {provider}")

        rate = db.get_rate(date_str, symbol, provider)

        # On-demand fetch if rate not found
        if rate is None:
            logger.debug("rate not cached, fetching on-demand")
            rate = _fetch_rate_on_demand(dt, symbol, provider)

        logger.debug("returning rate=%s", rate)
        return RateResponse(rate=rate)

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
            if not registry.get(provider):
                raise HTTPException(400, f"Unknown provider: {provider}")
            providers = [provider]

        started = []
        already_running = []

        for p in providers:
            task_key = f"backfill:{p}"

            def make_run(prov: str, key: str):
                def run() -> None:
                    logger.info(f"Manual backfill started: provider={prov}, symbols={selected or 'all'}, days={length}")
                    task_manager.update_status(key, per_symbol={})
                    try:
                        results = backfill_service.backfill(
                            prov,
                            selected,
                            length,
                            on_progress=lambda msg: task_manager.update_status(key, message=msg),
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
                        task_manager.set_status(key, {"status": "error", "message": str(e)})
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

    @router.post("/populate_symbols", response_model=ScheduledResponse)
    def populate_symbols_endpoint(
        provider: str = Query(..., description="Provider: fcs, cnb, or all"),
    ) -> ScheduledResponse:
        # Determine which providers to populate
        if provider == "all":
            providers = registry.ids()
        else:
            if not registry.get(provider):
                raise HTTPException(400, f"Unknown provider: {provider}")
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
                            on_progress=lambda msg: task_manager.update_status(key, message=msg),
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
                        task_manager.set_status(key, {"status": "error", "message": str(e)})
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

    @router.get("/symbols/list", response_model=list[SymbolResponse])
    def symbols_list(
        provider: str | None = Query(None, description="Filter by provider: fcs, cnb"),
        type: SymbolType | None = Query(None, description="Filter by type: forex, crypto"),
        q: str | None = Query(None, description="Substring filter (case-insensitive)"),
    ) -> list[SymbolResponse]:
        logger.debug("symbols_list: provider=%s type=%s q=%s", provider, type, q)
        symbols = db.list_symbols(provider=provider, sym_type=type, query=q)
        logger.debug("returning %d symbols", len(symbols))
        return [SymbolResponse(provider=s.provider, symbol=s.symbol, name=s.name, type=s.type) for s in symbols]

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
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_data = {"rates": rates, "symbols": symbols, "metadata": metadata}
        backup_dir = _get_backup_dir()
        filename = _backup_filename(timestamp)
        backup_path = backup_dir / filename

        with open(backup_path, "w") as f:
            json.dump(backup_data, f, indent=2)

        logger.info("backup created: %s (%d rates, %d symbols, %d metadata)", filename, len(rates), len(symbols), len(metadata))
        return BackupResponse(
            filename=filename,
            timestamp=timestamp,
            rates_count=len(rates),
            symbols_count=len(symbols),
            metadata_count=len(metadata),
        )

    @router.post("/restore", response_model=RestoreResponse, response_model_exclude_none=True)
    def restore(
        timestamp: str = Query(..., description="Backup timestamp (e.g. 20250122_163000)"),
    ) -> RestoreResponse:
        """Restore database from backup file."""
        logger.debug("restore requested: timestamp=%s", timestamp)
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

        # Import symbols first (creates IDs)
        if data.get("symbols"):
            symbols_count = db.import_symbols(data["symbols"])
            logger.debug("restored %d symbols", symbols_count)

        # Then import rates (needs symbol IDs)
        if data.get("rates"):
            rates_count = db.import_rates(data["rates"])
            logger.debug("restored %d rates", rates_count)

        # Import metadata last
        if data.get("metadata"):
            metadata_count = db.import_metadata(data["metadata"])
            logger.debug("restored %d metadata entries", metadata_count)

        db.commit()
        logger.info("restored from %s: %d symbols, %d rates, %d metadata", timestamp, symbols_count or 0, rates_count or 0, metadata_count or 0)
        return RestoreResponse(timestamp=timestamp, rates=rates_count, symbols=symbols_count, metadata=metadata_count)

    def _check_no_task_running() -> None:
        # Check for any provider-specific running tasks
        provider_ids = registry.ids()
        task_keys = []
        for p in provider_ids:
            task_keys.append(f"populate_symbols:{p}")
            task_keys.append(f"backfill:{p}")
        running = task_manager.any_running(task_keys)
        if running:
            raise HTTPException(status_code=409, detail=f"{running} task is running")

    return router
