<script lang="ts">
  import { page } from '$app/state';
  import { goto } from '$app/navigation';
  import { journalApi } from '$api/journal';
  import type { JournalEntryUpdateInput } from '$api/journal';
  import Spinner from '$components/ui/Spinner.svelte';
  import Button from '$components/ui/Button.svelte';
  import Input from '$components/ui/Input.svelte';
  import Modal from '$components/ui/Modal.svelte';
  import { ArrowLeft, Pencil, Trash2, Save, X } from 'lucide-svelte';
  import type { JournalEntry } from '$lib/types/models';

  const vaultId = $derived(page.params.vaultId!);
  const entryId = $derived(page.params.entryId!);

  let entry = $state<JournalEntry | null>(null);
  let loading = $state(true);
  let loadError = $state('');
  let editing = $state(false);
  let saving = $state(false);
  let showDelete = $state(false);
  let deleting = $state(false);
  let editForm = $state<JournalEntryUpdateInput>({});

  const moodEmojis: Record<number, string> = { 1: '\u{1F622}', 2: '\u{1F641}', 3: '\u{1F610}', 4: '\u{1F642}', 5: '\u{1F604}' };

  $effect(() => {
    loading = true;
    loadError = '';
    (async () => {
      try {
        entry = await journalApi.get(vaultId, entryId);
      } catch (e) {
        loadError = e instanceof Error ? e.message : 'Failed to load entry';
      } finally {
        loading = false;
      }
    })();
  });

  function startEdit() {
    if (!entry) return;
    editForm = { entry_date: entry.entry_date, title: entry.title, body_markdown: entry.body_markdown, mood: entry.mood };
    editing = true;
  }

  async function handleSave() {
    saving = true;
    try { entry = await journalApi.update(vaultId, entryId, editForm); editing = false; } finally { saving = false; }
  }

  async function handleDelete() {
    deleting = true;
    try { await journalApi.del(vaultId, entryId); goto(`/vaults/${vaultId}/journal`); } finally { deleting = false; }
  }

  function formatDate(d: string): string {
    return new Date(d).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  }
</script>

<svelte:head><title>{entry ? entry.title || formatDate(entry.entry_date) : 'Journal Entry'}</title></svelte:head>

{#if loading}
  <div class="flex justify-center py-12"><Spinner /></div>
{:else if loadError}
  <div class="flex flex-col items-center justify-center gap-4 py-20">
    <p class="text-red-400">{loadError}</p>
    <a href="/vaults/{vaultId}/journal" class="text-sm text-brand-400 hover:underline">Go back</a>
  </div>
{:else if entry}
  <div class="mx-auto max-w-2xl space-y-6">
    <div class="flex items-center justify-between">
      <a href="/vaults/{vaultId}/journal" class="text-neutral-400 hover:text-neutral-300"><ArrowLeft size={20} /></a>
      <div class="flex gap-2">
        {#if editing}
          <Button variant="ghost" size="sm" onclick={() => (editing = false)}><X size={16} /> Cancel</Button>
          <Button size="sm" loading={saving} onclick={handleSave}><Save size={16} /> Save</Button>
        {:else}
          <Button variant="ghost" size="sm" onclick={startEdit}><Pencil size={16} /></Button>
          <Button variant="ghost" size="sm" onclick={() => (showDelete = true)}><Trash2 size={16} class="text-red-400" /></Button>
        {/if}
      </div>
    </div>

    {#if editing}
      <div class="space-y-4">
        <Input label="Date" type="date" bind:value={editForm.entry_date} />
        <Input label="Title" bind:value={editForm.title} />
        <div>
          <label class="mb-1 block text-sm font-medium text-neutral-300">Mood</label>
          <div class="flex gap-2">
            {#each [1, 2, 3, 4, 5] as mood}
              <button type="button" onclick={() => (editForm.mood = editForm.mood === mood ? null : mood)}
                class="rounded-lg p-2 text-xl transition {editForm.mood === mood ? 'bg-brand-500/20 ring-2 ring-brand-500' : 'hover:bg-neutral-800'}">
                {moodEmojis[mood]}
              </button>
            {/each}
          </div>
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-neutral-300">Content</label>
          <textarea bind:value={editForm.body_markdown} rows="12" class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"></textarea>
        </div>
      </div>
    {:else}
      <div class="space-y-4">
        <div class="flex items-center gap-3">
          <span class="text-sm text-neutral-500">{formatDate(entry.entry_date)}</span>
          {#if entry.mood && moodEmojis[entry.mood]}<span class="text-lg">{moodEmojis[entry.mood]}</span>{/if}
        </div>
        <h1 class="text-2xl font-semibold text-white">{entry.title || 'Untitled'}</h1>
        <div class="whitespace-pre-wrap text-sm leading-relaxed text-neutral-300">{entry.body_markdown}</div>
      </div>
    {/if}
  </div>

  {#if showDelete}
    <Modal title="Delete Entry" onclose={() => (showDelete = false)}>
      <p class="text-sm text-neutral-400">Delete this journal entry? This cannot be undone.</p>
      <div class="mt-4 flex justify-end gap-3">
        <Button variant="ghost" onclick={() => (showDelete = false)}>Cancel</Button>
        <Button variant="danger" loading={deleting} onclick={handleDelete}>Delete</Button>
      </div>
    </Modal>
  {/if}
{/if}
