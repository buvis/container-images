import time
from typing import Callable
from unittest.mock import Mock

import pytest

from app.config import Settings
from app.main import BACKFILL_RETRY_INITIAL_SECONDS, BACKFILL_RETRY_MAX_SECONDS, Application
from app.scheduler import BackgroundScheduler


class RecordingScheduler:
    """Stand-in for BackgroundScheduler that records one-shot jobs."""

    def __init__(self) -> None:
        self.once: list[tuple[float, Callable[[], None]]] = []

    def schedule_once(self, delay_seconds: float, job: Callable[[], None]) -> None:
        self.once.append((delay_seconds, job))


@pytest.fixture
def application(settings: Settings):
    app = Application(settings)
    app.scheduler = RecordingScheduler()
    yield app
    app.task_manager.shutdown()
    app.db.close()


def run_backfill_and_wait(app: Application, retry_on_failure: bool = True) -> None:
    assert app.start_backfill_if_idle("fcs", ["EURUSD"], 7, retry_on_failure=retry_on_failure)
    app.task_manager._futures["backfill:fcs"].result(timeout=5)


def test_failed_backfill_schedules_retry_with_doubling(application: Application) -> None:
    application.backfill_service.backfill = Mock(side_effect=ConnectionError("network down"))

    run_backfill_and_wait(application)
    run_backfill_and_wait(application)
    run_backfill_and_wait(application)

    delays = [delay for delay, _ in application.scheduler.once]
    assert delays == [
        BACKFILL_RETRY_INITIAL_SECONDS,
        BACKFILL_RETRY_INITIAL_SECONDS * 2,
        BACKFILL_RETRY_INITIAL_SECONDS * 4,
    ]


def test_retry_delay_is_capped(application: Application) -> None:
    application.backfill_service.backfill = Mock(side_effect=ConnectionError("network down"))
    application._backfill_retry_delays["fcs"] = BACKFILL_RETRY_MAX_SECONDS

    run_backfill_and_wait(application)
    run_backfill_and_wait(application)

    delays = [delay for delay, _ in application.scheduler.once]
    assert delays == [BACKFILL_RETRY_MAX_SECONDS, BACKFILL_RETRY_MAX_SECONDS]


def test_partial_failure_schedules_retry(application: Application) -> None:
    application.backfill_service.backfill = Mock(return_value=({"fcs:EURUSD": 5}, ["BTCUSD"]))

    run_backfill_and_wait(application)

    assert [delay for delay, _ in application.scheduler.once] == [BACKFILL_RETRY_INITIAL_SECONDS]


def test_success_resets_retry_delay(application: Application) -> None:
    application.backfill_service.backfill = Mock(side_effect=ConnectionError("network down"))
    run_backfill_and_wait(application)

    application.backfill_service.backfill = Mock(return_value=({"fcs:EURUSD": 5}, []))
    run_backfill_and_wait(application)

    application.backfill_service.backfill = Mock(side_effect=ConnectionError("network down"))
    run_backfill_and_wait(application)

    delays = [delay for delay, _ in application.scheduler.once]
    assert delays == [BACKFILL_RETRY_INITIAL_SECONDS, BACKFILL_RETRY_INITIAL_SECONDS]


def test_retry_job_reinvokes_backfill_with_retry_enabled(application: Application) -> None:
    application.backfill_service.backfill = Mock(side_effect=ConnectionError("network down"))
    run_backfill_and_wait(application)

    _, retry_job = application.scheduler.once[0]
    retry_job()
    application.task_manager._futures["backfill:fcs"].result(timeout=5)

    assert len(application.scheduler.once) == 2


def test_no_retry_when_not_requested(application: Application) -> None:
    application.backfill_service.backfill = Mock(side_effect=ConnectionError("network down"))

    run_backfill_and_wait(application, retry_on_failure=False)

    assert application.scheduler.once == []


def test_schedule_once_runs_job_exactly_once() -> None:
    scheduler = BackgroundScheduler(tick_seconds=0.01)
    runs: list[int] = []
    scheduler.schedule_once(1, lambda: runs.append(1))
    scheduler.start()
    deadline = time.monotonic() + 3
    while not runs and time.monotonic() < deadline:
        time.sleep(0.01)
    time.sleep(0.05)  # a few more ticks to prove the job doesn't repeat
    scheduler.stop()
    assert runs == [1]
