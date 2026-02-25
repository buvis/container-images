import uuid
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from clara.notifications.models import Notification


def _make_reminder(vault_id: uuid.UUID, days_offset: int = 0, **kwargs):
    r = MagicMock()
    r.id = uuid.uuid4()
    r.vault_id = vault_id
    r.title = kwargs.get("title", "Test reminder")
    r.next_expected_date = date.today() + timedelta(days=days_offset)
    r.status = "active"
    r.deleted_at = None
    r.frequency_type = kwargs.get("frequency_type", "one_time")
    r.frequency_number = kwargs.get("frequency_number", 1)
    r.last_triggered_at = None
    return r


def _make_membership(vault_id: uuid.UUID, user_id: uuid.UUID):
    m = MagicMock()
    m.vault_id = vault_id
    m.user_id = user_id
    m.deleted_at = None
    return m


@patch("clara.jobs.reminders.get_sync_session")
def test_due_reminders_create_notifications(mock_get_session):
    vault_id = uuid.uuid4()
    user_id = uuid.uuid4()
    due_reminder = _make_reminder(vault_id, days_offset=0)
    membership = _make_membership(vault_id, user_id)

    session = MagicMock()
    mock_get_session.return_value = session

    # first execute: fetch due reminders
    # second execute: fetch vault members (inside _notify_vault_members)
    reminder_result = MagicMock()
    reminder_result.scalars.return_value.all.return_value = [due_reminder]
    member_result = MagicMock()
    member_result.scalars.return_value.all.return_value = [membership]
    session.execute.side_effect = [reminder_result, member_result]

    from clara.jobs.reminders import evaluate_reminders
    evaluate_reminders()

    # notification added for the vault member
    session.add.assert_called_once()
    added = session.add.call_args[0][0]
    assert isinstance(added, Notification)
    assert added.user_id == user_id
    assert "Reminder" in added.title
    session.commit.assert_called_once()


@patch("clara.jobs.reminders.get_sync_session")
def test_non_due_skipped(mock_get_session):
    vault_id = uuid.uuid4()
    future_reminder = _make_reminder(vault_id, days_offset=7)

    session = MagicMock()
    mock_get_session.return_value = session

    # query returns no due reminders (future one excluded by WHERE clause)
    reminder_result = MagicMock()
    reminder_result.scalars.return_value.all.return_value = []
    session.execute.return_value = reminder_result

    from clara.jobs.reminders import evaluate_reminders
    evaluate_reminders()

    # no notifications added
    session.add.assert_not_called()
    session.commit.assert_called_once()


@patch("clara.jobs.reminders.get_sync_session")
def test_one_time_reminder_completed(mock_get_session):
    vault_id = uuid.uuid4()
    user_id = uuid.uuid4()
    reminder = _make_reminder(vault_id, days_offset=0, frequency_type="one_time")
    membership = _make_membership(vault_id, user_id)

    session = MagicMock()
    mock_get_session.return_value = session
    reminder_result = MagicMock()
    reminder_result.scalars.return_value.all.return_value = [reminder]
    member_result = MagicMock()
    member_result.scalars.return_value.all.return_value = [membership]
    session.execute.side_effect = [reminder_result, member_result]

    from clara.jobs.reminders import evaluate_reminders
    evaluate_reminders()

    assert reminder.status == "completed"


@patch("clara.jobs.reminders.get_sync_session")
def test_recurring_reminder_rescheduled(mock_get_session):
    vault_id = uuid.uuid4()
    user_id = uuid.uuid4()
    reminder = _make_reminder(
        vault_id, days_offset=0, frequency_type="week", frequency_number=2
    )
    original_date = reminder.next_expected_date
    membership = _make_membership(vault_id, user_id)

    session = MagicMock()
    mock_get_session.return_value = session
    reminder_result = MagicMock()
    reminder_result.scalars.return_value.all.return_value = [reminder]
    member_result = MagicMock()
    member_result.scalars.return_value.all.return_value = [membership]
    session.execute.side_effect = [reminder_result, member_result]

    from clara.jobs.reminders import evaluate_reminders
    evaluate_reminders()

    assert reminder.status == "active"
    assert reminder.next_expected_date == original_date + timedelta(weeks=2)
