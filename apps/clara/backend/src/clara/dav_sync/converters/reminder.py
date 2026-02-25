from datetime import date
from typing import Any

from icalendar import Todo

_FREQ_TO_RRULE = {"week": "WEEKLY", "month": "MONTHLY", "year": "YEARLY"}
_FREQ_FROM_RRULE = {v: k for k, v in _FREQ_TO_RRULE.items()}


def reminder_to_vtodo(reminder: Any) -> Todo:
    """Convert Reminder to VTODO with RRULE."""
    todo = Todo()
    todo.add("summary", reminder.title)
    if reminder.description:
        todo.add("description", reminder.description)
    todo.add("due", reminder.next_expected_date)
    if reminder.status == "completed":
        todo.add("status", "COMPLETED")
    else:
        todo.add("status", "NEEDS-ACTION")

    freq = _FREQ_TO_RRULE.get(reminder.frequency_type)
    if freq:
        todo.add("rrule", {"freq": freq, "interval": reminder.frequency_number})

    todo.add("x-clara-entity-type", "reminder")
    return todo


def vtodo_to_reminder_data(todo: Any) -> dict[str, Any]:
    """Parse VTODO+RRULE into Reminder field dict."""
    title = str(todo.get("summary", ""))
    description = str(todo.get("description", "")) or None

    next_expected_date: date | None = None
    due = todo.get("due")
    if due:
        dt = due.dt
        next_expected_date = (
            dt
            if isinstance(dt, date) and not isinstance(dt, type(None))
            else getattr(dt, "date", lambda: dt)()
        )

    vtodo_status = str(todo.get("status", "NEEDS-ACTION"))
    status = "completed" if vtodo_status == "COMPLETED" else "active"

    frequency_type = "one_time"
    frequency_number = 1
    rrule = todo.get("rrule")
    if rrule:
        freq_list = rrule.get("FREQ", [])
        if freq_list:
            freq_str = freq_list[0] if isinstance(freq_list, list) else str(freq_list)
            frequency_type = _FREQ_FROM_RRULE.get(freq_str, "one_time")
        interval_list = rrule.get("INTERVAL", [1])
        if interval_list:
            frequency_number = int(
                interval_list[0] if isinstance(interval_list, list) else interval_list
            )

    return {
        "title": title,
        "description": description,
        "next_expected_date": next_expected_date,
        "frequency_type": frequency_type,
        "frequency_number": frequency_number,
        "status": status,
    }
