from datetime import date
from types import SimpleNamespace

from clara.git_sync.markdown import (
    _parse_activities_from_section,
    _parse_relationships_from_section,
    contact_to_markdown,
    markdown_to_contact_data,
)


def _tag(name):
    return SimpleNamespace(name=name)


def _cm(type_, value):
    return SimpleNamespace(type=type_, value=value)


def _activity(title, happened_at):
    return SimpleNamespace(title=title, happened_at=happened_at)


def _relationship(other_first, other_last, rel_name):
    return SimpleNamespace(
        other_contact=SimpleNamespace(first_name=other_first, last_name=other_last),
        relationship_type=SimpleNamespace(name=rel_name),
    )


def _contact(
    first="Jane",
    last="Doe",
    birthdate=None,
    nickname=None,
    notes_summary=None,
    tags=None,
    contact_methods=None,
    activities=None,
    relationships=None,
):
    return SimpleNamespace(
        first_name=first,
        last_name=last,
        birthdate=birthdate,
        nickname=nickname,
        notes_summary=notes_summary,
        tags=tags or [],
        contact_methods=contact_methods or [],
        activities=activities or [],
        relationships=relationships or [],
    )


# ── round-trip with default mapping ──────────────────────────────────


def test_round_trip_default_mapping():
    c = _contact(
        first="Alice",
        last="Smith",
        birthdate=date(1990, 5, 15),
        tags=[_tag("friend"), _tag("work")],
        contact_methods=[_cm("email", "alice@example.com"), _cm("phone", "+1234")],
        notes_summary="Met at conference.",
    )
    md = contact_to_markdown(c)
    data = markdown_to_contact_data(md)

    assert data["contact_fields"]["first_name"] == "Alice"
    assert data["contact_fields"]["last_name"] == "Smith"
    assert data["contact_fields"]["birthdate"] == date(1990, 5, 15)
    assert data["tags"] == ["friend", "work"]
    emails = [m for m in data["contact_methods"] if m["type"] == "email"]
    phones = [m for m in data["contact_methods"] if m["type"] == "phone"]
    assert len(emails) == 1
    assert emails[0]["value"] == "alice@example.com"
    assert len(phones) == 1
    assert phones[0]["value"] == "+1234"
    assert data["sections"]["Notes"] == "Met at conference."


# ── minimal contact (just name) ─────────────────────────────────────


def test_minimal_contact():
    c = _contact(first="Bob", last="")
    md = contact_to_markdown(c)
    data = markdown_to_contact_data(md)

    assert data["contact_fields"]["first_name"] == "Bob"
    assert data["contact_fields"]["last_name"] == ""
    assert data["tags"] == []
    assert data["contact_methods"] == []
    assert data["addresses"] == []


# ── full contact with all relations ──────────────────────────────────


def test_full_contact():
    c = _contact(
        first="Charlie",
        last="Brown",
        birthdate=date(1985, 12, 1),
        tags=[_tag("vip")],
        contact_methods=[
            _cm("email", "c1@test.com"),
            _cm("email", "c2@test.com"),
            _cm("phone", "+111"),
            _cm("phone", "+222"),
        ],
        notes_summary="Important client.",
        activities=[
            _activity("Lunch", date(2025, 1, 10)),
            _activity("Call", date(2025, 2, 5)),
        ],
        relationships=[_relationship("Lucy", "Van Pelt", "friend")],
    )
    md = contact_to_markdown(c)

    # frontmatter assertions via re-parse
    data = markdown_to_contact_data(md)
    assert data["contact_fields"]["first_name"] == "Charlie"
    assert data["contact_fields"]["birthdate"] == date(1985, 12, 1)
    assert data["tags"] == ["vip"]

    # multiple emails/phones come back as lists
    emails = [m for m in data["contact_methods"] if m["type"] == "email"]
    phones = [m for m in data["contact_methods"] if m["type"] == "phone"]
    assert len(emails) == 2
    assert {e["value"] for e in emails} == {"c1@test.com", "c2@test.com"}
    assert len(phones) == 2

    # body sections
    assert "Important client." in data["sections"].get("Notes", "")
    assert "Timeline" in data["sections"]
    assert "2025-01-10: Lunch" in data["sections"]["Timeline"]
    assert "Relationships" in data["sections"]
    assert "Lucy Van Pelt (friend)" in data["sections"]["Relationships"]


# ── parse hand-written markdown ──────────────────────────────────────


def test_markdown_to_contact_data_handwritten():
    md = """\
---
title: John Appleseed
type: contact
birthdate: "2000-03-20"
tags:
  - family
  - running
email: john@apple.com
phone:
  - "+1-555-0100"
  - "+1-555-0200"
---

## Notes

Loves trail running on weekends.

## Projects

Building a cabin in Vermont.
"""
    data = markdown_to_contact_data(md)

    assert data["contact_fields"]["first_name"] == "John"
    assert data["contact_fields"]["last_name"] == "Appleseed"
    assert data["contact_fields"]["birthdate"] == date(2000, 3, 20)
    assert data["tags"] == ["family", "running"]

    emails = [m for m in data["contact_methods"] if m["type"] == "email"]
    phones = [m for m in data["contact_methods"] if m["type"] == "phone"]
    assert len(emails) == 1
    assert emails[0]["value"] == "john@apple.com"
    assert len(phones) == 2
    assert {p["value"] for p in phones} == {"+1-555-0100", "+1-555-0200"}

    assert data["sections"]["Notes"] == "Loves trail running on weekends."
    assert data["sections"]["Projects"] == "Building a cabin in Vermont."


# ── section parsing (## headers) ────────────────────────────────────


def test_section_parsing_multiple_headers():
    md = """\
---
title: Test Person
---

## First

Content of first section.
Second line.

## Second

Content of second section.

## Empty
"""
    data = markdown_to_contact_data(md)

    assert data["sections"]["First"] == "Content of first section.\nSecond line."
    assert data["sections"]["Second"] == "Content of second section."
    assert data["sections"]["Empty"] == ""


# ── activity section parsing ───────────────────────────────────────


def test_parse_activities_basic():
    content = "- 2025-01-10: Lunch\n- 2025-02-05: Call"
    acts = _parse_activities_from_section(content)
    assert len(acts) == 2
    assert acts[0] == {"title": "Lunch", "happened_at": date(2025, 1, 10)}
    assert acts[1] == {"title": "Call", "happened_at": date(2025, 2, 5)}


def test_parse_activities_with_type():
    content = "- 2025-03-01: Team standup (meeting)"
    acts = _parse_activities_from_section(content)
    assert len(acts) == 1
    assert acts[0]["title"] == "Team standup"
    assert acts[0]["activity_type_name"] == "meeting"


def test_parse_activities_skips_bad_lines():
    content = "Some preamble\n- not-a-date: Oops\n- 2025-01-01: Valid"
    acts = _parse_activities_from_section(content)
    assert len(acts) == 1
    assert acts[0]["title"] == "Valid"


# ── relationship section parsing ───────────────────────────────────


def test_parse_relationships_basic():
    content = "- Lucy Van Pelt (friend)\n- Charlie Brown (colleague)"
    rels = _parse_relationships_from_section(content)
    assert len(rels) == 2
    assert rels[0] == {"name": "Lucy Van Pelt", "relationship_type_name": "friend"}
    assert rels[1] == {"name": "Charlie Brown", "relationship_type_name": "colleague"}


def test_parse_relationships_skips_bad_lines():
    content = "- No parens here\n- Valid Name (sibling)"
    rels = _parse_relationships_from_section(content)
    assert len(rels) == 1
    assert rels[0]["name"] == "Valid Name"


# ── round-trip: activities + relationships in sections ─────────────


def test_roundtrip_activities_and_relationships():
    c = _contact(
        first="Charlie",
        last="Brown",
        activities=[
            _activity("Lunch", date(2025, 1, 10)),
            _activity("Call", date(2025, 2, 5)),
        ],
        relationships=[_relationship("Lucy", "Van Pelt", "friend")],
    )
    md = contact_to_markdown(c)
    data = markdown_to_contact_data(md)

    assert len(data["activities"]) == 2
    assert data["activities"][0]["title"] == "Lunch"
    assert data["activities"][0]["happened_at"] == date(2025, 1, 10)
    assert data["activities"][1]["title"] == "Call"

    assert len(data["relationships"]) == 1
    assert data["relationships"][0]["name"] == "Lucy Van Pelt"
    assert data["relationships"][0]["relationship_type_name"] == "friend"
