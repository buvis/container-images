import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings, configure_logging, load_settings
from app.database import SQLiteDatabase
from app.routes import create_router
from app.scheduler import BackgroundScheduler
from app.services.backfill import BackfillService
from app.services.symbols import SymbolsService
from app.sources.registry import SourceRegistry
from app.sources.fcs import FcsSource
from app.sources.cnb import CnbSource
from app.task_manager import TaskManager
from app.utils.retry import set_shutdown
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ShutdownRequested(Exception):
    """Raised when shutdown is requested during a background task."""
    pass


class Application:
    def __init__(self, settings: Settings):
        logger.debug("initializing app with db_path=%s", settings.db_path)
        self.settings = settings
        self.db = SQLiteDatabase(settings.db_path)
        self.task_manager = TaskManager()
        self.scheduler = BackgroundScheduler(settings.scheduler_tick_seconds)

        # Create source registry and register providers
        self.registry = SourceRegistry()
        self._register_sources(settings)

        # Create services
        self.backfill_service = BackfillService(
            db=self.db,
            registry=self.registry,
        )
        self.symbols_service = SymbolsService(
            db=self.db,
            registry=self.registry,
        )
        logger.debug("app initialized, providers=%s", self.registry.ids())

    def _register_sources(self, settings: Settings) -> None:
        """Register available rate sources based on configuration."""
        # FCS source (requires API key)
        if "fcs" in settings.provider_api_keys:
            logger.debug("registering fcs source")
            fcs_source = FcsSource(
                settings.provider_api_keys["fcs"],
                settings.rate_limit_wait,
            )
            self.registry.register(fcs_source)

        # CNB source (no auth needed)
        logger.debug("registering cnb source")
        cnb_source = CnbSource()
        self.registry.register(cnb_source)

    def start_backfill_if_idle(self, provider: str, symbols: list[str], length: int) -> bool:
        task_key = f"backfill:{provider}"

        def on_progress(msg: str) -> None:
            if self.task_manager.shutdown_requested:
                raise ShutdownRequested()
            self.task_manager.update_status(task_key, message=msg)

        def run() -> None:
            logger.info(f"Backfill started: provider={provider}, symbols={symbols}, days={length}")
            self.task_manager.update_status(task_key, per_symbol={})
            try:
                results = self.backfill_service.backfill(
                    provider,
                    symbols,
                    length,
                    on_progress=on_progress,
                )
                total = sum(results.values())
                self.task_manager.set_status(task_key, {
                    "status": "done",
                    "message": f"Completed: {total} rows",
                    "per_symbol": results,
                    "rows_written": total,
                })
                logger.info(f"Backfill completed: {total} rows")
            except ShutdownRequested:
                logger.info(f"Backfill {provider} interrupted by shutdown")
                self.task_manager.set_status(task_key, {"status": "cancelled", "message": "Shutdown requested"})
            except Exception as e:
                logger.error(f"Backfill {provider} failed: {e}")
                self.task_manager.set_status(task_key, {"status": "error", "message": str(e)})

        return self.task_manager.start_if_idle(task_key, run)

    def _build_backfill_map(self) -> dict[str, list[str]]:
        """Build map of provider → symbols for backfill.

        Combines explicit provider:symbol entries with global symbols
        (expanded to all providers that support them).
        """
        result: dict[str, list[str]] = {}

        # Add explicit provider:symbol entries
        for provider, symbols in self.settings.symbols.items():
            result.setdefault(provider, []).extend(symbols)

        # Expand global symbols to all providers that have them
        for symbol in self.settings.global_symbols:
            providers = self.db.get_providers_for_symbol(symbol)
            for provider in providers:
                if symbol not in result.get(provider, []):
                    result.setdefault(provider, []).append(symbol)

        return result

    def startup(self) -> None:
        logger.debug(
            "startup: symbols=%s, global_symbols=%s, backfill_time=%s",
            self.settings.symbols,
            self.settings.global_symbols,
            self.settings.auto_backfill_time,
        )

        # Populate symbols first (required before backfill) - only if stale/missing
        # Include all providers that have explicit symbols OR could serve global symbols
        providers_to_check = set(self.settings.symbols.keys())
        if self.settings.global_symbols:
            providers_to_check.update(self.registry.ids())

        providers_needing_population = [
            p for p in providers_to_check
            if self.registry.get(p) and self.symbols_service.needs_population(p)
        ]

        if providers_needing_population:
            def populate_provider(provider: str) -> None:
                logger.debug("populating symbols for %s", provider)
                self.symbols_service.populate(provider)

            with ThreadPoolExecutor(max_workers=len(providers_needing_population)) as executor:
                executor.map(populate_provider, providers_needing_population)
        else:
            logger.debug("symbols up to date, skipping population")

        # Build combined backfill map: provider → symbols
        backfill_map = self._build_backfill_map()

        # Auto-backfill configured symbols per provider
        for provider, symbols in backfill_map.items():
            if self.registry.get(provider):
                self.start_backfill_if_idle(provider, symbols, self.settings.auto_backfill_days)
            else:
                logger.warning("provider %s not registered, skipping symbols: %s", provider, symbols)

        def scheduled_backfill() -> None:
            logger.debug("scheduled backfill triggered")
            for provider, symbols in self._build_backfill_map().items():
                if self.registry.get(provider):
                    self.start_backfill_if_idle(provider, symbols, self.settings.auto_backfill_days)

        self.scheduler.schedule_daily(self.settings.auto_backfill_time, scheduled_backfill)
        self.scheduler.start()
        logger.info("app started, scheduler running")

    def shutdown(self) -> None:
        logger.debug("shutting down")
        set_shutdown()  # Interrupt any rate-limit waits
        self.scheduler.stop()
        self.task_manager.shutdown()
        self.db.close()
        logger.info("app shutdown complete")


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = load_settings()

    configure_logging(settings.log_level)
    logger.debug("log_level=%s", settings.log_level)

    application = Application(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        application.startup()
        yield
        application.shutdown()

    fastapi_app = FastAPI(
        title="Exchanger",
        description="Multi-provider caching proxy for exchange rates",
        version="1.0.0",
        lifespan=lifespan,
    )

    router = create_router(
        settings=application.settings,
        db=application.db,
        task_manager=application.task_manager,
        backfill_service=application.backfill_service,
        symbols_service=application.symbols_service,
        registry=application.registry,
    )
    fastapi_app.include_router(router, prefix="/api")
    static_directory = Path(__file__).resolve().parent / "static"
    fastapi_app.mount("/", StaticFiles(directory=static_directory, html=True), name="static")

    @fastapi_app.exception_handler(StarletteHTTPException)
    async def spa_fallback(request: Request, exc: StarletteHTTPException) -> FileResponse:
        if exc.status_code == 404 and not request.url.path.startswith("/api"):
            return FileResponse(static_directory / "index.html")
        raise exc

    return fastapi_app


def get_app() -> FastAPI:
    """Factory function for uvicorn."""
    return create_app()


if __name__ == "__main__":
    uvicorn.run("app.main:get_app", factory=True, host="0.0.0.0", port=8000)
