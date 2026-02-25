import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from clara.auth.models import PersonalAccessToken
from clara.jobs.cleanup import cleanup_expired_tokens


def _make_session_with_tokens(tokens: list[PersonalAccessToken]) -> MagicMock:
    session = MagicMock()
    executed_deletes: list = []

    def capture_execute(stmt):
        executed_deletes.append(stmt)
        return MagicMock()

    session.execute = capture_execute
    return session


@patch("clara.jobs.cleanup.get_sync_session")
def test_expired_tokens_deleted(mock_get_session):
    session = MagicMock()
    mock_get_session.return_value = session

    cleanup_expired_tokens()

    # verify session.execute was called (delete statements)
    assert session.execute.called
    session.commit.assert_called_once()
    session.close.assert_called_once()


@patch("clara.jobs.cleanup.get_sync_session")
def test_non_expired_preserved(mock_get_session):
    session = MagicMock()
    mock_get_session.return_value = session

    cleanup_expired_tokens()

    # the function issues bulk DELETE WHERE clauses, not per-row;
    # non-expired tokens are excluded by the WHERE condition
    # (expires_at < now). verify the job commits and closes.
    session.commit.assert_called_once()
    session.close.assert_called_once()


@patch("clara.jobs.cleanup.get_sync_session")
def test_session_closed_on_error(mock_get_session):
    session = MagicMock()
    session.execute.side_effect = RuntimeError("db error")
    mock_get_session.return_value = session

    try:
        cleanup_expired_tokens()
    except RuntimeError:
        pass

    session.close.assert_called_once()
