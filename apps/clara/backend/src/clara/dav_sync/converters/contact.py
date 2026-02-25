from datetime import date
from typing import Any

import vobject

from clara.contacts.models import Contact


def contact_to_vcard(contact: Contact) -> vobject.vCard:
    """Convert a Contact to a vCard object."""
    vc = vobject.vCard()

    vc.add("n")
    vc.n.value = vobject.vcard.Name(family=contact.last_name, given=contact.first_name)
    vc.add("fn")
    vc.fn.value = f"{contact.first_name} {contact.last_name}".strip()

    if contact.nickname:
        vc.add("nickname")
        vc.nickname.value = contact.nickname

    if contact.birthdate:
        vc.add("bday")
        vc.bday.value = contact.birthdate.isoformat()

    if contact.gender:
        vc.add("gender")
        vc.gender.value = contact.gender

    for tag in getattr(contact, "tags", []):
        cat = vc.add("categories")
        cat.value = [tag.name]

    for cm in getattr(contact, "contact_methods", []):
        if cm.type == "email":
            entry = vc.add("email")
            entry.value = cm.value
            if cm.label:
                entry.type_param = cm.label
        elif cm.type == "phone":
            entry = vc.add("tel")
            entry.value = cm.value
            if cm.label:
                entry.type_param = cm.label

    for addr in getattr(contact, "addresses", []):
        adr = vc.add("adr")
        adr.value = vobject.vcard.Address(
            street=addr.line1,
            city=addr.city,
            code=addr.postal_code,
            country=addr.country,
        )
        if addr.label:
            adr.type_param = addr.label

    return vc


def vcard_to_contact_data(vcard: vobject.vCard) -> dict[str, Any]:
    """Parse a vCard into a dict of Contact fields + sub-entity lists.

    Returns dict with keys:
        contact_fields: dict for Contact creation/update
        contact_methods: list of dicts for ContactMethod
        addresses: list of dicts for Address
        tags: list of tag name strings
    """
    first_name = ""
    last_name = ""
    if hasattr(vcard, "n"):
        last_name = vcard.n.value.family or ""
        first_name = vcard.n.value.given or ""
    elif hasattr(vcard, "fn"):
        parts = vcard.fn.value.split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

    birthdate: date | None = None
    if hasattr(vcard, "bday"):
        try:
            bday_str = vcard.bday.value
            if isinstance(bday_str, str):
                birthdate = date.fromisoformat(bday_str)
            else:
                birthdate = bday_str
        except (ValueError, AttributeError):
            pass

    nickname: str | None = None
    if hasattr(vcard, "nickname"):
        nickname = vcard.nickname.value or None

    gender: str | None = None
    if hasattr(vcard, "gender"):
        gender = vcard.gender.value or None

    # Contact methods
    methods: list[dict[str, Any]] = []
    for email_entry in getattr(vcard, "email_list", []):
        methods.append(
            {
                "type": "email",
                "label": _get_type_param(email_entry),
                "value": email_entry.value,
            }
        )
    for tel_entry in getattr(vcard, "tel_list", []):
        methods.append(
            {
                "type": "phone",
                "label": _get_type_param(tel_entry),
                "value": tel_entry.value,
            }
        )

    # Addresses
    addresses: list[dict[str, Any]] = []
    for adr_entry in getattr(vcard, "adr_list", []):
        adr = adr_entry.value
        addresses.append(
            {
                "label": _get_type_param(adr_entry),
                "line1": adr.street or "",
                "city": adr.city or "",
                "postal_code": adr.code or "",
                "country": adr.country or "",
            }
        )

    # Tags from CATEGORIES
    tags: list[str] = []
    if hasattr(vcard, "categories"):
        cat_val = vcard.categories.value
        if isinstance(cat_val, list):
            tags = [t for t in cat_val if isinstance(t, str)]

    return {
        "contact_fields": {
            "first_name": first_name,
            "last_name": last_name,
            "nickname": nickname,
            "birthdate": birthdate,
            "gender": gender,
        },
        "contact_methods": methods,
        "addresses": addresses,
        "tags": tags,
    }


def _get_type_param(entry: Any) -> str:
    params = getattr(entry, "params", {})
    type_list = params.get("TYPE", [])
    if type_list:
        return type_list[0].lower()
    return ""
