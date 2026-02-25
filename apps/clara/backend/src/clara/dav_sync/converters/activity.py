from datetime import datetime, timedelta
from typing import Any

from icalendar import Event


def activity_to_vevent(
    activity: Any, participant_names: list[str] | None = None
) -> Event:
    """Convert Activity to iCalendar VEVENT."""
    event = Event()
    event.add("summary", activity.title)
    if activity.description:
        event.add("description", activity.description)
    event.add("dtstart", activity.happened_at)
    if activity.duration_minutes:
        event.add("duration", timedelta(minutes=activity.duration_minutes))
    else:
        event.add("duration", timedelta(hours=1))
    if activity.location:
        event.add("location", activity.location)
    for name in participant_names or []:
        event.add("attendee", f"CN={name}")
    event.add("x-clara-entity-type", "activity")
    return event


def vevent_to_activity_data(event: Any) -> dict[str, Any]:
    """Parse VEVENT into Activity field dict.

    Returns dict with:
        activity_fields: dict for Activity creation
        attendee_names: list of attendee CN values
    """
    title = str(event.get("summary", ""))
    description = str(event.get("description", "")) or None

    dtstart = event.get("dtstart")
    happened_at: datetime | None = None
    if dtstart:
        happened_at = dtstart.dt
        if not isinstance(happened_at, datetime):
            happened_at = datetime.combine(happened_at, datetime.min.time())

    duration_minutes: int | None = None
    duration = event.get("duration")
    if duration:
        duration_minutes = int(duration.dt.total_seconds() // 60)

    location = str(event.get("location", "")) or None

    attendee_names: list[str] = []
    attendees = event.get("attendee")
    if attendees:
        if not isinstance(attendees, list):
            attendees = [attendees]
        for att in attendees:
            cn = att.params.get("CN", str(att).removeprefix("CN="))
            attendee_names.append(str(cn))

    return {
        "activity_fields": {
            "title": title,
            "description": description,
            "happened_at": happened_at,
            "duration_minutes": duration_minutes,
            "location": location,
        },
        "attendee_names": attendee_names,
    }
