from datetime import date
from typing import Any

from icalendar import Todo

_STATUS_TO_VTODO = {
    "pending": "NEEDS-ACTION",
    "in_progress": "IN-PROCESS",
    "done": "COMPLETED",
}
_STATUS_FROM_VTODO = {v: k for k, v in _STATUS_TO_VTODO.items()}

_PRIORITY_TO_VTODO = {0: 0, 1: 1, 2: 5, 3: 9}
_PRIORITY_FROM_VTODO = {0: 0, 1: 1, 5: 2, 9: 3}


def task_to_vtodo(task: Any) -> Todo:
    """Convert Task to iCalendar VTODO."""
    todo = Todo()
    todo.add("summary", task.title)
    if task.description:
        todo.add("description", task.description)
    if task.due_date:
        todo.add("due", task.due_date)
    todo.add("status", _STATUS_TO_VTODO.get(task.status, "NEEDS-ACTION"))
    todo.add("priority", _PRIORITY_TO_VTODO.get(task.priority, 0))
    todo.add("x-clara-entity-type", "task")
    return todo


def vtodo_to_task_data(todo: Any) -> dict[str, Any]:
    """Parse VTODO into Task field dict."""
    title = str(todo.get("summary", ""))
    description = str(todo.get("description", "")) or None

    due_date: date | None = None
    due = todo.get("due")
    if due:
        dt = due.dt
        due_date = (
            dt
            if isinstance(dt, date) and not isinstance(dt, type(None))
            else dt.date()
            if hasattr(dt, "date")
            else dt
        )

    vtodo_status = str(todo.get("status", "NEEDS-ACTION"))
    status = _STATUS_FROM_VTODO.get(vtodo_status, "pending")

    vtodo_priority = int(todo.get("priority", 0) or 0)
    priority = _PRIORITY_FROM_VTODO.get(vtodo_priority, 0)
    if vtodo_priority not in _PRIORITY_FROM_VTODO and vtodo_priority > 0:
        priority = 1 if vtodo_priority <= 3 else (2 if vtodo_priority <= 6 else 3)

    return {
        "title": title,
        "description": description,
        "due_date": due_date,
        "status": status,
        "priority": priority,
    }
