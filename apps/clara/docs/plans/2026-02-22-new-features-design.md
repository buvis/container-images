# New Features Design

Source: `.local/plans/3-new-features.md`

---

## 1. Files Rename

**Backend**: Add `FileUpdate` schema (filename) + `PATCH /files/{file_id}` endpoint.

**Frontend**: Click filename text -> inline `<input>`, Enter saves, Escape cancels. Saving indicator.

## 2. Notifications — Clear All Read

**Backend**: Add `DELETE /notifications/read` bulk endpoint. Soft-deletes all where `read=True`.

**Frontend**: "Clear read" button in header next to "Mark all read". Removes read notifications from list on success.

## 3. Contact Photo Upload

**Backend**: Add `photo_file_id` to `ContactUpdate` schema.

**Frontend**: Click initials avatar -> file picker (images only) -> upload via `filesApi.upload` -> update contact with `photo_file_id`. Display `<img>` from download URL when photo exists. Camera icon overlay on hover. Also show on contact list items.

## 4. Notes Standalone Page

**Backend**: Already done — `GET /notes` without filters returns all notes.

**Frontend**: New `/notes/+page.svelte`. Uses `DataList` for pagination. Filter by contact/activity. Shows title, body snippet, linked entity, date. New note modal with title, body (markdown), optional contact/activity picker. Edit/delete per note.

## 5. Activity Type Management

**Backend**: Already done — full CRUD.

**Frontend**: New "Activity Types" tab in settings. List types with name, Lucide icon, color swatch. Add/edit via inline form or modal: name, Lucide icon picker (searchable), color picker. Delete per type.

## 6. Template Pages/Modules Editing

**Backend**: Already done — full CRUD for pages and modules.

**Frontend**: Add API client methods for pages/modules. In Templates tab: click template -> expand to show pages. Each page: name, order, edit/delete, expand for modules. Each module: type, label, order, edit/delete. Add page/module buttons. Up/down arrows for reorder.

## 7. Custom Field Display on Entities

**Backend**: Already done — get/set values endpoints.

**Frontend**: Reusable `CustomFieldsSection.svelte` taking `entityType` + `entityId`. Loads definitions + values. Renders per field type: text, number, date, checkbox, select. Click to edit inline. Add to contact, activity, task detail pages.

## 8. Multi-Vault Switching

**Backend**: Add `PATCH /vaults/{vault_id}` for rename + `VaultUpdate` schema.

**Frontend**: New `/vaults/+page.svelte` (outside vault scope). Lists vaults: name, members, created date. Click -> navigate to vault dashboard. Create vault modal. Delete with confirmation (owner only). Root `/` redirects to `/vaults`.
