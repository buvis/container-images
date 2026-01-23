import os
import tempfile
from typing import Generator

import pytest

from app.config import Settings
from app.database import SQLiteDatabase


@pytest.fixture
def temp_db() -> Generator[SQLiteDatabase, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    db = SQLiteDatabase(db_path)
    yield db
    db.close()
    os.unlink(db_path)


@pytest.fixture
def settings(temp_db: SQLiteDatabase, tmp_path: str) -> Settings:
    return Settings(
        provider_api_keys={"fcs": "test-key"},
        db_path=":memory:",
        backup_dir=str(tmp_path / "backups"),
        symbols={"fcs": ["EURUSD", "BTCUSD"]},
        auto_backfill_time="00:30",
        auto_backfill_days=7,
        scheduler_tick_seconds=0.1,
        rate_limit_wait=1,
    )
