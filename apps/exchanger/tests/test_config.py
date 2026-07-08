import pytest

from app.config import (
    DEFAULT_AUTO_BACKFILL_DAYS,
    DEFAULT_AUTO_BACKFILL_TIME,
    DEFAULT_DB_PATH,
    DEFAULT_RATE_LIMIT_WAIT,
    DEFAULT_SCHEDULER_TICK_SECONDS,
    Settings,
    load_settings,
    parse_backfill_times,
)


class TestSettings:
    def test_settings_immutable(self) -> None:
        s = Settings()
        with pytest.raises(Exception):
            s.provider_api_keys = {}  # type: ignore

    def test_settings_defaults(self) -> None:
        s = Settings()
        assert s.provider_api_keys == {}
        assert s.db_path == DEFAULT_DB_PATH
        assert s.symbols == {}
        assert s.auto_backfill_times == (DEFAULT_AUTO_BACKFILL_TIME,)
        assert s.auto_backfill_days == DEFAULT_AUTO_BACKFILL_DAYS
        assert s.scheduler_tick_seconds == DEFAULT_SCHEDULER_TICK_SECONDS
        assert s.rate_limit_wait == DEFAULT_RATE_LIMIT_WAIT


class TestLoadSettings:
    def test_load_settings_without_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PROVIDER_FCS_API_KEY", raising=False)
        settings = load_settings()
        assert "fcs" not in settings.provider_api_keys

    def test_load_settings_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PROVIDER_FCS_API_KEY", "test-key-123")
        monkeypatch.setenv("DB_PATH", "/tmp/test.db")
        monkeypatch.setenv("SYMBOLS", "fcs:GBPUSD,fcs:ETHUSD,cnb:EURCZK")
        monkeypatch.setenv("AUTO_BACKFILL_TIME", "12:00")
        monkeypatch.setenv("AUTO_BACKFILL_DAYS", "14")

        settings = load_settings()

        assert settings.provider_api_keys["fcs"] == "test-key-123"
        assert settings.db_path == "/tmp/test.db"
        assert settings.symbols == {"fcs": ["GBPUSD", "ETHUSD"], "cnb": ["EURCZK"]}
        assert settings.auto_backfill_times == ("12:00",)
        assert settings.auto_backfill_days == 14

    def test_load_settings_multiple_backfill_times(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AUTO_BACKFILL_TIME", "16:30,8:00")
        settings = load_settings()
        assert settings.auto_backfill_times == ("08:00", "16:30")

    def test_load_settings_empty_symbols(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PROVIDER_FCS_API_KEY", raising=False)
        monkeypatch.setenv("SYMBOLS", "  ,  ,  ")

        settings = load_settings()
        assert settings.symbols == {}

    def test_load_settings_ignores_unprefixed_symbols(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Symbols without provider prefix are ignored."""
        monkeypatch.delenv("PROVIDER_FCS_API_KEY", raising=False)
        monkeypatch.setenv("SYMBOLS", "EURCZK,USDCZK,fcs:BTCEUR")

        settings = load_settings()
        assert settings.symbols == {"fcs": ["BTCEUR"]}

    def test_load_multiple_provider_keys(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PROVIDER_FCS_API_KEY", "fcs-key")
        monkeypatch.setenv("PROVIDER_OTHER_API_KEY", "other-key")

        settings = load_settings()

        assert settings.provider_api_keys["fcs"] == "fcs-key"
        assert settings.provider_api_keys["other"] == "other-key"


class TestParseBackfillTimes:
    def test_single(self) -> None:
        assert parse_backfill_times("16:30") == ("16:30",)

    def test_multiple_sorted_and_deduped(self) -> None:
        assert parse_backfill_times("16:30, 08:00 ,16:30") == ("08:00", "16:30")

    def test_normalizes_padding(self) -> None:
        assert parse_backfill_times("8:5") == ("08:05",)

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_backfill_times("  ,  ")

    def test_bad_format_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_backfill_times("noon")

    def test_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_backfill_times("25:00")
