"""Markdown <-> Contact data conversion with configurable field/section mapping."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import frontmatter
import structlog

logger = structlog.get_logger()

_PHOTO_RE = re.compile(r"!\[.*?\|.*?\]\((assets/[^)]+)\)")


@dataclass
class MarkdownContactData:
    """Parsed representation of a contact markdown file."""

    markdown_id: str  # from frontmatter or filename
    frontmatter_fields: dict[str, Any]  # raw YAML frontmatter
    sections: dict[str, str]  # section_name -> markdown content
    raw_content: str  # full file content


def contact_to_markdown(
    contact: Any,
    field_mapping: list[dict[str, Any]] | None = None,
    section_mapping: list[dict[str, Any]] | None = None,
    existing_markdown_id: str | None = None,
) -> str:
    """Convert a Contact + relations to a markdown file string.

    Args:
        contact: Contact model instance (with relations loaded)
        field_mapping: frontmatter field config from GitSyncConfig.field_mapping_json
        section_mapping: body section config from GitSyncConfig.section_mapping_json
        existing_markdown_id: reuse existing ID if updating
    """
    fm: dict[str, Any] = {}

    if field_mapping:
        for entry in field_mapping:
            key = entry.get("key", "")
            value = _resolve_field_source(contact, entry)
            if value is not None:
                fm[key] = value
    else:
        # Default mapping
        fm["title"] = f"{contact.first_name} {contact.last_name}".strip()
        fm["type"] = "contact"
        if contact.birthdate:
            fm["birthdate"] = contact.birthdate.isoformat()
        tags = [t.name for t in getattr(contact, "tags", [])]
        if tags:
            fm["tags"] = tags
        emails = [
            cm.value
            for cm in getattr(contact, "contact_methods", [])
            if cm.type == "email"
        ]
        if emails:
            fm["email"] = emails if len(emails) > 1 else emails[0]
        phones = [
            cm.value
            for cm in getattr(contact, "contact_methods", [])
            if cm.type == "phone"
        ]
        if phones:
            fm["phone"] = phones if len(phones) > 1 else phones[0]

    # Build body sections
    body_parts: list[str] = []

    # Photo reference
    photo_path = getattr(contact, "_photo_path", None)
    if photo_path:
        full_name = f"{contact.first_name} {contact.last_name}".strip() or "photo"
        body_parts.append(f"![{full_name} photo|180]({photo_path})")

    if section_mapping:
        for entry in section_mapping:
            section_name = entry.get("name", "")
            section_type = entry.get("type", "freeform")
            content = _build_section_content(contact, section_type, entry)
            if content:
                body_parts.append(f"## {section_name}\n\n{content}")
    else:
        # Default sections
        if contact.notes_summary:
            body_parts.append(f"## Notes\n\n{contact.notes_summary}")

        activities = getattr(contact, "activities", None)
        if activities:
            lines = []
            for act in activities:
                dt = act.happened_at.strftime("%Y-%m-%d") if act.happened_at else ""
                lines.append(f"- {dt}: {act.title}")
            if lines:
                body_parts.append("## Timeline\n\n" + "\n".join(lines))

        relationships = getattr(contact, "relationships", [])
        if relationships:
            lines = []
            for rel in relationships:
                other = getattr(rel, "other_contact", None)
                rel_type = getattr(rel, "relationship_type", None)
                if other and rel_type:
                    name = f"{other.first_name} {other.last_name}".strip()
                    lines.append(f"- {name} ({rel_type.name})")
            if lines:
                body_parts.append("## Relationships\n\n" + "\n".join(lines))

    body = "\n\n".join(body_parts)

    post = frontmatter.Post(body, **fm)
    return frontmatter.dumps(post) + "\n"  # type: ignore[no-any-return]


def markdown_to_contact_data(
    content: str,
    field_mapping: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Parse markdown file into contact creation/update data.

    Returns dict with:
        contact_fields: dict for Contact model
        contact_methods: list of dicts
        addresses: list of dicts
        tags: list of tag name strings
        sections: dict of section_name -> content
        markdown_id: from frontmatter id field or None
    """
    post = frontmatter.loads(content)
    fm = dict(post.metadata)
    body = post.content

    contact_fields: dict[str, Any] = {}
    contact_methods: list[dict[str, Any]] = []
    tags: list[str] = []

    if field_mapping:
        for entry in field_mapping:
            key = entry.get("key", "")
            source = entry.get("source", "")
            clara_field = entry.get("clara_field", "")
            clara_relation = entry.get("clara_relation", "")

            if source == "static":
                continue  # ignored on read

            value = fm.get(key)
            if value is None:
                continue

            if source == "field" and clara_field:
                contact_fields[clara_field] = _coerce_field(clara_field, value)
            elif source == "computed" and entry.get("expression") == "full_name":
                _parse_full_name(str(value), contact_fields)
            elif source == "relation" and clara_relation == "tags":
                if isinstance(value, list):
                    tags.extend(str(t) for t in value)
                elif isinstance(value, str):
                    tags.append(value)
            elif source == "relation" and clara_relation == "contact_methods":
                filt = entry.get("filter", {})
                cm_type = filt.get("type", "email")
                if isinstance(value, list):
                    for v in value:
                        contact_methods.append(
                            {"type": cm_type, "label": "", "value": str(v)}
                        )
                elif isinstance(value, str):
                    contact_methods.append(
                        {"type": cm_type, "label": "", "value": value}
                    )
    else:
        # Default mapping
        title = fm.get("title", "")
        if title:
            _parse_full_name(str(title), contact_fields)

        if "birthdate" in fm:
            contact_fields["birthdate"] = _coerce_field("birthdate", fm["birthdate"])

        fm_tags = fm.get("tags", [])
        if isinstance(fm_tags, list):
            tags = [str(t) for t in fm_tags]

        email = fm.get("email")
        if email:
            if isinstance(email, list):
                for e in email:
                    contact_methods.append(
                        {"type": "email", "label": "", "value": str(e)}
                    )
            else:
                contact_methods.append(
                    {"type": "email", "label": "", "value": str(email)}
                )

        phone = fm.get("phone")
        if phone:
            if isinstance(phone, list):
                for p in phone:
                    contact_methods.append(
                        {"type": "phone", "label": "", "value": str(p)}
                    )
            else:
                contact_methods.append(
                    {"type": "phone", "label": "", "value": str(phone)}
                )

    # Parse body sections
    sections = _parse_sections(body)

    # Parse structured sections into typed data
    activities: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    for name, content in sections.items():
        if name.lower() in ("timeline", "activities"):
            activities.extend(_parse_activities_from_section(content))
        elif name.lower() == "relationships":
            relationships.extend(_parse_relationships_from_section(content))

    # Photo reference
    photo_match = _PHOTO_RE.search(body)
    photo_path = photo_match.group(1) if photo_match else None

    return {
        "contact_fields": contact_fields,
        "contact_methods": contact_methods,
        "addresses": [],
        "tags": tags,
        "sections": sections,
        "activities": activities,
        "relationships": relationships,
        "photo_path": photo_path,
    }


def _resolve_field_source(
    contact: Any, entry: dict[str, Any],
) -> Any:
    """Resolve a field mapping entry to a value from the contact."""
    source = entry.get("source", "")

    if source == "static":
        return entry.get("value")

    if source == "computed":
        expr = entry.get("expression", "")
        if expr == "full_name":
            return f"{contact.first_name} {contact.last_name}".strip()
        return None

    if source == "field":
        clara_field = entry.get("clara_field", "")
        value = getattr(contact, clara_field, None)
        fmt = entry.get("format", "")
        if value is None:
            return None
        if fmt == "iso8601" and isinstance(value, (date, datetime)):
            return value.isoformat()
        return value

    if source == "relation":
        clara_relation = entry.get("clara_relation", "")
        attribute = entry.get("attribute", "name")
        filt = entry.get("filter", {})
        items = getattr(contact, clara_relation, [])
        values = []
        for item in items:
            if filt:
                match = all(getattr(item, k, None) == v for k, v in filt.items())
                if not match:
                    continue
            values.append(getattr(item, attribute, str(item)))
        if not values:
            return None
        return values if len(values) > 1 else values[0]

    if source == "custom_field":
        slug = entry.get("slug", "")
        for cfv in getattr(contact, "custom_field_values", []):
            if getattr(cfv, "definition", None) and cfv.definition.slug == slug:
                return cfv.value_json
        return None

    return None


def _build_section_content(
    contact: Any, section_type: str, entry: dict[str, Any],
) -> str:
    """Build body section content based on type."""
    if section_type == "note":
        title = entry.get("title", "")
        for note in getattr(contact, "notes", []):
            if getattr(note, "title", "") == title:
                return getattr(note, "body_markdown", "") or ""
        return ""

    if section_type == "activities":
        lines = []
        for act in getattr(contact, "activities", []):
            dt = act.happened_at.strftime("%Y-%m-%d") if act.happened_at else ""
            act_type = ""
            if hasattr(act, "activity_type") and act.activity_type:
                act_type = f" ({act.activity_type.name})"
            lines.append(f"- {dt}: {act.title}{act_type}")
        return "\n".join(lines)

    if section_type == "relationships":
        lines = []
        for rel in getattr(contact, "relationships", []):
            other = getattr(rel, "other_contact", None)
            rel_type = getattr(rel, "relationship_type", None)
            if other and rel_type:
                name = f"{other.first_name} {other.last_name}".strip()
                lines.append(f"- {name} ({rel_type.name})")
        return "\n".join(lines)

    return ""


def _parse_full_name(full_name: str, fields: dict[str, Any]) -> None:
    """Split a full name into first_name and last_name."""
    parts = full_name.strip().split(" ", 1)
    fields["first_name"] = parts[0]
    fields["last_name"] = parts[1] if len(parts) > 1 else ""


def _coerce_field(field_name: str, value: Any) -> Any:
    """Coerce a frontmatter value to the expected type."""
    if field_name in ("birthdate", "created_at") and isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return value


def _parse_activities_from_section(content: str) -> list[dict[str, Any]]:
    """Parse ``- YYYY-MM-DD: title`` or ``- YYYY-MM-DD: title (type)``."""
    results: list[dict[str, Any]] = []
    for line in content.split("\n"):
        m = re.match(
            r"^-\s+(\d{4}-\d{2}-\d{2}):\s+(.+?)(?:\s+\(([^)]+)\))?\s*$", line
        )
        if not m:
            continue
        entry: dict[str, Any] = {"title": m.group(2).strip()}
        try:
            entry["happened_at"] = date.fromisoformat(m.group(1))
        except ValueError:
            continue
        if m.group(3):
            entry["activity_type_name"] = m.group(3).strip()
        results.append(entry)
    return results


def _parse_relationships_from_section(content: str) -> list[dict[str, Any]]:
    """Parse bullet list: ``- Full Name (relationship_type)``."""
    results: list[dict[str, Any]] = []
    for line in content.split("\n"):
        m = re.match(r"^-\s+(.+?)\s+\(([^)]+)\)\s*$", line)
        if not m:
            continue
        results.append({
            "name": m.group(1).strip(),
            "relationship_type_name": m.group(2).strip(),
        })
    return results


def _parse_sections(body: str) -> dict[str, str]:
    """Parse markdown body into {section_name: content} by ## headers."""
    sections: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    for line in body.split("\n"):
        match = re.match(r"^##\s+(.+)$", line)
        if match:
            if current_name is not None:
                sections[current_name] = "\n".join(current_lines).strip()
            current_name = match.group(1).strip()
            current_lines = []
        elif current_name is not None:
            current_lines.append(line)

    if current_name is not None:
        sections[current_name] = "\n".join(current_lines).strip()

    return sections
