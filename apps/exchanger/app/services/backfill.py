import logging
from datetime import datetime, time, timezone
from typing import Any, Callable, Protocol

from app.models import Symbol, SymbolType
from app.sources.protocol import RateSource
from app.sources.registry import SourceRegistry

logger = logging.getLogger(__name__)


class BackfillDatabase(Protocol):
    def get_rate(self, date: str, provider_symbol: str, provider: str) -> float | None: ...
    def get_symbol(self, provider_symbol: str, provider: str) -> Symbol | None: ...
    def list_symbols(self, provider: str | None = None, sym_type: SymbolType | None = None, query: str | None = None) -> list[Symbol]: ...
    def upsert_rate(self, date: str, provider_symbol: str, provider: str, rate: float) -> None: ...
    def get_backfill_done_at(self, provider: str) -> str | None: ...
    def set_backfill_done_at(self, provider: str, timestamp: str) -> None: ...
    def get_backfill_checkpoint(self, provider: str) -> dict | None: ...
    def set_backfill_checkpoint(self, provider: str, checkpoint: dict) -> None: ...
    def clear_backfill_checkpoint(self, provider: str) -> None: ...
    def commit(self) -> None: ...


class BackfillService:
    def __init__(self, db: BackfillDatabase, registry: SourceRegistry, auto_backfill_time: str = "16:30"):
        self._db = db
        self._registry = registry
        self._auto_backfill_time = auto_backfill_time

    def needs_backfill(self, provider: str) -> bool:
        """Check if provider needs backfill.

        Returns True if:
        - There's an interrupted checkpoint to resume
        - Backfill was never done
        - Backfill was done on a different day
        - Backfill was done before scheduled time and we're now past scheduled time
        """
        # Always resume interrupted backfills
        checkpoint = self._db.get_backfill_checkpoint(provider)
        if checkpoint:
            logger.debug("found interrupted checkpoint for %s: %s", provider, checkpoint)
            return True

        last_done = self._db.get_backfill_done_at(provider)
        if not last_done:
            return True

        try:
            last_dt = datetime.fromisoformat(last_done)
            # Convert UTC to local (mark_done stores UTC, scheduler uses local)
            if last_dt.tzinfo is not None:
                last_dt = last_dt.astimezone()
        except ValueError:
            return True

        now = datetime.now()

        # Not today? Needs backfill
        if last_dt.date() != now.date():
            return True

        # Parse scheduled time
        hour, minute = map(int, self._auto_backfill_time.split(":"))
        scheduled = time(hour, minute)

        last_time = last_dt.time()
        current_time = now.time()

        # Done after scheduled time → already ran today's scheduled task
        if last_time >= scheduled:
            return False

        # Done before scheduled time:
        # - Current time before scheduled → skip (haven't reached scheduled time)
        # - Current time at/after scheduled → need to run (catch up)
        return current_time >= scheduled

    def mark_done(self, provider: str) -> None:
        """Record backfill completion timestamp."""
        self._db.set_backfill_done_at(provider, datetime.now(timezone.utc).isoformat())
        self._db.commit()

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
        on_rates: Callable[[str, str, float], None] | None = None,
    ) -> dict[str, int]:
        provider = source.source_id

        # Build provider_symbol -> type map from DB (source of truth for metadata)
        if symbols:
            # Specific symbols requested - look them up in DB
            symbol_types: dict[str, SymbolType] = {}
            for provider_sym in symbols:
                db_symbol = self._db.get_symbol(provider_sym, provider)
                if db_symbol:
                    symbol_types[provider_sym] = db_symbol.type
                else:
                    logger.warning("provider_symbol %s not in DB for provider %s, skipping (run populate_symbols first)", provider_sym, provider)
            source_symbols = list(symbol_types.keys())
        else:
            # No specific symbols - use all from DB for this provider
            db_symbols = self._db.list_symbols(provider=provider)
            symbol_types = {s.provider_symbol: s.type for s in db_symbols}
            source_symbols = list(symbol_types.keys())
            logger.debug("_backfill_source: provider=%s, using %d symbols from DB", provider, len(source_symbols))

        if not source_symbols:
            logger.debug("no symbols to backfill for provider=%s (populate_symbols first?)", provider)
            return {}

        # Check for resumable checkpoint
        start_idx = 0
        checkpoint = self._db.get_backfill_checkpoint(provider)
        if checkpoint and checkpoint.get("length") == length:
            resume_idx = checkpoint.get("last_symbol_idx", -1) + 1
            if 0 < resume_idx < len(source_symbols):
                start_idx = resume_idx
                logger.info("resuming backfill from symbol %d/%d", start_idx + 1, len(source_symbols))
                if on_progress:
                    on_progress({"message": f"Resuming from symbol {start_idx + 1}/{len(source_symbols)}"})

        logger.debug("backfilling %d symbols from %s (starting at %d)", len(source_symbols), provider, start_idx)

        # Get total work units from source
        total_units = source.estimate_work_units(len(source_symbols) - start_idx, length)
        completed_units = 0

        def track_progress(data: str | dict[str, Any]) -> None:
            """Track work unit completions and forward other progress info."""
            nonlocal completed_units
            if not on_progress:
                return

            if isinstance(data, dict):
                if data.get("work_unit_done"):
                    completed_units += 1
                    pct = int((completed_units / total_units) * 100) if total_units > 0 else 0
                    msg = data.get("message", "Working...")
                    on_progress({
                        "message": msg,
                        "progress": pct,
                        "progress_detail": f"{completed_units}/{total_units} units",
                    })
                else:
                    # Forward rate limit, etc.
                    on_progress(data)
            elif isinstance(data, str):
                on_progress({"message": data})

        # Fetch and store one symbol at a time
        results: dict[str, int] = {}
        for i, provider_sym in enumerate(source_symbols[start_idx:], start_idx + 1):
            if on_progress:
                pct = int((completed_units / total_units) * 100) if total_units > 0 else 0
                on_progress({
                    "message": f"Fetching {provider_sym}...",
                    "progress": pct,
                    "progress_detail": f"{i}/{len(source_symbols)} symbols",
                })

            try:
                # Pass symbol types so source knows which endpoint to use
                count = 0

                def handle_rate(sym: str, date_str: str, rate: float) -> None:
                    nonlocal count
                    self._db.upsert_rate(date_str, sym, provider, rate)
                    self._db.commit()
                    count += 1
                    if on_rates:
                        on_rates(sym, date_str, rate)

                history = source.fetch_history(
                    [provider_sym],
                    length,
                    track_progress,
                    on_rates=handle_rate,
                    symbol_types=symbol_types,
                )
            except Exception as e:
                logger.warning("failed to fetch %s from %s: %s", provider_sym, provider, e)
                # Save checkpoint before continuing
                self._db.set_backfill_checkpoint(provider, {"last_symbol_idx": i - 1, "length": length})
                self._db.commit()
                continue

            if not history or provider_sym not in history or not history[provider_sym]:
                logger.debug("no history returned for %s from %s", provider_sym, provider)
                # Still save checkpoint
                self._db.set_backfill_checkpoint(provider, {"last_symbol_idx": i - 1, "length": length})
                self._db.commit()
                continue

            logger.debug("received history for %s", provider_sym)

            # Save checkpoint after each symbol
            self._db.set_backfill_checkpoint(provider, {"last_symbol_idx": i - 1, "length": length})
            self._db.commit()
            results[f"{provider}:{provider_sym}"] = count
            logger.debug("stored %d rates for %s:%s", count, provider, provider_sym)

        # Clear checkpoint on successful completion
        self._db.clear_backfill_checkpoint(provider)
        self._db.commit()

        return results
