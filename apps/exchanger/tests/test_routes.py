import os
import tempfile
import time
from datetime import date
from typing import Callable, Generator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.database import SQLiteDatabase
from app.main import create_app
from app.models import Symbol, SymbolInfo


@pytest.fixture
def test_settings() -> Generator[Settings, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    backup_dir = tempfile.mkdtemp()

    settings = Settings(
        provider_api_keys={"fcs": "test-key"},
        db_path=db_path,
        backup_dir=backup_dir,
        symbols={},  # Empty to prevent startup backfill
        auto_backfill_time="23:59",
        auto_backfill_days=1,
        scheduler_tick_seconds=10,
        rate_limit_wait=0,
    )
    yield settings
    os.unlink(db_path)
    import shutil
    shutil.rmtree(backup_dir, ignore_errors=True)


class MockFcsApi:
    def __init__(self, key: str):
        pass

    def request(self, endpoint: str, params: dict) -> dict | None:
        return {"code": 200, "response": []}


@pytest.fixture
def client(test_settings: Settings, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setattr("app.sources.fcs.FcsApi", MockFcsApi)

    app = create_app(test_settings)
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestHealthEndpoint:
    def test_health(self, client: TestClient) -> None:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestProvidersEndpoint:
    def test_list_providers(self, client: TestClient) -> None:
        response = client.get("/api/providers")
        assert response.status_code == 200
        providers = response.json()
        assert "fcs" in providers
        assert "cnb" in providers


class TestProvidersStatusEndpoint:
    def test_providers_status(self, client: TestClient, test_settings: Settings) -> None:
        db = SQLiteDatabase(test_settings.db_path)
        db.populate_symbols("fcs", [Symbol(provider="fcs", symbol="EURUSD", type="forex", name="Euro")])
        db.commit()
        db.close()

        response = client.get("/api/providers/status")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        status_by_name = {item["name"]: item for item in data}
        assert status_by_name["fcs"]["symbol_count"] == 1
        assert status_by_name["fcs"]["healthy"] is True
        assert status_by_name["cnb"]["symbol_count"] == 0
        assert status_by_name["cnb"]["healthy"] is False


class TestRatesEndpoint:
    def test_get_rate_not_found(self, client: TestClient) -> None:
        response = client.get("/api/rates", params={"date": "2024-01-01", "symbol": "EURUSD", "provider": "fcs"})
        assert response.status_code == 200
        assert response.json() == {"rate": None}

    def test_get_rate_found(self, client: TestClient, test_settings: Settings) -> None:
        db = SQLiteDatabase(test_settings.db_path)
        db.populate_symbols("fcs", [Symbol(provider="fcs", symbol="EURUSD", type="forex", name="Euro")])
        db.commit()
        db.upsert_rate("2024-01-15", "EURUSD", "fcs", 1.0850)
        db.commit()
        db.close()

        response = client.get("/api/rates", params={"date": "2024-01-15", "symbol": "EURUSD", "provider": "fcs"})
        assert response.status_code == 200
        assert response.json() == {"rate": 1.0850}

    def test_get_rate_missing_provider(self, client: TestClient) -> None:
        response = client.get("/api/rates", params={"date": "2024-01-01", "symbol": "EURUSD"})
        assert response.status_code == 422


class TestBackfillEndpoint:
    def test_backfill_starts(self, client: TestClient) -> None:
        response = client.post("/api/backfill", params={"provider": "fcs", "length": 5})
        assert response.status_code == 200
        data = response.json()
        assert data["scheduled"] is True

    def test_backfill_custom_symbols(self, client: TestClient) -> None:
        response = client.post("/api/backfill", params={"provider": "fcs", "length": 5, "symbols": "GBPUSD,JPYUSD"})
        assert response.status_code == 200
        assert response.json()["scheduled"] is True

    def test_backfill_all_providers(self, client: TestClient) -> None:
        response = client.post("/api/backfill", params={"provider": "all", "length": 5})
        assert response.status_code == 200
        assert response.json()["scheduled"] is True

    def test_backfill_missing_provider(self, client: TestClient) -> None:
        response = client.post("/api/backfill", params={"length": 5})
        assert response.status_code == 422


class TestPopulateSymbolsEndpoint:
    def test_populate_starts(self, client: TestClient) -> None:
        response = client.post("/api/populate_symbols", params={"provider": "fcs"})
        assert response.status_code == 200
        data = response.json()
        assert data["scheduled"] is True

    def test_populate_all_providers(self, client: TestClient) -> None:
        response = client.post("/api/populate_symbols", params={"provider": "all"})
        assert response.status_code == 200
        assert response.json()["scheduled"] is True

    def test_populate_missing_provider(self, client: TestClient) -> None:
        response = client.post("/api/populate_symbols")
        assert response.status_code == 422


class TestTaskStatusEndpoint:
    def test_task_status_empty(self, client: TestClient) -> None:
        time.sleep(0.5)
        response = client.get("/api/task_status")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)


class TestSymbolListEndpoints:
    def test_forex_list_empty(self, client: TestClient) -> None:
        response = client.get("/api/forex/list")
        assert response.status_code == 200
        assert response.json() == []

    def test_crypto_list_empty(self, client: TestClient) -> None:
        response = client.get("/api/crypto/list")
        assert response.status_code == 200
        assert response.json() == []

    def test_forex_list_with_data(self, client: TestClient, test_settings: Settings) -> None:
        db = SQLiteDatabase(test_settings.db_path)
        db.populate_symbols("fcs", [Symbol(provider="fcs", symbol="EURUSD", type="forex", name="Euro")])
        db.commit()
        db.close()

        response = client.get("/api/forex/list")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "EURUSD"
        assert data[0]["provider"] == "fcs"

    def test_forex_list_with_query(self, client: TestClient, test_settings: Settings) -> None:
        db = SQLiteDatabase(test_settings.db_path)
        db.populate_symbols("fcs", [
            Symbol(provider="fcs", symbol="EURUSD", type="forex", name="Euro"),
            Symbol(provider="fcs", symbol="GBPUSD", type="forex", name="Pound"),
        ])
        db.commit()
        db.close()

        response = client.get("/api/forex/list", params={"q": "EUR"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "EURUSD"

    def test_symbols_list_by_provider(self, client: TestClient, test_settings: Settings) -> None:
        db = SQLiteDatabase(test_settings.db_path)
        db.populate_symbols("fcs", [Symbol(provider="fcs", symbol="EURUSD", type="forex", name="FCS Euro")])
        db.populate_symbols("cnb", [Symbol(provider="cnb", symbol="EURCZK", type="forex", name="CNB Euro")])
        db.commit()
        db.close()

        response = client.get("/api/symbols/list", params={"provider": "cnb"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["provider"] == "cnb"


class TestBackupRestoreEndpoints:
    def test_backup_creates_file(self, client: TestClient, test_settings: Settings) -> None:
        time.sleep(0.5)
        response = client.post("/api/backup")
        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "timestamp" in data
        assert data["rates_count"] == 0
        assert data["symbols_count"] == 0

        # Verify file was created
        from pathlib import Path
        backup_path = Path(test_settings.backup_dir) / data["filename"]
        assert backup_path.exists()

    def test_backup_with_data(self, client: TestClient, test_settings: Settings) -> None:
        db = SQLiteDatabase(test_settings.db_path)
        db.populate_symbols("fcs", [Symbol(provider="fcs", symbol="EURUSD", type="forex", name="Euro")])
        db.commit()
        db.upsert_rate("2024-01-15", "EURUSD", "fcs", 1.0850)
        db.commit()
        db.close()

        time.sleep(0.5)
        response = client.post("/api/backup")
        assert response.status_code == 200
        data = response.json()
        assert data["rates_count"] == 1
        assert data["symbols_count"] == 1

        # Verify file contents
        import json
        from pathlib import Path
        backup_path = Path(test_settings.backup_dir) / data["filename"]
        with open(backup_path) as f:
            backup_data = json.load(f)
        assert len(backup_data["rates"]) == 1
        assert backup_data["rates"][0]["provider"] == "fcs"

    def test_list_backups(self, client: TestClient) -> None:
        time.sleep(0.5)
        # Create a backup first
        client.post("/api/backup")

        response = client.get("/api/backups")
        assert response.status_code == 200
        backups = response.json()
        assert len(backups) >= 1
        assert "filename" in backups[0]
        assert "timestamp" in backups[0]

    def test_restore(self, client: TestClient, test_settings: Settings) -> None:
        # Add data and create backup
        db = SQLiteDatabase(test_settings.db_path)
        db.populate_symbols("fcs", [Symbol(provider="fcs", symbol="EURUSD", type="forex", name="Euro")])
        db.commit()
        db.upsert_rate("2024-01-15", "EURUSD", "fcs", 1.0850)
        db.commit()
        db.close()

        time.sleep(0.5)
        backup_response = client.post("/api/backup")
        timestamp = backup_response.json()["timestamp"]

        # Clear and restore
        response = client.post("/api/restore", params={"timestamp": timestamp})
        assert response.status_code == 200
        data = response.json()
        assert data["timestamp"] == timestamp
        assert data["rates"] == 1
        assert data["symbols"] == 1

    def test_restore_not_found(self, client: TestClient) -> None:
        time.sleep(0.5)
        response = client.post("/api/restore", params={"timestamp": "nonexistent"})
        assert response.status_code == 404
