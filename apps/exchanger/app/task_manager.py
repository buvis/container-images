import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable


class TaskManager:
    def __init__(self, max_workers: int = 4):
        self._status: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._futures: dict[str, Future] = {}
        self._shutdown_requested = False

    @property
    def shutdown_requested(self) -> bool:
        return self._shutdown_requested

    def get_status(self, task: str) -> dict[str, Any]:
        with self._lock:
            return self._status.get(task, {}).copy()

    def get_all_status(self) -> dict[str, Any]:
        with self._lock:
            return {k: v.copy() for k, v in self._status.items()}

    def set_status(self, task: str, status: dict[str, Any]) -> None:
        with self._lock:
            self._status[task] = status

    def update_status(self, task: str, **updates: Any) -> None:
        with self._lock:
            if task not in self._status:
                self._status[task] = {}
            self._status[task].update(updates)

    def is_running(self, task: str) -> bool:
        with self._lock:
            return self._status.get(task, {}).get("status") == "running"

    def any_running(self, tasks: list[str]) -> str | None:
        with self._lock:
            for task in tasks:
                if self._status.get(task, {}).get("status") == "running":
                    return task
        return None

    def start_if_idle(self, task: str, fn: Callable[[], None]) -> bool:
        """Atomically check if task is idle and start it. Returns True if started."""
        with self._lock:
            if self._status.get(task, {}).get("status") == "running":
                return False
            self._status[task] = {"status": "running", "message": "Starting..."}
            future = self._executor.submit(fn)
            self._futures[task] = future
            return True

    def shutdown(self) -> None:
        """Signal shutdown and cancel pending tasks."""
        self._shutdown_requested = True
        # Cancel any pending futures
        for future in self._futures.values():
            future.cancel()
        # Don't wait - let threads check shutdown_requested flag
        self._executor.shutdown(wait=False, cancel_futures=True)
