import asyncio
import logging
import threading
from datetime import datetime, timezone
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class TaskManager:
    def __init__(self, max_workers: int = 4):
        self._status: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._futures: dict[str, Future] = {}
        self._shutdown_requested = False
        self._clients: set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._clients.add(ws)
        await ws.send_json(self.get_all_status())

    def disconnect(self, ws: WebSocket) -> None:
        self._clients.discard(ws)
        logger.debug("ws client disconnected, %d remaining", len(self._clients))

    def _broadcast(self) -> None:
        """Schedule broadcast from sync context (background threads)."""
        if not self._loop or not self._clients:
            return
        data = self.get_all_status()
        asyncio.run_coroutine_threadsafe(self._async_broadcast(data), self._loop)

    async def _async_broadcast(self, data: dict) -> None:
        dead = []
        for ws in self._clients:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._clients.discard(ws)

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
            self._status[task] = self._normalize_status(status)
        self._broadcast()

    def update_status(self, task: str, **updates: Any) -> None:
        with self._lock:
            if task not in self._status:
                self._status[task] = {}
            if "status" in updates:
                updates = self._normalize_status(updates)
                if updates.get("status") != "error":
                    self._status[task].pop("error", None)
            self._status[task].update(updates)
        self._broadcast()

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
            self._status[task] = self._normalize_status({"status": "running", "message": "Starting..."})
            future = self._executor.submit(fn)
            self._futures[task] = future
        self._broadcast()
        return True

    def shutdown(self) -> None:
        """Signal shutdown and cancel pending tasks."""
        self._shutdown_requested = True
        # Cancel any pending futures
        for future in self._futures.values():
            future.cancel()
        # Don't wait - let threads check shutdown_requested flag
        self._executor.shutdown(wait=False, cancel_futures=True)

    @staticmethod
    def _normalize_status(status: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(status)
        if "status" in normalized:
            normalized.setdefault("last_run", datetime.now(timezone.utc).isoformat())
            if normalized.get("status") == "error":
                normalized.setdefault("error", normalized.get("message"))
            else:
                normalized["error"] = None
        return normalized
