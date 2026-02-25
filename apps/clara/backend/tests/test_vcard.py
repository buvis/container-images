import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from clara.integrations.vcard import export_vcard, import_vcard


async def test_export_vcard(db_session: AsyncSession):
    from clara.contacts.repository import ContactRepository

    vault_id = uuid.uuid4()
    repo = ContactRepository(session=db_session, vault_id=vault_id)
    await repo.create(first_name="Alice", last_name="Smith")

    result = await export_vcard(db_session, vault_id)

    assert "BEGIN:VCARD" in result
    assert "END:VCARD" in result
    assert "Alice" in result
    assert "Smith" in result


async def test_import_vcard(db_session: AsyncSession):
    vcard_data = (
        "BEGIN:VCARD\r\n"
        "VERSION:3.0\r\n"
        "N:Doe;Jane;;;\r\n"
        "FN:Jane Doe\r\n"
        "EMAIL;TYPE=home:jane@example.com\r\n"
        "TEL;TYPE=cell:+1234567890\r\n"
        "END:VCARD\r\n"
    )
    vault_id = uuid.uuid4()

    created = await import_vcard(db_session, vault_id, vcard_data)

    assert len(created) == 1
    contact = created[0]
    assert contact.first_name == "Jane"
    assert contact.last_name == "Doe"


async def test_import_multiple_vcards(db_session: AsyncSession):
    vcard_data = (
        "BEGIN:VCARD\r\n"
        "VERSION:3.0\r\n"
        "N:Smith;Alice;;;\r\n"
        "FN:Alice Smith\r\n"
        "END:VCARD\r\n"
        "BEGIN:VCARD\r\n"
        "VERSION:3.0\r\n"
        "N:Jones;Bob;;;\r\n"
        "FN:Bob Jones\r\n"
        "END:VCARD\r\n"
    )
    vault_id = uuid.uuid4()

    created = await import_vcard(db_session, vault_id, vcard_data)

    assert len(created) == 2
    names = {c.first_name for c in created}
    assert names == {"Alice", "Bob"}
