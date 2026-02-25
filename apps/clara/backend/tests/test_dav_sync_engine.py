"""Unit tests for DAV sync engine classification + execution logic."""

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


def _make_mapping(local_id, remote_uid, etag="etag-1", local_updated_at=None):
    return SimpleNamespace(
        account_id=ACCOUNT_ID,
        entity_type="contact",
        local_id=local_id,
        remote_uid=remote_uid,
        remote_etag=etag,
        remote_href=f"/dav/addressbook/{remote_uid}.vcf",
        local_updated_at=local_updated_at or NOW,
        remote_updated_at=None,
        deleted_at=None,
    )


def _mock_session(mappings, contacts):
    """Build a mock session that handles query(DavSyncMapping) and query(Contact)."""
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


# -- NEW_REMOTE: remote resource with no mapping → creates local entity --


@patch("clara.dav_sync.sync_engine._create_local_from_remote")
def test_new_remote_creates_local_entity(mock_create):
    """Remote vCard not in mappings → classified NEW_REMOTE, local entity created."""
    remote = DavResource(
        uid="new-remote-uid", href="/dav/ab/new.vcf", etag="e1", data=VCARD_DATA
    )
    client = MagicMock()
    client.list_vcards.return_value = [remote]

    account = _make_account()
    session = _mock_session(mappings=[], contacts=[])

    created = _make_contact()
    created.updated_at = NOW
    mock_create.return_value = created

    counts = sync_entity_type(session, client, account, "contact")

    assert counts.get("new_remote") == 1
    mock_create.assert_called_once()
    # A new DavSyncMapping should be added to the session
    session.add.assert_called()
    added = session.add.call_args[0][0]
    assert isinstance(added, DavSyncMapping)
    assert added.remote_uid == "new-remote-uid"


# -- NEW_LOCAL: local entity with no mapping → pushes to remote --


@patch("clara.dav_sync.sync_engine._push_local_to_remote")
def test_new_local_pushes_to_remote(mock_push):
    """Local contact not in mappings → classified NEW_LOCAL, pushed to remote."""
    contact = _make_contact()
    client = MagicMock()
    client.list_vcards.return_value = []

    account = _make_account()
    session = _mock_session(mappings=[], contacts=[contact])

    pushed = DavResource(
        uid=str(contact.id), href="/dav/ab/x.vcf", etag="e-pushed", data=""
    )
    mock_push.return_value = pushed

    counts = sync_entity_type(session, client, account, "contact")

    assert counts.get("new_local") == 1
    mock_push.assert_called_once()
    session.add.assert_called()
    added = session.add.call_args[0][0]
    assert isinstance(added, DavSyncMapping)
    assert added.local_id == contact.id


# -- UNCHANGED: mapping exists, etag same, local not changed --


def test_unchanged_no_action():
    """Mapping exists, etag matches, local not updated → UNCHANGED, no writes."""
    contact_id = uuid.uuid4()
    remote_uid = "unchanged-uid"
    contact = _make_contact(contact_id=contact_id, updated_at=PAST)
    mapping = _make_mapping(
        contact_id, remote_uid, etag="same-etag", local_updated_at=NOW
    )
    remote = DavResource(
        uid=remote_uid, href="/dav/ab/u.vcf", etag="same-etag", data=VCARD_DATA
    )

    client = MagicMock()
    client.list_vcards.return_value = [remote]

    account = _make_account()
    session = _mock_session(mappings=[mapping], contacts=[contact])

    counts = sync_entity_type(session, client, account, "contact")

    assert counts.get("unchanged") == 1
    # No entities should be added or pushed
    session.add.assert_not_called()
    client.put_vcard.assert_not_called()


# -- DELETED_REMOTE: mapping exists but remote gone → soft-deletes local --


def test_deleted_remote_soft_deletes_local():
    """Mapping exists, remote resource gone → DELETED_REMOTE, local soft-deleted."""
    contact_id = uuid.uuid4()
    remote_uid = "gone-uid"
    contact = _make_contact(contact_id=contact_id)
    mapping = _make_mapping(contact_id, remote_uid)

    # Remote list does NOT include this UID
    client = MagicMock()
    client.list_vcards.return_value = []

    account = _make_account()
    session = _mock_session(mappings=[mapping], contacts=[contact])

    counts = sync_entity_type(session, client, account, "contact")

    assert counts.get("deleted_remote") == 1
    # Local entity and mapping should be soft-deleted
    assert contact.deleted_at is not None
    assert mapping.deleted_at is not None
