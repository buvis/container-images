"""DAV sync engine integration tests: error propagation, conflicts."""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-clara-tests-123")
os.environ.setdefault("DATABASE_URL", "postgresql://u:p@localhost/testdb")

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from clara.dav_sync.client import DavResource
from clara.dav_sync.models import DavSyncMapping
from clara.dav_sync.sync_engine import sync_entity_type

VAULT_ID = uuid.uuid4()
ACCOUNT_ID = uuid.uuid4()
NOW = datetime.now(UTC)
PAST = NOW - timedelta(hours=1)
FUTURE = NOW + timedelta(hours=1)

VCARD_DATA = """\
BEGIN:VCARD
VERSION:3.0
FN:Test User
N:User;Test;;;
UID:remote-uid-1
END:VCARD"""


def _make_account(**overrides):
    defaults = dict(
        id=ACCOUNT_ID,
        vault_id=VAULT_ID,
        carddav_enabled=True,
        caldav_enabled=False,
        carddav_path="/dav/addressbook",
        caldav_path=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_contact(contact_id=None, deleted_at=None, updated_at=None):
    return SimpleNamespace(
        id=contact_id or uuid.uuid4(),
        vault_id=VAULT_ID,
        deleted_at=deleted_at,
        updated_at=updated_at or NOW,
    )


def _make_mapping(local_id, remote_uid, etag="etag-1", local_updated_at=None,
                  remote_updated_at=None):
    return SimpleNamespace(
        account_id=ACCOUNT_ID,
        entity_type="contact",
        local_id=local_id,
        remote_uid=remote_uid,
        remote_etag=etag,
        remote_href=f"/dav/addressbook/{remote_uid}.vcf",
        local_updated_at=local_updated_at or NOW,
        remote_updated_at=remote_updated_at,
        deleted_at=None,
    )


def _mock_session(mappings, contacts):
    session = MagicMock()

    from clara.contacts.models import Contact

    def query_side_effect(model_cls):
        chain = MagicMock()
        if model_cls is DavSyncMapping:
            chain.filter.return_value.all.return_value = mappings
        elif model_cls is Contact:
            chain.filter.return_value.all.return_value = contacts
        else:
            chain.filter.return_value.all.return_value = []
        return chain

    session.query.side_effect = query_side_effect
    return session


# -- Error propagation: converter failure doesn't crash the whole sync --


@patch("clara.dav_sync.sync_engine._create_local_from_remote")
def test_error_in_one_item_does_not_block_others(mock_create):
    """When _create_local_from_remote raises for one resource, the other still syncs.

    The failing item should NOT appear in counts (exception path skips the count bump).
    """
    good_remote = DavResource(uid="good-uid", href="/dav/ab/good.vcf", etag="e1",
                              data=VCARD_DATA)
    bad_remote = DavResource(uid="bad-uid", href="/dav/ab/bad.vcf", etag="e2",
                             data=VCARD_DATA)

    client = MagicMock()
    client.list_vcards.return_value = [bad_remote, good_remote]

    account = _make_account()
    session = _mock_session(mappings=[], contacts=[])

    good_entity = _make_contact()
    good_entity.updated_at = NOW

    # First call (bad) raises, second call (good) succeeds
    mock_create.side_effect = [ValueError("bad vcard parse"), good_entity]

    counts = sync_entity_type(session, client, account, "contact")

    # Only the successful one counted
    assert counts.get("new_remote") == 1
    assert mock_create.call_count == 2
    # The good entity's mapping was added; bad one was not
    session.add.assert_called()
    added = session.add.call_args[0][0]
    assert isinstance(added, DavSyncMapping)
    assert added.remote_uid == "good-uid"


# -- Conflict resolution: last-write-wins by timestamp --


@patch("clara.dav_sync.sync_engine._push_local_to_remote")
@patch("clara.dav_sync.sync_engine._update_local_from_remote")
def test_conflict_local_wins_when_newer(mock_update_local, mock_push):
    """Both sides changed; local updated_at > mapping.remote_updated_at → push local."""
    contact_id = uuid.uuid4()
    remote_uid = "conflict-uid"

    # Local was updated more recently than the remote snapshot
    contact = _make_contact(contact_id=contact_id, updated_at=FUTURE)
    mapping = _make_mapping(
        contact_id, remote_uid, etag="old-etag", local_updated_at=PAST,
        remote_updated_at=NOW,
    )
    # Remote has a different etag → remote changed
    remote = DavResource(uid=remote_uid, href="/dav/ab/c.vcf", etag="new-etag",
                         data=VCARD_DATA)

    client = MagicMock()
    client.list_vcards.return_value = [remote]

    account = _make_account()
    session = _mock_session(mappings=[mapping], contacts=[contact])

    pushed = DavResource(uid=str(contact_id), href="/dav/ab/c.vcf", etag="pushed-etag",
                         data="")
    mock_push.return_value = pushed

    counts = sync_entity_type(session, client, account, "contact")

    assert counts.get("conflict") == 1
    mock_push.assert_called_once()
    mock_update_local.assert_not_called()
    # Mapping etag updated to the pushed version
    assert mapping.remote_etag == "pushed-etag"


@patch("clara.dav_sync.sync_engine._push_local_to_remote")
@patch("clara.dav_sync.sync_engine._update_local_from_remote")
def test_conflict_remote_wins_when_newer(mock_update_local, mock_push):
    """Remote newer than local → pull remote."""
    contact_id = uuid.uuid4()
    remote_uid = "conflict-uid-2"

    # Local older than the remote snapshot time stored in mapping
    contact = _make_contact(contact_id=contact_id, updated_at=PAST)
    mapping = _make_mapping(
        contact_id,
        remote_uid,
        etag="old-etag",
        local_updated_at=PAST - timedelta(hours=1),
        remote_updated_at=FUTURE,
    )
    remote = DavResource(uid=remote_uid, href="/dav/ab/c2.vcf", etag="new-etag",
                         data=VCARD_DATA)

    client = MagicMock()
    client.list_vcards.return_value = [remote]

    account = _make_account()
    session = _mock_session(mappings=[mapping], contacts=[contact])

    counts = sync_entity_type(session, client, account, "contact")

    assert counts.get("conflict") == 1
    mock_update_local.assert_called_once()
    mock_push.assert_not_called()
    assert mapping.remote_etag == "new-etag"


# -- Mixed successes and failures across different action types --


@patch("clara.dav_sync.sync_engine._create_local_from_remote")
@patch("clara.dav_sync.sync_engine._push_local_to_remote")
def test_mixed_success_and_failure_counts(mock_push, mock_create):
    """Mixed results: counts reflect only successes."""
    remote_ok = DavResource(
        uid="r-ok", href="/dav/ab/ok.vcf", etag="e1", data=VCARD_DATA
    )
    remote_bad = DavResource(
        uid="r-bad", href="/dav/ab/bad.vcf", etag="e2", data=VCARD_DATA
    )

    local_contact = _make_contact()

    client = MagicMock()
    client.list_vcards.return_value = [remote_bad, remote_ok]

    account = _make_account()
    session = _mock_session(mappings=[], contacts=[local_contact])

    created_entity = _make_contact()
    created_entity.updated_at = NOW
    # _create_local_from_remote: first call fails, second succeeds
    mock_create.side_effect = [RuntimeError("parse error"), created_entity]

    pushed = DavResource(uid=str(local_contact.id), href="/dav/ab/x.vcf",
                         etag="e-pushed", data="")
    mock_push.return_value = pushed

    counts = sync_entity_type(session, client, account, "contact")

    # 1 new_remote succeeded (the other raised), 1 new_local succeeded
    assert counts.get("new_remote") == 1
    assert counts.get("new_local") == 1
    # Total counted actions = 2, the failed one is absent from counts
    assert sum(counts.values()) == 2
