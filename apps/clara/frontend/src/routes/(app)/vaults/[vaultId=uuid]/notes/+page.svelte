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

  let dataList: DataList<Note>;
  let contacts = $state<Contact[]>([]);
  let filterContactId = $state<string>('');

  let showModal = $state(false);
  let editingNote = $state<Note | null>(null);
  let form = $state<NoteCreateInput>({ title: '', body_markdown: '', contact_id: null, activity_id: null });
  let saving = $state(false);
  let formError = $state('');

  let deleteId = $state<string | null>(null);
  let deleting = $state(false);

  $effect(() => {
    contactsApi.list(vaultId, { limit: 200 }).then((r) => (contacts = r.items));
  });

  async function loadNotes(params: { offset: number; limit: number; search: string; filter: string | null }) {
    return notesApi.list(vaultId, {
      offset: params.offset,
      limit: params.limit,
      q: params.search || undefined,
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

  async function handleSave(e: SubmitEvent) {
    e.preventDefault();
    formError = '';
    saving = true;
    try {
      if (editingNote) {
        await notesApi.update(vaultId, editingNote.id, form as NoteUpdateInput);
      } else {
        await notesApi.create(vaultId, form);
      }
      showModal = false;
      dataList.refresh();
    } catch (err) {
      formError = err instanceof Error ? err.message : 'Something went wrong';
    } finally {
      saving = false;
    }
  }

  async function handleDelete(id: string) {
    deleting = true;
    try {
      await notesApi.del(vaultId, id);
      deleteId = null;
      dataList.refresh();
    } finally {
      deleting = false;
    }
  }

  function contactName(contactId: string | null): string {
    if (!contactId) return '';
    const c = contacts.find((ct) => ct.id === contactId);
    return c ? `${c.first_name} ${c.last_name}` : '';
  }
</script>

<svelte:head><title>Notes</title></svelte:head>

<div class="space-y-4">
  <div class="flex items-center gap-3">
    <select
      bind:value={filterContactId}
      onchange={() => dataList.refresh()}
      class="rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-1.5 text-sm text-white outline-none"
    >
      <option value="">All contacts</option>
      {#each contacts as c (c.id)}
        <option value={c.id}>{c.first_name} {c.last_name}</option>
      {/each}
    </select>
  </div>

    <DataList
      bind:this={dataList}
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
      {#if formError}<p class="text-sm text-red-400">{formError}</p>{/if}
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (showModal = false)}>Cancel</Button>
        <Button type="submit" loading={saving}>Save</Button>
      </div>
    </form>
  </Modal>
{/if}
