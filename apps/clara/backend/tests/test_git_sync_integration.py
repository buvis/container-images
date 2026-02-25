"""Integration tests for git sync run_sync()."""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-clara-tests-123")
os.environ.setdefault("DATABASE_URL", "postgresql://u:p@localhost/testdb")

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

from clara.git_sync.sync import _hash, run_sync

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VAULT_ID = uuid.uuid4()
CONFIG_ID = uuid.uuid4()


def _make_contact(
    *,
    first_name="Jane",
    last_name="Doe",
    contact_id=None,
    deleted_at=None,
    updated_at=None,
    tags=None,
    contact_methods=None,
    relationships=None,
    activities=None,
    notes_summary=None,
    birthdate=None,
):
    cid = contact_id or uuid.uuid4()
    now = updated_at or datetime.now(UTC)
    c = SimpleNamespace(
        id=cid,
        vault_id=VAULT_ID,
        first_name=first_name,
        last_name=last_name,
        nickname=None,
        birthdate=birthdate,
        gender=None,
        pronouns=None,
        notes_summary=notes_summary,
        favorite=False,
        deleted_at=deleted_at,
        created_at=now,
        updated_at=now,
        tags=tags if tags is not None else [],
        contact_methods=contact_methods if contact_methods is not None else [],
        relationships=relationships if relationships is not None else [],
        activities=activities if activities is not None else [],
    )
    # full_name property
    c.full_name = f"{first_name} {last_name}".strip()
    return c


def _make_config(config_id=None, vault_id=None, subfolder=""):
    return SimpleNamespace(
        id=config_id or CONFIG_ID,
        vault_id=vault_id or VAULT_ID,
        field_mapping_json=None,
        section_mapping_json=None,
        subfolder=subfolder,
        last_sync_at=None,
        last_sync_status=None,
        last_sync_error=None,
    )


def _make_mapping(
    *,
    contact_id,
    markdown_id,
    file_path,
    file_hash,
    config_id=None,
    deleted_at=None,
    last_db_updated_at=None,
    last_file_updated_at=None,
):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        vault_id=VAULT_ID,
        config_id=config_id or CONFIG_ID,
        contact_id=contact_id,
        markdown_id=markdown_id,
        file_path=file_path,
        file_hash=file_hash,
        last_db_updated_at=last_db_updated_at or now,
        last_file_updated_at=last_file_updated_at or now,
        deleted_at=deleted_at,
    )


def _md_content(title="Jane Doe", birthdate=None, tags=None):
    """Build a simple default-mapping markdown string."""
    lines = ["---"]
    lines.append(f"title: {title}")
    lines.append("type: contact")
    if birthdate:
        lines.append(f"birthdate: '{birthdate}'")
    if tags:
        lines.append("tags:")
        for t in tags:
            lines.append(f"  - {t}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _mock_repo(files=None, file_timestamps=None):
    """Create a MagicMock GitRepo with configurable file contents."""
    files = files or {}
    file_timestamps = file_timestamps or {}
    repo = MagicMock()
    repo.clone_or_open.return_value = None
    repo.pull.return_value = []
    repo.list_markdown_files.return_value = list(files.keys())
    repo.read_file.side_effect = lambda p: files[p]
    repo.write_file.return_value = None
    repo.delete_file.return_value = None
    repo.commit_and_push.return_value = True
    repo.file_last_modified.side_effect = lambda p: file_timestamps.get(p)
    return repo


class _QueryChain:
    """Minimal chainable mock for session.query(...).filter(...).all/first/count."""

    def __init__(self, results=None):
        self._results = results if results is not None else []

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return list(self._results)

    def first(self):
        return self._results[0] if self._results else None

    def count(self):
        return len(self._results)

    def get(self, pk):
        for r in self._results:
            if getattr(r, "id", None) == pk:
                return r
        return None


def _mock_session(mappings=None, contacts=None, tags=None):
    """Build a MagicMock session that routes query() calls based on model type.

    Supports:
    - session.query(GitSyncMapping) -> mappings
    - session.query(Contact) -> contacts
    - session.query(Tag) -> tags (or empty)
    - session.query(ActivityParticipant) -> empty
    - session.query(ContactRelationship) -> empty
    - session.query(Activity).get(id) -> None
    - session.add / session.delete / session.flush are no-ops
    """
    mappings = mappings or []
    contacts = contacts or []
    tags = tags or []

    # Import the model classes so we can match on them
    from clara.activities.models import Activity, ActivityParticipant
    from clara.contacts.models import (
        Contact as ContactModel,
    )
    from clara.contacts.models import (
        ContactRelationship,
        RelationshipType,
    )
    from clara.contacts.models import (
        Tag as TagModel,
    )
    from clara.git_sync.models import GitSyncMapping

    def _query_side_effect(model):
        if model is GitSyncMapping:
            return _QueryChain(mappings)
        if model is ContactModel:
            return _QueryChain(contacts)
        if model is TagModel:
            return _QueryChain(tags)
        if model is ActivityParticipant:
            return _QueryChain([])
        if model is ContactRelationship:
            return _QueryChain([])
        if model is Activity:
            return _QueryChain([])
        if model is RelationshipType:
            return _QueryChain([])
        return _QueryChain([])

    session = MagicMock()
    session.query.side_effect = _query_side_effect
    session.add.return_value = None
    session.delete.return_value = None
    session.flush.return_value = None
    return session


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestNewFromFile:
    """Markdown file with no mapping -> creates Contact + mapping."""

    def test_creates_contact_and_mapping(self):
        content = _md_content("Alice Smith")
        files = {"alice-smith.md": content}
        ts = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
        repo = _mock_repo(files, {"alice-smith.md": ts})
        config = _make_config()
        session = _mock_session(mappings=[], contacts=[])

        counts = run_sync(session, config, repo)

        assert counts.get("new_from_file", 0) == 1
        # Contact added to session
        add_calls = session.add.call_args_list
        # Should have added a Contact and a GitSyncMapping (at minimum)
        assert len(add_calls) >= 2
        repo.clone_or_open.assert_called_once()
        repo.pull.assert_called_once()
        repo.commit_and_push.assert_called_once()

    def test_first_sync_matches_existing_contact_by_slug(self):
        """When no mappings exist yet, match file stem to existing contact by slug."""
        contact = _make_contact(first_name="Alice", last_name="Smith")
        content = _md_content("Alice Smith")
        files = {"alice-smith.md": content}
        ts = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
        repo = _mock_repo(files, {"alice-smith.md": ts})
        config = _make_config()
        session = _mock_session(mappings=[], contacts=[contact])

        counts = run_sync(session, config, repo)

        assert counts.get("new_from_file", 0) == 1
        # Should NOT add a new Contact (reused existing), but still adds mapping
        added_types = [
            type(c.args[0]).__name__
            for c in session.add.call_args_list
            if c.args
        ]
        # The matched_contact path skips session.add(contact) + flush
        # so we expect no Contact object to be added (it sets attrs on existing)
        assert "Contact" not in added_types


class TestNewFromDB:
    """DB contact with no mapping -> writes file, creates mapping."""

    def test_writes_file_and_creates_mapping(self):
        contact = _make_contact(first_name="Bob", last_name="Jones")
        # No files in repo, one unmapped contact
        repo = _mock_repo(files={})
        config = _make_config()
        session = _mock_session(mappings=[], contacts=[contact])

        counts = run_sync(session, config, repo)

        assert counts.get("new_from_db", 0) == 1
        repo.write_file.assert_called_once()
        written_path = repo.write_file.call_args[0][0]
        assert written_path == "bob-jones.md"
        # Mapping added
        assert session.add.call_count >= 1

    def test_subfolder_prepended(self):
        contact = _make_contact(first_name="Bob", last_name="Jones")
        repo = _mock_repo(files={})
        config = _make_config(subfolder="people")
        session = _mock_session(mappings=[], contacts=[contact])

        run_sync(session, config, repo)

        written_path = repo.write_file.call_args[0][0]
        assert written_path == "people/bob-jones.md"


class TestUpdateFromFile:
    """File changed, file timestamp newer -> updates contact fields."""

    def test_updates_contact_from_newer_file(self):
        contact_id = uuid.uuid4()
        old_ts = datetime.now(UTC) - timedelta(hours=2)
        contact = _make_contact(
            first_name="Jane",
            last_name="Doe",
            contact_id=contact_id,
            updated_at=old_ts,
        )
        old_content = _md_content("Jane Doe")
        old_hash = _hash(old_content)

        # New file content — title changed
        new_content = _md_content("Janet Doe")
        new_hash = _hash(new_content)
        assert old_hash != new_hash

        mapping = _make_mapping(
            contact_id=contact_id,
            markdown_id="20260101120000",
            file_path="jane-doe.md",
            file_hash=old_hash,
            last_db_updated_at=old_ts,
        )

        files = {"jane-doe.md": new_content}
        file_ts = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
        repo = _mock_repo(files, {"jane-doe.md": file_ts})
        config = _make_config()
        session = _mock_session(mappings=[mapping], contacts=[contact])

        counts = run_sync(session, config, repo)

        assert counts.get("update_from_file", 0) == 1
        # Contact first_name updated
        assert contact.first_name == "Janet"
        assert contact.last_name == "Doe"
        # Mapping hash updated
        assert mapping.file_hash == new_hash


class TestDeleteFile:
    """Mapped contact soft-deleted -> calls repo.delete_file."""

    def test_deletes_file_for_soft_deleted_contact(self):
        contact_id = uuid.uuid4()
        contact = _make_contact(
            first_name="Gone",
            last_name="Person",
            contact_id=contact_id,
            deleted_at=datetime.now(UTC),
        )

        content = _md_content("Gone Person")
        file_hash = _hash(content)
        mapping = _make_mapping(
            contact_id=contact_id,
            markdown_id="20260101120000",
            file_path="gone-person.md",
            file_hash=file_hash,
        )

        files = {"gone-person.md": content}
        repo = _mock_repo(files)
        config = _make_config()
        session = _mock_session(mappings=[mapping], contacts=[contact])

        counts = run_sync(session, config, repo)

        assert counts.get("delete_file", 0) == 1
        repo.delete_file.assert_called_once_with("gone-person.md")
        # Mapping gets soft-deleted
        assert mapping.deleted_at is not None

    def test_skip_when_hash_unchanged(self):
        """File present, hash matches -> SKIP."""
        contact_id = uuid.uuid4()
        contact = _make_contact(contact_id=contact_id)
        content = _md_content("Jane Doe")
        file_hash = _hash(content)
        mapping = _make_mapping(
            contact_id=contact_id,
            markdown_id="20260101120000",
            file_path="jane-doe.md",
            file_hash=file_hash,
        )

        files = {"jane-doe.md": content}
        repo = _mock_repo(files)
        config = _make_config()
        session = _mock_session(mappings=[mapping], contacts=[contact])

        counts = run_sync(session, config, repo)

        assert counts.get("skip", 0) == 1
        assert counts.get("new_from_file", 0) == 0
        repo.write_file.assert_not_called()
        repo.delete_file.assert_not_called()


class TestPartialFailure:
    """One action fails but others succeed."""

    def test_error_in_one_action_doesnt_block_others(self):
        # Two unmapped contacts: first write_file call will raise, second succeeds
        c1 = _make_contact(first_name="Fail", last_name="Contact")
        c2 = _make_contact(first_name="Good", last_name="Contact")
        repo = _mock_repo(files={})
        config = _make_config()
        session = _mock_session(mappings=[], contacts=[c1, c2])

        call_count = 0

        def _write_file_side_effect(path, content):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("disk full")

        repo.write_file.side_effect = _write_file_side_effect

        counts = run_sync(session, config, repo)

        # One succeeded, one failed (swallowed by except)
        assert counts.get("new_from_db", 0) == 1
        # commit_and_push still called
        repo.commit_and_push.assert_called_once()
        # Config still marked ok
        assert config.last_sync_status == "ok"


class TestSyncStateUpdate:
    """run_sync updates config status fields after sync."""

    def test_config_updated_on_success(self):
        repo = _mock_repo(files={})
        config = _make_config()
        session = _mock_session()

        run_sync(session, config, repo)

        assert config.last_sync_status == "ok"
        assert config.last_sync_error is None
        assert config.last_sync_at is not None
