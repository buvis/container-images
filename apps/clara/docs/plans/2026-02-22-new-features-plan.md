# New Features Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement 8 new features: file rename, notification clear-read, contact photo, notes page, activity type settings, template editing, custom fields on entities, multi-vault switching.

**Architecture:** Backend changes are minimal (2 new endpoints, 2 schema additions). Bulk of work is frontend: new pages, settings tabs, reusable components. All features follow existing patterns — DataList for lists, Modal for forms, inline editing for sections.

**Tech Stack:** FastAPI + SQLAlchemy (backend), SvelteKit + TypeScript + Tailwind (frontend), Lucide icons

---

## Task 1: File rename — backend

**Files:**
- Modify: `backend/src/clara/files/schemas.py`
- Modify: `backend/src/clara/files/service.py`
- Modify: `backend/src/clara/files/api.py`
- Modify: `backend/tests/test_files.py`

**Step 1: Write the failing test**

Add to `backend/tests/test_files.py`:

```python
async def test_file_rename(authenticated_client: AsyncClient, vault: Vault):
    resp = await authenticated_client.post(
        f"/api/v1/vaults/{vault.id}/files",
        files={"file": ("original.txt", b"data", "text/plain")},
    )
    assert resp.status_code == 201
    file_id = resp.json()["id"]

    resp = await authenticated_client.patch(
        f"/api/v1/vaults/{vault.id}/files/{file_id}",
        json={"filename": "renamed.txt"},
    )
    assert resp.status_code == 200
    assert resp.json()["filename"] == "renamed.txt"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/bob/git/src/github.com/buvis/clara && uv run pytest backend/tests/test_files.py::test_file_rename -v`
Expected: FAIL — 405 Method Not Allowed (no PATCH endpoint)

**Step 3: Add FileUpdate schema**

In `backend/src/clara/files/schemas.py`, add after `FileLinkCreate`:

```python
class FileUpdate(BaseModel):
    filename: str | None = None
```

**Step 4: Add update_file to service**

In `backend/src/clara/files/service.py`, add method to `FileService` after `download_file`:

```python
async def update_file(self, file_id: uuid.UUID, filename: str) -> File:
    return await self.repo.update(file_id, filename=filename)
```

**Step 5: Add PATCH endpoint**

In `backend/src/clara/files/api.py`, add after `delete_file` (line 77) and before `/links` routes:

```python
@router.patch("/{file_id}", response_model=FileRead)
async def update_file(
    file_id: uuid.UUID, body: FileUpdate, svc: FileSvc
) -> FileRead:
    return FileRead.model_validate(
        await svc.update_file(file_id, **body.model_dump(exclude_none=True))
    )
```

Update imports to include `FileUpdate`:
```python
from clara.files.schemas import FileLinkCreate, FileLinkRead, FileRead, FileUpdate
```

Also update `update_file` in service to accept **kwargs:
```python
async def update_file(self, file_id: uuid.UUID, **kwargs: Any) -> File:
    return await self.repo.update(file_id, **kwargs)
```

Add `from typing import Any` import to service.py.

**Step 6: Run test to verify it passes**

Run: `uv run pytest backend/tests/test_files.py::test_file_rename -v`
Expected: PASS

**Step 7: Commit**

```bash
git add backend/src/clara/files/schemas.py backend/src/clara/files/service.py backend/src/clara/files/api.py backend/tests/test_files.py
git commit -m "feat(backend): add file rename endpoint"
```

---

## Task 2: Notifications clear-read — backend

**Files:**
- Modify: `backend/src/clara/notifications/api.py`
- Modify: `backend/tests/test_notifications.py`

**Step 1: Write the failing test**

Add to `backend/tests/test_notifications.py`:

```python
async def test_clear_read_notifications(
    authenticated_client: AsyncClient,
    vault: Vault,
    user: User,
    db_session: AsyncSession,
):
    # create 3 notifications
    for _ in range(3):
        await _create_notification(db_session, vault.id, user.id)

    # mark 2 as read
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/notifications"
    )
    items = resp.json()
    for notif in items[:2]:
        await authenticated_client.patch(
            f"/api/v1/vaults/{vault.id}/notifications/{notif['id']}",
            json={"read": True},
        )

    # clear read
    resp = await authenticated_client.delete(
        f"/api/v1/vaults/{vault.id}/notifications/clear-read"
    )
    assert resp.status_code == 204

    # only unread remain
    resp = await authenticated_client.get(
        f"/api/v1/vaults/{vault.id}/notifications"
    )
    remaining = resp.json()
    assert all(not n["read"] for n in remaining)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest backend/tests/test_notifications.py::test_clear_read_notifications -v`
Expected: FAIL — 404 or 405

**Step 3: Add clear-read endpoint**

In `backend/src/clara/notifications/api.py`, add after `mark_all_read` (line 92), BEFORE single-notification routes:

```python
@router.delete("/clear-read", status_code=204)
async def clear_read_notifications(
    vault_id: uuid.UUID, user: CurrentUser, db: Db, _access: VaultAccess
) -> None:
    stmt = (
        update(Notification)
        .where(
            Notification.vault_id == vault_id,
            Notification.user_id == user.id,
            Notification.read.is_(True),
            Notification.deleted_at.is_(None),
        )
        .values(deleted_at=datetime.now(UTC))
    )
    await db.execute(stmt)
    await db.flush()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest backend/tests/test_notifications.py::test_clear_read_notifications -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/clara/notifications/api.py backend/tests/test_notifications.py
git commit -m "feat(backend): add clear-read notifications endpoint"
```

---

## Task 3: Contact photo — backend schema

**Files:**
- Modify: `backend/src/clara/contacts/schemas.py`
- Modify: `backend/tests/test_contacts.py` (if exists, or create test)

**Step 1: Write the failing test**

Add to `backend/tests/test_contacts.py` (or the relevant contact test file):

```python
async def test_update_contact_photo_file_id(
    authenticated_client: AsyncClient, vault: Vault
):
    from tests.conftest import create_contact
    import uuid

    contact_id = await create_contact(authenticated_client, str(vault.id))
    fake_file_id = str(uuid.uuid4())

    resp = await authenticated_client.patch(
        f"/api/v1/vaults/{vault.id}/contacts/{contact_id}",
        json={"photo_file_id": fake_file_id},
    )
    assert resp.status_code == 200
    assert resp.json()["photo_file_id"] == fake_file_id
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest backend/tests/test_contacts.py::test_update_contact_photo_file_id -v`
Expected: FAIL — photo_file_id not accepted by ContactUpdate

**Step 3: Add photo_file_id to ContactUpdate**

In `backend/src/clara/contacts/schemas.py`, add to `ContactUpdate` class:

```python
photo_file_id: uuid.UUID | None = None
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest backend/tests/test_contacts.py::test_update_contact_photo_file_id -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/clara/contacts/schemas.py backend/tests/test_contacts.py
git commit -m "feat(backend): add photo_file_id to ContactUpdate schema"
```

---

## Task 4: File rename — frontend

**Files:**
- Modify: `frontend/src/lib/api/files.ts`
- Modify: `frontend/src/lib/types/models.ts`
- Modify: `frontend/src/routes/(app)/vaults/[vaultId=uuid]/files/+page.svelte`

**Step 1: Add update method to files API client**

In `frontend/src/lib/api/files.ts`, add before `del` method:

```typescript
rename(vaultId: string, fileId: string, filename: string) {
  return api.patch<FileRecord>(`/vaults/${vaultId}/files/${fileId}`, { filename });
},
```

**Step 2: Add updated_at to FileRecord type**

In `frontend/src/lib/types/models.ts`, add `updated_at` field to `FileRecord`:

```typescript
export interface FileRecord {
  id: string;
  vault_id: string;
  uploader_id: string;
  storage_key: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
  updated_at: string;
}
```

**Step 3: Add inline rename to files page**

In `frontend/src/routes/(app)/vaults/[vaultId=uuid]/files/+page.svelte`:

Add state variables:
```typescript
let editingId = $state<string | null>(null);
let editFilename = $state('');
```

Add rename handlers:
```typescript
function startRename(file: FileRecord) {
  editingId = file.id;
  editFilename = file.filename;
}

async function handleRename(fileId: string) {
  if (!editFilename.trim()) return;
  await filesApi.rename(vaultId, fileId, editFilename.trim());
  editingId = null;
  listKey++;
}

function cancelRename() {
  editingId = null;
}
```

Replace the filename display in the row snippet (the `<p>` with `item.filename`) with:
```svelte
{#if editingId === item.id}
  <input
    type="text"
    bind:value={editFilename}
    onkeydown={(e) => {
      if (e.key === 'Enter') handleRename(item.id);
      if (e.key === 'Escape') cancelRename();
    }}
    onblur={() => cancelRename()}
    class="w-full rounded border border-brand-500 bg-neutral-800 px-2 py-0.5 text-sm text-white outline-none"
    autofocus
  />
{:else}
  <button onclick={() => startRename(item)} class="truncate text-sm font-medium text-white hover:text-brand-400 text-left">
    {item.filename}
  </button>
{/if}
```

Add `Pencil` to lucide imports.

**Step 4: Verify manually**

Start dev server, navigate to files page, click filename, verify inline edit works.

**Step 5: Commit**

```bash
git add frontend/src/lib/api/files.ts frontend/src/lib/types/models.ts frontend/src/routes/\(app\)/vaults/\[vaultId=uuid\]/files/+page.svelte
git commit -m "feat(frontend): inline file rename on files page"
```

---

## Task 5: Notifications clear-read — frontend

**Files:**
- Modify: `frontend/src/lib/api/notifications.ts`
- Modify: `frontend/src/routes/(app)/vaults/[vaultId=uuid]/notifications/+page.svelte`

**Step 1: Add clearRead to API client**

In `frontend/src/lib/api/notifications.ts`, add after `markAllRead`:

```typescript
clearRead(vaultId: string) {
  return api.del(`/vaults/${vaultId}/notifications/clear-read`);
},
```

**Step 2: Add clear-read button and handler to page**

In `frontend/src/routes/(app)/vaults/[vaultId=uuid]/notifications/+page.svelte`:

Add state: `let clearingRead = $state(false);`

Add handler:
```typescript
async function clearRead() {
  clearingRead = true;
  try {
    await notificationsApi.clearRead(vaultId);
    notifications = notifications.filter((n) => !n.read);
  } finally {
    clearingRead = false;
  }
}
```

Add derived: `const readCount = $derived(notifications.filter((n) => n.read).length);`

Add button in the header section, after the "Mark all read" button:
```svelte
{#if readCount > 0}
  <Button size="sm" variant="ghost" loading={clearingRead} onclick={clearRead}>
    <Trash2 size={16} class="mr-1.5" />Clear read
  </Button>
{/if}
```

**Step 3: Verify manually**

Start dev server, create some notifications, mark some as read, verify "Clear read" button appears and works.

**Step 4: Commit**

```bash
git add frontend/src/lib/api/notifications.ts frontend/src/routes/\(app\)/vaults/\[vaultId=uuid\]/notifications/+page.svelte
git commit -m "feat(frontend): clear-read notifications button"
```

---

## Task 6: Contact photo — frontend types and API

**Files:**
- Modify: `frontend/src/lib/types/models.ts`
- Modify: `frontend/src/lib/api/contacts.ts`

**Step 1: Add photo_file_id to Contact type**

In `frontend/src/lib/types/models.ts`, add to `Contact` interface after `favorite`:

```typescript
photo_file_id: string | null;
template_id: string | null;
```

Add to `ContactUpdate` interface:
```typescript
photo_file_id?: string | null;
```

**Step 2: Verify no type errors**

Run: `cd frontend && pnpm check`

**Step 3: Commit**

```bash
git add frontend/src/lib/types/models.ts
git commit -m "feat(frontend): add photo_file_id to Contact types"
```

---

## Task 7: Contact photo — upload and display

**Files:**
- Modify: `frontend/src/lib/components/contacts/ContactCard.svelte`
- Modify: `frontend/src/routes/(app)/vaults/[vaultId=uuid]/contacts/[contactId=uuid]/+page.svelte`

**Step 1: Update ContactCard to show photo**

In `frontend/src/lib/components/contacts/ContactCard.svelte`, replace the initials div (lines 16-18):

```svelte
{#if contact.photo_file_id}
  <img
    src="/api/v1/vaults/{contact.vault_id}/files/{contact.photo_file_id}/download"
    alt="{contact.first_name}"
    class="h-10 w-10 shrink-0 rounded-full object-cover"
  />
{:else}
  <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-500/20 text-sm font-semibold text-brand-400">
    {initials}
  </div>
{/if}
```

**Step 2: Update contact detail page**

In the contact detail page, replace the initials avatar (line ~140) with a clickable photo upload:

Add state variables:
```typescript
let photoUploading = $state(false);
```

Add handler:
```typescript
async function handlePhotoUpload(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  photoUploading = true;
  try {
    const uploaded = await filesApi.upload(vaultId, file);
    contact = await contactsApi.update(vaultId, contactId, { photo_file_id: uploaded.id });
  } finally {
    photoUploading = false;
    (e.target as HTMLInputElement).value = '';
  }
}
```

Add hidden file input and replace avatar:
```svelte
<input id="photo-upload" type="file" accept="image/*" class="hidden" onchange={handlePhotoUpload} />

<button onclick={() => document.getElementById('photo-upload')?.click()} class="group relative" disabled={photoUploading}>
  {#if contact.photo_file_id}
    <img
      src="/api/v1/vaults/{vaultId}/files/{contact.photo_file_id}/download"
      alt="{contact.first_name}"
      class="h-14 w-14 rounded-full object-cover"
    />
  {:else}
    <div class="flex h-14 w-14 items-center justify-center rounded-full bg-brand-500/20 text-lg font-semibold text-brand-400">
      {contact.first_name[0]}{contact.last_name?.[0] ?? ''}
    </div>
  {/if}
  <div class="absolute inset-0 flex items-center justify-center rounded-full bg-black/50 opacity-0 transition group-hover:opacity-100">
    <Camera size={18} class="text-white" />
  </div>
</button>
```

Add `Camera` to lucide imports. Add `filesApi` import.

**Step 3: Verify manually**

Upload a photo on contact detail, verify it appears. Check contact list shows photo too.

**Step 4: Commit**

```bash
git add frontend/src/lib/components/contacts/ContactCard.svelte frontend/src/routes/\(app\)/vaults/\[vaultId=uuid\]/contacts/\[contactId=uuid\]/+page.svelte
git commit -m "feat(frontend): contact photo upload and display"
```

---

## Task 8: Notes standalone page

**Files:**
- Create: `frontend/src/routes/(app)/vaults/[vaultId=uuid]/notes/+page.svelte`
- Modify: `frontend/src/lib/api/notes.ts`
- Modify: `frontend/src/lib/components/layout/Sidebar.svelte`

**Step 1: Add filter-by-activity to notes API client**

In `frontend/src/lib/api/notes.ts`, add after `forContact`:

```typescript
forActivity(vaultId: string, activityId: string, params?: { offset?: number; limit?: number }) {
  return api.get<PaginatedResponse<Note>>(
    `/vaults/${vaultId}/notes${qs({ activity_id: activityId, ...params })}`
  );
},
```

Update `list` to accept optional filters:

```typescript
list(vaultId: string, params?: { offset?: number; limit?: number; contact_id?: string; activity_id?: string }) {
  return api.get<PaginatedResponse<Note>>(`/vaults/${vaultId}/notes${qs(params ?? {})}`);
},
```

**Step 2: Add Notes to sidebar**

In `frontend/src/lib/components/layout/Sidebar.svelte`:

Add `StickyNote` to lucide imports.

Add nav item after Reminders:
```typescript
{ label: 'Notes', icon: StickyNote, path: 'notes' },
```

**Step 3: Create notes page**

Create `frontend/src/routes/(app)/vaults/[vaultId=uuid]/notes/+page.svelte`:

```svelte
<script lang="ts">
  import { page } from '$app/state';
  import { notesApi } from '$api/notes';
  import type { NoteCreateInput, NoteUpdateInput } from '$api/notes';
  import { contactsApi } from '$api/contacts';
  import DataList from '$components/data/DataList.svelte';
  import Button from '$components/ui/Button.svelte';
  import Input from '$components/ui/Input.svelte';
  import Modal from '$components/ui/Modal.svelte';
  import { Plus, Pencil, Trash2, StickyNote } from 'lucide-svelte';
  import type { Note, Contact } from '$lib/types/models';

  const vaultId = $derived(page.params.vaultId!);

  let listKey = $state(0);
  let contacts = $state<Contact[]>([]);
  let filterContactId = $state<string>('');

  // Modal state
  let showModal = $state(false);
  let editingNote = $state<Note | null>(null);
  let form = $state<NoteCreateInput>({ title: '', body_markdown: '', contact_id: null, activity_id: null });
  let saving = $state(false);

  // Delete state
  let deleteId = $state<string | null>(null);
  let deleting = $state(false);

  $effect(() => {
    contactsApi.list(vaultId, { limit: 200 }).then((r) => (contacts = r.items));
  });

  async function loadNotes(params: { offset: number; limit: number; search: string; filter: string | null }) {
    return notesApi.list(vaultId, {
      offset: params.offset,
      limit: params.limit,
      ...(filterContactId ? { contact_id: filterContactId } : {})
    });
  }

  function openCreate() {
    editingNote = null;
    form = { title: '', body_markdown: '', contact_id: null, activity_id: null };
    showModal = true;
  }

  function openEdit(note: Note) {
    editingNote = note;
    form = {
      title: note.title,
      body_markdown: note.body_markdown,
      contact_id: note.contact_id,
      activity_id: note.activity_id
    };
    showModal = true;
  }

  async function handleSave(e: Event) {
    e.preventDefault();
    saving = true;
    try {
      if (editingNote) {
        await notesApi.update(vaultId, editingNote.id, form as NoteUpdateInput);
      } else {
        await notesApi.create(vaultId, form);
      }
      showModal = false;
      listKey++;
    } finally {
      saving = false;
    }
  }

  async function handleDelete(id: string) {
    deleting = true;
    try {
      await notesApi.del(vaultId, id);
      deleteId = null;
      listKey++;
    } finally {
      deleting = false;
    }
  }

  function contactName(contactId: string | null): string {
    if (!contactId) return '';
    const c = contacts.find((c) => c.id === contactId);
    return c ? `${c.first_name} ${c.last_name}` : '';
  }
</script>

<svelte:head><title>Notes</title></svelte:head>

<div class="space-y-4">
  <div class="flex items-center gap-3">
    <select
      bind:value={filterContactId}
      onchange={() => listKey++}
      class="rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-1.5 text-sm text-white outline-none"
    >
      <option value="">All contacts</option>
      {#each contacts as c (c.id)}
        <option value={c.id}>{c.first_name} {c.last_name}</option>
      {/each}
    </select>
  </div>

  {#key listKey}
    <DataList
      load={loadNotes}
      searchPlaceholder="Search notes..."
      emptyIcon={StickyNote}
      emptyTitle="No notes yet"
      emptyDescription="Create notes to keep track of important information"
    >
      {#snippet header()}
        <Button onclick={openCreate}>
          <Plus size={16} />
          New Note
        </Button>
      {/snippet}
      {#snippet row(item: Note)}
        <div class="flex items-start gap-3 px-4 py-3">
          <div class="min-w-0 flex-1">
            <p class="text-sm font-medium text-white">{item.title || 'Untitled'}</p>
            {#if item.body_markdown}
              <p class="mt-0.5 line-clamp-2 text-xs text-neutral-400">{item.body_markdown}</p>
            {/if}
            <div class="mt-1 flex gap-2 text-xs text-neutral-500">
              {#if item.contact_id}
                <span>{contactName(item.contact_id)}</span>
              {/if}
              <span>{new Date(item.updated_at).toLocaleDateString()}</span>
            </div>
          </div>
          <div class="flex items-center gap-1">
            <button onclick={() => openEdit(item)} class="rounded p-1 text-neutral-600 transition hover:bg-neutral-800 hover:text-white">
              <Pencil size={14} />
            </button>
            {#if deleteId === item.id}
              <Button size="sm" variant="danger" loading={deleting} onclick={() => handleDelete(item.id)}>Delete</Button>
              <Button size="sm" variant="ghost" onclick={() => (deleteId = null)}>Cancel</Button>
            {:else}
              <button onclick={() => (deleteId = item.id)} class="rounded p-1 text-neutral-600 transition hover:bg-neutral-800 hover:text-red-400">
                <Trash2 size={14} />
              </button>
            {/if}
          </div>
        </div>
      {/snippet}
    </DataList>
  {/key}
</div>

{#if showModal}
  <Modal title={editingNote ? 'Edit Note' : 'New Note'} onclose={() => (showModal = false)}>
    <form onsubmit={handleSave} class="space-y-4">
      <Input label="Title" bind:value={form.title} />
      <div>
        <label class="mb-1 block text-sm font-medium text-neutral-300">Content</label>
        <textarea
          bind:value={form.body_markdown}
          rows="6"
          class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
          placeholder="Write in markdown..."
        ></textarea>
      </div>
      <div>
        <label class="mb-1.5 block text-sm font-medium text-neutral-300">Contact (optional)</label>
        <select bind:value={form.contact_id} class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500">
          <option value={null}>None</option>
          {#each contacts as c (c.id)}
            <option value={c.id}>{c.first_name} {c.last_name}</option>
          {/each}
        </select>
      </div>
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (showModal = false)}>Cancel</Button>
        <Button type="submit" loading={saving}>Save</Button>
      </div>
    </form>
  </Modal>
{/if}
```

**Step 4: Verify manually**

Navigate to /notes page, create a note, filter by contact, edit, delete.

**Step 5: Commit**

```bash
git add frontend/src/routes/\(app\)/vaults/\[vaultId=uuid\]/notes/+page.svelte frontend/src/lib/api/notes.ts frontend/src/lib/components/layout/Sidebar.svelte
git commit -m "feat(frontend): notes standalone page with CRUD"
```

---

## Task 9: Activity types — settings tab

**Files:**
- Modify: `frontend/src/routes/(app)/vaults/[vaultId=uuid]/settings/+page.svelte`

**Step 1: Add Activity Types tab**

In the settings page, add `'Activity Types'` to the `tabs` array after `'Relationship Types'`:

```typescript
const tabs = ['General', 'Members', 'Templates', 'Custom Fields', 'Relationship Types', 'Activity Types', 'Security', 'Import/Export'] as const;
```

**Step 2: Add state variables**

Add after existing state declarations:

```typescript
import { activitiesApi } from '$api/activities';
import type { ActivityTypeCreateInput } from '$api/activities';
import type { ActivityType } from '$lib/types/models';

let activityTypes = $state<ActivityType[]>([]);
let activityTypesLoading = $state(true);
let showActivityTypeModal = $state(false);
let editActivityTypeId = $state<string | null>(null);
let activityTypeForm = $state<ActivityTypeCreateInput>({ name: '', icon: '', color: '#6b7280' });
let activityTypeSaving = $state(false);
let activityTypeDeleteId = $state<string | null>(null);
```

**Step 3: Add loader in $effect**

In the existing `$effect` that watches `activeTab`, add case:

```typescript
if (activeTab === 'Activity Types') {
  activityTypesLoading = true;
  activitiesApi.listTypes(vaultId, { limit: 100 }).then((r) => {
    activityTypes = r.items;
    activityTypesLoading = false;
  });
}
```

**Step 4: Add CRUD handlers**

```typescript
function openActivityTypeCreate() {
  editActivityTypeId = null;
  activityTypeForm = { name: '', icon: '', color: '#6b7280' };
  showActivityTypeModal = true;
}

function openActivityTypeEdit(t: ActivityType) {
  editActivityTypeId = t.id;
  activityTypeForm = { name: t.name, icon: t.icon, color: t.color };
  showActivityTypeModal = true;
}

async function handleActivityTypeSave(e: Event) {
  e.preventDefault();
  activityTypeSaving = true;
  try {
    if (editActivityTypeId) {
      const updated = await activitiesApi.updateType(vaultId, editActivityTypeId, activityTypeForm);
      activityTypes = activityTypes.map((t) => (t.id === updated.id ? updated : t));
    } else {
      const created = await activitiesApi.createType(vaultId, activityTypeForm);
      activityTypes = [...activityTypes, created];
    }
    showActivityTypeModal = false;
  } finally {
    activityTypeSaving = false;
  }
}

async function handleActivityTypeDelete(id: string) {
  await activitiesApi.deleteType(vaultId, id);
  activityTypes = activityTypes.filter((t) => t.id !== id);
  activityTypeDeleteId = null;
}
```

**Step 5: Add template section**

Add after the Relationship Types tab section:

```svelte
{#if activeTab === 'Activity Types'}
  <section class="space-y-4 rounded-xl border border-neutral-800 bg-neutral-900 p-6">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold text-white">Activity Types</h2>
      <Button size="sm" onclick={openActivityTypeCreate}>Add type</Button>
    </div>
    {#if activityTypesLoading}
      <p class="text-sm text-neutral-500">Loading activity types…</p>
    {:else if activityTypes.length === 0}
      <p class="text-sm text-neutral-500">No activity types configured.</p>
    {:else}
      <div class="space-y-2">
        {#each activityTypes as t (t.id)}
          <div class="group flex items-center justify-between rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2">
            <div class="flex items-center gap-3">
              <div class="h-3 w-3 rounded-full" style="background-color: {t.color}"></div>
              <p class="text-sm font-medium text-white">{t.name}</p>
              {#if t.icon}
                <span class="text-xs text-neutral-500">{t.icon}</span>
              {/if}
            </div>
            <div class="flex items-center gap-2">
              {#if activityTypeDeleteId === t.id}
                <span class="text-xs text-red-400">Delete?</span>
                <Button size="sm" variant="danger" onclick={() => handleActivityTypeDelete(t.id)}>Yes</Button>
                <Button size="sm" variant="ghost" onclick={() => (activityTypeDeleteId = null)}>No</Button>
              {:else}
                <button onclick={() => openActivityTypeEdit(t)} class="text-neutral-600 opacity-0 transition hover:text-white group-hover:opacity-100"><Pencil size={14} /></button>
                <button onclick={() => (activityTypeDeleteId = t.id)} class="text-neutral-600 opacity-0 transition hover:text-red-400 group-hover:opacity-100"><Trash2 size={14} /></button>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </section>

  {#if showActivityTypeModal}
    <Modal title={editActivityTypeId ? 'Edit Activity Type' : 'New Activity Type'} onclose={() => (showActivityTypeModal = false)}>
      <form onsubmit={handleActivityTypeSave} class="space-y-4">
        <Input label="Name" bind:value={activityTypeForm.name} required />
        <Input label="Icon (Lucide name)" bind:value={activityTypeForm.icon} placeholder="e.g. phone, coffee, video" />
        <div>
          <label class="mb-1.5 block text-sm font-medium text-neutral-300">Color</label>
          <div class="flex items-center gap-3">
            <input type="color" bind:value={activityTypeForm.color} class="h-9 w-9 cursor-pointer rounded border border-neutral-700 bg-transparent" />
            <Input bind:value={activityTypeForm.color} />
          </div>
        </div>
        <div class="flex justify-end gap-3">
          <Button variant="ghost" onclick={() => (showActivityTypeModal = false)}>Cancel</Button>
          <Button type="submit" loading={activityTypeSaving}>Save</Button>
        </div>
      </form>
    </Modal>
  {/if}
{/if}
```

**Step 6: Verify manually**

Navigate to settings, click Activity Types tab, add/edit/delete types.

**Step 7: Commit**

```bash
git add frontend/src/routes/\(app\)/vaults/\[vaultId=uuid\]/settings/+page.svelte
git commit -m "feat(frontend): activity types management in settings"
```

---

## Task 10: Template pages/modules — API client

**Files:**
- Modify: `frontend/src/lib/api/customization.ts`
- Modify: `frontend/src/lib/types/models.ts`

**Step 1: Add page and module API methods**

In `frontend/src/lib/api/customization.ts`, add types and methods:

```typescript
import type { Template, TemplatePage, TemplateModule, CustomField } from '$lib/types/models';

export interface TemplatePageCreateInput {
  slug: string;
  name: string;
  order?: number;
  modules?: TemplateModuleCreateInput[];
}

export interface TemplateModuleCreateInput {
  module_type: string;
  order?: number;
  config_json?: string | null;
}
```

Add methods to `customizationApi`:

```typescript
// Pages
addPage(vaultId: string, templateId: string, data: TemplatePageCreateInput) {
  return api.post<TemplatePage>(`/vaults/${vaultId}/templates/${templateId}/pages`, data);
},

updatePage(vaultId: string, pageId: string, data: Partial<TemplatePageCreateInput>) {
  return api.patch<TemplatePage>(`/vaults/${vaultId}/templates/pages/${pageId}`, data);
},

deletePage(vaultId: string, pageId: string) {
  return api.del(`/vaults/${vaultId}/templates/pages/${pageId}`);
},

// Modules
addModule(vaultId: string, pageId: string, data: TemplateModuleCreateInput) {
  return api.post<TemplateModule>(`/vaults/${vaultId}/templates/pages/${pageId}/modules`, data);
},

updateModule(vaultId: string, moduleId: string, data: Partial<TemplateModuleCreateInput>) {
  return api.patch<TemplateModule>(`/vaults/${vaultId}/templates/modules/${moduleId}`, data);
},

deleteModule(vaultId: string, moduleId: string) {
  return api.del(`/vaults/${vaultId}/templates/modules/${moduleId}`);
},
```

**Step 2: Add custom field value types and API methods**

Also add to `customizationApi` (needed for Task 12):

```typescript
// Custom field values
getFieldValues(vaultId: string, entityType: string, entityId: string) {
  return api.get<CustomFieldValue[]>(`/vaults/${vaultId}/custom-fields/values/${entityType}/${entityId}`);
},

setFieldValue(vaultId: string, data: { definition_id: string; entity_type: string; entity_id: string; value_json: string }) {
  return api.put<CustomFieldValue>(`/vaults/${vaultId}/custom-fields/values`, data);
},

deleteFieldValue(vaultId: string, valueId: string) {
  return api.del(`/vaults/${vaultId}/custom-fields/values/${valueId}`);
},
```

Add `CustomFieldValue` type to `frontend/src/lib/types/models.ts`:

```typescript
export interface CustomFieldValue {
  id: string;
  vault_id: string;
  definition_id: string;
  entity_type: string;
  entity_id: string;
  value_json: string;
  created_at: string;
  updated_at: string;
}
```

**Step 3: Commit**

```bash
git add frontend/src/lib/api/customization.ts frontend/src/lib/types/models.ts
git commit -m "feat(frontend): API client for template pages/modules and custom field values"
```

---

## Task 11: Template pages/modules — settings UI

**Files:**
- Modify: `frontend/src/routes/(app)/vaults/[vaultId=uuid]/settings/+page.svelte`

**Step 1: Add expand/collapse state**

Add state variables:
```typescript
let expandedTemplateId = $state<string | null>(null);
let expandedPageId = $state<string | null>(null);
let showPageModal = $state(false);
let editPageId = $state<string | null>(null);
let pageForm = $state<{ slug: string; name: string; order: number }>({ slug: '', name: '', order: 0 });
let pageSaving = $state(false);
let showModuleModal = $state(false);
let editModuleId = $state<string | null>(null);
let moduleForm = $state<{ module_type: string; order: number; config_json: string }>({ module_type: '', order: 0, config_json: '' });
let moduleSaving = $state(false);
let pageDeleteId = $state<string | null>(null);
let moduleDeleteId = $state<string | null>(null);
let activeTemplateForPage = $state<string | null>(null);
let activePageForModule = $state<string | null>(null);
```

Import `TemplatePageCreateInput, TemplateModuleCreateInput` from customization API.
Import `ChevronRight, ChevronDown` from lucide.

**Step 2: Add handlers for page/module CRUD**

```typescript
async function toggleTemplate(templateId: string) {
  if (expandedTemplateId === templateId) {
    expandedTemplateId = null;
    return;
  }
  const full = await customizationApi.getTemplate(vaultId, templateId);
  templates = templates.map((t) => (t.id === full.id ? full : t));
  expandedTemplateId = templateId;
}

function openPageCreate(templateId: string) {
  activeTemplateForPage = templateId;
  editPageId = null;
  const t = templates.find((t) => t.id === templateId);
  pageForm = { slug: '', name: '', order: (t?.pages?.length ?? 0) + 1 };
  showPageModal = true;
}

function openPageEdit(p: TemplatePage) {
  editPageId = p.id;
  pageForm = { slug: p.slug, name: p.name, order: p.order };
  showPageModal = true;
}

async function handlePageSave(e: Event) {
  e.preventDefault();
  pageSaving = true;
  try {
    if (editPageId) {
      await customizationApi.updatePage(vaultId, editPageId, pageForm);
    } else if (activeTemplateForPage) {
      await customizationApi.addPage(vaultId, activeTemplateForPage, pageForm);
    }
    showPageModal = false;
    if (expandedTemplateId) await toggleTemplate(expandedTemplateId);
    expandedTemplateId = activeTemplateForPage;
  } finally {
    pageSaving = false;
  }
}

async function handlePageDelete(pageId: string) {
  await customizationApi.deletePage(vaultId, pageId);
  pageDeleteId = null;
  if (expandedTemplateId) {
    const full = await customizationApi.getTemplate(vaultId, expandedTemplateId);
    templates = templates.map((t) => (t.id === full.id ? full : t));
  }
}

function openModuleCreate(pageId: string) {
  activePageForModule = pageId;
  editModuleId = null;
  moduleForm = { module_type: '', order: 0, config_json: '' };
  showModuleModal = true;
}

function openModuleEdit(m: TemplateModule) {
  editModuleId = m.id;
  moduleForm = { module_type: m.module_type, order: m.order, config_json: m.config_json ?? '' };
  showModuleModal = true;
}

async function handleModuleSave(e: Event) {
  e.preventDefault();
  moduleSaving = true;
  try {
    if (editModuleId) {
      await customizationApi.updateModule(vaultId, editModuleId, moduleForm);
    } else if (activePageForModule) {
      await customizationApi.addModule(vaultId, activePageForModule, moduleForm);
    }
    showModuleModal = false;
    if (expandedTemplateId) {
      const full = await customizationApi.getTemplate(vaultId, expandedTemplateId);
      templates = templates.map((t) => (t.id === full.id ? full : t));
    }
  } finally {
    moduleSaving = false;
  }
}

async function handleModuleDelete(moduleId: string) {
  await customizationApi.deleteModule(vaultId, moduleId);
  moduleDeleteId = null;
  if (expandedTemplateId) {
    const full = await customizationApi.getTemplate(vaultId, expandedTemplateId);
    templates = templates.map((t) => (t.id === full.id ? full : t));
  }
}
```

Import `TemplatePage, TemplateModule` types.

**Step 3: Replace templates list with expandable UI**

Replace the templates list (lines 639-656) with expandable rows:

```svelte
<div class="space-y-2">
  {#each templates as t (t.id)}
    <div class="rounded-lg border border-neutral-800 bg-neutral-950">
      <div class="group flex items-center justify-between px-3 py-2">
        <button onclick={() => toggleTemplate(t.id)} class="flex items-center gap-2 text-sm font-medium text-white">
          {#if expandedTemplateId === t.id}
            <ChevronDown size={14} />
          {:else}
            <ChevronRight size={14} />
          {/if}
          {t.name}
        </button>
        <div class="flex items-center gap-2">
          {#if templateDeleteId === t.id}
            <span class="text-xs text-red-400">Delete?</span>
            <Button size="sm" variant="danger" onclick={() => handleTemplateDelete(t.id)}>Yes</Button>
            <Button size="sm" variant="ghost" onclick={() => (templateDeleteId = null)}>No</Button>
          {:else}
            <button onclick={() => openTemplateEdit(t)} class="text-neutral-600 opacity-0 transition hover:text-white group-hover:opacity-100"><Pencil size={14} /></button>
            <button onclick={() => (templateDeleteId = t.id)} class="text-neutral-600 opacity-0 transition hover:text-red-400 group-hover:opacity-100"><Trash2 size={14} /></button>
          {/if}
        </div>
      </div>

      {#if expandedTemplateId === t.id}
        <div class="border-t border-neutral-800 px-3 py-2">
          <div class="mb-2 flex items-center justify-between">
            <span class="text-xs font-medium uppercase text-neutral-500">Pages</span>
            <Button size="sm" variant="ghost" onclick={() => openPageCreate(t.id)}>+ Page</Button>
          </div>
          {#if t.pages && t.pages.length > 0}
            <div class="space-y-1 pl-4">
              {#each t.pages.sort((a, b) => a.order - b.order) as p (p.id)}
                <div class="rounded border border-neutral-800 bg-neutral-900">
                  <div class="group flex items-center justify-between px-2 py-1.5">
                    <button onclick={() => (expandedPageId = expandedPageId === p.id ? null : p.id)} class="flex items-center gap-2 text-xs font-medium text-neutral-300">
                      {#if expandedPageId === p.id}
                        <ChevronDown size={12} />
                      {:else}
                        <ChevronRight size={12} />
                      {/if}
                      {p.name} <span class="text-neutral-600">({p.slug})</span>
                    </button>
                    <div class="flex items-center gap-1">
                      {#if pageDeleteId === p.id}
                        <Button size="sm" variant="danger" onclick={() => handlePageDelete(p.id)}>Del</Button>
                        <Button size="sm" variant="ghost" onclick={() => (pageDeleteId = null)}>No</Button>
                      {:else}
                        <button onclick={() => openPageEdit(p)} class="text-neutral-600 opacity-0 transition hover:text-white group-hover:opacity-100"><Pencil size={12} /></button>
                        <button onclick={() => (pageDeleteId = p.id)} class="text-neutral-600 opacity-0 transition hover:text-red-400 group-hover:opacity-100"><Trash2 size={12} /></button>
                      {/if}
                    </div>
                  </div>

                  {#if expandedPageId === p.id}
                    <div class="border-t border-neutral-800 px-2 py-1.5">
                      <div class="mb-1 flex items-center justify-between">
                        <span class="text-xs text-neutral-600">Modules</span>
                        <Button size="sm" variant="ghost" onclick={() => openModuleCreate(p.id)}>+ Module</Button>
                      </div>
                      {#if p.modules && p.modules.length > 0}
                        <div class="space-y-1 pl-3">
                          {#each p.modules.sort((a, b) => a.order - b.order) as m (m.id)}
                            <div class="group flex items-center justify-between rounded bg-neutral-950 px-2 py-1 text-xs text-neutral-400">
                              <span>{m.module_type} (order: {m.order})</span>
                              <div class="flex items-center gap-1">
                                {#if moduleDeleteId === m.id}
                                  <Button size="sm" variant="danger" onclick={() => handleModuleDelete(m.id)}>Del</Button>
                                  <Button size="sm" variant="ghost" onclick={() => (moduleDeleteId = null)}>No</Button>
                                {:else}
                                  <button onclick={() => openModuleEdit(m)} class="text-neutral-600 opacity-0 transition hover:text-white group-hover:opacity-100"><Pencil size={10} /></button>
                                  <button onclick={() => (moduleDeleteId = m.id)} class="text-neutral-600 opacity-0 transition hover:text-red-400 group-hover:opacity-100"><Trash2 size={10} /></button>
                                {/if}
                              </div>
                            </div>
                          {/each}
                        </div>
                      {:else}
                        <p class="pl-3 text-xs text-neutral-600">No modules</p>
                      {/if}
                    </div>
                  {/if}
                </div>
              {/each}
            </div>
          {:else}
            <p class="pl-4 text-xs text-neutral-600">No pages</p>
          {/if}
        </div>
      {/if}
    </div>
  {/each}
</div>
```

Add page modal after template modal:
```svelte
{#if showPageModal}
  <Modal title={editPageId ? 'Edit Page' : 'New Page'} onclose={() => (showPageModal = false)}>
    <form onsubmit={handlePageSave} class="space-y-4">
      <Input label="Name" bind:value={pageForm.name} required />
      <Input label="Slug" bind:value={pageForm.slug} required />
      <Input label="Order" type="number" bind:value={pageForm.order} />
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (showPageModal = false)}>Cancel</Button>
        <Button type="submit" loading={pageSaving}>Save</Button>
      </div>
    </form>
  </Modal>
{/if}

{#if showModuleModal}
  <Modal title={editModuleId ? 'Edit Module' : 'New Module'} onclose={() => (showModuleModal = false)}>
    <form onsubmit={handleModuleSave} class="space-y-4">
      <Input label="Module type" bind:value={moduleForm.module_type} required />
      <Input label="Order" type="number" bind:value={moduleForm.order} />
      <Input label="Config (JSON)" bind:value={moduleForm.config_json} />
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (showModuleModal = false)}>Cancel</Button>
        <Button type="submit" loading={moduleSaving}>Save</Button>
      </div>
    </form>
  </Modal>
{/if}
```

**Step 4: Verify manually**

Navigate to settings > Templates, expand a template, add pages, add modules, edit, delete.

**Step 5: Commit**

```bash
git add frontend/src/routes/\(app\)/vaults/\[vaultId=uuid\]/settings/+page.svelte
git commit -m "feat(frontend): template pages/modules inline editing in settings"
```

---

## Task 12: Custom fields on entities — component

**Files:**
- Create: `frontend/src/lib/components/customization/CustomFieldsSection.svelte`

**Step 1: Create reusable CustomFieldsSection component**

```svelte
<script lang="ts">
  import { customizationApi } from '$api/customization';
  import type { CustomField, CustomFieldValue } from '$lib/types/models';
  import Button from '$components/ui/Button.svelte';
  import Input from '$components/ui/Input.svelte';
  import Spinner from '$components/ui/Spinner.svelte';
  import { Check, X } from 'lucide-svelte';

  let { vaultId, entityType, entityId }: { vaultId: string; entityType: string; entityId: string } = $props();

  let definitions = $state<CustomField[]>([]);
  let values = $state<CustomFieldValue[]>([]);
  let loading = $state(true);
  let editingFieldId = $state<string | null>(null);
  let editValue = $state('');
  let saving = $state(false);

  $effect(() => {
    load();
  });

  async function load() {
    loading = true;
    const [defResult, vals] = await Promise.all([
      customizationApi.listCustomFields(vaultId, { scope: entityType, limit: 100 }),
      customizationApi.getFieldValues(vaultId, entityType, entityId)
    ]);
    definitions = defResult.items;
    values = vals;
    loading = false;
  }

  function getValueForField(defId: string): CustomFieldValue | undefined {
    return values.find((v) => v.definition_id === defId);
  }

  function displayValue(def: CustomField, val: CustomFieldValue | undefined): string {
    if (!val) return '—';
    try {
      const parsed = JSON.parse(val.value_json);
      if (def.data_type === 'boolean') return parsed ? 'Yes' : 'No';
      if (def.data_type === 'date') return new Date(parsed).toLocaleDateString();
      return String(parsed);
    } catch {
      return val.value_json;
    }
  }

  function startEdit(def: CustomField) {
    const val = getValueForField(def.id);
    if (val) {
      try {
        const parsed = JSON.parse(val.value_json);
        editValue = String(parsed);
      } catch {
        editValue = val.value_json;
      }
    } else {
      editValue = def.data_type === 'boolean' ? 'false' : '';
    }
    editingFieldId = def.id;
  }

  async function saveField(defId: string, dataType: string) {
    saving = true;
    try {
      let jsonValue: string;
      if (dataType === 'number') jsonValue = JSON.stringify(Number(editValue));
      else if (dataType === 'boolean') jsonValue = JSON.stringify(editValue === 'true');
      else jsonValue = JSON.stringify(editValue);

      const result = await customizationApi.setFieldValue(vaultId, {
        definition_id: defId,
        entity_type: entityType,
        entity_id: entityId,
        value_json: jsonValue
      });
      values = values.some((v) => v.definition_id === defId)
        ? values.map((v) => (v.definition_id === defId ? result : v))
        : [...values, result];
      editingFieldId = null;
    } finally {
      saving = false;
    }
  }
</script>

{#if loading}
  <div class="flex justify-center py-4"><Spinner /></div>
{:else if definitions.length === 0}
  <!-- no custom fields defined for this entity type -->
{:else}
  <section class="space-y-3 rounded-xl border border-neutral-800 bg-neutral-900 p-4">
    <h3 class="text-sm font-semibold text-neutral-400">Custom Fields</h3>
    <div class="space-y-2">
      {#each definitions as def (def.id)}
        {@const val = getValueForField(def.id)}
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm text-neutral-400">{def.name}</span>
          {#if editingFieldId === def.id}
            <div class="flex items-center gap-2">
              {#if def.data_type === 'boolean'}
                <select bind:value={editValue} class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-sm text-white outline-none">
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              {:else if def.data_type === 'date'}
                <input type="date" bind:value={editValue} class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-sm text-white outline-none" />
              {:else if def.data_type === 'number'}
                <input type="number" bind:value={editValue} class="w-24 rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-sm text-white outline-none" />
              {:else if def.data_type === 'select'}
                {@const options = (() => { try { return JSON.parse(def.config_json ?? '[]'); } catch { return []; } })()}
                <select bind:value={editValue} class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-sm text-white outline-none">
                  <option value="">—</option>
                  {#each options as opt}
                    <option value={opt}>{opt}</option>
                  {/each}
                </select>
              {:else}
                <input type="text" bind:value={editValue} class="w-40 rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-sm text-white outline-none" />
              {/if}
              <button onclick={() => saveField(def.id, def.data_type)} disabled={saving} class="text-green-400 hover:text-green-300">
                <Check size={14} />
              </button>
              <button onclick={() => (editingFieldId = null)} class="text-neutral-500 hover:text-white">
                <X size={14} />
              </button>
            </div>
          {:else}
            <button onclick={() => startEdit(def)} class="text-sm text-white hover:text-brand-400">
              {displayValue(def, val)}
            </button>
          {/if}
        </div>
      {/each}
    </div>
  </section>
{/if}
```

**Step 2: Commit**

```bash
git add frontend/src/lib/components/customization/CustomFieldsSection.svelte
git commit -m "feat(frontend): reusable CustomFieldsSection component"
```

---

## Task 13: Custom fields — add to detail pages

**Files:**
- Modify: `frontend/src/routes/(app)/vaults/[vaultId=uuid]/contacts/[contactId=uuid]/+page.svelte`
- Modify: `frontend/src/routes/(app)/vaults/[vaultId=uuid]/activities/[activityId=uuid]/+page.svelte`
- Modify: `frontend/src/routes/(app)/vaults/[vaultId=uuid]/tasks/[taskId=uuid]/+page.svelte`

**Step 1: Add to contact detail**

Import and add section to overview tab, after existing sections:

```svelte
<script>
  import CustomFieldsSection from '$components/customization/CustomFieldsSection.svelte';
</script>

<!-- In the overview tab section -->
<CustomFieldsSection {vaultId} entityType="contact" entityId={contactId} />
```

**Step 2: Add to activity detail**

Same pattern with `entityType="activity"`.

**Step 3: Add to task detail**

Same pattern with `entityType="task"`.

**Step 4: Verify manually**

Create a custom field for contacts in settings, then visit a contact detail page. Verify the field appears and can be edited.

**Step 5: Commit**

```bash
git add frontend/src/routes/\(app\)/vaults/\[vaultId=uuid\]/contacts/\[contactId=uuid\]/+page.svelte \
       frontend/src/routes/\(app\)/vaults/\[vaultId=uuid\]/activities/\[activityId=uuid\]/+page.svelte \
       frontend/src/routes/\(app\)/vaults/\[vaultId=uuid\]/tasks/\[taskId=uuid\]/+page.svelte
git commit -m "feat(frontend): custom fields section on contact/activity/task detail pages"
```

---

## Task 14: Multi-vault — backend rename

**Files:**
- Modify: `backend/src/clara/auth/vault_api.py`
- Modify: `backend/tests/test_vaults.py` (or create)

**Step 1: Write the failing test**

```python
async def test_rename_vault(authenticated_client: AsyncClient, vault: Vault):
    resp = await authenticated_client.patch(
        f"/api/v1/vaults/{vault.id}",
        json={"name": "Renamed Vault"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Vault"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest backend/tests/test_vaults.py::test_rename_vault -v`
Expected: FAIL — 405 Method Not Allowed

**Step 3: Add VaultUpdate schema and PATCH endpoint**

In `backend/src/clara/auth/vault_api.py`, add schema after `VaultCreate`:

```python
class VaultUpdate(BaseModel):
    name: str | None = None
```

Add endpoint after `get_vault`:

```python
@router.patch("/{vault_id}", response_model=VaultRead)
async def update_vault(
    vault_id: uuid.UUID,
    body: VaultUpdate,
    db: Db,
    _: VaultMembership = require_role("owner"),
) -> VaultRead:
    vault = await db.get(Vault, vault_id)
    if vault is None:
        raise HTTPException(status_code=404, detail="Vault not found")
    if body.name is not None:
        vault.name = body.name
    await db.flush()
    return VaultRead.model_validate(vault)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest backend/tests/test_vaults.py::test_rename_vault -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/clara/auth/vault_api.py backend/tests/test_vaults.py
git commit -m "feat(backend): add vault rename endpoint"
```

---

## Task 15: Multi-vault — frontend page

**Files:**
- Create: `frontend/src/routes/(app)/vaults/+page.svelte`
- Modify: `frontend/src/lib/api/vaults.ts`
- Modify: `frontend/src/routes/+page.svelte`

**Step 1: Add rename method to vaults API**

In `frontend/src/lib/api/vaults.ts`, add after `del`:

```typescript
rename(vaultId: string, name: string) {
  return api.patch<Vault>(`/vaults/${vaultId}`, { name });
},
```

**Step 2: Create vaults page**

Create `frontend/src/routes/(app)/vaults/+page.svelte`:

```svelte
<script lang="ts">
  import { goto } from '$app/navigation';
  import { vaultsApi } from '$api/vaults';
  import Button from '$components/ui/Button.svelte';
  import Input from '$components/ui/Input.svelte';
  import Modal from '$components/ui/Modal.svelte';
  import Spinner from '$components/ui/Spinner.svelte';
  import { Vault as VaultIcon, Plus, Pencil, Trash2 } from 'lucide-svelte';
  import type { Vault } from '$lib/types/models';

  let vaults = $state<Vault[]>([]);
  let loading = $state(true);

  // Create
  let showCreate = $state(false);
  let createName = $state('');
  let creating = $state(false);

  // Edit
  let editId = $state<string | null>(null);
  let editName = $state('');
  let saving = $state(false);

  // Delete
  let deleteId = $state<string | null>(null);
  let deleting = $state(false);

  $effect(() => {
    loadVaults();
  });

  async function loadVaults() {
    loading = true;
    vaults = await vaultsApi.list();
    loading = false;
  }

  async function handleCreate(e: Event) {
    e.preventDefault();
    creating = true;
    try {
      await vaultsApi.create({ name: createName });
      showCreate = false;
      createName = '';
      await loadVaults();
    } finally {
      creating = false;
    }
  }

  function startEdit(v: Vault) {
    editId = v.id;
    editName = v.name;
  }

  async function handleRename(id: string) {
    saving = true;
    try {
      await vaultsApi.rename(id, editName);
      editId = null;
      await loadVaults();
    } finally {
      saving = false;
    }
  }

  async function handleDelete(id: string) {
    deleting = true;
    try {
      await vaultsApi.del(id);
      deleteId = null;
      await loadVaults();
    } finally {
      deleting = false;
    }
  }

  function selectVault(v: Vault) {
    goto(`/vaults/${v.id}/dashboard`);
  }
</script>

<svelte:head><title>Vaults</title></svelte:head>

<div class="mx-auto max-w-2xl space-y-6 p-8">
  <div class="flex items-center justify-between">
    <h1 class="text-2xl font-semibold text-white">Your Vaults</h1>
    <Button onclick={() => (showCreate = true)}>
      <Plus size={16} />
      New Vault
    </Button>
  </div>

  {#if loading}
    <div class="flex justify-center py-12"><Spinner /></div>
  {:else if vaults.length === 0}
    <div class="flex flex-col items-center gap-3 py-16 text-neutral-500">
      <VaultIcon size={40} strokeWidth={1.5} />
      <p class="text-sm">No vaults yet. Create one to get started.</p>
    </div>
  {:else}
    <div class="space-y-2">
      {#each vaults as v (v.id)}
        <div class="group flex items-center gap-4 rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-3 transition hover:border-neutral-700">
          <button onclick={() => selectVault(v)} class="min-w-0 flex-1 text-left">
            {#if editId === v.id}
              <!-- stop propagation -->
            {:else}
              <p class="text-sm font-medium text-white">{v.name}</p>
              <p class="text-xs text-neutral-500">Created {new Date(v.created_at).toLocaleDateString()}</p>
            {/if}
          </button>

          {#if editId === v.id}
            <div class="flex flex-1 items-center gap-2">
              <input
                type="text"
                bind:value={editName}
                onkeydown={(e) => { if (e.key === 'Enter') handleRename(v.id); if (e.key === 'Escape') editId = null; }}
                class="flex-1 rounded border border-brand-500 bg-neutral-800 px-2 py-1 text-sm text-white outline-none"
                autofocus
              />
              <Button size="sm" loading={saving} onclick={() => handleRename(v.id)}>Save</Button>
              <Button size="sm" variant="ghost" onclick={() => (editId = null)}>Cancel</Button>
            </div>
          {:else}
            <div class="flex items-center gap-1">
              {#if deleteId === v.id}
                <span class="text-xs text-red-400">Delete vault?</span>
                <Button size="sm" variant="danger" loading={deleting} onclick={() => handleDelete(v.id)}>Yes</Button>
                <Button size="sm" variant="ghost" onclick={() => (deleteId = null)}>No</Button>
              {:else}
                <button onclick={() => startEdit(v)} class="rounded p-1 text-neutral-600 opacity-0 transition hover:text-white group-hover:opacity-100">
                  <Pencil size={14} />
                </button>
                <button onclick={() => (deleteId = v.id)} class="rounded p-1 text-neutral-600 opacity-0 transition hover:text-red-400 group-hover:opacity-100">
                  <Trash2 size={14} />
                </button>
              {/if}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

{#if showCreate}
  <Modal title="Create Vault" onclose={() => (showCreate = false)}>
    <form onsubmit={handleCreate} class="space-y-4">
      <Input label="Vault name" bind:value={createName} required />
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (showCreate = false)}>Cancel</Button>
        <Button type="submit" loading={creating}>Create</Button>
      </div>
    </form>
  </Modal>
{/if}
```

**Step 3: Update root redirect**

In `frontend/src/routes/+page.svelte`, change the redirect logic. Replace:
```typescript
const vaults = await api.get<Vault[]>('/vaults');
if (vaults.length > 0) {
  goto(`/vaults/${vaults[0].id}/dashboard`);
} else {
  error = 'No vaults found. Create one first.';
}
```

With:
```typescript
goto('/vaults');
```

Remove the vault-related try/catch and unused import.

**Step 4: Verify manually**

Navigate to /, should redirect to /vaults. Create, rename, delete vaults. Click vault to enter dashboard.

**Step 5: Commit**

```bash
git add frontend/src/routes/\(app\)/vaults/+page.svelte frontend/src/lib/api/vaults.ts frontend/src/routes/+page.svelte
git commit -m "feat(frontend): multi-vault page with create/rename/delete"
```

---

## Task 16: Final verification

**Step 1: Run backend tests**

Run: `uv run pytest backend/tests/ -v`
Expected: All pass

**Step 2: Run frontend type check**

Run: `cd frontend && pnpm check`
Expected: No errors

**Step 3: Manual smoke test each feature**

1. Files page: click filename → rename
2. Notifications: mark some read → click "Clear read"
3. Contact detail: click avatar → upload photo
4. /notes page: create, filter, edit, delete
5. Settings > Activity Types: add, edit, delete
6. Settings > Templates: expand → pages → modules
7. Contact detail: custom fields section
8. /vaults page: create, rename, delete, select

**Step 4: Commit any fixes**

```bash
git add -A && git commit -m "fix: smoke test fixes"
```
