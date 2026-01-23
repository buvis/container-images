from app.task_manager import TaskManager


class TestTaskManager:
    def test_initial_status_empty(self) -> None:
        tm = TaskManager()
        assert tm.get_status("backfill") == {}
        assert tm.get_all_status() == {}

    def test_set_and_get_status(self) -> None:
        tm = TaskManager()
        tm.set_status("backfill", {"status": "running", "message": "Starting..."})

        status = tm.get_status("backfill")
        assert status["status"] == "running"
        assert status["message"] == "Starting..."

    def test_update_status(self) -> None:
        tm = TaskManager()
        tm.set_status("backfill", {"status": "running", "message": "Starting..."})
        tm.update_status("backfill", message="Page 1...")

        status = tm.get_status("backfill")
        assert status["message"] == "Page 1..."
        assert status["status"] == "running"

    def test_update_creates_if_missing(self) -> None:
        tm = TaskManager()
        tm.update_status("new_task", status="pending")

        assert tm.get_status("new_task") == {"status": "pending"}

    def test_is_running(self) -> None:
        tm = TaskManager()
        assert not tm.is_running("backfill")

        tm.set_status("backfill", {"status": "running"})
        assert tm.is_running("backfill")

        tm.set_status("backfill", {"status": "done"})
        assert not tm.is_running("backfill")

    def test_any_running_none(self) -> None:
        tm = TaskManager()
        assert tm.any_running(["backfill", "populate"]) is None

    def test_any_running_found(self) -> None:
        tm = TaskManager()
        tm.set_status("backfill", {"status": "done"})
        tm.set_status("populate", {"status": "running"})

        assert tm.any_running(["backfill", "populate"]) == "populate"

    def test_get_status_returns_copy(self) -> None:
        tm = TaskManager()
        tm.set_status("task", {"status": "running"})

        status = tm.get_status("task")
        status["status"] = "modified"

        assert tm.get_status("task")["status"] == "running"

    def test_get_all_status_returns_copies(self) -> None:
        tm = TaskManager()
        tm.set_status("task1", {"status": "running"})
        tm.set_status("task2", {"status": "done"})

        all_status = tm.get_all_status()
        assert len(all_status) == 2
        assert all_status["task1"]["status"] == "running"
        assert all_status["task2"]["status"] == "done"

        all_status["task1"]["status"] = "modified"
        assert tm.get_status("task1")["status"] == "running"
