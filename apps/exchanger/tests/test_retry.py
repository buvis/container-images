import threading

import pytest

from app.utils.retry import is_rate_limited, fetch_with_retry, _shutdown_event


class MockApi:
    def __init__(self, responses: list[dict | None]):
        self._responses = list(responses)
        self.call_count = 0

    def request(self, endpoint: str, params: dict) -> dict | None:
        self.call_count += 1
        return self._responses.pop(0) if self._responses else None


class TestIsRateLimited:
    def test_code_213(self):
        assert is_rate_limited({"code": 213}) is True

    def test_code_200(self):
        assert is_rate_limited({"code": 200}) is False

    def test_none_response(self):
        assert is_rate_limited(None) is False

    def test_no_code_key(self):
        assert is_rate_limited({"data": "ok"}) is False


class TestFetchWithRetry:
    def setup_method(self):
        _shutdown_event.clear()

    def test_returns_response_directly(self):
        api = MockApi([{"code": 200, "response": "ok"}])
        result = fetch_with_retry(api, "forex/history", {}, rate_limit_wait=1)
        assert result == {"code": 200, "response": "ok"}
        assert api.call_count == 1

    def test_retries_after_rate_limit(self):
        api = MockApi([{"code": 213}, {"code": 200, "response": "ok"}])
        result = fetch_with_retry(api, "forex/history", {}, rate_limit_wait=0)
        assert result == {"code": 200, "response": "ok"}
        assert api.call_count == 2

    def test_raises_on_persistent_rate_limit(self):
        api = MockApi([{"code": 213}, {"code": 213}])
        with pytest.raises(RuntimeError, match="quota exceeded"):
            fetch_with_retry(api, "forex/history", {}, rate_limit_wait=0)
        assert api.call_count == 2

    def test_returns_none_on_shutdown(self):
        api = MockApi([{"code": 213}])
        # Set shutdown before the wait
        _shutdown_event.set()
        result = fetch_with_retry(api, "forex/history", {}, rate_limit_wait=60)
        assert result is None
        assert api.call_count == 1  # no retry after shutdown

    def test_progress_callback_on_rate_limit(self):
        api = MockApi([{"code": 213}, {"code": 200}])
        updates: list = []
        fetch_with_retry(api, "forex/history", {}, rate_limit_wait=0, on_progress=updates.append)
        # Should have rate_limit_until set, then cleared
        assert any(isinstance(u, dict) and "rate_limit_until" in u and u["rate_limit_until"] is not None for u in updates)
        assert any(isinstance(u, dict) and u.get("rate_limit_until") is None for u in updates)

    def test_returns_none_response(self):
        api = MockApi([None])
        result = fetch_with_retry(api, "forex/history", {})
        assert result is None
