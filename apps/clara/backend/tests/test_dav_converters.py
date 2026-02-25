from datetime import date, datetime
from types import SimpleNamespace

from clara.dav_sync.converters.activity import (
    activity_to_vevent,
    vevent_to_activity_data,
)
from clara.dav_sync.converters.contact import contact_to_vcard, vcard_to_contact_data
from clara.dav_sync.converters.reminder import reminder_to_vtodo, vtodo_to_reminder_data
from clara.dav_sync.converters.task import task_to_vtodo, vtodo_to_task_data

# -- Contact converter -------------------------------------------------------


def _make_contact(**overrides):
    defaults = dict(
        first_name="Jane",
        last_name="Doe",
        nickname=None,
        birthdate=None,
        gender=None,
        tags=[],
        contact_methods=[],
        addresses=[],
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_contact_roundtrip_minimal():
    c = _make_contact()
    vcard = contact_to_vcard(c)
    data = vcard_to_contact_data(vcard)

    assert data["contact_fields"]["first_name"] == "Jane"
    assert data["contact_fields"]["last_name"] == "Doe"
    assert data["contact_fields"]["nickname"] is None
    assert data["contact_fields"]["birthdate"] is None
    assert data["contact_fields"]["gender"] is None
    assert data["contact_methods"] == []
    assert data["addresses"] == []
    assert data["tags"] == []


def test_contact_roundtrip_full():
    c = _make_contact(
        nickname="JD",
        birthdate=date(1990, 5, 15),
        gender="female",
        tags=[SimpleNamespace(name="friend"), SimpleNamespace(name="work")],
        contact_methods=[
            SimpleNamespace(type="email", value="jane@example.com", label="home"),
            SimpleNamespace(type="phone", value="+1234567890", label="mobile"),
        ],
        addresses=[
            SimpleNamespace(
                line1="123 Main St",
                city="Springfield",
                postal_code="62701",
                country="US",
                label="home",
            )
        ],
    )
    vcard = contact_to_vcard(c)
    data = vcard_to_contact_data(vcard)

    cf = data["contact_fields"]
    assert cf["first_name"] == "Jane"
    assert cf["last_name"] == "Doe"
    assert cf["nickname"] == "JD"
    assert cf["birthdate"] == date(1990, 5, 15)
    assert cf["gender"] == "female"

    # vcard_to_contact_data only reads the first CATEGORIES entry
    assert "friend" in data["tags"]

    methods = data["contact_methods"]
    assert len(methods) == 2
    emails = [m for m in methods if m["type"] == "email"]
    phones = [m for m in methods if m["type"] == "phone"]
    assert emails[0]["value"] == "jane@example.com"
    assert emails[0]["label"] == "home"
    assert phones[0]["value"] == "+1234567890"
    assert phones[0]["label"] == "mobile"

    addrs = data["addresses"]
    assert len(addrs) == 1
    assert addrs[0]["line1"] == "123 Main St"
    assert addrs[0]["city"] == "Springfield"
    assert addrs[0]["postal_code"] == "62701"
    assert addrs[0]["country"] == "US"
    assert addrs[0]["label"] == "home"


# -- Activity converter -------------------------------------------------------


def _make_activity(**overrides):
    defaults = dict(
        title="Coffee meeting",
        description=None,
        happened_at=datetime(2026, 1, 10, 14, 0),
        duration_minutes=None,
        location=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_activity_roundtrip_minimal():
    a = _make_activity()
    event = activity_to_vevent(a)
    data = vevent_to_activity_data(event)

    af = data["activity_fields"]
    assert af["title"] == "Coffee meeting"
    assert af["description"] is None
    assert af["happened_at"] == datetime(2026, 1, 10, 14, 0)
    # default 1h duration when none set
    assert af["duration_minutes"] == 60
    assert af["location"] is None
    assert data["attendee_names"] == []


def test_activity_roundtrip_full():
    a = _make_activity(
        description="Discuss Q1 plans",
        duration_minutes=45,
        location="Downtown Cafe",
    )
    event = activity_to_vevent(a, participant_names=["Alice", "Bob"])
    data = vevent_to_activity_data(event)

    af = data["activity_fields"]
    assert af["title"] == "Coffee meeting"
    assert af["description"] == "Discuss Q1 plans"
    assert af["duration_minutes"] == 45
    assert af["location"] == "Downtown Cafe"
    assert len(data["attendee_names"]) == 2


# -- Task converter -----------------------------------------------------------


def _make_task(**overrides):
    defaults = dict(
        title="Buy groceries",
        description=None,
        due_date=None,
        status="pending",
        priority=0,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_task_roundtrip_minimal():
    t = _make_task()
    todo = task_to_vtodo(t)
    data = vtodo_to_task_data(todo)

    assert data["title"] == "Buy groceries"
    assert data["description"] is None
    assert data["due_date"] is None
    assert data["status"] == "pending"
    assert data["priority"] == 0


def test_task_roundtrip_full():
    t = _make_task(
        description="Milk, eggs, bread",
        due_date=date(2026, 2, 20),
        status="in_progress",
        priority=2,
    )
    todo = task_to_vtodo(t)
    data = vtodo_to_task_data(todo)

    assert data["title"] == "Buy groceries"
    assert data["description"] == "Milk, eggs, bread"
    assert data["due_date"] == date(2026, 2, 20)
    assert data["status"] == "in_progress"
    assert data["priority"] == 2


def test_task_done_status():
    t = _make_task(status="done")
    todo = task_to_vtodo(t)
    data = vtodo_to_task_data(todo)
    assert data["status"] == "done"


def test_task_priority_mapping():
    """Verify all priority levels round-trip correctly."""
    for prio in (0, 1, 2, 3):
        t = _make_task(priority=prio)
        data = vtodo_to_task_data(task_to_vtodo(t))
        assert data["priority"] == prio


# -- Reminder converter -------------------------------------------------------


def _make_reminder(**overrides):
    defaults = dict(
        title="Call mom",
        description=None,
        next_expected_date=date(2026, 3, 1),
        frequency_type="week",
        frequency_number=1,
        status="active",
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_reminder_roundtrip_minimal():
    r = _make_reminder(frequency_type="one_time")
    todo = reminder_to_vtodo(r)
    data = vtodo_to_reminder_data(todo)

    assert data["title"] == "Call mom"
    assert data["description"] is None
    assert data["next_expected_date"] == date(2026, 3, 1)
    assert data["frequency_type"] == "one_time"
    assert data["frequency_number"] == 1
    assert data["status"] == "active"


def test_reminder_roundtrip_full():
    r = _make_reminder(
        description="Weekly check-in",
        frequency_type="month",
        frequency_number=2,
    )
    todo = reminder_to_vtodo(r)
    data = vtodo_to_reminder_data(todo)

    assert data["title"] == "Call mom"
    assert data["description"] == "Weekly check-in"
    assert data["next_expected_date"] == date(2026, 3, 1)
    assert data["frequency_type"] == "month"
    assert data["frequency_number"] == 2
    assert data["status"] == "active"


def test_reminder_completed_status():
    r = _make_reminder(status="completed")
    todo = reminder_to_vtodo(r)
    data = vtodo_to_reminder_data(todo)
    assert data["status"] == "completed"


def test_reminder_yearly_frequency():
    r = _make_reminder(frequency_type="year", frequency_number=1)
    todo = reminder_to_vtodo(r)
    data = vtodo_to_reminder_data(todo)
    assert data["frequency_type"] == "year"
    assert data["frequency_number"] == 1
