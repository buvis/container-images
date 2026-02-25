from clara.config import Settings


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost/db")
    s = Settings()
    assert s.secret_key.get_secret_value() == "test-secret"
    assert "asyncpg" in s.async_database_url
