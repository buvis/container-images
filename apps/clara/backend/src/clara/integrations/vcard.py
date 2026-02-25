"""vCard import/export using shared DAV converters."""

import uuid

import vobject
from sqlalchemy.ext.asyncio import AsyncSession

from clara.contacts.models import Address, Contact, ContactMethod
from clara.contacts.repository import ContactRepository
from clara.dav_sync.converters.contact import contact_to_vcard, vcard_to_contact_data

EXPORT_LIMIT = 100_000  # practical upper bound for single-file export


async def import_vcard(
    session: AsyncSession, vault_id: uuid.UUID, vcard_data: str
) -> list[Contact]:
    repo = ContactRepository(session=session, vault_id=vault_id)
    created: list[Contact] = []

    for vcard in vobject.readComponents(vcard_data):
        data = vcard_to_contact_data(vcard)

        contact = await repo.create(**data["contact_fields"])

        for cm_data in data["contact_methods"]:
            session.add(
                ContactMethod(vault_id=vault_id, contact_id=contact.id, **cm_data)
            )

        for addr_data in data["addresses"]:
            session.add(Address(vault_id=vault_id, contact_id=contact.id, **addr_data))

        await session.flush()
        created.append(contact)

    return created


async def export_vcard(session: AsyncSession, vault_id: uuid.UUID) -> str:
    repo = ContactRepository(session=session, vault_id=vault_id)
    contacts, _ = await repo.list(offset=0, limit=EXPORT_LIMIT)
    output_parts: list[str] = []

    for contact in contacts:
        vc = contact_to_vcard(contact)
        output_parts.append(vc.serialize())

    return "\r\n".join(output_parts)
