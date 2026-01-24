from datetime import date
from typing import Callable

import pytest

from app.database import SQLiteDatabase
from app.models import SymbolInfo
from app.services.symbols import SymbolsService
from app.sources.registry import SourceRegistry


class MockSource:
    def __init__(self, source_id: str, symbols: list[SymbolInfo]):
        self._source_id = source_id
        self._symbols = symbols

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
    ) -> dict[str, dict[str, float]]:
        return {}

    def fetch_rate(self, symbol: str, dt: date) -> float | None:
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


class TestSymbolsService:
    def test_populate_single_provider(self, temp_db: SQLiteDatabase) -> None:
        source = MockSource("fcs", [
            SymbolInfo(symbol="EURUSD", provider_symbol="EURUSD", type="forex", name="Euro / US Dollar"),
            SymbolInfo(symbol="GBPUSD", provider_symbol="GBPUSD", type="forex", name="British Pound"),
        ])
        registry = SourceRegistry()
        registry.register(source)

        service = SymbolsService(db=temp_db, registry=registry)
        results = service.populate("fcs")

        assert results["fcs"] == 2

        symbols = temp_db.list_symbols(provider="fcs")
        assert len(symbols) == 2
        symbol_names = [s.symbol for s in symbols]
        assert "EURUSD" in symbol_names
        assert "GBPUSD" in symbol_names

    def test_populate_all_providers(self, temp_db: SQLiteDatabase) -> None:
        fcs_source = MockSource("fcs", [SymbolInfo(symbol="EURUSD", provider_symbol="EURUSD", type="forex", name="Euro")])
        cnb_source = MockSource("cnb", [SymbolInfo(symbol="EURCZK", provider_symbol="EURCZK", type="forex", name="Euro CZK")])

        registry = SourceRegistry()
        registry.register(fcs_source)
        registry.register(cnb_source)

        service = SymbolsService(db=temp_db, registry=registry)
        results = service.populate("all")

        assert results["fcs"] == 1
        assert results["cnb"] == 1

        fcs_symbols = temp_db.list_symbols(provider="fcs")
        cnb_symbols = temp_db.list_symbols(provider="cnb")
        assert len(fcs_symbols) == 1
        assert len(cnb_symbols) == 1

    def test_populate_with_progress_callback(self, temp_db: SQLiteDatabase) -> None:
        source = MockSource("fcs", [SymbolInfo(symbol="EURUSD", provider_symbol="EURUSD", type="forex", name="Euro")])
        registry = SourceRegistry()
        registry.register(source)

        service = SymbolsService(db=temp_db, registry=registry)
        messages: list[str] = []
        service.populate("fcs", on_progress=messages.append)

        assert len(messages) >= 2  # Fetching + Saving
        assert any("fcs" in m for m in messages)

    def test_populate_unknown_provider(self, temp_db: SQLiteDatabase) -> None:
        registry = SourceRegistry()
        service = SymbolsService(db=temp_db, registry=registry)

        results = service.populate("unknown")
        assert results == {}

    def test_populate_replaces_existing_symbols(self, temp_db: SQLiteDatabase) -> None:
        source1 = MockSource("fcs", [SymbolInfo(symbol="EURUSD", provider_symbol="EURUSD", type="forex", name="Old Euro")])
        registry = SourceRegistry()
        registry.register(source1)

        service = SymbolsService(db=temp_db, registry=registry)
        service.populate("fcs")

        # Update the source with different symbols
        registry._sources["fcs"] = MockSource("fcs", [SymbolInfo(symbol="GBPUSD", provider_symbol="GBPUSD", type="forex", name="Pound")])
        service.populate("fcs")

        symbols = temp_db.list_symbols(provider="fcs")
        assert len(symbols) == 1
        assert symbols[0].symbol == "GBPUSD"

    def test_populate_stores_correct_type(self, temp_db: SQLiteDatabase) -> None:
        source = MockSource("fcs", [
            SymbolInfo(symbol="EURUSD", provider_symbol="EURUSD", type="forex", name="Euro"),
            SymbolInfo(symbol="BTCUSD", provider_symbol="BTCUSD", type="crypto", name="Bitcoin"),
        ])
        registry = SourceRegistry()
        registry.register(source)

        service = SymbolsService(db=temp_db, registry=registry)
        service.populate("fcs")

        forex = temp_db.list_symbols(provider="fcs", sym_type="forex")
        crypto = temp_db.list_symbols(provider="fcs", sym_type="crypto")

        assert len(forex) == 1
        assert forex[0].symbol == "EURUSD"
        assert len(crypto) == 1
        assert crypto[0].symbol == "BTCUSD"

    def test_populate_empty_source(self, temp_db: SQLiteDatabase) -> None:
        source = MockSource("fcs", [])
        registry = SourceRegistry()
        registry.register(source)

        service = SymbolsService(db=temp_db, registry=registry)
        results = service.populate("fcs")

        assert results["fcs"] == 0
        assert temp_db.list_symbols(provider="fcs") == []
