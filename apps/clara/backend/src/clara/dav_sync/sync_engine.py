"""Core DAV sync algorithm — per account, per entity type."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import structlog
import vobject
from icalendar import Calendar
from sqlalchemy.orm import Session

from clara.activities.models import Activity
from clara.contacts.models import Address, Contact, ContactMethod, Tag
from clara.dav_sync.client import DavClient, DavResource
from clara.dav_sync.converters.activity import (
    activity_to_vevent,
    vevent_to_activity_data,
)
from clara.dav_sync.converters.contact import contact_to_vcard, vcard_to_contact_data
from clara.dav_sync.converters.reminder import reminder_to_vtodo, vtodo_to_reminder_data
from clara.dav_sync.converters.task import task_to_vtodo, vtodo_to_task_data
from clara.dav_sync.models import DavSyncAccount, DavSyncMapping
from clara.reminders.models import Reminder
from clara.tasks.models import Task

logger = structlog.get_logger()


class SyncAction(Enum):
    NEW_REMOTE = "new_remote"
    NEW_LOCAL = "new_local"
    UPDATED_REMOTE = "updated_remote"
    UPDATED_LOCAL = "updated_local"
    DELETED_LOCAL = "deleted_local"
    DELETED_REMOTE = "deleted_remote"
    CONFLICT = "conflict"
    UNCHANGED = "unchanged"


@dataclass
class SyncItem:
    action: SyncAction
    mapping: DavSyncMapping | None
    local_entity: Any | None
    remote_resource: DavResource | None


def sync_entity_type(
    session: Session,
    client: DavClient,
    account: DavSyncAccount,
    entity_type: str,
) -> dict[str, int]:
    """Sync one entity type for an account. Returns action counts."""
    vault_id = account.vault_id

    # Fetch remote resources
    if entity_type == "contact":
        if not account.carddav_enabled or not account.carddav_path:
            return {}
        remote_resources = client.list_vcards(account.carddav_path)
    else:
        if not account.caldav_enabled or not account.caldav_path:
            return {}
        remote_resources = client.list_events(account.caldav_path)

    remote_by_uid: dict[str, DavResource] = {r.uid: r for r in remote_resources}

    # Fetch mappings
    mappings = (
        session.query(DavSyncMapping)
        .filter(
            DavSyncMapping.account_id == account.id,
            DavSyncMapping.entity_type == entity_type,
            DavSyncMapping.deleted_at.is_(None),
        )
        .all()
    )
    mapping_by_local: dict[uuid.UUID, DavSyncMapping] = {
        m.local_id: m for m in mappings
    }
    mapping_by_remote: dict[str, DavSyncMapping] = {m.remote_uid: m for m in mappings}

    # Fetch local entities
    model_cls = _get_model_class(entity_type)
    local_entities = (
        session.query(model_cls).filter(model_cls.vault_id == vault_id).all()
    )
    # Include soft-deleted for detecting local deletions
    local_by_id: dict[uuid.UUID, Any] = {e.id: e for e in local_entities}

    # Classify
    items: list[SyncItem] = []

    # Check mapped items
    for mapping in mappings:
        local = local_by_id.get(mapping.local_id)
        remote = remote_by_uid.get(mapping.remote_uid)

        if local and local.deleted_at is not None:
            items.append(SyncItem(SyncAction.DELETED_LOCAL, mapping, local, remote))
        elif not remote:
            items.append(SyncItem(SyncAction.DELETED_REMOTE, mapping, local, None))
        elif local and remote:
            remote_changed = mapping.remote_etag and remote.etag != mapping.remote_etag
            local_changed = local.updated_at > mapping.local_updated_at
            if remote_changed and local_changed:
                items.append(SyncItem(SyncAction.CONFLICT, mapping, local, remote))
            elif remote_changed:
                items.append(
                    SyncItem(SyncAction.UPDATED_REMOTE, mapping, local, remote)
                )
            elif local_changed:
                items.append(SyncItem(SyncAction.UPDATED_LOCAL, mapping, local, remote))
            else:
                items.append(SyncItem(SyncAction.UNCHANGED, mapping, local, remote))

    # New remote (UID not in any mapping)
    for uid, resource in remote_by_uid.items():
        if uid not in mapping_by_remote:
            items.append(SyncItem(SyncAction.NEW_REMOTE, None, None, resource))

    # New local (entity with no mapping and not soft-deleted)
    for entity in local_entities:
        if entity.deleted_at is None and entity.id not in mapping_by_local:
            items.append(SyncItem(SyncAction.NEW_LOCAL, None, entity, None))

    # Execute
    counts: dict[str, int] = {}
    for item in items:
        try:
            _execute_sync_item(session, client, account, entity_type, item)
            counts[item.action.value] = counts.get(item.action.value, 0) + 1
        except Exception:
            logger.exception(
                "sync_item_failed",
                entity_type=entity_type,
                action=item.action.value,
                account_id=str(account.id),
            )

    session.flush()
    return counts


def _execute_sync_item(
    session: Session,
    client: DavClient,
    account: DavSyncAccount,
    entity_type: str,
    item: SyncItem,
) -> None:
    vault_id = account.vault_id

    if item.action == SyncAction.NEW_REMOTE:
        if not item.remote_resource:
            return
        entity = _create_local_from_remote(
            session, vault_id, entity_type, item.remote_resource
        )
        if entity:
            mapping = DavSyncMapping(
                vault_id=vault_id,
                account_id=account.id,
                entity_type=entity_type,
                local_id=entity.id,
                remote_uid=item.remote_resource.uid,
                remote_etag=item.remote_resource.etag,
                remote_href=item.remote_resource.href,
                local_updated_at=entity.updated_at or datetime.now(UTC),
                remote_updated_at=datetime.now(UTC),
            )
            session.add(mapping)

    elif item.action == SyncAction.NEW_LOCAL:
        if not item.local_entity:
            return
        resource = _push_local_to_remote(
            client, account, entity_type, item.local_entity
        )
        if resource:
            mapping = DavSyncMapping(
                vault_id=vault_id,
                account_id=account.id,
                entity_type=entity_type,
                local_id=item.local_entity.id,
                remote_uid=resource.uid,
                remote_etag=resource.etag,
                remote_href=resource.href,
                local_updated_at=item.local_entity.updated_at or datetime.now(UTC),
            )
            session.add(mapping)

    elif item.action == SyncAction.UPDATED_REMOTE:
        if not (item.mapping and item.remote_resource and item.local_entity):
            return
        _update_local_from_remote(
            session, vault_id, entity_type, item.local_entity, item.remote_resource
        )
        item.mapping.remote_etag = item.remote_resource.etag
        item.mapping.remote_updated_at = datetime.now(UTC)
        item.mapping.local_updated_at = item.local_entity.updated_at or datetime.now(
            UTC
        )

    elif item.action == SyncAction.UPDATED_LOCAL:
        if not (item.mapping and item.local_entity):
            return
        resource = _push_local_to_remote(
            client, account, entity_type, item.local_entity
        )
        if resource:
            item.mapping.remote_etag = resource.etag
            item.mapping.remote_href = resource.href
            item.mapping.local_updated_at = (
                item.local_entity.updated_at or datetime.now(UTC)
            )

    elif item.action == SyncAction.CONFLICT:
        # Last-write-wins by timestamp
        if not (item.mapping and item.local_entity and item.remote_resource):
            return
        local_time = item.local_entity.updated_at or datetime.min.replace(tzinfo=UTC)
        remote_time = item.mapping.remote_updated_at or datetime.min.replace(tzinfo=UTC)
        if local_time >= remote_time:
            resource = _push_local_to_remote(
                client, account, entity_type, item.local_entity
            )
            if resource:
                item.mapping.remote_etag = resource.etag
                item.mapping.local_updated_at = local_time
        else:
            _update_local_from_remote(
                session, vault_id, entity_type, item.local_entity, item.remote_resource
            )
            item.mapping.remote_etag = item.remote_resource.etag
            item.mapping.remote_updated_at = datetime.now(UTC)
            item.mapping.local_updated_at = (
                item.local_entity.updated_at or datetime.now(UTC)
            )

    elif item.action == SyncAction.DELETED_LOCAL:
        if not item.mapping:
            return
        if item.remote_resource:
            _delete_remote(client, account, entity_type, item.remote_resource)
        item.mapping.deleted_at = datetime.now(UTC)

    elif item.action == SyncAction.DELETED_REMOTE:
        if not (item.mapping and item.local_entity):
            return
        item.local_entity.deleted_at = datetime.now(UTC)
        item.mapping.deleted_at = datetime.now(UTC)


def _get_model_class(entity_type: str) -> type[Any]:
    return {
        "contact": Contact,
        "activity": Activity,
        "task": Task,
        "reminder": Reminder,
    }[entity_type]


def _create_local_from_remote(
    session: Session, vault_id: uuid.UUID, entity_type: str, resource: DavResource
) -> Any | None:
    if entity_type == "contact":
        vc = vobject.readOne(resource.data)
        data = vcard_to_contact_data(vc)
        contact = Contact(vault_id=vault_id, **data["contact_fields"])
        session.add(contact)
        session.flush()
        for cm_data in data["contact_methods"]:
            session.add(
                ContactMethod(vault_id=vault_id, contact_id=contact.id, **cm_data)
            )
        for addr_data in data["addresses"]:
            session.add(Address(vault_id=vault_id, contact_id=contact.id, **addr_data))
        for tag_name in data["tags"]:
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
        session.flush()
        return contact

    cal = Calendar.from_ical(resource.data)
    for component in cal.walk():
        if entity_type == "activity" and component.name == "VEVENT":
            data = vevent_to_activity_data(component)
            activity = Activity(vault_id=vault_id, **data["activity_fields"])
            session.add(activity)
            session.flush()
            return activity
        if component.name == "VTODO":
            # Disambiguate: RRULE → reminder, else → task
            clara_type = str(
                component.get("x-clara-entity-type", "")
            )
            has_rrule = component.get("rrule") is not None
            if entity_type == "reminder" or (
                entity_type not in ("task",) and (clara_type == "reminder" or has_rrule)
            ):
                data = vtodo_to_reminder_data(component)
                reminder = Reminder(vault_id=vault_id, **data)
                session.add(reminder)
                session.flush()
                return reminder
            if entity_type == "task" or clara_type == "task" or not has_rrule:
                data = vtodo_to_task_data(component)
                task = Task(vault_id=vault_id, **data)
                session.add(task)
                session.flush()
                return task
    return None


def _update_local_from_remote(
    session: Session,
    vault_id: uuid.UUID,
    entity_type: str,
    entity: Any,
    resource: DavResource,
) -> None:
    if entity_type == "contact":
        vc = vobject.readOne(resource.data)
        data = vcard_to_contact_data(vc)
        for key, value in data["contact_fields"].items():
            setattr(entity, key, value)
        # Full replace sub-entities
        for cm in list(entity.contact_methods):
            session.delete(cm)
        for cm_data in data["contact_methods"]:
            session.add(
                ContactMethod(vault_id=vault_id, contact_id=entity.id, **cm_data)
            )
        for addr in list(entity.addresses):
            session.delete(addr)
        for addr_data in data["addresses"]:
            session.add(Address(vault_id=vault_id, contact_id=entity.id, **addr_data))
        entity.tags.clear()
        for tag_name in data["tags"]:
            tag = (
                session.query(Tag)
                .filter(Tag.vault_id == vault_id, Tag.name == tag_name)
                .first()
            )
            if not tag:
                tag = Tag(vault_id=vault_id, name=tag_name)
                session.add(tag)
                session.flush()
            entity.tags.append(tag)
        return

    cal = Calendar.from_ical(resource.data)
    for component in cal.walk():
        if entity_type == "activity" and component.name == "VEVENT":
            data = vevent_to_activity_data(component)
            for key, value in data["activity_fields"].items():
                setattr(entity, key, value)
            return
        if entity_type == "task" and component.name == "VTODO":
            data = vtodo_to_task_data(component)
            for key, value in data.items():
                setattr(entity, key, value)
            return
        if entity_type == "reminder" and component.name == "VTODO":
            data = vtodo_to_reminder_data(component)
            for key, value in data.items():
                setattr(entity, key, value)
            return


def _push_local_to_remote(
    client: DavClient, account: DavSyncAccount, entity_type: str, entity: Any
) -> DavResource | None:
    uid = str(entity.id)

    if entity_type == "contact":
        if not account.carddav_path:
            return None
        vc = contact_to_vcard(entity)
        vc.add("uid")
        vc.uid.value = uid
        vcard_text = vc.serialize()
        etag = client.put_vcard(account.carddav_path, uid, vcard_text)
        return DavResource(
            uid=uid,
            href=f"{account.carddav_path}/{uid}.vcf",
            etag=etag,
            data=vcard_text,
        )

    if not account.caldav_path:
        return None

    cal = Calendar()
    cal.add("prodid", "-//CLARA//EN")
    cal.add("version", "2.0")

    if entity_type == "activity":
        event = activity_to_vevent(entity)
        event.add("uid", uid)
        cal.add_component(event)
    elif entity_type == "task":
        todo = task_to_vtodo(entity)
        todo.add("uid", uid)
        cal.add_component(todo)
    elif entity_type == "reminder":
        todo = reminder_to_vtodo(entity)
        todo.add("uid", uid)
        cal.add_component(todo)

    ical_text = cal.to_ical().decode()
    etag = client.put_event(account.caldav_path, uid, ical_text)
    return DavResource(uid=uid, href="", etag=etag, data=ical_text)


def _delete_remote(
    client: DavClient, account: DavSyncAccount, entity_type: str, resource: DavResource
) -> None:
    if entity_type == "contact":
        client.delete_vcard(resource.href, resource.etag)
    else:
        client.delete_event(resource.href)
