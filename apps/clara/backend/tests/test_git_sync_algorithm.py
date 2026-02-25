import hashlib
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-clara-tests-123")
os.environ.setdefault("DATABASE_URL", "postgresql://u:p@localhost/testdb")

from datetime import UTC, datetime

from clara.git_sync.sync import SyncAction, _hash, _parse_git_timestamp, _parse_json

# -- _hash --


def test_hash_sha256():
    content = "hello world"
    expected = hashlib.sha256(content.encode()).hexdigest()
    assert _hash(content) == expected


def test_hash_empty_string():
    expected = hashlib.sha256(b"").hexdigest()
    assert _hash("") == expected


# -- _parse_git_timestamp --


def test_parse_git_timestamp_valid_iso():
    result = _parse_git_timestamp("2025-06-15T10:30:00+00:00")
    assert isinstance(result, datetime)
    assert result == datetime(2025, 6, 15, 10, 30, 0, tzinfo=UTC)


def test_parse_git_timestamp_none():
    assert _parse_git_timestamp(None) is None


def test_parse_git_timestamp_invalid():
    assert _parse_git_timestamp("not-a-date") is None


# -- _parse_json --


def test_parse_json_valid_list():
    result = _parse_json('[{"key": "value"}, {"a": 1}]')
    assert result == [{"key": "value"}, {"a": 1}]


def test_parse_json_none():
    assert _parse_json(None) is None


def test_parse_json_invalid():
    assert _parse_json("{bad json") is None


def test_parse_json_non_list():
    assert _parse_json('{"key": "value"}') is None


# -- SyncAction enum --


def test_sync_action_values():
    assert SyncAction.NEW_FROM_FILE.value == "new_from_file"
    assert SyncAction.NEW_FROM_DB.value == "new_from_db"
    assert SyncAction.UPDATE_FROM_FILE.value == "update_from_file"
    assert SyncAction.UPDATE_FROM_DB.value == "update_from_db"
    assert SyncAction.DELETE_FILE.value == "delete_file"
    assert SyncAction.DELETE_DB.value == "delete_db"
    assert SyncAction.SKIP.value == "skip"
    assert len(SyncAction) == 7
