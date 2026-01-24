import logging
from datetime import datetime, timezone
from typing import Any, Protocol

from app.models import Symbol
from app.sources.protocol import RateSource
from app.sources.registry import SourceRegistry

logger = logging.getLogger(__name__)

DEFAULT_SYMBOLS_MAX_AGE_DAYS = 30


class SymbolsDatabase(Protocol):
    def populate_symbols(self, provider: str, symbols: list[Symbol]) -> None: ...
    def get_symbols_populated_at(self, provider: str) -> str | None: ...
    def set_symbols_populated_at(self, provider: str, timestamp: str) -> None: ...
    def count_symbols(self, provider: str) -> int: ...
    def commit(self) -> None: ...


class SymbolsService:
    def __init__(
        self,
        db: SymbolsDatabase,
        registry: SourceRegistry,
        max_age_days: int = DEFAULT_SYMBOLS_MAX_AGE_DAYS,
    ):
        self._db = db
        self._registry = registry
        self._max_age_days = max_age_days

    def needs_population(self, provider: str) -> bool:
        """Check if provider needs symbol population (no symbols or stale)."""
        if self._db.count_symbols(provider) == 0:
            return True
        last_populated = self._db.get_symbols_populated_at(provider)
        if not last_populated:
            return True
        try:
            last_dt = datetime.fromisoformat(last_populated)
            age_days = (datetime.now(timezone.utc) - last_dt).days
            return age_days >= self._max_age_days
        except ValueError:
            return True

    def populate(
        self,
        provider: str,
        on_progress: Any | None = None,
    ) -> dict[str, int]:
        """Populate symbols from a provider.

        Args:
            provider: Provider ID ('fcs', 'cnb', or 'all')
            on_progress: Optional callback for progress updates

        Returns:
            Dict mapping provider -> count of symbols
        """
        logger.debug("populate: provider=%s", provider)
        results: dict[str, int] = {}

        if provider == "all":
            logger.debug("populating from all providers")
            for source in self._registry.all():
                count = self._populate_source(source, on_progress)
                results[source.source_id] = count
        else:
            source = self._registry.get(provider)
            if source:
                count = self._populate_source(source, on_progress)
                results[provider] = count
            else:
                logger.debug("provider %s not found", provider)

        logger.debug("populate complete: %s", results)
        return results

    def _populate_source(
        self,
        source: RateSource,
        on_progress: Any | None,
    ) -> int:
        provider = source.source_id
        logger.debug("_populate_source: provider=%s", provider)

        if on_progress:
            on_progress(f"Fetching symbols from {provider}...")

        symbol_infos = source.list_symbols()
        logger.debug("fetched %d symbol infos from %s", len(symbol_infos), provider)

        # Convert SymbolInfo to Symbol with provider
        symbols = [
            Symbol(provider=provider, symbol=si.symbol, provider_symbol=si.provider_symbol, type=si.type, name=si.name)
            for si in symbol_infos
        ]

        if on_progress:
            on_progress(f"Saving {len(symbols)} symbols from {provider}...")

        self._db.populate_symbols(provider, symbols)
        self._db.set_symbols_populated_at(provider, datetime.now(timezone.utc).isoformat())
        self._db.commit()
        logger.debug("saved %d symbols for provider=%s", len(symbols), provider)

        # Update source's internal cache (needed for FCS backfill to know types)
        if hasattr(source, "set_symbol_cache"):
            from app.models import SymbolInfo
            symbol_infos_for_cache = [SymbolInfo(symbol=s.symbol, provider_symbol=s.provider_symbol, type=s.type, name=s.name) for s in symbols]
            source.set_symbol_cache(symbol_infos_for_cache)
            logger.debug("set %d symbols in %s source cache", len(symbol_infos_for_cache), provider)

        return len(symbols)
