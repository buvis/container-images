"""Git markdown sync algorithm."""

from __future__ import annotations

import hashlib
import itertools
import uuid
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import structlog
from slugify import slugify
from sqlalchemy.orm import Session

from clara.activities.models import Activity, ActivityParticipant
from clara.contacts.models import (
    Contact,
    ContactMethod,
    ContactRelationship,
    RelationshipType,
    Tag,
)
from clara.git_sync.git_ops import GitRepo
from clara.git_sync.markdown import (
    contact_to_markdown,
    markdown_to_contact_data,
)
from clara.git_sync.models import GitSyncConfig, GitSyncMapping

logger = structlog.get_logger()


class SyncAction(Enum):
    NEW_FROM_FILE = "new_from_file"
    NEW_FROM_DB = "new_from_db"
    UPDATE_FROM_FILE = "update_from_file"
    UPDATE_FROM_DB = "update_from_db"
    DELETE_FILE = "delete_file"
    DELETE_DB = "delete_db"
    SKIP = "skip"


_md_id_counter = itertools.count()


def _generate_markdown_id() -> str:
    """Generate a unique 14-char markdown_id (timestamp + counter suffix)."""
    ts = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    seq = next(_md_id_counter) % 100
    return f"{ts[:12]}{seq:02d}" if seq > 0 else ts


def run_sync(session: Session, config: GitSyncConfig, repo: GitRepo) -> dict[str, int]:
    """Execute full git sync cycle. Returns action counts."""
    vault_id = config.vault_id
    field_mapping = _parse_json(config.field_mapping_json)
    section_mapping = _parse_json(config.section_mapping_json)
    subfolder = config.subfolder or ""

    # Phase 1: PULL
    repo.clone_or_open()
    repo.pull()

    # Phase 2: DIFF
    md_files = repo.list_markdown_files(subfolder)
    md_by_stem: dict[str, str] = {}  # filename stem -> path
    for path in md_files:
        stem = Path(path).stem
        md_by_stem[stem] = path

    # Load mappings
    mappings = (
        session.query(GitSyncMapping)
        .filter(
            GitSyncMapping.config_id == config.id,
            GitSyncMapping.deleted_at.is_(None),
        )
        .all()
    )
    mapping_by_contact: dict[uuid.UUID, GitSyncMapping] = {
        m.contact_id: m for m in mappings
    }
    mapping_by_md_id: dict[str, GitSyncMapping] = {
        m.markdown_id: m for m in mappings
    }

    # Load contacts
    contacts = session.query(Contact).filter(Contact.vault_id == vault_id).all()
    contact_by_id: dict[uuid.UUID, Contact] = {c.id: c for c in contacts}

    actions: list[tuple[SyncAction, dict[str, Any]]] = []

    # Check each markdown file
    for path in md_files:
        content = repo.read_file(path)
        file_hash = _hash(content)
        stem = Path(path).stem

        # Extract markdown_id: try to find it from existing mapping by path
        mapping = None
        for m in mappings:
            if m.file_path == path:
                mapping = m
                break

        if mapping is None:
            mapping = mapping_by_md_id.get(stem)

        if mapping is None:
            # NEW_FROM_FILE
            # First sync heuristic: match by slugified full_name
            matched_contact = None
            if not mappings:  # first sync
                for c in contacts:
                    if (
                        c.deleted_at is None
                        and slugify(c.full_name) == slugify(stem)
                        and c.id not in mapping_by_contact
                    ):
                            matched_contact = c
                            break
            actions.append(
                (
                    SyncAction.NEW_FROM_FILE,
                    {
                        "path": path,
                        "content": content,
                        "file_hash": file_hash,
                        "matched_contact": matched_contact,
                    },
                )
            )
        else:
            contact = contact_by_id.get(mapping.contact_id)
            if contact and contact.deleted_at is not None:
                actions.append(
                    (SyncAction.DELETE_FILE, {"path": path, "mapping": mapping})
                )
            elif mapping.file_hash == file_hash:
                actions.append((SyncAction.SKIP, {}))
            else:
                # File changed — compare timestamps
                file_ts = _parse_git_timestamp(repo.file_last_modified(path))
                db_ts = (
                    contact.updated_at
                    if contact
                    else datetime.min.replace(tzinfo=UTC)
                )
                if file_ts and file_ts > (mapping.last_db_updated_at or db_ts):
                    actions.append(
                        (
                            SyncAction.UPDATE_FROM_FILE,
                            {
                                "path": path,
                                "content": content,
                                "file_hash": file_hash,
                                "contact": contact,
                                "mapping": mapping,
                            },
                        )
                    )
                elif contact:
                    actions.append(
                        (
                            SyncAction.UPDATE_FROM_DB,
                            {"contact": contact, "mapping": mapping},
                        )
                    )
                else:
                    actions.append((SyncAction.SKIP, {}))

    # Check DB contacts with no mapping
    mapped_contact_ids = {m.contact_id for m in mappings}
    for contact in contacts:
        if contact.deleted_at is None and contact.id not in mapped_contact_ids:
            actions.append((SyncAction.NEW_FROM_DB, {"contact": contact}))

    # Check mappings where file is gone
    existing_paths = set(md_files)
    for mapping in mappings:
        if mapping.file_path not in existing_paths:
            contact = contact_by_id.get(mapping.contact_id)
            if contact and contact.deleted_at is None:
                actions.append(
                    (SyncAction.DELETE_DB, {"contact": contact, "mapping": mapping})
                )

    # Phase 3: APPLY
    counts: dict[str, int] = {}
    add_count = 0
    update_count = 0
    delete_count = 0

    for action, data in actions:
        try:
            if action == SyncAction.NEW_FROM_FILE:
                _create_contact_from_file(
                    session, config, repo, vault_id, data, field_mapping, subfolder
                )
                add_count += 1
            elif action == SyncAction.NEW_FROM_DB:
                _create_file_from_contact(
                    session,
                    config,
                    repo,
                    data["contact"],
                    field_mapping,
                    section_mapping,
                    subfolder,
                )
                add_count += 1
            elif action == SyncAction.UPDATE_FROM_FILE:
                _update_contact_from_file(
                    session, vault_id, data, field_mapping, subfolder, repo
                )
                update_count += 1
            elif action == SyncAction.UPDATE_FROM_DB:
                _update_file_from_contact(
                    session, config, repo, data, field_mapping, section_mapping
                )
                update_count += 1
            elif action == SyncAction.DELETE_FILE:
                repo.delete_file(data["path"])
                data["mapping"].deleted_at = datetime.now(UTC)
                delete_count += 1
            elif action == SyncAction.DELETE_DB:
                data["contact"].deleted_at = datetime.now(UTC)
                data["mapping"].deleted_at = datetime.now(UTC)
                delete_count += 1
            counts[action.value] = counts.get(action.value, 0) + 1
        except Exception:
            logger.exception("git_sync_action_failed", action=action.value)

    session.flush()

    # Phase 4: PUSH
    message = (
        f"Sync: add {add_count}, update {update_count}, delete {delete_count} contacts"
    )
    repo.commit_and_push(message)

    # Phase 5: UPDATE STATE
    config.last_sync_at = datetime.now(UTC)
    config.last_sync_status = "ok"
    config.last_sync_error = None
    session.flush()

    return counts


def _create_contact_from_file(
    session: Session,
    config: GitSyncConfig,
    repo: GitRepo,
    vault_id: uuid.UUID,
    data: dict[str, Any],
    field_mapping: list[dict[str, Any]] | None,
    subfolder: str,
) -> None:
    content = data["content"]
    file_hash = data["file_hash"]
    path = data["path"]
    matched_contact = data.get("matched_contact")

    parsed = markdown_to_contact_data(content, field_mapping)

    if matched_contact:
        contact = matched_contact
        for k, v in parsed["contact_fields"].items():
            setattr(contact, k, v)
    else:
        contact = Contact(vault_id=vault_id, **parsed["contact_fields"])
        session.add(contact)
        session.flush()

    _apply_sub_entities(session, vault_id, contact, parsed)
    _import_photo(session, vault_id, contact.id, parsed, subfolder, repo)

    now = datetime.now(UTC)
    md_id = _generate_markdown_id()
    mapping = GitSyncMapping(
        vault_id=vault_id,
        config_id=config.id,
        contact_id=contact.id,
        markdown_id=md_id,
        file_path=path,
        last_db_updated_at=contact.updated_at or now,
        last_file_updated_at=now,
        file_hash=file_hash,
    )
    session.add(mapping)


def _create_file_from_contact(
    session: Session,
    config: GitSyncConfig,
    repo: GitRepo,
    contact: Contact,
    field_mapping: list[dict[str, Any]] | None,
    section_mapping: list[dict[str, Any]] | None,
    subfolder: str,
) -> None:
    now = datetime.now(UTC)
    md_id = _generate_markdown_id()
    name_slug = slugify(contact.full_name)
    filename = f"{name_slug}.md"
    path = f"{subfolder}/{filename}" if subfolder else filename

    # Export photo
    photo_rel = _export_photo(session, contact, name_slug, subfolder, repo)
    if photo_rel:
        contact._photo_path = photo_rel  # type: ignore[attr-defined]

    content = contact_to_markdown(contact, field_mapping, section_mapping, md_id)
    repo.write_file(path, content)

    mapping = GitSyncMapping(
        vault_id=config.vault_id,
        config_id=config.id,
        contact_id=contact.id,
        markdown_id=md_id,
        file_path=path,
        last_db_updated_at=contact.updated_at or now,
        last_file_updated_at=now,
        file_hash=_hash(content),
    )
    session.add(mapping)


def _update_contact_from_file(
    session: Session,
    vault_id: uuid.UUID,
    data: dict[str, Any],
    field_mapping: list[dict[str, Any]] | None,
    subfolder: str,
    repo: GitRepo,
) -> None:
    contact = data["contact"]
    content = data["content"]
    mapping = data["mapping"]

    parsed = markdown_to_contact_data(content, field_mapping)
    for k, v in parsed["contact_fields"].items():
        setattr(contact, k, v)

    _apply_sub_entities(session, vault_id, contact, parsed)
    _import_photo(session, vault_id, contact.id, parsed, subfolder, repo)

    now = datetime.now(UTC)
    mapping.file_hash = data["file_hash"]
    mapping.last_file_updated_at = now
    mapping.last_db_updated_at = contact.updated_at or now


def _update_file_from_contact(
    session: Session,
    config: GitSyncConfig,
    repo: GitRepo,
    data: dict[str, Any],
    field_mapping: list[dict[str, Any]] | None,
    section_mapping: list[dict[str, Any]] | None,
) -> None:
    contact = data["contact"]
    mapping = data["mapping"]
    subfolder = config.subfolder or ""

    # Export photo
    name_slug = slugify(contact.full_name)
    photo_rel = _export_photo(session, contact, name_slug, subfolder, repo)
    if photo_rel:
        contact._photo_path = photo_rel

    content = contact_to_markdown(
        contact, field_mapping, section_mapping, mapping.markdown_id
    )
    repo.write_file(mapping.file_path, content)

    now = datetime.now(UTC)
    mapping.file_hash = _hash(content)
    mapping.last_db_updated_at = contact.updated_at or now
    mapping.last_file_updated_at = now


def _apply_sub_entities(
    session: Session,
    vault_id: uuid.UUID,
    contact: Contact,
    parsed: dict[str, Any],
) -> None:
    """Apply contact_methods, addresses, tags, activities, relationships."""
    # Full replace contact methods
    for cm in list(getattr(contact, "contact_methods", [])):
        session.delete(cm)
    for cm_data in parsed.get("contact_methods", []):
        session.add(ContactMethod(vault_id=vault_id, contact_id=contact.id, **cm_data))

    # Tags
    contact.tags.clear()
    for tag_name in parsed.get("tags", []):
        tag = (
            session.query(Tag)
            .filter(Tag.vault_id == vault_id, Tag.name == tag_name)
            .first()
        )
        if not tag:
            tag = Tag(vault_id=vault_id, name=tag_name)
            session.add(tag)
            session.flush()
        contact.tags.append(tag)

    # Activities — full replace participants, create new activities
    for ap in list(
        session.query(ActivityParticipant)
        .filter(ActivityParticipant.contact_id == contact.id)
        .all()
    ):
        activity = session.query(Activity).get(ap.activity_id)
        session.delete(ap)
        # Delete activity if this contact was the only participant
        if activity:
            remaining = (
                session.query(ActivityParticipant)
                .filter(
                    ActivityParticipant.activity_id == activity.id,
                    ActivityParticipant.contact_id != contact.id,
                )
                .count()
            )
            if remaining == 0:
                session.delete(activity)

    for act_data in parsed.get("activities", []):
        activity = Activity(
            vault_id=vault_id,
            title=act_data["title"],
            happened_at=act_data.get("happened_at"),
        )
        session.add(activity)
        session.flush()
        session.add(
            ActivityParticipant(
                vault_id=vault_id,
                activity_id=activity.id,
                contact_id=contact.id,
                role="participant",
            )
        )

    # Relationships — full replace
    for rel in list(
        session.query(ContactRelationship)
        .filter(ContactRelationship.contact_id == contact.id)
        .all()
    ):
        session.delete(rel)

    for rel_data in parsed.get("relationships", []):
        name = rel_data.get("name", "")
        parts = name.strip().split(" ", 1)
        first = parts[0]
        last = parts[1] if len(parts) > 1 else ""
        other = (
            session.query(Contact)
            .filter(
                Contact.vault_id == vault_id,
                Contact.first_name == first,
                Contact.last_name == last,
                Contact.deleted_at.is_(None),
            )
            .first()
        )
        if not other:
            logger.warning(
                "git_sync_relationship_skip",
                name=name,
                reason="contact not found",
            )
            continue

        type_name = rel_data.get("relationship_type_name", "")
        rel_type = (
            session.query(RelationshipType)
            .filter(
                RelationshipType.vault_id == vault_id,
                RelationshipType.name == type_name,
            )
            .first()
        )
        if not rel_type:
            rel_type = RelationshipType(vault_id=vault_id, name=type_name)
            session.add(rel_type)
            session.flush()

        session.add(
            ContactRelationship(
                vault_id=vault_id,
                contact_id=contact.id,
                other_contact_id=other.id,
                relationship_type_id=rel_type.id,
            )
        )

    session.flush()


def _export_photo(
    session: Session,
    contact: Contact,
    name_slug: str,
    subfolder: str,
    repo: GitRepo,
) -> str | None:
    """Export contact photo to git repo assets/ folder. Returns relative asset path."""
    from clara.config import get_settings
    from clara.files.models import File

    photo_file_id = getattr(contact, "photo_file_id", None)
    if not photo_file_id:
        return None
    file_rec = session.get(File, photo_file_id)
    if not file_rec:
        return None
    storage_path = Path(get_settings().storage_path) / file_rec.storage_key
    if not storage_path.exists():
        return None
    photo_data = storage_path.read_bytes()
    ext = Path(file_rec.filename).suffix or ".jpeg"
    asset_rel = f"assets/{name_slug}{ext}"
    asset_path = f"{subfolder}/{asset_rel}" if subfolder else asset_rel
    repo.write_binary(asset_path, photo_data)
    return asset_rel


def _import_photo(
    session: Session,
    vault_id: uuid.UUID,
    contact_id: uuid.UUID,
    parsed: dict[str, Any],
    subfolder: str,
    repo: GitRepo,
) -> None:
    """Import photo from git repo into local file storage."""
    from clara.config import get_settings
    from clara.files.models import File

    photo_path = parsed.get("photo_path")
    if not photo_path:
        return
    full_path = f"{subfolder}/{photo_path}" if subfolder else photo_path
    try:
        photo_data = repo.read_binary(full_path)
    except Exception:
        return
    filename = Path(photo_path).name
    storage_key = f"{uuid.uuid4()}/{filename}"
    dest = Path(get_settings().storage_path) / storage_key
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(photo_data)
    file_rec = File(
        vault_id=vault_id,
        uploader_id=uuid.UUID(int=0),
        storage_key=storage_key,
        filename=filename,
        mime_type="image/jpeg",
        size_bytes=len(photo_data),
    )
    session.add(file_rec)
    session.flush()
    contact = session.get(Contact, contact_id)
    if contact:
        contact.photo_file_id = file_rec.id


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def _parse_git_timestamp(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _parse_json(json_str: str | None) -> list[dict[str, Any]] | None:
    if not json_str:
        return None
    import json

    try:
        data = json.loads(json_str)
        return data if isinstance(data, list) else None
    except (json.JSONDecodeError, TypeError):
        return None
