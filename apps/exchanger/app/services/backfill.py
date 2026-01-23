import logging
from typing import Any, Protocol

from app.models import Symbol, SymbolType
from app.sources.protocol import RateSource
from app.sources.registry import SourceRegistry

logger = logging.getLogger(__name__)


class BackfillDatabase(Protocol):
    def get_symbol(self, symbol: str, provider: str) -> Symbol | None: ...
    def list_symbols(self, provider: str | None = None, sym_type: SymbolType | None = None, query: str | None = None) -> list[Symbol]: ...
    def upsert_rate(self, date: str, symbol: str, provider: str, rate: float) -> None: ...
    def commit(self) -> None: ...


class BackfillService:
    def __init__(self, db: BackfillDatabase, registry: SourceRegistry):
        self._db = db
        self._registry = registry

    def backfill(
        self,
        provider: str,
        symbols: list[str],
        length: int,
        on_progress: Any | None = None,
    ) -> dict[str, int]:
        """Backfill rates for symbols from a provider.

        Symbols MUST already exist in DB (via populate_symbols). This ensures
        correct type/name metadata and prevents guessing.

        Args:
            provider: Provider ID ('fcs', 'cnb', or 'all')
            symbols: List of symbol names to backfill. If empty, backfills all
                    symbols in DB for this provider.
            length: Number of days of history
            on_progress: Optional callback for progress updates

        Returns:
            Dict mapping symbol -> count of rates written
        """
        logger.debug("backfill: provider=%s symbols=%s length=%d", provider, symbols, length)
        results: dict[str, int] = {}

        if provider == "all":
            logger.debug("backfilling from all providers")
            for source in self._registry.all():
                source_results = self._backfill_source(source, symbols, length, on_progress)
                results.update(source_results)
        else:
            source = self._registry.get(provider)
            if source:
                results = self._backfill_source(source, symbols, length, on_progress)
            else:
                logger.debug("provider %s not found", provider)

        logger.debug("backfill complete: %s", results)
        return results

    def _backfill_source(
        self,
        source: RateSource,
        symbols: list[str],
        length: int,
        on_progress: Any | None,
    ) -> dict[str, int]:
        provider = source.source_id

        # Build symbol -> type map from DB (source of truth for metadata)
        if symbols:
            # Specific symbols requested - look them up in DB
            symbol_types: dict[str, SymbolType] = {}
            for sym in symbols:
                db_symbol = self._db.get_symbol(sym, provider)
                if db_symbol:
                    symbol_types[sym] = db_symbol.type
                else:
                    logger.warning("symbol %s not in DB for provider %s, skipping (run populate_symbols first)", sym, provider)
            source_symbols = list(symbol_types.keys())
        else:
            # No specific symbols - use all from DB for this provider
            db_symbols = self._db.list_symbols(provider=provider)
            symbol_types = {s.symbol: s.type for s in db_symbols}
            source_symbols = list(symbol_types.keys())
            logger.debug("_backfill_source: provider=%s, using %d symbols from DB", provider, len(source_symbols))

        if not source_symbols:
            logger.debug("no symbols to backfill for provider=%s (populate_symbols first?)", provider)
            return {}

        logger.debug("backfilling %d symbols from %s", len(source_symbols), provider)

        # Fetch and store one symbol at a time
        results: dict[str, int] = {}
        for i, symbol in enumerate(source_symbols, 1):
            if on_progress:
                on_progress(f"Fetching {symbol} ({i}/{len(source_symbols)})...")

            try:
                # Pass symbol types so source knows which endpoint to use
                history = source.fetch_history([symbol], length, on_progress, symbol_types=symbol_types)
            except Exception as e:
                logger.warning("failed to fetch %s from %s: %s", symbol, provider, e)
                continue

            if not history or symbol not in history or not history[symbol]:
                logger.debug("no history returned for %s from %s", symbol, provider)
                continue

            logger.debug("received history for %s", symbol)

            rates = history[symbol]
            count = 0
            for date_str, rate in rates.items():
                self._db.upsert_rate(date_str, symbol, provider, rate)
                count += 1
            self._db.commit()
            results[f"{provider}:{symbol}"] = count
            logger.debug("stored %d rates for %s:%s", count, provider, symbol)

        return results