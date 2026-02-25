<script lang="ts">
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { journalApi } from '$api/journal';
  import type { JournalEntryCreateInput } from '$api/journal';
  import DataList from '$components/data/DataList.svelte';
  import Button from '$components/ui/Button.svelte';
  import Modal from '$components/ui/Modal.svelte';
  import Input from '$components/ui/Input.svelte';
  import Textarea from '$components/ui/Textarea.svelte';
  import { Plus, BookOpen } from 'lucide-svelte';
  import type { JournalEntry } from '$lib/types/models';

  const vaultId = $derived(page.params.vaultId!);

  let showCreate = $state(false);
  let createForm = $state<JournalEntryCreateInput>({
    entry_date: new Date().toISOString().split('T')[0],
    title: '',
    body_markdown: '',
    mood: null
  });
  let creating = $state(false);

  async function loadEntries(params: { offset: number; limit: number; search: string; filter: string | null }) {
    return journalApi.list(vaultId, {
      search: params.search || undefined,
      offset: params.offset,
      limit: params.limit
    });
  }

  async function handleCreate(e: SubmitEvent) {
    e.preventDefault();
    creating = true;
    try {
      const entry = await journalApi.create(vaultId, createForm);
      showCreate = false;
      createForm = { entry_date: new Date().toISOString().split('T')[0], title: '', body_markdown: '', mood: null };
      goto(`/vaults/${vaultId}/journal/${entry.id}`);
    } finally {
      creating = false;
    }
  }

  const moodEmojis: Record<number, string> = { 1: '\u{1F622}', 2: '\u{1F641}', 3: '\u{1F610}', 4: '\u{1F642}', 5: '\u{1F604}' };

  function formatDate(d: string): string {
    return new Date(d).toLocaleDateString(undefined, { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });
  }
</script>

<svelte:head><title>Journal</title></svelte:head>

<div class="space-y-4">
  <DataList
    load={loadEntries}
    searchPlaceholder="Search journal..."
    emptyIcon={BookOpen}
    emptyTitle="No journal entries yet"
    emptyDescription="Write about your day"
  >
    {#snippet header()}
      <Button onclick={() => (showCreate = true)}><Plus size={16} /> New Entry</Button>
    {/snippet}
    {#snippet row(item: JournalEntry)}
      <a href="/vaults/{vaultId}/journal/{item.id}" class="block px-4 py-3 transition hover:bg-neutral-800/50">
        <div class="flex items-center gap-2">
          <BookOpen size={16} class="text-neutral-400" />
          <span class="text-xs text-neutral-500">{formatDate(item.entry_date)}</span>
          {#if item.mood && moodEmojis[item.mood]}<span class="text-sm">{moodEmojis[item.mood]}</span>{/if}
        </div>
        <h3 class="mt-1 truncate text-sm font-medium text-white">{item.title || 'Untitled'}</h3>
        {#if item.body_markdown}<p class="mt-1 line-clamp-2 text-xs text-neutral-500">{item.body_markdown}</p>{/if}
      </a>
    {/snippet}
  </DataList>
</div>

{#if showCreate}
  <Modal title="New Journal Entry" onclose={() => (showCreate = false)}>
    <form onsubmit={handleCreate} class="space-y-4">
      <Input label="Date" type="date" bind:value={createForm.entry_date} required />
      <Input label="Title" bind:value={createForm.title} />
      <div>
        <label class="mb-1 block text-sm font-medium text-neutral-300">Mood</label>
        <div class="flex gap-2">
          {#each [1, 2, 3, 4, 5] as mood}
            <button
              type="button"
              onclick={() => (createForm.mood = createForm.mood === mood ? null : mood)}
              class="rounded-lg p-2 text-xl transition {createForm.mood === mood ? 'bg-brand-500/20 ring-2 ring-brand-500' : 'hover:bg-neutral-800'}"
            >
              {moodEmojis[mood]}
            </button>
          {/each}
        </div>
      </div>
      <Textarea label="Content" bind:value={createForm.body_markdown} rows={6} placeholder="Write about your day..." />
      <div class="flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (showCreate = false)}>Cancel</Button>
        <Button type="submit" loading={creating}>Create</Button>
      </div>
    </form>
  </Modal>
{/if}
