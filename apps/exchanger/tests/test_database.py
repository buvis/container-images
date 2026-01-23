import pytest

from app.database import SQLiteDatabase
from app.models import Symbol


class TestSQLiteDatabase:
    def test_get_rate_not_found(self, temp_db: SQLiteDatabase) -> None:
        assert temp_db.get_rate("2024-01-01", "EURUSD", "fcs") is None

    def test_upsert_and_get_rate(self, temp_db: SQLiteDatabase) -> None:
        # First create a symbol
        temp_db.populate_symbols("fcs", [Symbol(provider="fcs", symbol="EURUSD", type="forex", name="Euro")])
        temp_db.commit()

        temp_db.upsert_rate("2024-01-15", "EURUSD", "fcs", 1.0850)
        temp_db.commit()

        result = temp_db.get_rate("2024-01-15", "EURUSD", "fcs")
        assert result == 1.0850

    def test_upsert_rate_replaces(self, temp_db: SQLiteDatabase) -> None:
        temp_db.populate_symbols("fcs", [Symbol(provider="fcs", symbol="EURUSD", type="forex", name="Euro")])
        temp_db.commit()

        temp_db.upsert_rate("2024-01-15", "EURUSD", "fcs", 1.0850)
        temp_db.upsert_rate("2024-01-15", "EURUSD", "fcs", 1.0900)
        temp_db.commit()

        assert temp_db.get_rate("2024-01-15", "EURUSD", "fcs") == 1.0900

    def test_get_symbol_type_not_found(self, temp_db: SQLiteDatabase) -> None:
        assert temp_db.get_symbol_type("EURUSD", "fcs") is None

    def test_list_symbols_empty(self, temp_db: SQLiteDatabase) -> None:
        assert temp_db.list_symbols(sym_type="forex") == []

    def test_populate_symbols_workflow(self, temp_db: SQLiteDatabase) -> None:
        symbols = [
            Symbol(provider="fcs", symbol="EURUSD", type="forex", name="Euro / US Dollar"),
            Symbol(provider="fcs", symbol="BTCUSD", type="crypto", name="Bitcoin / US Dollar"),
        ]
        temp_db.populate_symbols("fcs", symbols)
        temp_db.commit()

        forex = temp_db.list_symbols(sym_type="forex")
        crypto = temp_db.list_symbols(sym_type="crypto")

        assert len(forex) == 1
        assert forex[0].symbol == "EURUSD"
        assert len(crypto) == 1
        assert crypto[0].symbol == "BTCUSD"

        assert temp_db.get_symbol_type("EURUSD", "fcs") == "forex"
        assert temp_db.get_symbol_type("BTCUSD", "fcs") == "crypto"

    def test_list_symbols_by_provider(self, temp_db: SQLiteDatabase) -> None:
        fcs_symbols = [Symbol(provider="fcs", symbol="EURUSD", type="forex", name="Euro")]
        cnb_symbols = [Symbol(provider="cnb", symbol="EURCZK", type="forex", name="Euro CZK")]
        temp_db.populate_symbols("fcs", fcs_symbols)
        temp_db.populate_symbols("cnb", cnb_symbols)
        temp_db.commit()

        fcs = temp_db.list_symbols(provider="fcs")
        cnb = temp_db.list_symbols(provider="cnb")

        assert len(fcs) == 1
        assert fcs[0].symbol == "EURUSD"
        assert len(cnb) == 1
        assert cnb[0].symbol == "EURCZK"

    def test_list_symbols_with_query(self, temp_db: SQLiteDatabase) -> None:
        symbols = [
            Symbol(provider="fcs", symbol="EURUSD", type="forex", name="Euro / US Dollar"),
            Symbol(provider="fcs", symbol="GBPUSD", type="forex", name="British Pound / US Dollar"),
        ]
        temp_db.populate_symbols("fcs", symbols)
        temp_db.commit()

        results = temp_db.list_symbols(sym_type="forex", query="EUR")
        assert len(results) == 1
        assert results[0].symbol == "EURUSD"

    def test_export_import_rates(self, temp_db: SQLiteDatabase) -> None:
        symbols = [Symbol(provider="fcs", symbol="EURUSD", type="forex", name="Euro")]
        temp_db.populate_symbols("fcs", symbols)
        temp_db.commit()

        temp_db.upsert_rate("2024-01-15", "EURUSD", "fcs", 1.0850)
        temp_db.upsert_rate("2024-01-16", "EURUSD", "fcs", 1.0860)
        temp_db.commit()

        exported = temp_db.export_rates()
        assert len(exported) == 2
        # Verify export includes provider and symbol
        assert exported[0]["provider"] == "fcs"
        assert exported[0]["symbol"] == "EURUSD"

        temp_db.import_rates([])
        temp_db.commit()
        assert temp_db.export_rates() == []

        temp_db.import_rates(exported)
        temp_db.commit()
        assert len(temp_db.export_rates()) == 2

    def test_export_import_symbols(self, temp_db: SQLiteDatabase) -> None:
        symbols = [Symbol(provider="fcs", symbol="EURUSD", type="forex", name="Euro")]
        temp_db.populate_symbols("fcs", symbols)
        temp_db.commit()

        exported = temp_db.export_symbols()
        assert len(exported) == 1
        # Verify export includes provider
        assert exported[0]["provider"] == "fcs"

        temp_db.import_symbols([])
        temp_db.commit()
        assert temp_db.export_symbols() == []

        temp_db.import_symbols(exported)
        temp_db.commit()
        assert len(temp_db.export_symbols()) == 1

    def test_populate_symbols_removes_stale(self, temp_db: SQLiteDatabase) -> None:
        """Symbols removed from provider should be deleted."""
        # Initial populate
        temp_db.populate_symbols("fcs", [
            Symbol(provider="fcs", symbol="EURUSD", type="forex", name="Euro"),
            Symbol(provider="fcs", symbol="GBPUSD", type="forex", name="Pound"),
        ])
        temp_db.commit()

        # Second populate removes GBPUSD
        temp_db.populate_symbols("fcs", [
            Symbol(provider="fcs", symbol="EURUSD", type="forex", name="Euro"),
        ])
        temp_db.commit()

        symbols = temp_db.list_symbols(provider="fcs")
        assert len(symbols) == 1
        assert symbols[0].symbol == "EURUSD"

    def test_populate_symbols_updates_existing(self, temp_db: SQLiteDatabase) -> None:
        """Existing symbols should be updated."""
        temp_db.populate_symbols("fcs", [
            Symbol(provider="fcs", symbol="EURUSD", type="forex", name="Old Name"),
        ])
        temp_db.commit()

        temp_db.populate_symbols("fcs", [
            Symbol(provider="fcs", symbol="EURUSD", type="forex", name="New Name"),
        ])
        temp_db.commit()

        symbols = temp_db.list_symbols(provider="fcs")
        assert len(symbols) == 1
        assert symbols[0].name == "New Name"

    def test_different_providers_same_symbol(self, temp_db: SQLiteDatabase) -> None:
        """Same symbol can exist for different providers."""
        temp_db.populate_symbols("fcs", [
            Symbol(provider="fcs", symbol="EURCZK", type="forex", name="FCS Euro"),
        ])
        temp_db.populate_symbols("cnb", [
            Symbol(provider="cnb", symbol="EURCZK", type="forex", name="CNB Euro"),
        ])
        temp_db.commit()

        # Add rates for both
        temp_db.upsert_rate("2024-01-15", "EURCZK", "fcs", 25.5)
        temp_db.upsert_rate("2024-01-15", "EURCZK", "cnb", 25.6)
        temp_db.commit()

        assert temp_db.get_rate("2024-01-15", "EURCZK", "fcs") == 25.5
        assert temp_db.get_rate("2024-01-15", "EURCZK", "cnb") == 25.6

    def test_get_providers_for_symbol(self, temp_db: SQLiteDatabase) -> None:
        """Get all providers that have a given symbol."""
        temp_db.populate_symbols("fcs", [
            Symbol(provider="fcs", symbol="EURCZK", type="forex", name="FCS Euro"),
            Symbol(provider="fcs", symbol="BTCUSD", type="crypto", name="Bitcoin"),
        ])
        temp_db.populate_symbols("cnb", [
            Symbol(provider="cnb", symbol="EURCZK", type="forex", name="CNB Euro"),
        ])
        temp_db.commit()

        # EURCZK exists in both providers
        providers = temp_db.get_providers_for_symbol("EURCZK")
        assert set(providers) == {"fcs", "cnb"}

        # BTCUSD only in fcs
        providers = temp_db.get_providers_for_symbol("BTCUSD")
        assert providers == ["fcs"]

        # Unknown symbol
        providers = temp_db.get_providers_for_symbol("UNKNOWN")
        assert providers == []
