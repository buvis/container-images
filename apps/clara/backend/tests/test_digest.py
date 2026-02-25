import uuid
from unittest.mock import MagicMock, patch

from clara.auth.models import User, Vault, VaultMembership
from clara.jobs.digest import _build_digest_html, daily_digest, weekly_summary


def test_digest_html_escapes_user_name():
    html = _build_digest_html("<script>xss</script>", ["item"], "Title")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_digest_html_escapes_items():
    html = _build_digest_html("Bob", ["<b>bold</b>"], "Title")
    assert "<b>bold</b>" not in html
    assert "&lt;b&gt;" in html


def test_digest_html_escapes_title():
    html = _build_digest_html("Bob", ["item"], "<img onerror=alert(1)>")
    assert "<img " not in html
    assert "&lt;img " in html


def test_digest_html_empty_items():
    html = _build_digest_html("Bob", [], "Title")
    assert "<ul></ul>" in html
    assert "Bob" in html


def test_digest_html_empty_name():
    html = _build_digest_html("", ["item"], "Title")
    assert "there" in html


@patch("clara.jobs.digest.get_sender")
@patch("clara.jobs.digest.get_sync_session")
def test_daily_digest_no_activities(mock_get_session, mock_get_sender):
    session = MagicMock()
    mock_get_session.return_value = session
    sender = MagicMock()
    mock_get_sender.return_value = sender

    user_id = uuid.uuid4()
    vault_id = uuid.uuid4()
    # reminder counts: empty; task counts: empty; membership rows
    reminder_result = MagicMock()
    reminder_result.all.return_value = []
    task_result = MagicMock()
    task_result.all.return_value = []
    membership_result = MagicMock()
    membership_result.all.return_value = [
        (user_id, "bob@test.com", "Bob", vault_id, "My Vault"),
    ]
    session.execute.side_effect = [reminder_result, task_result, membership_result]

    daily_digest()

    # no reminders or tasks due -> no email sent
    sender.send.assert_not_called()
    session.close.assert_called_once()


@patch("clara.jobs.digest.get_sender")
@patch("clara.jobs.digest.get_sync_session")
def test_weekly_summary_no_contacts(mock_get_session, mock_get_sender):
    session = MagicMock()
    mock_get_session.return_value = session
    sender = MagicMock()
    mock_get_sender.return_value = sender

    user_id = uuid.uuid4()
    vault_id = uuid.uuid4()
    # activity counts: empty; stay_in_touch configs: empty; membership rows
    activity_result = MagicMock()
    activity_result.all.return_value = []
    config_result = MagicMock()
    config_result.all.return_value = []
    membership_result = MagicMock()
    membership_result.all.return_value = [
        (user_id, "bob@test.com", "Bob", vault_id, "My Vault"),
    ]
    session.execute.side_effect = [activity_result, config_result, membership_result]

    weekly_summary()

    # no activities or overdue contacts -> no email sent
    sender.send.assert_not_called()
    session.close.assert_called_once()
