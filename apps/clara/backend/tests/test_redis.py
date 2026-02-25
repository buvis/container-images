from unittest.mock import patch

import pytest

from clara.redis import get_queue, get_redis


def test_get_redis_creates_connection_lazily(monkeypatch: pytest.MonkeyPatch):
    """get_redis() should not connect at import time."""
    import clara.redis as redis_mod

    # restore real function (conftest autouse replaces it)
    monkeypatch.setattr("clara.redis.get_redis", get_redis)
    redis_mod._redis = None

    with patch("clara.redis.Redis.from_url") as mock_from_url:
        mock_from_url.return_value = "fake-conn"
        conn = redis_mod.get_redis()
        assert conn == "fake-conn"
        mock_from_url.assert_called_once()

        # second call reuses
        conn2 = redis_mod.get_redis()
        assert conn2 == "fake-conn"
        mock_from_url.assert_called_once()


def test_get_queue_creates_lazily(monkeypatch: pytest.MonkeyPatch):
    import clara.redis as redis_mod

    # restore real functions (conftest autouse replaces get_redis)
    monkeypatch.setattr("clara.redis.get_redis", get_redis)
    redis_mod._redis = None
    redis_mod._queue = None

    with patch("clara.redis.Redis.from_url") as mock_from_url:
        mock_from_url.return_value = "fake-conn"
        with patch("clara.redis.Queue") as mock_queue:
            mock_queue.return_value = "fake-queue"
            q = redis_mod.get_queue()
            assert q == "fake-queue"
            mock_queue.assert_called_once_with("default", connection="fake-conn")
