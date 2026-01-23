import threading
from typing import Protocol, Callable

# Global shutdown event - set when app is shutting down
_shutdown_event = threading.Event()


def set_shutdown() -> None:
    """Signal shutdown to interrupt any rate-limit waits."""
    _shutdown_event.set()


def is_shutting_down() -> bool:
    return _shutdown_event.is_set()


class FcsApiClient(Protocol):
    def request(self, endpoint: str, params: dict) -> dict | None: ...


def is_rate_limited(response: dict | None) -> bool:
    if not response:
        return False
    return response.get("code") == 213


def fetch_with_retry(
    api: FcsApiClient,
    endpoint: str,
    params: dict,
    rate_limit_wait: int = 65,
    on_progress: Callable[[str], None] | None = None,
) -> dict | None:
    response = api.request(endpoint, params)

    if is_rate_limited(response):
        if on_progress:
            on_progress(f"Rate limited, waiting {rate_limit_wait}s...")
        # Use event.wait() so shutdown can interrupt
        if _shutdown_event.wait(rate_limit_wait):
            return None  # Shutdown requested
        response = api.request(endpoint, params)

        if is_rate_limited(response):
            raise RuntimeError("Rate limit persists after retry - likely monthly quota exceeded")

    return response
