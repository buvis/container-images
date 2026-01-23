from datetime import date
from typing import Callable

import pytest

from app.database import SQLiteDatabase
from app.models import Symbol, SymbolInfo, SymbolType
from app.services.backfill import BackfillService
from app.sources.registry import SourceRegistry


class MockSource:
    def __init__(self, source_id: str, symbols: list[SymbolInfo], history: dict[str, dict[str, float]] | None = None):
        self._source_id = source_id
        self._symbols = symbols
        self._history = history or {}

    @property
    def source_id(self) -> str:
        return self._source_id

    def available_symbols(
        self, on_progress: Callable[[str], None] | None = None
    ) -> list[str]:
        return [s.symbol for s in self._symbols]

    def fetch_history(
        self,
        symbols: list[str],
        days: int,
        on_progress: Callable[[str], None] | None = None,
        symbol_types: dict[str, SymbolType] | None = None,
    ) -> dict[str, dict[str, float]]:
        result = {}
        for sym in symbols:
            if sym in self._history:
                result[sym] = self._history[sym]
        return result

    def fetch_rate(self, symbol: str, dt: date) -> float | None:
        date_str = dt.strftime("%Y-%m-%d")
        if symbol in self._history and date_str in self._history[symbol]:
            return self._history[symbol][date_str]
        return None

    def list_symbols(
        self, on_progress: Callable[[str], None] | None = None
    ) -> list[SymbolInfo]:
        return self._symbols

    def get_symbol_info(self, symbol: str) -> SymbolInfo | None:
        for s in self._symbols:
            if s.symbol == symbol:
                return s
        return None


def _setup_symbols(db: SQLiteDatabase, provider: str, symbols: list[tuple[str, str]]) -> None:
    db.populate_symbols(provider, [
        Symbol(provider=provider, symbol=sym, type=sym_type, name=sym)
        for sym_type, sym in symbols
    ])
    db.commit()


class TestBackfillService:
    def test_backfill_single_provider(self, temp_db: SQLiteDatabase) -> None:
        _setup_symbols(temp_db, "fcs", [("forex", "EURUSD")])

        history = {"EURUSD": {"2024-01-15": 1.0850, "2024-01-14": 1.0840}}
        source = MockSource("fcs", [SymbolInfo("EURUSD", "forex", "Euro")], history)
        registry = SourceRegistry()
        registry.register(source)

        service = BackfillService(db=temp_db, registry=registry)
        results = service.backfill("fcs", ["EURUSD"], length=5)

        assert results["fcs:EURUSD"] == 2
        assert temp_db.get_rate("2024-01-15", "EURUSD", "fcs") == 1.0850

    def test_backfill_all_providers(self, temp_db: SQLiteDatabase) -> None:
        _setup_symbols(temp_db, "fcs", [("forex", "EURUSD")])
        _setup_symbols(temp_db, "cnb", [("forex", "EURCZK")])

        fcs_source = MockSource(
            "fcs",
            [SymbolInfo("EURUSD", "forex", "Euro")],
            {"EURUSD": {"2024-01-15": 1.0850}},
        )
        cnb_source = MockSource(
            "cnb",
            [SymbolInfo("EURCZK", "forex", "Euro CZK")],
            {"EURCZK": {"2024-01-15": 25.5}},
        )

        registry = SourceRegistry()
        registry.register(fcs_source)
        registry.register(cnb_source)

        service = BackfillService(db=temp_db, registry=registry)
        results = service.backfill("all", [], length=5)

        assert "fcs:EURUSD" in results
        assert "cnb:EURCZK" in results

    def test_backfill_uses_all_source_symbols_when_none_specified(self, temp_db: SQLiteDatabase) -> None:
        _setup_symbols(temp_db, "fcs", [("forex", "EURUSD"), ("crypto", "BTCUSD")])

        history = {
            "EURUSD": {"2024-01-15": 1.0850},
            "BTCUSD": {"2024-01-15": 42000.0},
        }
        source = MockSource(
            "fcs",
            [SymbolInfo("EURUSD", "forex", "Euro"), SymbolInfo("BTCUSD", "crypto", "BTC")],
            history,
        )
        registry = SourceRegistry()
        registry.register(source)

        service = BackfillService(db=temp_db, registry=registry)
        results = service.backfill("fcs", [], length=5)

        assert "fcs:EURUSD" in results
        assert "fcs:BTCUSD" in results

    def test_backfill_filters_to_available_symbols(self, temp_db: SQLiteDatabase) -> None:
        _setup_symbols(temp_db, "fcs", [("forex", "EURUSD")])

        history = {"EURUSD": {"2024-01-15": 1.0850}}
        source = MockSource("fcs", [SymbolInfo("EURUSD", "forex", "Euro")], history)
        registry = SourceRegistry()
        registry.register(source)

        service = BackfillService(db=temp_db, registry=registry)
        # Request symbols that include one not available
        results = service.backfill("fcs", ["EURUSD", "GBPUSD"], length=5)

        assert "fcs:EURUSD" in results
        assert "fcs:GBPUSD" not in results

    def test_backfill_with_progress_callback(self, temp_db: SQLiteDatabase) -> None:
        _setup_symbols(temp_db, "fcs", [("forex", "EURUSD")])

        source = MockSource("fcs", [SymbolInfo("EURUSD", "forex", "Euro")], {"EURUSD": {"2024-01-15": 1.0850}})
        registry = SourceRegistry()
        registry.register(source)

        service = BackfillService(db=temp_db, registry=registry)
        messages: list[str] = []
        service.backfill("fcs", ["EURUSD"], length=5, on_progress=messages.append)

        assert len(messages) > 0
        assert any("EURUSD" in m for m in messages)

    def test_backfill_unknown_provider(self, temp_db: SQLiteDatabase) -> None:
        registry = SourceRegistry()
        service = BackfillService(db=temp_db, registry=registry)

        results = service.backfill("unknown", ["EURUSD"], length=5)
        assert results == {}

    def test_backfill_stores_rates_in_db(self, temp_db: SQLiteDatabase) -> None:
        _setup_symbols(temp_db, "fcs", [("forex", "EURUSD")])

        history = {"EURUSD": {"2024-01-15": 1.0850}}
        source = MockSource("fcs", [SymbolInfo("EURUSD", "forex", "Euro")], history)
        registry = SourceRegistry()
        registry.register(source)

        service = BackfillService(db=temp_db, registry=registry)
        service.backfill("fcs", ["EURUSD"], length=5)

        rate = temp_db.get_rate("2024-01-15", "EURUSD", "fcs")
        assert rate == 1.0850
