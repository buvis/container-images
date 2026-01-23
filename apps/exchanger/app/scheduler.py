import threading
from typing import Callable

import schedule


class BackgroundScheduler:
    def __init__(self, tick_seconds: float = 2.0):
        self._tick_seconds = tick_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._scheduler = schedule.Scheduler()  # Instance, not global
        self._lock = threading.Lock()

    def schedule_daily(self, time_str: str, job: Callable[[], None]) -> None:
        self._scheduler.every().day.at(time_str).do(job)

    def start(self) -> None:
        with self._lock:
            # Guard: don't start if already running
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._scheduler.clear()  # Clear jobs on stop

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            self._scheduler.run_pending()
            self._stop_event.wait(self._tick_seconds)
